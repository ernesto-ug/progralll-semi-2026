from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib import parse
from urllib.parse import urlparse, parse_qs
import json

import crud_clientes
import crud_periodos


port = 3000
crudClientes = crud_clientes.crud_clientes()
crudPeriodos = crud_periodos.crud_periodos()


class miServidor(SimpleHTTPRequestHandler):

    def _responder(self, datos, codigo=200):
        contenido = json.dumps(datos, default=str).encode('utf-8')
        self.send_response(codigo)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(contenido)))
        self.end_headers()
        self.wfile.write(contenido)

    def _leer_json(self):
        longitud = int(self.headers.get('Content-Length', 0))
        cuerpo = self.rfile.read(longitud).decode('utf-8')
        return json.loads(cuerpo)

    def do_POST(self):
        try:
            datos = self._leer_json()
            ruta = urlparse(self.path).path

            if ruta in ('/cliente', '/clientes'):
                respuesta = {'msg': crudClientes.administrar(datos)}
                self._responder(respuesta)
                return

            if ruta == '/periodo/calcular':
                respuesta = crudPeriodos.calcular(datos)
                self._responder(respuesta)
                return

            if ruta == '/periodo':
                respuesta = {'msg': crudPeriodos.administrar(datos)}
                self._responder(respuesta)
                return

            self._responder({'msg': 'Ruta POST no encontrada'}, 404)

        except Exception as e:
            self._responder({'msg': f'Error del servidor: {e}'}, 500)

    def do_GET(self):
        try:
            urlParse = urlparse(self.path)
            qs = parse_qs(urlParse.query)

            if urlParse.path == '/clientes':
                buscar = qs.get('buscar', [''])[0]
                self._responder(crudClientes.consultar(buscar))
                return

            if urlParse.path == '/clientes/empresas':
                self._responder(crudClientes.consultar_empresas())
                return

            if urlParse.path == '/productos':
                self._responder(crudPeriodos.productos())
                return

            if urlParse.path == '/periodos':
                id_cliente = qs.get('idCliente', [''])[0]
                if not id_cliente:
                    self._responder({'msg': 'Debe indicar idCliente'}, 400)
                    return
                self._responder(crudPeriodos.listar(int(id_cliente)))
                return

            if urlParse.path == '/':
                self.path = '/index.html'
                return SimpleHTTPRequestHandler.do_GET(self)

            return SimpleHTTPRequestHandler.do_GET(self)

        except Exception as e:
            self._responder({'msg': f'Error del servidor: {e}'}, 500)


print(f'Servidor corriendo en el puerto {port}')
server = HTTPServer(('localhost', port), miServidor)
server.serve_forever()
