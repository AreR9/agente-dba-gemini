"""
agent.py
--------
Orquestador y cerebro del Agente DBA de Analitica SQL.
Utiliza el SDK de Google Gemini con llamada nativa a funciones (Tool Calling)
para razonar, inspeccionar la base de datos, ejecutar consultas seguras y
responder preguntas de negocio en lenguaje natural.
"""
import os
import sys
import time

from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env si existe
load_dotenv()

from google import genai
from google.genai import types
from google.genai.errors import ServerError

# Importamos las herramientas locales
from tools import get_database_schema, execute_sql_query

# 1. Verificacion de API Key
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Error: No se encontro la variable de entorno 'GEMINI_API_KEY'.")
    print("Verifica tu archivo .env o variable de sistema.")
    sys.exit(1)

client = genai.Client(api_key=api_key)

# Modelo activo oficial
MODELO_ACTIVO = "gemini-3.6-flash"

# 2. Definicion del System Prompt (Instrucciones del Agente)
SYSTEM_INSTRUCTION = """
Eres un Asistente Senior DBA y Analista de Datos especializado en bases de
datos SQLite y modelos Django.
Tu objetivo es responder con precision a preguntas de negocio formuladas por
usuarios, utilizando las herramientas a tu disposicion.

Sigue rigurosamente estas reglas de operacion:
1. SIEMPRE invoca primero 'get_database_schema' si no conoces o necesitas
   validar los nombres exactos de tablas y columnas.
2. Recuerda que los puestos de los empleados se almacenan con codigos
   especificos:
   - 'GE' representa Gerente
   - 'VE' representa Vendedor
   - 'AL' representa Almacenista
3. Construye consultas SQL compatibles con la sintaxis de SQLite.
4. NUNCA intentes ejecutar sentencias de escritura (INSERT, UPDATE, DELETE,
   DROP). Solo tienes permisos SELECT.
5. Si 'execute_sql_query' devuelve un error de sintaxis o columna, lee con
   atencion el mensaje de error, corrige tu consulta y vuelve a intentar
   (autorreparacion).
6. Presenta tu respuesta final en espanol, de forma clara, profesional y
   estructurada (usa vinetas o tablas de texto si es util).
"""


def _enviar_mensaje_con_reintento(chat, mensaje_o_parte, max_intentos: int = 4):
    """Envia un mensaje a Gemini gestionando reintentos ante saturacion
    temporal (503)."""
    demora = 2
    for intento in range(max_intentos):
        try:
            return chat.send_message(mensaje_o_parte)
        except ServerError as e:
            if "503" in str(e) and intento < max_intentos - 1:
                print(f"[Aviso] Servidor con alta demanda. Reintentando en {demora} segundos...")
                time.sleep(demora)
                demora *= 2
            else:
                raise e


def preguntar_al_agente(pregunta: str, verbose: bool = True) -> str:
    """
    Envia una consulta en lenguaje natural al agente y gestiona el ciclo
    de razonamiento y ejecucion de herramientas.
    """
    herramientas_disponibles = {
        "get_database_schema": get_database_schema,
        "execute_sql_query": execute_sql_query,
    }

    # Inicializar chat con el modelo activo
    chat = client.chats.create(
        model=MODELO_ACTIVO,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.1,
            tools=[get_database_schema, execute_sql_query],
        ),
    )

    if verbose:
        print(f"\n[Usuario]: {pregunta}")
        print("-" * 60)

    # Envio del mensaje con proteccion contra 503
    response = _enviar_mensaje_con_reintento(chat, pregunta)

    # Ciclo ReAct / Tool Calling
    while response.function_calls:
        for function_call in response.function_calls:
            func_name = function_call.name
            func_args = function_call.args

            if verbose:
                print(f"[Agente Acción] Invocando herramienta: '{func_name}'")
                if func_args:
                    print(f"  Argumentos: {dict(func_args)}")

            # Ejecutar la funcion en backend
            if func_name in herramientas_disponibles:
                tool_output = herramientas_disponibles[func_name](**func_args)
            else:
                tool_output = f"Error: Herramienta '{func_name}' no reconocida."

            if verbose:
                vista_previa = str(tool_output).strip().replace("\n", " ")
                if len(vista_previa) > 120:
                    vista_previa = vista_previa[:120] + "..."
                print(f"[Observación]: {vista_previa}\n")

            # Retornar el resultado al modelo con control de reintentos
            response = _enviar_mensaje_con_reintento(
                chat,
                types.Part.from_function_response(
                    name=func_name,
                    response={"result": tool_output},
                ),
            )

    return response.text


if __name__ == "__main__":
    print(f"Iniciando prueba del Agente DBA con modelo: {MODELO_ACTIVO}...\n")
    consulta_prueba = (
        "¿Cual es el puesto que tiene mas empleados activos y cuantos productos "
        "tienen a su cargo los empleados de ese puesto?"
    )
    respuesta = preguntar_al_agente(consulta_prueba, verbose=True)
    print("\n" + "=" * 60)
    print("[RESPUESTA FINAL DEL AGENTE]:")
    print("=" * 60)
    print(respuesta)
