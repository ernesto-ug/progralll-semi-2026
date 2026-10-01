from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP, InvalidOperation
from datetime import date, datetime
from mysql.connector.errors import Error
import conexion


db = conexion.Conexion()


class crud_periodos:

    def productos(self):
        return db.consultar(
            """
            SELECT idProducto, codigo, nombre, actividad
            FROM productos
            WHERE activo = 1
            ORDER BY actividad
            """
        )

    def clientes_empresa(self):
        return db.consultar(
            """
            SELECT idCliente, codigo, nombre
            FROM clientes
            WHERE tipo = 'empresa'
            ORDER BY nombre
            """
        )

    def listar(self, id_cliente):
        return db.consultar(
            """
            SELECT p.idPeriodo, p.idCliente, c.codigo AS codigoCliente,
                   c.nombre AS cliente, pr.codigo AS codigoProducto,
                   pr.nombre AS producto, pr.actividad,
                   DATE_FORMAT(p.desde, '%Y-%m-%d') AS desde,
                   DATE_FORMAT(p.hasta, '%Y-%m-%d') AS hasta,
                   p.monto, p.cantidad, ROUND(p.precio, 2) AS precio,
                   ROUND(p.subtotal, 2) AS subtotal, p.estado,
                   t.desde AS tarifaDesde, t.hasta AS tarifaHasta,
                   t.precioBase, t.adicional, t.porcentaje,
                   p.versionTarifa, p.formula, p.fechaCalculo
            FROM periodos_impuesto p
            INNER JOIN clientes c ON c.idCliente = p.idCliente
            INNER JOIN productos pr ON pr.idProducto = p.idProducto
            INNER JOIN tarifas t ON t.idTarifa = p.idTarifa
            WHERE p.idCliente = %s
            ORDER BY p.desde DESC, p.idPeriodo DESC
            """,
            (id_cliente,)
        )

    def calcular(self, datos):
        try:
            id_cliente = int(datos['idCliente'])
            id_producto = int(datos['idProducto'])
            fecha_desde = self._fecha(datos['desde'])
            fecha_hasta = self._fecha(datos['hasta'])
            monto = Decimal(str(datos['monto']))

            if fecha_desde >= fecha_hasta:
                return {'ok': False, 'msg': 'La fecha Hasta debe ser posterior a la fecha Desde.'}

            if monto <= 0:
                return {'ok': False, 'msg': 'Ingrese un balance mayor que cero.'}

            cliente = db.consultar(
                "SELECT idCliente, nombre, tipo FROM clientes WHERE idCliente=%s",
                (id_cliente,)
            )
            if not cliente:
                return {'ok': False, 'msg': 'El cliente no existe.'}

            if cliente[0]['tipo'] != 'empresa':
                return {
                    'ok': False,
                    'msg': 'El Impuesto a las Actividades Económicas requiere un cliente de tipo empresa.'
                }

            producto = db.consultar(
                "SELECT idProducto, codigo, nombre, actividad FROM productos WHERE idProducto=%s AND activo=1",
                (id_producto,)
            )
            if not producto:
                return {'ok': False, 'msg': 'El producto no existe o está inactivo.'}

            tarifas = db.consultar(
                """
                SELECT * FROM tarifas
                WHERE idProducto=%s
                  AND activo=1
                  AND fechaDesde <= %s
                  AND (fechaHasta IS NULL OR %s < fechaHasta)
                  AND desde <= %s
                  AND hasta >= %s
                ORDER BY idTarifa
                """,
                (id_producto, fecha_desde, fecha_desde, monto, monto)
            )

            if len(tarifas) == 0:
                return {
                    'ok': False,
                    'msg': 'No existe una tarifa configurada para el balance indicado.'
                }

            if len(tarifas) > 1:
                return {
                    'ok': False,
                    'msg': 'Existe más de una tarifa aplicable. Corrija la tabla tarifaria.'
                }

            tarifa = tarifas[0]
            precio_base = Decimal(str(tarifa['precioBase']))
            adicional = Decimal(str(tarifa['adicional']))
            porcentaje = Decimal(str(tarifa['porcentaje']))
            desde_tarifa = Decimal(str(tarifa['desde']))

            if porcentaje > 0:
                precio = monto * porcentaje / Decimal('100')
                excedente = monto - desde_tarifa
                bloques = Decimal('0')
                formula = (
                    f"Impuesto mensual = {monto:.2f} x {porcentaje:.4f}% / 100 "
                    f"= {precio.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}"
                )
            else:
                excedente = monto - desde_tarifa
                if excedente <= 0:
                    bloques_int = 0
                else:
                    bloques_int = int((excedente / Decimal('1000')).to_integral_value(rounding=ROUND_CEILING))
                bloques = Decimal(bloques_int)
                precio = precio_base + (bloques * adicional)
                formula = (
                    f"Excedente = {monto:.2f} - {desde_tarifa:.2f} = {excedente:.2f}; "
                    f"Bloques = CEIL({excedente:.2f} / 1,000) = {bloques_int}; "
                    f"Impuesto mensual = {precio_base:.2f} + ({bloques_int} x {adicional:.2f}) = "
                    f"{precio.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}"
                )

            precio = precio.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
            subtotal = precio

            return {
                'ok': True,
                'cliente': cliente[0]['nombre'],
                'producto': producto[0]['nombre'],
                'actividad': producto[0]['actividad'],
                'tarifa': {
                    'idTarifa': tarifa['idTarifa'],
                    'desde': str(tarifa['desde']),
                    'hasta': str(tarifa['hasta']),
                    'precioBase': str(tarifa['precioBase']),
                    'adicional': str(tarifa['adicional']),
                    'porcentaje': str(tarifa['porcentaje']),
                    'version': tarifa['version']
                },
                'monto': str(monto),
                'excedente': str(excedente),
                'bloques': str(bloques),
                'precio': str(precio),
                'subtotal': str(subtotal),
                'formula': formula
            }

        except (KeyError, ValueError, InvalidOperation) as e:
            return {'ok': False, 'msg': f'Datos invalidos: {e}'}
        except Error as e:
            return {'ok': False, 'msg': f'Error de base de datos: {e}'}

    def administrar(self, datos):
        conn = db.conectar()
        if not conn:
            return 'Error de conexion'

        try:
            accion = datos.get('accion', 'nuevo')
            if accion != 'nuevo':
                return 'Los periodos historicos no se modifican automaticamente.'

            calculo = self.calcular(datos)
            if not calculo.get('ok'):
                return calculo['msg']

            id_cliente = int(datos['idCliente'])
            id_producto = int(datos['idProducto'])
            fecha_desde = self._fecha(datos['desde'])
            fecha_hasta = self._fecha(datos['hasta'])
            monto = Decimal(str(datos['monto']))

            # Evita períodos superpuestos para la misma empresa y producto.
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT idPeriodo FROM periodos_impuesto
                WHERE idCliente=%s AND idProducto=%s
                  AND desde < %s AND hasta > %s
                LIMIT 1
                """,
                (id_cliente, id_producto, fecha_hasta, fecha_desde)
            )
            conflicto = cursor.fetchone()
            if conflicto:
                cursor.close()
                return 'El período indicado se superpone con un período existente.'

            cursor.execute(
                """
                INSERT INTO periodos_impuesto
                (idCliente, idProducto, desde, hasta, monto, cantidad,
                 precio, subtotal, idTarifa, formula, versionTarifa,
                 estado, usuarioCreacion)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    id_cliente, id_producto, fecha_desde, fecha_hasta,
                    monto, Decimal('1.00'), Decimal(calculo['precio']),
                    Decimal(calculo['subtotal']), calculo['tarifa']['idTarifa'],
                    calculo['formula'], calculo['tarifa']['version'],
                    self._estado(fecha_desde, fecha_hasta),
                    datos.get('usuario', 'sistema')
                )
            )
            id_periodo = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO bitacora_periodos
                (idPeriodo, accion, usuario, balanceNuevo, motivo)
                VALUES (%s,%s,%s,%s,%s)
                """,
                (
                    id_periodo, 'CREACION', datos.get('usuario', 'sistema'),
                    monto, 'Creación del período anual'
                )
            )

            conn.commit()
            cursor.close()
            return 'ok'

        except Error as e:
            conn.rollback()
            return f'Error al guardar el período: {e}'

    def _fecha(self, valor):
        return datetime.strptime(str(valor), '%Y-%m-%d').date()

    def _estado(self, desde, hasta):
        hoy = date.today()
        if desde <= hoy < hasta:
            return 'vigente'
        return 'historico'
