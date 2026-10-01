from mysql.connector.errors import Error
import conexion


db = conexion.Conexion()


class crud_clientes:

    def consultar(self, buscar):
        return db.consultar(
            """
            SELECT idCliente, codigo, nombre, direccion, telefono, email, tipo
            FROM clientes
            WHERE codigo LIKE %s OR nombre LIKE %s
            ORDER BY nombre
            """,
            (f"%{buscar}%", f"%{buscar}%")
        )

    def consultar_empresas(self):
        return db.consultar(
            """
            SELECT idCliente, codigo, nombre, tipo
            FROM clientes
            WHERE tipo = 'empresa'
            ORDER BY nombre
            """
        )

    def administrar(self, datos):
        try:
            accion = datos.get('accion', 'nuevo')

            if accion == 'nuevo':
                sql = """
                    INSERT INTO clientes(codigo, nombre, direccion, telefono, email, tipo)
                    VALUES(%s, %s, %s, %s, %s, %s)
                """
                valores = (
                    datos['codigo'], datos['nombre'], datos['direccion'],
                    datos['telefono'], datos['email'], datos['tipo']
                )

            elif accion == 'modificar':
                sql = """
                    UPDATE clientes
                    SET codigo=%s, nombre=%s, direccion=%s,
                        telefono=%s, email=%s, tipo=%s
                    WHERE idCliente=%s
                """
                valores = (
                    datos['codigo'], datos['nombre'], datos['direccion'],
                    datos['telefono'], datos['email'], datos['tipo'],
                    datos['idCliente']
                )

            elif accion == 'eliminar':
                sql = "DELETE FROM clientes WHERE idCliente=%s"
                valores = (datos['idCliente'],)

            else:
                return "Accion no valida"

            return db.ejecutar(sql, valores)

        except Error as e:
            return f"Error al guardar el cliente: {e}"
        except KeyError as e:
            return f"Falta el campo: {e}"
