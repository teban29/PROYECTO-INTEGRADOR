from flask import Flask, render_template, request, redirect, url_for, g
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

DATABASE = "barberia.db"


# Función para obtener la conexión a la base de datos
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


# Función para cerrar la conexión a la base de datos al final de la solicitud
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


# Rutas de la aplicación
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        tipo_usuario = request.form["tipo_usuario"]
        nombre = request.form["nombre"]
        apellidos = request.form["apellidos"]
        telefono = request.form["telefono"]
        username = request.form["username"]
        password = request.form["password"]

        # Obtener el tipo_usuario_id correspondiente
        if tipo_usuario == "cliente":
            tipo_usuario_id = 1
        elif tipo_usuario == "barbero":
            tipo_usuario_id = 2
        else:
            # Manejar el caso de error si no se selecciona un tipo válido
            return "Error: Tipo de usuario no válido"

        # Insertar los datos del usuario en la tabla correspondiente
        cursor = get_db().cursor()
        if tipo_usuario_id == 1:
            cursor.execute(
                "INSERT INTO cliente (nombre, apellidos, telefono, username, password, tipo_usuario_id) VALUES (?, ?, ?, ?, ?, ?)",
                (nombre, apellidos, telefono, username, password, tipo_usuario_id),
            )
        elif tipo_usuario_id == 2:
            cursor.execute(
                "INSERT INTO barbero (nombre, apellidos, telefono, username, password, tipo_usuario_id) VALUES (?, ?, ?, ?, ?, ?)",
                (nombre, apellidos, telefono, username, password, tipo_usuario_id),
            )

        get_db().commit()
        return redirect("/")
    else:
        return render_template("registro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        cursor = get_db().cursor()
        cursor.execute(
            "SELECT * FROM cliente WHERE username = ? AND password = ?",
            (username, password),
        )
        cliente = cursor.fetchone()

        if cliente:
            # Iniciar sesión como cliente
            # Aquí podrías redirigir a la página de perfil del cliente
            return render_template("cliente_dashboard.html")
        else:
            cursor.execute(
                "SELECT * FROM barbero WHERE username = ? AND password = ?",
                (username, password),
            )
            barbero = cursor.fetchone()
            if barbero:
                # Iniciar sesión como barbero
                # Aquí podrías redirigir a la página de perfil del barbero
                return render_template("barbero.html")
            else:
                return "Credenciales incorrectas. Vuelve a intentarlo."

    return render_template("login.html")


@app.route("/agendar_cita", methods=["GET", "POST"])
def agendar_cita():
    if request.method == "POST":
        servicio_id = request.form["servicio"]
        barbero_id = request.form["barbero"]
        fecha = request.form["fecha"]
        hora = request.form["hora"]

        # Realizar la conexión a la base de datos
        conn = sqlite3.connect("barberia.db")
        cursor = conn.cursor()

        # Insertar la cita en la tabla cita
        cursor.execute(
            "INSERT INTO cita (cliente, barbero, servicio, fecha, estado) VALUES (?, ?, ?, ?, ?)",
            (1, barbero_id, servicio_id, fecha + " " + hora, 1),
        )

        # Guardar los cambios en la base de datos
        conn.commit()

        # Cerrar la conexión a la base de datos
        conn.close()

        # Redirigir a una página de confirmación o a donde desees
        return render_template("cliente_dashboard.html")
    else:
        horas_disponibles = []
        hora_inicio = datetime.strptime("09:00", "%H:%M")
        hora_fin = datetime.strptime("19:00", "%H:%M")

        hora_actual = hora_inicio
        while hora_actual <= hora_fin:
            horas_disponibles.append(hora_actual.strftime("%H:%M"))
            hora_actual += timedelta(minutes=30)

        # Realizar la conexión a la base de datos
        conn = sqlite3.connect("barberia.db")
        cursor = conn.cursor()

        # Obtener los servicios y barberos de la base de datos
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


@app.route("/ver_cita")
def ver_cita():
    return render_template("ver_cita.html")


@app.route("/mi_cuenta")
def mi_cuenta():
    return render_template("mi_cuenta.html")


if __name__ == "__main__":
    app.run(debug=True)
