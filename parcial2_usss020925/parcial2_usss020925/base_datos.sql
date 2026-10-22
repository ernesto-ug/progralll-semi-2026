CREATE DATABASE IF NOT EXISTS db_academica;
USE db_academica;

CREATE TABLE usuarios_usss020925 (
  idUsuario INT(10) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  usuario   CHAR(35),
  clave     CHAR(35),
  nombre    CHAR(85),
  direccion CHAR(100),
  telefono  CHAR(9)
);

-- Usuario de prueba para entrar al login
INSERT INTO usuarios_usss020925 (usuario, clave, nombre, direccion, telefono)
VALUES ('admin', '123', 'Administrador', 'San Salvador', '7000-0000');
