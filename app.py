"""
app.py
------
Interfaz web interactiva para el Agente DBA de Analítica SQL.
Desarrollada con Streamlit para transformar la solución de consola
en un producto de software web completo y visualmente profesional.
"""
import os

import streamlit as st
from dotenv import load_dotenv

# 1. Configuración general de la página web
st.set_page_config(
    page_title="Agente DBA - Analítica SQL",
    layout="wide",
)

# Verificar la API Key antes de importar el agente
# (agent.py termina el programa con sys.exit si no la encuentra)
load_dotenv()
if not os.environ.get("GEMINI_API_KEY"):
    st.error(
        "No se encontró la variable de entorno 'GEMINI_API_KEY'. "
        "Verifica tu archivo .env y vuelve a ejecutar la aplicación."
    )
    st.stop()

from agent import preguntar_al_agente  # noqa: E402

# 2. Inicialización de la base de datos si no existe
if not os.path.exists("tienda_django.db"):
    from database import init_db, seed_db

    init_db()
    seed_db()

# 3. Barra lateral (Sidebar) con información y controles
with st.sidebar:
    st.title("Panel de Control")
    st.markdown("---")

    # Interruptor para ver la traza técnica del agente en consola
    modo_verbose = st.checkbox("Modo depuración (Verbose en consola)", value=True)

    st.markdown("### Preguntas Sugeridas")
    ejemplos = [
        "¿Cuál es el puesto con más empleados activos y cuántos productos gestionan?",
        "¿Cuál es el producto con el mayor valor de inventario (precio * stock)?",
        "Lista los empleados inactivos y su puesto.",
        "¿Hay productos sin empleado responsable asignado?",
        "Intenta borrar un empleado con id 1 (Prueba de seguridad).",
    ]
    for i, ejemplo in enumerate(ejemplos, start=1):
        if st.button(f"Consulta {i}", help=ejemplo, use_container_width=True):
            st.session_state["pregunta_seleccionada"] = ejemplo

    st.markdown("---")
    if st.button("Limpiar Historial", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# 4. Título principal de la aplicación
st.title("Asistente DBA & Analítica SQL")
st.caption("Interactúa en lenguaje natural con la base de datos SQLite basada en modelos Django.")

# 5. Gestión del estado de la conversación (Session State)
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "¡Hola! Soy tu Asistente DBA. Puedo inspeccionar la base de datos, "
                "diseñar consultas SQL seguras y responder tus dudas analíticas sobre "
                "empleados, puestos y productos. ¿Qué deseas consultar hoy?"
            ),
        }
    ]

# Renderizar el historial de mensajes acumulados
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. Captura de la entrada del usuario (por input manual o botón lateral)
prompt_usuario = st.chat_input("Escribe tu consulta analítica aquí...")
if "pregunta_seleccionada" in st.session_state:
    prompt_usuario = st.session_state.pop("pregunta_seleccionada")

if prompt_usuario:
    # Mostrar el mensaje del usuario en la interfaz
    st.session_state.messages.append({"role": "user", "content": prompt_usuario})
    with st.chat_message("user"):
        st.markdown(prompt_usuario)

    # Procesar la respuesta con el agente y mostrar un indicador de carga
    with st.chat_message("assistant"):
        with st.spinner("El agente está inspeccionando la base de datos y razonando la respuesta..."):
            try:
                respuesta = preguntar_al_agente(prompt_usuario, verbose=modo_verbose)
                st.markdown(respuesta)
                st.session_state.messages.append({"role": "assistant", "content": respuesta})
            except Exception as e:
                mensaje_error = f"Ocurrió un error al procesar la solicitud: `{str(e)}`"
                st.error(mensaje_error)
                st.session_state.messages.append({"role": "assistant", "content": mensaje_error})
