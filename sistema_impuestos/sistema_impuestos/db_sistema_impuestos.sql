CREATE DATABASE IF NOT EXISTS db_sistema_impuestos CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE db_sistema_impuestos;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS bitacora_periodos;
DROP TABLE IF EXISTS periodos_impuesto;
DROP TABLE IF EXISTS tarifas;
DROP TABLE IF EXISTS productos;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE IF NOT EXISTS clientes (
    idCliente INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(10) NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    direccion VARCHAR(200) NULL,
    telefono VARCHAR(20) NULL,
    email VARCHAR(100) NULL,
    tipo VARCHAR(20) NOT NULL DEFAULT 'particular'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE clientes ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS productos (
    idProducto INT AUTO_INCREMENT PRIMARY KEY,
    codigo CHAR(10) NOT NULL UNIQUE,
    nombre VARCHAR(150) NOT NULL,
    actividad ENUM('comercio','industria') NOT NULL,
    precioGeneral DECIMAL(12,6) NULL,
    activo TINYINT(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE tarifas (
    idTarifa INT AUTO_INCREMENT PRIMARY KEY,
    idProducto INT NOT NULL,
    desde DECIMAL(14,2) NOT NULL,
    hasta DECIMAL(14,2) NOT NULL,
    precioBase DECIMAL(12,6) NOT NULL DEFAULT 0,
    adicional DECIMAL(12,6) NOT NULL DEFAULT 0,
    porcentaje DECIMAL(8,4) NOT NULL DEFAULT 0,
    version VARCHAR(30) NOT NULL DEFAULT '1.0',
    fechaDesde DATE NOT NULL,
    fechaHasta DATE NULL,
    activo TINYINT(1) NOT NULL DEFAULT 1,
    FOREIGN KEY (idProducto) REFERENCES productos(idProducto),
    INDEX idx_tarifa_busqueda (idProducto, desde, hasta, fechaDesde, fechaHasta)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE periodos_impuesto (
    idPeriodo INT AUTO_INCREMENT PRIMARY KEY,
    idCliente INT NOT NULL,
    idProducto INT NOT NULL,
    desde DATE NOT NULL,
    hasta DATE NOT NULL,
    monto DECIMAL(14,2) NOT NULL,
    cantidad DECIMAL(12,2) NOT NULL DEFAULT 1.00,
    precio DECIMAL(14,6) NOT NULL,
    subtotal DECIMAL(14,6) NOT NULL,
    idTarifa INT NOT NULL,
    formula TEXT NOT NULL,
    versionTarifa VARCHAR(30) NOT NULL,
    fechaCalculo DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado ENUM('historico','vigente','facturado') NOT NULL DEFAULT 'historico',
    usuarioCreacion VARCHAR(100) NOT NULL DEFAULT 'sistema',
    fechaCreacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    usuarioModificacion VARCHAR(100) NULL,
    fechaModificacion DATETIME NULL,
    FOREIGN KEY (idCliente) REFERENCES clientes(idCliente),
    FOREIGN KEY (idProducto) REFERENCES productos(idProducto),
    FOREIGN KEY (idTarifa) REFERENCES tarifas(idTarifa),
    INDEX idx_periodo_cliente_producto (idCliente, idProducto, desde, hasta)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE bitacora_periodos (
    idBitacora INT AUTO_INCREMENT PRIMARY KEY,
    idPeriodo INT NOT NULL,
    accion VARCHAR(50) NOT NULL,
    usuario VARCHAR(100) NOT NULL,
    fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    balanceAnterior DECIMAL(14,2) NULL,
    balanceNuevo DECIMAL(14,2) NULL,
    motivo TEXT NULL,
    FOREIGN KEY (idPeriodo) REFERENCES periodos_impuesto(idPeriodo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO productos (codigo, nombre, actividad, precioGeneral)
VALUES
('11801', 'Impuesto a las Actividades Económicas Comercio', 'comercio', NULL),
('11802', 'Impuesto a las Actividades Económicas Industria', 'industria', NULL)
ON DUPLICATE KEY UPDATE nombre = VALUES(nombre), actividad = VALUES(actividad);

DELETE FROM tarifas;

INSERT INTO tarifas (idProducto, desde, hasta, precioBase, adicional, porcentaje, version, fechaDesde)
SELECT p.idProducto, t.desde, t.hasta, t.precioBase, t.adicional, t.porcentaje, '1.0', '2026-01-01'
FROM productos p
CROSS JOIN (
    SELECT 0.01 desde, 500.00 hasta, 1.50 precioBase, 0.00 adicional, 0.00 porcentaje
    UNION ALL SELECT 500.01, 1000.00, 1.50, 3.00, 0.00
    UNION ALL SELECT 1000.01, 2000.00, 3.00, 3.00, 0.00
    UNION ALL SELECT 2000.01, 3000.00, 6.00, 3.00, 0.00
    UNION ALL SELECT 3000.01, 6000.00, 9.00, 2.00, 0.00
    UNION ALL SELECT 8000.01, 18000.00, 15.00, 2.00, 0.00
    UNION ALL SELECT 18000.01, 30000.00, 39.00, 2.00, 0.00
    UNION ALL SELECT 30000.01, 60000.00, 63.00, 1.00, 0.00
    UNION ALL SELECT 60000.01, 100000.00, 93.00, 0.80, 0.00
    UNION ALL SELECT 100000.01, 200000.00, 125.00, 0.70, 0.00
    UNION ALL SELECT 200000.01, 300000.00, 195.00, 0.60, 0.00
    UNION ALL SELECT 300000.01, 400000.00, 255.00, 0.45, 0.00
    UNION ALL SELECT 400000.01, 500000.00, 300.00, 0.40, 0.00
    UNION ALL SELECT 500000.01, 1000000.00, 340.00, 0.30, 0.00
    UNION ALL SELECT 1000000.01, 99999999.99, 490.00, 0.18, 0.00
) t;

-- IMPORTANTE: el requerimiento no proporciona una tarifa para 6,000.01 a 8,000.00.
-- Por eso no se inserta ese rango. El sistema rechazará balances en ese intervalo.
