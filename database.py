"""
database.py
-----------
Script para inicializar la base de datos SQLite 'tienda_django.db'.
Replica el esquema relacional de los modelos de Django (Empleado y Producto)
e inserta registros semilla para realizar pruebas de analítica con agentes.
"""
import sqlite3
from datetime import datetime


def get_connection(db_path: str = "tienda_django.db") -> sqlite3.Connection:
    """Crea y retorna una conexion a la base de datos SQLite con soporte de
    llaves foraneas."""
    conn = sqlite3.connect(db_path)
    # Habilitar la restriccion de llaves foraneas en SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: str = "tienda_django.db") -> None:
    """Crea las tablas correspondientes a los modelos Empleado y
    Producto."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Eliminar tablas existentes para garantizar un entorno limpio en cada
    # ejecucion
    cursor.execute("DROP TABLE IF EXISTS productos;")
    cursor.execute("DROP TABLE IF EXISTS empleados;")

    # 1. Tabla: empleados (Mapeo de clase Empleado)
    # Puestos validos: 'GE' (Gerente), 'VE' (Vendedor), 'AL' (Almacenista)
    cursor.execute("""
        CREATE TABLE empleados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(150) NOT NULL,
            email VARCHAR(254) NOT NULL UNIQUE,
            telefono VARCHAR(20),
            puesto VARCHAR(2) NOT NULL CHECK (puesto IN ('GE', 'VE', 'AL'))
                DEFAULT 'VE',
            activo BOOLEAN NOT NULL DEFAULT 1,
            fecha_ingreso DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. Tabla: productos (Mapeo de clase Producto)
    cursor.execute("""
        CREATE TABLE productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(200) NOT NULL,
            descripcion TEXT,
            precio DECIMAL(10, 2) NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
            creado_por_id INTEGER NOT NULL,
            responsable_id INTEGER,
            creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (responsable_id) REFERENCES empleados (id) ON DELETE SET NULL
        );
    """)

    conn.commit()
    conn.close()
    print("✓ Tablas 'empleados' y 'productos' creadas exitosamente.")


def seed_db(db_path: str = "tienda_django.db") -> None:
    """Inserta registros de prueba con casos representativos para consultas
    analiticas."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Registros para 'empleados'
    # Incluye gerentes, vendedores y almacenistas; activos e inactivos.
    empleados_data = [
        ("Carlos Martinez", "carlos.martinez@empresa.com", "555-0101", "GE", 1, "2024-01-15 08:30:00"),
        ("Laura Gomez", "laura.gomez@empresa.com", "555-0102", "VE", 1, "2024-02-01 09:00:00"),
        ("Miguel Torres", "miguel.torres@empresa.com", "555-0103", "VE", 1, "2024-02-20 09:15:00"),
        ("Sofia Ramirez", "sofia.ramirez@empresa.com", "555-0104", "AL", 1, "2024-03-05 08:00:00"),
        ("Diego Herrera", "diego.herrera@empresa.com", "555-0105", "AL", 0, "2023-11-10 08:00:00"),
        ("Ana Morales", "ana.morales@empresa.com", "555-0106", "VE", 0, "2023-08-12 10:00:00"),
    ]
    cursor.executemany("""
        INSERT INTO empleados (nombre, email, telefono, puesto, activo, fecha_ingreso)
        VALUES (?, ?, ?, ?, ?, ?);
    """, empleados_data)

    # Registros para 'productos'
    # Se asignan responsables con diferentes puestos y productos sin
    # responsable (NULL)
    # creado_por_id simula el id del usuario administrador de Django
    productos_data = [
        ("Laptop Pro 15", "Laptop con procesador i7 y 16GB RAM", 1250.00, 15, 1, 1, "2024-04-01 10:00:00"),
        ("Monitor Gamer 27", "Monitor IPS 144Hz 1ms", 299.99, 40, 1, 2, "2024-04-05 11:30:00"),
        ("Teclado Mecanico RGB", "Teclado mecanico switch azul", 85.50, 0, 1, 2, "2024-04-10 14:20:00"),
        ("Mouse Inalambrico", "Mouse optico ergonomico", 25.00, 120, 1, 3, "2024-04-12 16:45:00"),
        ("Silla Ergonomica", "Silla ajustable para oficina", 210.00, 8, 1, 4, "2024-04-15 09:10:00"),
        ("Escritorio Elevable", "Escritorio electrico con altura ajustable", 450.00, 5, 1, 4, "2024-04-18 12:00:00"),
        ("Auriculares Cancelacion Ruido", "Auriculares bluetooth con microfono", 140.00, 0, 1, None, "2024-04-20 15:30:00"),
        ("Webcam Full HD 1080p", "Camara web para videollamadas con tripode", 55.00, 25, 1, 3, "2024-04-22 17:00:00"),
        ("Disco Solido NVMe 1TB", "Almacenamiento de alta velocidad M.2", 95.00, 60, 1, 1, "2024-04-25 10:45:00"),
        ("Cable HDMI 2.1", "Cable mallado 2 metros soporte 4K 120Hz", 12.50, 200, 1, None, "2024-04-28 13:15:00"),
    ]
    cursor.executemany("""
        INSERT INTO productos (nombre, descripcion, precio, stock, creado_por_id, responsable_id, creado_en)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """, productos_data)

    conn.commit()
    conn.close()
    print("✓ Datos semilla insertados correctamente (6 empleados, 10 productos).")


if __name__ == "__main__":
    init_db()
    seed_db()
