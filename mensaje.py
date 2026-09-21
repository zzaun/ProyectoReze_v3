# mensaje.py
#
# Aquí se imprimen todos los mensajes del programa en la consola: info,
# advertencias y errores. Los demás archivos no usan print() directo, siempre
# llaman a estas funciones. Así todos los mensajes se ven igual y, si un día
# queremos silenciarlos o guardarlos en un log, solo se cambia este archivo.

# Etiqueta que va al inicio de los mensajes normales
_PREFIJO_INFO = "[INFO]"
# Etiqueta de los avisos (algo no salió como se esperaba, pero el programa sigue)
_PREFIJO_ADVERTENCIA = "[ADVERTENCIA]"
# Etiqueta de los errores (algo impidió terminar lo que se pidió)
_PREFIJO_ERROR = "[ERROR]"

# Colores ANSI para la consola. Si la consola no los soporta, solo se ve
# texto normal y no pasa nada.
# Color cian para info
_COLOR_INFO = "\033[36m"
# Color amarillo para advertencias
_COLOR_ADVERTENCIA = "\033[33m"
# Color rojo para errores
_COLOR_ERROR = "\033[31m"
# Regresa la consola al color normal
_COLOR_RESET = "\033[0m"


# info(texto): imprime un mensaje del funcionamiento normal del programa
def info(texto):
    # Imprime el prefijo en cian, regresa al color normal y luego va el texto
    print(f"{_COLOR_INFO}{_PREFIJO_INFO}{_COLOR_RESET} {texto}")


# advertencia(texto): avisa que algo no vino como se esperaba pero el programa
# puede seguir (por ejemplo, se usó un valor por defecto)
def advertencia(texto):
    # Igual que info, pero con el prefijo y color de advertencia
    print(f"{_COLOR_ADVERTENCIA}{_PREFIJO_ADVERTENCIA}{_COLOR_RESET} {texto}")


# error(texto): avisa que algo impidió completar la operación
def error(texto):
    # Igual que info, pero con el prefijo y color de error
    print(f"{_COLOR_ERROR}{_PREFIJO_ERROR}{_COLOR_RESET} {texto}")
