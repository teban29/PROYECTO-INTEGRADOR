CREATE TABLE "admin" (
  id INTEGER PRIMARY KEY,
  username VARCHAR(50) NOT NULL,
  "password" VARCHAR(12) NOT NULL,
  tipo_usuario_id INTEGER NOT NULL,
  FOREIGN KEY (tipo_usuario_id) REFERENCES tipo_usuario(id)
);

CREATE TABLE "cita" (
  id_cita INTEGER PRIMARY KEY,
  cliente INTEGER NOT NULL,
  barbero INTEGER NOT NULL,
  servicio INTEGER NOT NULL,
  fecha DATETIME NOT NULL,
  estado INTEGER NOT NULL,
  FOREIGN KEY (cliente) REFERENCES cliente(id),
  FOREIGN KEY (barbero) REFERENCES barbero(id),
  FOREIGN KEY (servicio) REFERENCES servicio(id_servicio),
  FOREIGN KEY (estado) REFERENCES estado_cita(id)
);

CREATE TABLE cliente (
  id INTEGER PRIMARY KEY,
  nombre VARCHAR(50) NOT NULL,
  apellidos VARCHAR(50) NOT NULL,
  telefono NUMERIC(28, 10) NOT NULL,
  username VARCHAR(50) NOT NULL,
  "password" VARCHAR(12) NOT NULL,
  tipo_usuario_id INTEGER NOT NULL,
  FOREIGN KEY (tipo_usuario_id) REFERENCES tipo_usuario(id)
);

CREATE TABLE estado_cita (
  id INTEGER PRIMARY KEY,
  estado VARCHAR NOT NULL
);

CREATE TABLE tipo_usuario (
  id INTEGER PRIMARY KEY,
  tipo VARCHAR(50) NOT NULL
);

CREATE TABLE "barbero" (
  id INTEGER PRIMARY KEY,
  nombre VARCHAR(50) NOT NULL,
  apellidos VARCHAR(50) NOT NULL,
  telefono NUMERIC(28, 10) NOT NULL,
  username VARCHAR(50) NOT NULL,
  "password" VARCHAR(12) NOT NULL,
  tipo_usuario_id INTEGER NOT NULL,
  FOREIGN KEY (tipo_usuario_id) REFERENCES tipo_usuario(id)
);

CREATE TABLE "servicio" (
  id_servicio INTEGER PRIMARY KEY,
  tipo VARCHAR(50) NOT NULL,
  duracion INTEGER(50) NOT NULL,
  precio INTEGER(50) NOT NULL
);
