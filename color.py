"""
color.py

Recibe un color en distintos formatos (con alta tolerancia a errores de
escritura) y lo convierte a una tupla RGBA de floats en el rango [0, 1],
lista para usarse en OpenGL (por ejemplo con glColor4f(*color)).

Formatos soportados (no distingue mayusculas/minusculas ni espacios):
    "0,0,0"            -> RGB decimal (0-255), separado por comas
    "0,0,0,0"          -> RGBA decimal (0-255), separado por comas
    "(0,0,0)"          -> RGB decimal entre parentesis
    "(0, 0,0,0)"       -> RGBA decimal entre parentesis, con o sin espacios
    "#000000"          -> RGB hexadecimal (6 digitos)
    "000000"           -> RGB hexadecimal (6 digitos), sin '#'
    "#0000"            -> RGBA hexadecimal corto (4 digitos, estilo CSS)
    "0000"             -> RGBA hexadecimal corto (4 digitos), sin '#'
    "#000"             -> RGB hexadecimal corto (3 digitos, estilo CSS)
    "#00000000"        -> RGBA hexadecimal (8 digitos)
    "rgb(255,0,0)"     -> RGB estilo CSS
    "rgba(255,0,0,128)"-> RGBA estilo CSS
    "rojo", "black"... -> algunos nombres comunes de color

Si el valor no se puede interpretar, se reporta con mensaje.advertencia
y se regresa el color por defecto (negro opaco), para nunca detener el
programa por un color mal escrito.
"""

import re
import mensaje

COLOR_DEFECTO = (0.0, 0.0, 0.0, 1.0)

_NOMBRES_COLOR = {
    "negro": (0, 0, 0), "black": (0, 0, 0),
    "blanco": (255, 255, 255), "white": (255, 255, 255),
    "rojo": (255, 0, 0), "red": (255, 0, 0),
    "verde": (0, 255, 0), "green": (0, 255, 0),
    "azul": (0, 0, 255), "blue": (0, 0, 255),
    "amarillo": (255, 255, 0), "yellow": (255, 255, 0),
    "gris": (128, 128, 128), "gray": (128, 128, 128), "grey": (128, 128, 128),
    "naranja": (255, 165, 0), "orange": (255, 165, 0),
    "morado": (128, 0, 128), "purple": (128, 0, 128),
    "transparente": (0, 0, 0, 0), "transparent": (0, 0, 0, 0),
}

_PATRON_HEX = re.compile(r"^[0-9a-f]+$")

def _clamp01(valor):
    return max(0.0, min(1.0, valor))

def _limpiar(valor):
    """Deja el string en su forma minima: sin espacios, sin '#', sin
    prefijos rgb()/rgba(), sin parentesis, en minusculas."""
    texto = str(valor).strip().lower()
    texto = re.sub(r"^rgba?\(", "", texto)
    texto = texto.replace("(", "").replace(")", "")
    texto = texto.strip()
    if texto.startswith("#"):
        texto = texto[1:]
    return texto.strip()

def _desde_componentes_decimales(tokens):
    """
    Convierte una lista de tokens numericos (texto) a [r, g, b, (a)] en
    rango [0, 1]. Tolera tanto escala 0-255 como escala 0-1.
    Regresa None si algun token no es un numero valido.
    """
    valores = []
    for token in tokens:
        token = token.strip()
        if token == "":
            continue
        try:
            valores.append(float(token))
        except ValueError:
            return None

    if len(valores) not in (3, 4):
        return None

    parece_normalizado = all(0.0 <= v <= 1.0 for v in valores) and \
        any("." in t for t in tokens if t.strip() != "")

    resultado = []
    for v in valores:
        if parece_normalizado:
            resultado.append(_clamp01(v))
        else:
            resultado.append(_clamp01(v / 255.0))

    if len(resultado) == 3:
        resultado.append(1.0)

    return resultado

def _desde_hex(cadena):
    """
    Convierte una cadena hexadecimal pura (sin '#') de 3, 4, 6 u 8
    digitos a [r, g, b, a] en rango [0, 1]. Regresa None si no aplica.
    """
    if not _PATRON_HEX.fullmatch(cadena):
        return None

    longitud = len(cadena)
    try:
        if longitud == 3:
            r, g, b = (cadena[i] * 2 for i in range(3))
            a = "ff"
        elif longitud == 4:
            r, g, b, a = (cadena[i] * 2 for i in range(4))
        elif longitud == 6:
            r, g, b, a = cadena[0:2], cadena[2:4], cadena[4:6], "ff"
        elif longitud == 8:
            r, g, b, a = cadena[0:2], cadena[2:4], cadena[4:6], cadena[6:8]
        else:
            return None

        return [
            int(r, 16) / 255.0,
            int(g, 16) / 255.0,
            int(b, 16) / 255.0,
            int(a, 16) / 255.0,
        ]
    except ValueError:
        return None

def _desde_nombre(cadena):
    if cadena not in _NOMBRES_COLOR:
        return None

    componentes = _NOMBRES_COLOR[cadena]
    r, g, b = componentes[0], componentes[1], componentes[2]
    a = componentes[3] if len(componentes) == 4 else 255
    return [_clamp01(r / 255.0), _clamp01(g / 255.0), _clamp01(b / 255.0), _clamp01(a / 255.0)]

def obtenerColorOpenGL(valorColor):
    """
    Punto de entrada principal. Recibe el color en cualquiera de los
    formatos soportados y regresa siempre una tupla (r, g, b, a) de
    floats en [0, 1], lista para usarse en OpenGL.

    Ante cualquier formato no reconocido, reporta la advertencia via
    mensaje.py y regresa COLOR_DEFECTO (negro opaco) en vez de fallar.
    """
    if valorColor is None:
        mensaje.advertencia("Color vacio, se usara el color por defecto (negro).")
        return COLOR_DEFECTO

    # Ya viene como tupla/lista de numeros: se toma tal cual (con clamp).
    if isinstance(valorColor, (tuple, list)):
        resultado = _desde_componentes_decimales([str(v) for v in valorColor])
        return tuple(resultado) if resultado is not None else COLOR_DEFECTO

    texto_original = str(valorColor).strip()
    texto = _limpiar(texto_original)

    if texto == "":
        mensaje.advertencia("Color vacio, se usara el color por defecto (negro).")
        return COLOR_DEFECTO

    resultado = None

    if "," in texto:
        tokens = texto.split(",")
        resultado = _desde_componentes_decimales(tokens)
    else:
        resultado = _desde_nombre(texto)
        if resultado is None:
            resultado = _desde_hex(texto)

    if resultado is None:
        mensaje.advertencia(
            f"No se pudo interpretar el color '{texto_original}', "
            f"se usara el color por defecto (negro)."
        )
        return COLOR_DEFECTO

    return tuple(resultado)