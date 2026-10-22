"""
Parcial II - Programación Computacional III
Estudiante: USSS020925
Backend en Python nativo (sin frameworks): servidor http.server + MySQL.
"""
import json
import os
import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import mysql.connector

# ---------- Configuración de MySQL (XAMPP) ----------
CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',          # en XAMPP el root no tiene clave
    'port': 3306,
}
BASE = 'db_academica'
TABLA = 'usuarios_usss020925'

CARPETA = os.path.dirname(os.path.abspath(__file__))
tokens = set()               # sesiones iniciadas (login correcto)
crud = None


class crud_usuarios:
    def __init__(self):
        self.preparar_base()

    def conectar(self):
        return mysql.connector.connect(database=BASE, **CONFIG)

    # Crea la base y la tabla si todavía no existen
    def preparar_base(self):
        db = mysql.connector.connect(**CONFIG)
        cur = db.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {BASE}")
        cur.execute(f"USE {BASE}")
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLA} (
                idUsuario INT(10) NOT NULL AUTO_INCREMENT PRIMARY KEY,
                usuario   CHAR(35),
                clave     CHAR(35),
                nombre    CHAR(85),
                direccion CHAR(100),
                telefono  CHAR(9)
            )""")
        cur.execute(f"SELECT COUNT(*) FROM {TABLA}")
        if cur.fetchone()[0] == 0:
            cur.execute(f"""INSERT INTO {TABLA} (usuario, clave, nombre, direccion, telefono)
                            VALUES ('admin','123','Administrador','San Salvador','7000-0000')""")
        db.commit()
        cur.close()
        db.close()

    # Método CRUD: procesa los datos enviados por el cliente (JS)
    def crud_usuarios_usss020925(self, datos):
        accion = datos.get('accion')
        try:
            db = self.conectar()
            cur = db.cursor(dictionary=True)

            if accion == 'guardar':
                cur.execute(
                    f"""INSERT INTO {TABLA} (usuario, clave, nombre, direccion, telefono)
                        VALUES (%s,%s,%s,%s,%s)""",
                    (datos['usuario'], datos['clave'], datos['nombre'],
                     datos['direccion'], datos['telefono']))
                db.commit()
                resp = {'ok': True, 'msg': 'Usuario guardado correctamente'}

            elif accion == 'modificar':
                cur.execute(
                    f"""UPDATE {TABLA}
                        SET usuario=%s, clave=%s, nombre=%s, direccion=%s, telefono=%s
                        WHERE idUsuario=%s""",
                    (datos['usuario'], datos['clave'], datos['nombre'],
                     datos['direccion'], datos['telefono'], datos['idUsuario']))
                db.commit()
                resp = {'ok': True, 'msg': 'Usuario modificado correctamente'}

            elif accion == 'eliminar':
                cur.execute(f"DELETE FROM {TABLA} WHERE idUsuario=%s", (datos['idUsuario'],))
                db.commit()
                resp = {'ok': True, 'msg': 'Usuario eliminado correctamente'}

            elif accion == 'buscar':
                b = '%' + datos.get('valor', '') + '%'
                cur.execute(
                    f"""SELECT * FROM {TABLA}
                        WHERE usuario LIKE %s OR nombre LIKE %s OR telefono LIKE %s
                        ORDER BY idUsuario""", (b, b, b))
                resp = {'ok': True, 'usuarios': cur.fetchall()}

            else:
                resp = {'ok': False, 'msg': 'Acción no válida'}

            cur.close()
            db.close()
            return resp
        except Exception as e:
            return {'ok': False, 'msg': 'Error: ' + str(e)}

    # Login: autentica contra la base de datos
    def login_usss020925(self, usuario, clave):
        try:
            db = self.conectar()
            cur = db.cursor()
            cur.execute(f"SELECT idUsuario FROM {TABLA} WHERE usuario=%s AND clave=%s",
                        (usuario, clave))
            fila = cur.fetchone()
            cur.close()
            db.close()
            if fila:
                token = secrets.token_hex(16)
                tokens.add(token)
                return {'acceso': True, 'token': token}
            return {'acceso': False, 'msg': 'Usuario o clave incorrectos. Acceso denegado'}
        except Exception as e:
            return {'acceso': False, 'msg': 'Error de base de datos: ' + str(e)}


class Servidor(BaseHTTPRequestHandler):
    def responder(self, codigo, cuerpo, tipo='application/json; charset=utf-8'):
        if isinstance(cuerpo, (dict, list)):
            cuerpo = json.dumps(cuerpo, default=str).encode('utf-8')
        elif isinstance(cuerpo, str):
            cuerpo = cuerpo.encode('utf-8')
        self.send_response(codigo)
        self.send_header('Content-Type', tipo)
        self.send_header('Content-Length', str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_GET(self):
        # El login es lo primero que se muestra al abrir el servidor
        if self.path in ('/', '/index.html', '/login'):
            with open(os.path.join(CARPETA, 'web', 'index.html'), 'rb') as f:
                self.responder(200, f.read(), 'text/html; charset=utf-8')
        else:
            self.responder(404, {'msg': 'No encontrado'})

    def do_POST(self):
        try:
            largo = int(self.headers.get('Content-Length', 0))
            datos = json.loads(self.rfile.read(largo) or b'{}')
        except Exception:
            return self.responder(400, {'ok': False, 'msg': 'Datos inválidos'})

        if self.path == '/login':
            return self.responder(200, crud.login_usss020925(
                datos.get('usuario', ''), datos.get('clave', '')))

        if self.path == '/crud':
            if self.headers.get('X-Token') not in tokens:   # sin login = acceso denegado
                return self.responder(401, {'ok': False, 'msg': 'Acceso denegado. Inicia sesión'})
            return self.responder(200, crud.crud_usuarios_usss020925(datos))

        self.responder(404, {'msg': 'No encontrado'})

    def log_message(self, formato, *args):
        pass    # terminal limpia


def iniciar(puerto=8000, abrir=True):
    global crud
    crud = crud_usuarios()
    servidor = None
    for p in range(puerto, puerto + 10):          # si el puerto está ocupado, prueba el siguiente
        try:
            servidor = ThreadingHTTPServer(('localhost', p), Servidor)
            puerto = p
            break
        except OSError:
            continue
    if servidor is None:
        raise SystemExit('No hay ningún puerto libre entre 8000 y 8009')
    url = f'http://localhost:{puerto}'
    print(f'Servidor iniciado en {url}  (Ctrl + C para detenerlo)')
    if abrir:
        threading.Timer(1, webbrowser.open, [url]).start()
    return servidor


if __name__ == '__main__':
    try:
        iniciar().serve_forever()
    except mysql.connector.Error as e:
        print('No se pudo conectar a MySQL. Inicia MySQL en XAMPP y revisa CONFIG en main.py.')
        print('Detalle:', e)
    except KeyboardInterrupt:
        print('\nServidor detenido')
