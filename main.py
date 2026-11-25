"""
main.py
-------
Punto de entrada interactivo para el Agente DBA de Analitica SQL.
Implementa una interfaz de linea de comandos (CLI) con ciclo REPL
(Read-Eval-Print Loop) para consultar la base de datos en lenguaje natural.
"""
import os
import sys

from agent import preguntar_al_agente


def mostrar_banner() -> None:
    """Muestra el mensaje de bienvenida y comandos rapidos."""
    print("=" * 65)
    print("   AGENTE DBA / ASISTENTE DE ANALÍTICA SQL CON GEMINI   ")
    print("=" * 65)
    print("Puedes realizar preguntas sobre empleados, puestos y productos.")
    print("Comandos disponibles:")
    print("  'modo'    -> Alterna entre ver la traza técnica (verbose) o no.")
    print("  'ejemplos'-> Muestra ideas de consultas analíticas.")
    print("  'salir'   -> Finaliza la sesión.")
    print("-" * 65)


def mostrar_ejemplos() -> None:
    """Muestra preguntas de prueba sugeridas para los estudiantes."""
    print("\n[Preguntas de prueba sugeridas]:")
    print(" 1. ¿Cuál es el producto con el mayor valor de inventario total (precio * stock)?")
    print(" 2. Lista los empleados inactivos y qué puesto tenían asignado.")
    print(" 3. ¿Existen productos que actualmente no tengan ningún empleado responsable asignado?")
    print(" 4. Dame el promedio de precio de los productos gestionados por gerentes ('GE').")
    print(" 5. Intenta borrar a un empleado con id 1 (para probar los guardrails de seguridad).")
    print("-" * 65)


def iniciar_consola() -> None:
    """Bucle principal de interaccion con el usuario."""
    # Validar que exista la base de datos antes de arrancar
    if not os.path.exists("tienda_django.db"):
        print("[Alerta] No se encontró el archivo 'tienda_django.db'.")
        print("Ejecutando inicialización automática desde 'database.py'...")
        from database import init_db, seed_db
        init_db()
        seed_db()
        print("-" * 65)

    mostrar_banner()
    modo_verbose = True

    while True:
        try:
            # Captura de la entrada del usuario
            estado_modo = "ON" if modo_verbose else "OFF"
            prompt_texto = f"\n[Verbose: {estado_modo}] Consulta > "
            entrada = input(prompt_texto).strip()

            # Manejo de entradas vacias
            if not entrada:
                continue

            # Comandos de control
            if entrada.lower() in ("salir", "exit", "quit"):
                print("\nCerrando conexión con el agente. ¡Hasta luego!\n")
                sys.exit(0)

            if entrada.lower() == "modo":
                modo_verbose = not modo_verbose
                print(f"[Sistema] Modo detallado (verbose) establecido en: {'ACTIVADO' if modo_verbose else 'DESACTIVADO'}")
                continue

            if entrada.lower() == "ejemplos":
                mostrar_ejemplos()
                continue

            # Procesamiento de la consulta con el agente
            respuesta = preguntar_al_agente(entrada, verbose=modo_verbose)

            # Presentacion del resultado
            print("\n" + "=" * 65)
            print("[RESPUESTA FINAL]")
            print("=" * 65)
            print(respuesta)
            print("=" * 65)

        except KeyboardInterrupt:
            # Permite salir limpiamente con Ctrl + C
            print("\n\nSesión interrumpida por el usuario. ¡Hasta luego!\n")
            sys.exit(0)
        except Exception as e:
            print(f"\n[Error imprevisto]: {str(e)}")


if __name__ == "__main__":
    iniciar_consola()
