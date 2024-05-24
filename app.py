from flask import Flask, render_template, request, redirect, g, session
import sqlite3
from datetime import datetime, timedelta


class DatabaseManager:
    def __init__(self, database):
        self.database = database

    def get_connection(self):
        db = getattr(g, "_database", None)
        if db is None:
            db = g._database = sqlite3.connect(self.database)
        return db

    def close_connection(self, exception):
        db = getattr(g, "_database", None)
        if db is not None:
            db.close()


class Usuario:
    def __init__(self, nombre, apellidos, telefono, username, password, tipo_usuario):
        self.nombre = nombre
        self.apellidos = apellidos
        self.telefono = telefono
        self.username = username
        self.password = password
        self.tipo_usuario = tipo_usuario

    def registrar(self):
        try:
            conn = DatabaseManager("barberia.db").get_connection()
            cursor = conn.cursor()
            cursor.execute(
                f"INSERT INTO {self.tipo_usuario} (nombre, apellidos, telefono, username, password, tipo_usuario_id) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    self.nombre,
                    self.apellidos,
                    self.telefono,
                    self.username,
                    self.password,
                    1 if self.tipo_usuario == "cliente" else 2,
                ),
            )
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise e
        finally:
            conn.close()


class Cliente(Usuario):
    def __init__(self, nombre, apellidos, telefono, username, password):
        super().__init__(
            nombre, apellidos, telefono, username, password, tipo_usuario="cliente"
        )


class Barbero(Usuario):
    def __init__(self, nombre, apellidos, telefono, username, password):
        super().__init__(
            nombre, apellidos, telefono, username, password, tipo_usuario="barbero"
        )


class Cita:
    def __init__(self, cliente_id, barbero_id, servicio_id, fecha_hora):
        self.cliente_id = cliente_id
        self.barbero_id = barbero_id
        self.servicio_id = servicio_id
        self.fecha_hora = fecha_hora

    def agendar(self):
        try:
            conn = DatabaseManager("barberia.db").get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT COUNT(*) FROM cita WHERE barbero = ? AND fecha = ?",
                (self.barbero_id, self.fecha_hora),
            )
            if cursor.fetchone()[0] > 0:
                raise ValueError(
                    "El barbero ya tiene una cita agendada en esa fecha y hora."
                )

            cursor.execute(
                "SELECT COUNT(*) FROM cita WHERE cliente = ? AND fecha = ?",
                (self.cliente_id, self.fecha_hora),
            )
            if cursor.fetchone()[0] > 0:
                raise ValueError(
                    "El cliente ya tiene una cita agendada en esa fecha y hora."
                )

            cursor.execute(
                "INSERT INTO cita (cliente, barbero, servicio, fecha, estado) VALUES (?, ?, ?, ?, ?)",
                (
                    self.cliente_id,
                    self.barbero_id,
                    self.servicio_id,
                    self.fecha_hora,
                    1,
                ),
            )
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise e
        finally:
            conn.close()


class App:
    DATABASE = "barberia.db"

    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = "your_secret_key"
        self.setup_routes()

    def setup_routes(self):
        self.app.route("/")(self.index)
        self.app.route("/registro", methods=["GET", "POST"])(self.registro)
        self.app.route("/login", methods=["GET", "POST"])(self.login)
        self.app.route("/agendar_cita", methods=["GET", "POST"])(self.agendar_cita)
        self.app.route("/ver_cita")(self.ver_cita)
        self.app.route("/mi_cuenta")(self.mi_cuenta)
        self.app.route("/editar_informacion", methods=["POST"])(self.editar_informacion)
        self.app.route("/calendario")(self.calendario)
        self.app.route("/agendar_cita_barbero", methods=["GET", "POST"])(
            self.agendar_cita_barbero
        )
        self.app.route("/mi_cuenta_barbero")(self.mi_cuenta_barbero)
        self.app.route("/editar_informacion_barbero", methods=["POST"])(
            self.editar_informacion_barbero
        )
        self.app.route("/cliente_dashboard", methods=["GET", "POST"])(
            self.cliente_dashboard
        )

        self.app.route("/barbero_dashboard", methods=["GET", "POST"])(
            self.barbero_dashboard
        )
        self.app.teardown_appcontext(self.close_connection)

    def index(self):
        return render_template("index.html")

    def registro(self):
        if request.method == "POST":
            tipo_usuario = request.form.get("tipo_usuario")
            nombre = request.form["nombre"]
            apellidos = request.form["apellidos"]
            telefono = request.form["telefono"]
            username = request.form["username"]
            password = request.form["password"]

            if tipo_usuario == "cliente":
                usuario = Cliente(nombre, apellidos, telefono, username, password)
            elif tipo_usuario == "barbero":
                usuario = Barbero(nombre, apellidos, telefono, username, password)
            else:
                return 'Error: Tipo de usuario no válido. Por favor, seleccione "Barbero" o "Cliente".'

            usuario.registrar()

            return redirect("/")
        else:
            return render_template("registro.html")

    def login(self):
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")

            conn = DatabaseManager(self.DATABASE).get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM cliente WHERE username = ? AND password = ?",
                (username, password),
            )
            cliente = cursor.fetchone()

            if cliente:
                session["cliente_id"] = cliente[0]
                return render_template("cliente_dashboard.html")
            else:
                cursor.execute(
                    "SELECT * FROM barbero WHERE username = ? AND password = ?",
                    (username, password),
                )
                barbero = cursor.fetchone()
                if barbero:
                    session["barbero_id"] = barbero[0]
                    return render_template("barbero_dashboard.html")
                else:
                    return "Credenciales incorrectas. Vuelve a intentarlo."

        return render_template("login.html")

    def agendar_cita(self):
        if request.method == "POST":
            servicio_id = request.form.get("servicio")
            barbero_id = request.form.get("barbero")
            cliente_id = session.get("cliente_id")
            fecha = request.form.get("fecha")
            hora = request.form.get("hora")

            fecha_hora_cita = fecha + " " + hora

            if datetime.strptime(fecha_hora_cita, "%Y-%m-%d %H:%M") < datetime.now():
                return "No se pueden agendar citas en fechas pasadas"

            cita = Cita(cliente_id, barbero_id, servicio_id, fecha_hora_cita)
            try:
                cita.agendar()
            except ValueError as e:
                return str(e)

            return render_template("cliente_dashboard.html")
        else:
            horas_disponibles = []
            hora_inicio = datetime.strptime("09:00", "%H:%M")
            hora_fin = datetime.strptime("19:00", "%H:%M")

            hora_actual = hora_inicio
            while hora_actual <= hora_fin:
                horas_disponibles.append(hora_actual.strftime("%H:%M"))
                hora_actual += timedelta(minutes=30)

            conn = DatabaseManager(self.DATABASE).get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id_servicio, tipo FROM servicio")
            servicios = cursor.fetchall()
            cursor.execute("SELECT id, nombre FROM barbero")
            barberos = cursor.fetchall()
            conn.close()

            return render_template(
                "agendar_cita.html",
                servicios=servicios,
                barberos=barberos,
                horas_disponibles=horas_disponibles,
            )

    def ver_cita(self):
        cliente_id = session.get("cliente_id")
        if cliente_id:
            conn = DatabaseManager(self.DATABASE).get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """SELECT cita.id_cita, cita.fecha, barbero.nombre, servicio.tipo
                FROM cita
                INNER JOIN barbero ON cita.barbero = barbero.id
                INNER JOIN servicio ON cita.servicio = servicio.id_servicio
                WHERE cita.cliente = ?""",
                (cliente_id,),
            )
            citas = cursor.fetchall()
            conn.close()

            return render_template("ver_cita.html", citas=citas)
        else:
            return redirect("/login")

    def mi_cuenta(self):
        cliente_id = session.get("cliente_id")
        if cliente_id:
            conn = DatabaseManager(self.DATABASE).get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cliente WHERE id = ?", (cliente_id,))
            cliente = cursor.fetchone()
            conn.close()

            return render_template("mi_cuenta.html", cliente=cliente)
        else:
            return redirect("/login")

    def editar_informacion(self):
        if request.method == "POST":
            cliente_id = session.get("cliente_id")
            if cliente_id:
                nombre = request.form.get("nombre")
                apellidos = request.form.get("apellidos")
                telefono = request.form.get("telefono")

                try:
                    conn = DatabaseManager(self.DATABASE).get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE cliente SET nombre = ?, apellidos = ?, telefono = ? WHERE id = ?",
                        (nombre, apellidos, telefono, cliente_id),
                    )
                    conn.commit()
                    conn.close()
                    return redirect("/mi_cuenta")
                except sqlite3.Error as e:
                    return str(e)
            else:
                return redirect("/login")
        else:
            return redirect("/")

    def calendario(self):
        barbero_id = session.get("barbero_id")
        if barbero_id:
            conn = DatabaseManager(self.DATABASE).get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """SELECT cita.id_cita, cita.fecha, cliente.nombre, servicio.tipo
                FROM cita
                INNER JOIN cliente ON cita.cliente = cliente.id
                INNER JOIN servicio ON cita.servicio = servicio.id_servicio
                WHERE cita.barbero = ?""",
                (barbero_id,),
            )
            citas = cursor.fetchall()
            conn.close()

            return render_template("calendario.html", citas=citas)
        else:
            return redirect("/")

    def barbero_dashboard(self):
        return render_template("barbero_dashboard.html")

    def agendar_cita_barbero(self):
        if request.method == "POST":
            servicio_id = request.form.get("servicio")
            cliente_id = request.form.get("cliente")
            barbero_id = session.get(
                "barbero_id"
            )  # Obtener el ID del barbero desde la sesión
            fecha = request.form.get("fecha")
            hora = request.form.get("hora")

            fecha_hora_cita = fecha + " " + hora

            if datetime.strptime(fecha_hora_cita, "%Y-%m-%d %H:%M") < datetime.now():
                return "No se pueden agendar citas en fechas pasadas"

            cita = Cita(cliente_id, barbero_id, servicio_id, fecha_hora_cita)
            try:
                cita.agendar()
            except ValueError as e:
                return str(e)

            return redirect("/calendario")
        else:
            horas_disponibles = []
            hora_inicio = datetime.strptime("09:00", "%H:%M")
            hora_fin = datetime.strptime("19:00", "%H:%M")

            hora_actual = hora_inicio
            while hora_actual <= hora_fin:
                horas_disponibles.append(hora_actual.strftime("%H:%M"))
                hora_actual += timedelta(minutes=30)

            conn = DatabaseManager(self.DATABASE).get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id_servicio, tipo FROM servicio")
            servicios = cursor.fetchall()
            cursor.execute("SELECT id, nombre FROM cliente")
            clientes = cursor.fetchall()
            conn.close()

            return render_template(
                "agendar_cita_barbero.html",
                servicios=servicios,
                clientes=clientes,
                horas_disponibles=horas_disponibles,
            )

    def agendar_cita_barbero(self):
        if request.method == "POST":
            servicio_id = request.form.get("servicio")
            cliente_id = request.form.get("cliente")
            barbero_id = session.get(
                "barbero_id"
            )  # Obtener el ID del barbero desde la sesión
            fecha = request.form.get("fecha")
            hora = request.form.get("hora")

            fecha_hora_cita = fecha + " " + hora

            if datetime.strptime(fecha_hora_cita, "%Y-%m-%d %H:%M") < datetime.now():
                return "No se pueden agendar citas en fechas pasadas"

            cita = Cita(cliente_id, barbero_id, servicio_id, fecha_hora_cita)
            try:
                cita.agendar()
            except ValueError as e:
                return str(e)

            return redirect("/calendario")
        else:
            horas_disponibles = []
            hora_inicio = datetime.strptime("09:00", "%H:%M")
            hora_fin = datetime.strptime("19:00", "%H:%M")

            hora_actual = hora_inicio
            while hora_actual <= hora_fin:
                horas_disponibles.append(hora_actual.strftime("%H:%M"))
                hora_actual += timedelta(minutes=30)

            conn = DatabaseManager(self.DATABASE).get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id_servicio, tipo FROM servicio")
            servicios = cursor.fetchall()
            cursor.execute("SELECT id, nombre FROM cliente")
            clientes = cursor.fetchall()
            conn.close()

            return render_template(
                "agendar_cita_barbero.html",
                servicios=servicios,
                clientes=clientes,
                horas_disponibles=horas_disponibles,
            )

    def mi_cuenta_barbero(self):
        barbero_id = session.get("barbero_id")
        if barbero_id:
            conn = DatabaseManager(self.DATABASE).get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM barbero WHERE id = ?", (barbero_id,))
            barbero = cursor.fetchone()
            conn.close()

            return render_template("mi_cuenta_barbero.html", barbero=barbero)
        else:
            return redirect("/login")

    def editar_informacion_barbero(self):
        if request.method == "POST":
            barbero_id = session.get("barbero_id")
            if barbero_id:
                nombre = request.form.get("nombre")
                apellidos = request.form.get("apellidos")
                telefono = request.form.get("telefono")

                try:
                    conn = DatabaseManager(self.DATABASE).get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE barbero SET nombre = ?, apellidos = ?, telefono = ? WHERE id = ?",
                        (nombre, apellidos, telefono, barbero_id),
                    )
                    conn.commit()
                    conn.close()
                    return redirect("/mi_cuenta_barbero")
                except sqlite3.Error as e:
                    return str(e)
            else:
                return redirect("/login")
        else:
            return redirect("/")

    def close_connection(self, exception):
        DatabaseManager(self.DATABASE).close_connection(exception)

    def run(self):
        self.app.run(debug=True)

    def cliente_dashboard(self):
        return render_template("cliente_dashboard.html")

    def barbero_dashboard(self):
        return render_template("barbero_dashboard.html")


if __name__ == "__main__":
    app_instance = App()
    app_instance.run()
