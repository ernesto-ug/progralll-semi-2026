import mysql.connector
from mysql.connector import Error


class Conexion:
    def __init__(self):
        self.host = "localhost"
        self.user = "root"
        self.password = ""
        self.database = "db_sistema_impuestos"
        self.conexion = None

    def conectar(self):
        try:
            if self.conexion is None or not self.conexion.is_connected():
                self.conexion = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database
                )
            return self.conexion
        except Error as e:
            print(f"Error al conectar a la base de datos: {e}")
            return None

    def consultar(self, sql, datos=None):
        try:
            conn = self.conectar()
            if not conn:
                return []

            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, datos or ())
            resultado = cursor.fetchall()
            cursor.close()
            return resultado
        except Error as e:
            print(f"Error al consultar la base de datos: {e}")
            return []

    def ejecutar(self, sql, datos=None):
        try:
            conn = self.conectar()
            if not conn:
                return "Error de conexion"

            cursor = conn.cursor()
            cursor.execute(sql, datos or ())
            conn.commit()
            cursor.close()
            return "ok"
        except Error as e:
            if self.conexion and self.conexion.is_connected():
                self.conexion.rollback()
            print(f"Error al ejecutar la consulta: {e}")
            return f"Error: {e}"

    def cerrar(self):
        if self.conexion and self.conexion.is_connected():
            self.conexion.close()
