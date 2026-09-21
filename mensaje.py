"""
mensaje.py

Unico responsable de imprimir en consola la informacion relevante del
sistema (info, advertencias y errores). El resto de los modulos no
deben usar print() directamente: siempre pasan por aqui, para tener un
formato consistente y poder cambiarlo en un solo lugar (por ejemplo,
silenciar mensajes, mandarlos a un log, etc.).
"""

_PREFIJO_INFO = "[INFO]"
_PREFIJO_ADVERTENCIA = "[ADVERTENCIA]"
_PREFIJO_ERROR = "[ERROR]"

# Colores ANSI, opcionales. Si la consola no los soporta simplemente se
# veran como texto plano sin romper nada.
_COLOR_INFO = "\033[36m"       # cian
_COLOR_ADVERTENCIA = "\033[33m"  # amarillo
_COLOR_ERROR = "\033[31m"       # rojo
_COLOR_RESET = "\033[0m"


def info(texto):
    """Informacion general del funcionamiento normal del programa."""
    print(f"{_COLOR_INFO}{_PREFIJO_INFO}{_COLOR_RESET} {texto}")


def advertencia(texto):
    """Algo no vino como se esperaba, pero el programa puede continuar
    (por ejemplo, se aplico un valor por defecto)."""
    print(f"{_COLOR_ADVERTENCIA}{_PREFIJO_ADVERTENCIA}{_COLOR_RESET} {texto}")


def error(texto):
    """Algo impidio completar la operacion solicitada."""
    print(f"{_COLOR_ERROR}{_PREFIJO_ERROR}{_COLOR_RESET} {texto}")