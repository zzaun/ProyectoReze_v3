# color.py
#
# Recibe un color escrito de muchas formas (con tolerancia a errores de
# escritura) y lo convierte a una tupla RGBA de decimales entre 0 y 1, que es
# lo que usa OpenGL (por ejemplo glColor4f(*color)).
#
# Formatos que acepta (no importan mayúsculas ni espacios):
#   "0,0,0"             -> RGB decimal (0-255), separado por comas
#   "0,0,0,0"           -> RGBA decimal (0-255), separado por comas
#   "(0,0,0)"           -> RGB decimal entre paréntesis
#   "(0, 0,0,0)"        -> RGBA decimal entre paréntesis, con o sin espacios
#   "#000000"           -> RGB hexadecimal (6 dígitos)
#   "000000"            -> RGB hexadecimal (6 dígitos), sin '#'
#   "#0000"             -> RGBA hexadecimal corto (4 dígitos, estilo CSS)
#   "0000"              -> RGBA hexadecimal corto (4 dígitos), sin '#'
#   "#000"              -> RGB hexadecimal corto (3 dígitos, estilo CSS)
#   "#00000000"         -> RGBA hexadecimal (8 dígitos)
#   "rgb(255,0,0)"      -> RGB estilo CSS
#   "rgba(255,0,0,128)" -> RGBA estilo CSS
#   "rojo", "black"...  -> algunos nombres comunes de color
#
# Si el valor no se puede entender, avisa con mensaje.advertencia y regresa el
# color por defecto (negro opaco). Así un color mal escrito nunca detiene el
# programa.

# re sirve para trabajar con expresiones regulares (buscar patrones en texto)
import re
# Para mostrar advertencias en la consola
import mensaje

# Color que se usa cuando no se puede entender el que llegó: negro, totalmente
# opaco. Está en el orden (rojo, verde, azul, alfa).
COLOR_DEFECTO = (0.0, 0.0, 0.0, 1.0)

# Diccionario con nombres de color (en español y en inglés) y su valor en escala
# 0-255. Cada valor es (rojo, verde, azul), o (rojo, verde, azul, alfa) cuando
# tiene transparencia. Todas las líneas siguen el mismo patrón, por eso solo se
# explica aquí.
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

# Patrón para saber si un texto son solo dígitos hexadecimales (0-9 y a-f).
# Es en minúsculas porque _limpiar() ya pasa todo a minúsculas.
_PATRON_HEX = re.compile(r"^[0-9a-f]+$")

# _clamp01(valor): limita un número para que quede entre 0 y 1
def _clamp01(valor):
    # min(1.0, valor) evita que pase de 1, y max(0.0, ...) evita que baje de 0
    return max(0.0, min(1.0, valor))

# _limpiar(valor): deja el texto en su forma mínima: sin espacios, sin '#',
# sin prefijo rgb(/rgba(, sin paréntesis y en minúsculas
def _limpiar(valor):
    # Lo convierte a texto, quita espacios de los lados y lo pasa a minúsculas
    texto = str(valor).strip().lower()
    # Si empieza con "rgb(" o "rgba(" ese pedazo se borra (la "?" hace opcional la "a")
    texto = re.sub(r"^rgba?\(", "", texto)
    # Quita los paréntesis que queden
    texto = texto.replace("(", "").replace(")", "")
    # Quita los espacios que pudieron quedar
    texto = texto.strip()
    # Si empieza con "#", se lo quita
    if texto.startswith("#"):
        texto = texto[1:]
    # Regresa el texto ya limpio
    return texto.strip()

# _desde_componentes_decimales(tokens): convierte una lista de textos con
# números (ej. ["255", "0", "0"]) a [r, g, b, a] entre 0 y 1. Acepta escala
# 0-255 y también escala 0-1. Regresa None si algún dato no es número o si no
# hay 3 o 4 valores.
def _desde_componentes_decimales(tokens):
    # Aquí se van guardando los números ya convertidos
    valores = []
    # Revisa cada pedazo de texto
    for token in tokens:
        # Le quita los espacios
        token = token.strip()
        # Si quedó vacío (por ejemplo, una coma de más) lo salta
        if token == "":
            continue
        # Intenta convertirlo a número decimal
        try:
            valores.append(float(token))
        # Si no es un número válido, no hay color y regresa None
        except ValueError:
            return None

    # Un color debe tener 3 valores (RGB) o 4 (RGBA). Si no, no sirve
    if len(valores) not in (3, 4):
        return None

    # Decide si los números ya vienen en escala 0-1. Para eso todos deben estar
    # entre 0 y 1 y al menos uno debe traer punto decimal. Así "1,0,0" se toma
    # como escala 0-255 y "1.0,0.0,0.0" como escala 0-1.
    parece_normalizado = all(0.0 <= v <= 1.0 for v in valores) and \
        any("." in t for t in tokens if t.strip() != "")

    # Aquí se guardan los valores ya convertidos a 0-1
    resultado = []
    # Revisa cada número
    for v in valores:
        # Si ya está en escala 0-1, solo se limita al rango
        if parece_normalizado:
            resultado.append(_clamp01(v))
        # Si está en escala 0-255, se divide entre 255 para pasarlo a 0-1
        else:
            resultado.append(_clamp01(v / 255.0))

    # Si no trajo alfa (solo 3 valores), se agrega 1.0 = totalmente opaco
    if len(resultado) == 3:
        resultado.append(1.0)

    # Regresa la lista [r, g, b, a]
    return resultado

# _desde_hex(cadena): convierte un texto hexadecimal sin '#' de 3, 4, 6 u 8
# dígitos a [r, g, b, a] entre 0 y 1. Regresa None si no aplica.
def _desde_hex(cadena):
    # Si el texto tiene algo que no sea hexadecimal, no aplica
    if not _PATRON_HEX.fullmatch(cadena):
        return None

    # Cuántos dígitos tiene, para saber en qué formato viene
    longitud = len(cadena)
    # try por si algún pedazo no se puede convertir a número
    try:
        # Formato corto de 3 dígitos (ej. "f0a"): cada dígito se repite (f -> ff)
        if longitud == 3:
            r, g, b = (cadena[i] * 2 for i in range(3))
            # Sin alfa: totalmente opaco
            a = "ff"
        # Formato corto de 4 dígitos: igual, pero el cuarto es el alfa
        elif longitud == 4:
            r, g, b, a = (cadena[i] * 2 for i in range(4))
        # Formato de 6 dígitos: dos por cada color, sin alfa (opaco)
        elif longitud == 6:
            r, g, b, a = cadena[0:2], cadena[2:4], cadena[4:6], "ff"
        # Formato de 8 dígitos: dos por cada color y dos para el alfa
        elif longitud == 8:
            r, g, b, a = cadena[0:2], cadena[2:4], cadena[4:6], cadena[6:8]
        # Cualquier otra cantidad de dígitos no es un color válido
        else:
            return None

        # int(x, 16) pasa de hexadecimal a número (0-255) y se divide entre 255
        # para dejarlo entre 0 y 1. Se hace igual con los cuatro valores.
        return [
            int(r, 16) / 255.0,
            int(g, 16) / 255.0,
            int(b, 16) / 255.0,
            int(a, 16) / 255.0,
        ]
    # Si algo falló al convertir, no hay color
    except ValueError:
        return None

# _desde_nombre(cadena): busca el nombre en el diccionario de colores y lo
# convierte a [r, g, b, a] entre 0 y 1. Regresa None si el nombre no existe.
def _desde_nombre(cadena):
    # Si el nombre no está en el diccionario, no aplica
    if cadena not in _NOMBRES_COLOR:
        return None

    # Toma los valores del color (3 o 4 números en escala 0-255)
    componentes = _NOMBRES_COLOR[cadena]
    # Separa rojo, verde y azul
    r, g, b = componentes[0], componentes[1], componentes[2]
    # Si el color trae alfa se usa, si no, es 255 (opaco)
    a = componentes[3] if len(componentes) == 4 else 255
    # Pasa los cuatro valores de 0-255 a 0-1 y los regresa en una lista
    return [_clamp01(r / 255.0), _clamp01(g / 255.0), _clamp01(b / 255.0), _clamp01(a / 255.0)]

# obtenerColorOpenGL(valorColor): es la función principal del archivo. Recibe
# el color en cualquiera de los formatos de arriba y siempre regresa una tupla
# (r, g, b, a) de decimales entre 0 y 1, lista para OpenGL. Si el formato no
# se reconoce, avisa por mensaje.py y regresa COLOR_DEFECTO en vez de fallar.
def obtenerColorOpenGL(valorColor):
    # Si no llegó nada, avisa y usa el color por defecto
    if valorColor is None:
        mensaje.advertencia("Color vacio, se usara el color por defecto (negro).")
        return COLOR_DEFECTO

    # Si ya viene como tupla o lista de números, se convierte directo
    if isinstance(valorColor, (tuple, list)):
        # Cada número se pasa a texto porque la función de abajo trabaja con textos
        resultado = _desde_componentes_decimales([str(v) for v in valorColor])
        # Si salió bien regresa la tupla, si no, el color por defecto
        return tuple(resultado) if resultado is not None else COLOR_DEFECTO

    # Guarda el texto original (sin limpiar) para usarlo en el mensaje de error
    texto_original = str(valorColor).strip()
    # Versión limpia del texto, que es la que se analiza
    texto = _limpiar(texto_original)

    # Si después de limpiar no quedó nada, avisa y usa el color por defecto
    if texto == "":
        mensaje.advertencia("Color vacio, se usara el color por defecto (negro).")
        return COLOR_DEFECTO

    # Aquí se guardará el color ya convertido
    resultado = None

    # Si tiene comas es un color decimal como "255,0,0"
    if "," in texto:
        # Separa el texto por comas
        tokens = texto.split(",")
        # Convierte los números a [r, g, b, a]
        resultado = _desde_componentes_decimales(tokens)
    # Si no tiene comas, puede ser un nombre o un hexadecimal
    else:
        # Primero prueba si es un nombre de color
        resultado = _desde_nombre(texto)
        # Si no era un nombre, prueba si es hexadecimal
        if resultado is None:
            resultado = _desde_hex(texto)

    # Si ninguna opción funcionó, avisa y usa el color por defecto
    if resultado is None:
        mensaje.advertencia(
            f"No se pudo interpretar el color '{texto_original}', "
            f"se usara el color por defecto (negro)."
        )
        return COLOR_DEFECTO

    # Todo salió bien: regresa el color como tupla (r, g, b, a)
    return tuple(resultado)
