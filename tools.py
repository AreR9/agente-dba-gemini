"""
tools.py
--------
Capa de herramientas (Tooling) para el Agente DBA.
Define las funciones que el agente puede invocar de forma autonoma:
1. Inspeccionar el esquema relacional de la base de datos.
2. Ejecutar consultas SQL en modo solo lectura con validaciones de
   seguridad.
"""
import sqlite3
import json

DB_NAME = "tienda_django.db"


def get_database_schema(db_path: str = DB_NAME) -> str:
    """
    Inspecciona la base de datos y retorna el esquema DDL completo de las
    tablas.

    Esta funcion es la primera que debe invocar el agente para saber
    que tablas existen, como se llaman las columnas y que llaves foraneas
    hay.

    Returns:
        str: Las sentencias CREATE TABLE originales de la base de datos.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Consultamos la tabla interna sqlite_master para obtener los CREATE TABLE
        cursor.execute("""
            SELECT name, sql
            FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%';
        """)
        tables = cursor.fetchall()
        conn.close()

        if not tables:
            return "No se encontraron tablas en la base de datos."

        schema_description = []
        for table_name, create_sql in tables:
            schema_description.append(f"--- Tabla: {table_name} ---")
            schema_description.append(create_sql.strip())
            schema_description.append("")

        return "\n".join(schema_description)
    except sqlite3.Error as e:
        return f"Error al leer el esquema de la base de datos: {str(e)}"


def execute_sql_query(query: str, db_path: str = DB_NAME) -> str:
    """
    Ejecuta una consulta SQL y retorna los registros encontrados en formato
    JSON.

    Aplica una barrera defensiva (guardrail): rechaza sentencias de
    escritura, modificacion o eliminacion (DROP, DELETE, UPDATE, INSERT, ALTER).

    Args:
        query (str): Sentencia SQL SELECT que el agente desea ejecutar.

    Returns:
        str: Resultados serializados en JSON si la consulta es exitosa,
        o el mensaje descriptivo del error en caso de fallo.
    """
    cleaned_query = query.strip()

    # --- GUARDRAIL DE SEGURIDAD (Principio de Minimo Privilegio) ---
    # Comprobar que comience estrictamente con SELECT o WITH (para CTEs)
    first_word = cleaned_query.split()[0].upper() if cleaned_query else ""
    if first_word not in ("SELECT", "WITH"):
        return (
            "Error de Seguridad: Operacion no permitida. "
            "El agente solo tiene permisos de lectura ('SELECT'). "
            "Operaciones como INSERT, UPDATE, DELETE o DROP estan bloqueadas."
        )

    # Validacion adicional: rechazar si contiene palabras clave destructivas
    palabras_prohibidas = ["DROP", "DELETE", "TRUNCATE", "ALTER", "INSERT", "UPDATE"]
    tokens = [token.strip(";").upper() for token in cleaned_query.split()]
    for palabra in palabras_prohibidas:
        if palabra in tokens:
            return f"Error de Seguridad: La consulta contiene la instruccion prohibida '{palabra}'."

    # --- EJECUCION DE LA CONSULTA ---
    try:
        conn = sqlite3.connect(db_path)
        # Permite acceder a las columnas por nombre como diccionarios
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(cleaned_query)
        rows = cursor.fetchall()
        conn.close()

        # Convertir los resultados a una lista de diccionarios
        resultados = [dict(row) for row in rows]

        if not resultados:
            return "La consulta no arrojo registros."

        # Retornamos los datos formateados en JSON para que el LLM los
        # interprete facilmente
        return json.dumps(resultados, ensure_ascii=False, indent=2)
    except sqlite3.Error as e:
        # En caso de error de sintaxis, se retorna el error exacto
        # para que el agente pueda razonar y autocorregir la consulta (Self-Healing).
        return f"Error de sintaxis en SQLite: {str(e)}"


# --- PRUEBA MANUAL DE LAS HERRAMIENTAS ---
if __name__ == "__main__":
    print("=== 1. PRUEBA DE ESQUEMA ===")
    print(get_database_schema())

    print("\n=== 2. PRUEBA DE CONSULTA VALIDA ===")
    test_query = "SELECT nombre, precio, stock FROM productos WHERE stock > 10;"
    print(execute_sql_query(test_query))

    print("\n=== 3. PRUEBA DE BLOQUEO DE SEGURIDAD ===")
    malicious_query = "DELETE FROM empleados WHERE id = 1;"
    print(execute_sql_query(malicious_query))
