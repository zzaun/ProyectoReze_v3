"""
lectorcapas.py

Se encarga de leer la informacion de archivos excel con formato de
"capas" (usando pandas) y exponerla mediante tres funciones:

    getListGruposCapas(archivo=RUTA_ARCHIVO_DEFECTO)
    getListCapaPorGrupoCapa(grupoCapa, archivo=RUTA_ARCHIVO_DEFECTO)
    getListCoordenadas(grupoCapa, indice, archivo=RUTA_ARCHIVO_DEFECTO)

El parametro 'archivo' permite reutilizar este mismo lector tanto para
capas.xlsx (imagenes estaticas) como para fotogramas.xlsx (animacion:
cada hoja = un fotograma) u otro archivo cualquiera con el mismo
formato. Si no se especifica, se usa capas.xlsx por defecto.

Estructura esperada dentro de cada hoja (grupoCapa / fotograma):
    CAPA    <nombre>
    TIPO    <tipo>
    COLOR   <color>
    GROSOR  <numero>
    X       Y
    <x1>    <y1>
    <x2>    <y2>
    ...
    CAPA    <siguiente capa>
    ...

Un mismo grupoCapa (hoja) puede tener varias capas con el mismo nombre,
por eso getListCapaPorGrupoCapa agrega un "indice" interno (no existe en
el excel) que identifica sin ambiguedad cada bloque, respetando el orden
de aparicion en la hoja, que es el mismo orden en que se dibujaran.

CACHE CON RECARGA AUTOMATICA:
Cada archivo leido se guarda en memoria junto con su fecha de
modificacion. En cada llamada se compara esa fecha contra la fecha
actual del archivo en disco (una operacion muy barata, no implica leer
el excel): si no cambio, se usa lo que ya esta en memoria (rapido, sin
tocar disco de nuevo); si cambio (por ejemplo, editaste y guardaste el
excel mientras el programa corria), se recarga automaticamente. Esto
permite iterar viendo los cambios en vivo, sin reiniciar el programa,
y sin pagar el costo de releer el archivo en cada frame si no hizo
falta.
"""

import os

import pandas as pd

import mensaje

RUTA_ARCHIVO_DEFECTO = "capas.xlsx"

COLOR_DEFECTO = "#000000"
GROSOR_DEFECTO = 10
TIPO_DEFECTO = "BACKGROUND"

_ETIQUETA_CAPA = "CAPA"
_ETIQUETA_TIPO = "TIPO"
_ETIQUETA_COLOR = "COLOR"
_ETIQUETA_GROSOR = "GROSOR"
_ETIQUETA_HEADER_X = "X"

# Cache: { ruta_archivo: {"mtime": float, "excel_file": pd.ExcelFile,
#                          "sheet_names": [...], "bloques": {hoja: [...]}} }
_cache = {}


def _normalizar_texto(valor):
    """Convierte el valor de una celda a texto limpio, o None si esta vacio/NaN."""
    if valor is None:
        return None
    if isinstance(valor, float) and pd.isna(valor):
        return None
    texto = str(valor).strip()
    return texto if texto != "" else None


def _es_etiqueta(valor, etiqueta):
    texto = _normalizar_texto(valor)
    return texto is not None and texto.upper() == etiqueta


def _obtener_mtime(archivo):
    try:
        return os.path.getmtime(archivo)
    except OSError:
        return None


def _obtener_entrada_cache(archivo):
    """
    Regresa la entrada de cache para 'archivo', (re)cargando el excel
    si es la primera vez que se pide o si el archivo cambio en disco
    desde la ultima vez. Regresa None si el archivo no se pudo abrir.
    """
    mtime_actual = _obtener_mtime(archivo)
    if mtime_actual is None:
        mensaje.error(f"No se encontro el archivo '{archivo}'.")
        _cache.pop(archivo, None)
        return None

    entrada = _cache.get(archivo)
    if entrada is not None and entrada["mtime"] == mtime_actual:
        return entrada

    try:
        excel_file = pd.ExcelFile(archivo)
    except Exception as e:
        mensaje.error(f"No se pudo abrir '{archivo}': {e}")
        _cache.pop(archivo, None)
        return None

    entrada = {
        "mtime": mtime_actual,
        "excel_file": excel_file,
        "sheet_names": excel_file.sheet_names,
        "bloques": {},
    }
    _cache[archivo] = entrada
    mensaje.info(f"'{archivo}' cargado/recargado ({len(entrada['sheet_names'])} hoja(s)).")
    return entrada


def _obtener_bloques_hoja(entrada, hoja, archivo):
    """Regresa (con cache) los bloques ya parseados de una hoja."""
    if hoja in entrada["bloques"]:
        return entrada["bloques"][hoja]

    try:
        df = pd.read_excel(entrada["excel_file"], sheet_name=hoja, header=None)
    except Exception as e:
        mensaje.error(f"No se pudo leer la hoja '{hoja}' de '{archivo}': {e}")
        return []

    bloques = _parsear_bloques_hoja(df, hoja)
    entrada["bloques"][hoja] = bloques
    return bloques


def _valor_celda(df, fila, columna):
    """Regresa el valor crudo de una celda, o None si esta fuera de rango."""
    if fila >= len(df.index) or columna >= len(df.columns):
        return None
    return df.iat[fila, columna]


def _parsear_bloques_hoja(df, hoja_nombre):
    """
    Recorre el DataFrame crudo de una hoja y regresa una lista de bloques,
    cada uno un dict:
        {
            "nombreCapa": str,
            "tipo": str,
            "color": str,
            "grosor": float,
            "coordenadas": [(x, y), ...],
        }
    en el mismo orden en que aparecen en la hoja.
    """
    bloques = []
    bloque_actual = None
    total_filas = len(df.index)

    for fila in range(total_filas):
        col_a = _valor_celda(df, fila, 0)
        col_b = _valor_celda(df, fila, 1)

        if _es_etiqueta(col_a, _ETIQUETA_CAPA):
            nombre_capa = _normalizar_texto(col_b)
            if nombre_capa is None:
                mensaje.advertencia(
                    f"Hoja '{hoja_nombre}', fila {fila + 1}: 'CAPA' sin nombre, "
                    f"se usara 'SIN_NOMBRE'."
                )
                nombre_capa = "SIN_NOMBRE"

            bloque_actual = {
                "nombreCapa": nombre_capa,
                "tipo": None,
                "color": None,
                "grosor": None,
                "coordenadas": [],
            }
            bloques.append(bloque_actual)
            continue

        if bloque_actual is None:
            # Contenido antes de la primera etiqueta CAPA: se ignora.
            continue

        if _es_etiqueta(col_a, _ETIQUETA_TIPO):
            bloque_actual["tipo"] = _normalizar_texto(col_b)
            continue

        if _es_etiqueta(col_a, _ETIQUETA_COLOR):
            bloque_actual["color"] = _normalizar_texto(col_b)
            continue

        if _es_etiqueta(col_a, _ETIQUETA_GROSOR):
            texto_grosor = _normalizar_texto(col_b)
            if texto_grosor is not None:
                try:
                    bloque_actual["grosor"] = float(texto_grosor)
                except ValueError:
                    mensaje.advertencia(
                        f"Hoja '{hoja_nombre}', capa '{bloque_actual['nombreCapa']}': "
                        f"GROSOR invalido ('{texto_grosor}')."
                    )
            continue

        if _es_etiqueta(col_a, _ETIQUETA_HEADER_X):
            # Fila de encabezado "X | Y", no aporta datos.
            continue

        # Si no es ninguna etiqueta conocida, se intenta leer como fila de
        # coordenadas (x, y) siempre que ambas columnas tengan numeros.
        texto_a = _normalizar_texto(col_a)
        texto_b = _normalizar_texto(col_b)
        if texto_a is not None and texto_b is not None:
            try:
                x = float(texto_a)
                y = float(texto_b)
                bloque_actual["coordenadas"].append((x, y))
            except ValueError:
                mensaje.advertencia(
                    f"Hoja '{hoja_nombre}', fila {fila + 1}: contenido no reconocido "
                    f"('{col_a}', '{col_b}'), se omite."
                )

    return bloques


def _aplicar_defectos(hoja_nombre, bloque):
    """Aplica los valores por defecto acordados cuando falta un campo."""
    if bloque["tipo"] is None:
        mensaje.advertencia(
            f"Hoja '{hoja_nombre}', capa '{bloque['nombreCapa']}': TIPO no "
            f"especificado, se usara '{TIPO_DEFECTO}'."
        )
        bloque["tipo"] = TIPO_DEFECTO

    if bloque["color"] is None:
        mensaje.advertencia(
            f"Hoja '{hoja_nombre}', capa '{bloque['nombreCapa']}': COLOR no "
            f"especificado, se usara '{COLOR_DEFECTO}'."
        )
        bloque["color"] = COLOR_DEFECTO

    if bloque["grosor"] is None:
        mensaje.advertencia(
            f"Hoja '{hoja_nombre}', capa '{bloque['nombreCapa']}': GROSOR no "
            f"especificado, se usara el maximo ({GROSOR_DEFECTO})."
        )
        bloque["grosor"] = GROSOR_DEFECTO

    return bloque


def getListGruposCapas(archivo=RUTA_ARCHIVO_DEFECTO):
    """
    Regresa la lista de nombres de hoja (grupoCapa o fotograma, segun el
    archivo), en el orden en que aparecen dentro del archivo.
    """
    entrada = _obtener_entrada_cache(archivo)
    if entrada is None:
        return []

    return entrada["sheet_names"]


def getListCapaPorGrupoCapa(grupoCapa, archivo=RUTA_ARCHIVO_DEFECTO):
    """
    Regresa la lista de capas de una hoja (grupoCapa), en orden de
    aparicion. Cada elemento es un dict con:
        indice, grupoCapa, nombreCapa, tipo, color, grosor

    'indice' es puramente interno (no existe en el excel) y sirve para
    identificar capas sin ambiguedad cuando se repite el nombreCapa
    dentro del mismo grupoCapa.
    """
    entrada = _obtener_entrada_cache(archivo)
    if entrada is None:
        return []

    if grupoCapa not in entrada["sheet_names"]:
        mensaje.error(f"El grupoCapa '{grupoCapa}' no existe en '{archivo}'.")
        return []

    bloques = _obtener_bloques_hoja(entrada, grupoCapa, archivo)

    resultado = []
    for indice, bloque in enumerate(bloques):
        bloque = _aplicar_defectos(grupoCapa, bloque)
        resultado.append({
            "indice": indice,
            "grupoCapa": grupoCapa,
            "nombreCapa": bloque["nombreCapa"],
            "tipo": bloque["tipo"],
            "color": bloque["color"],
            "grosor": bloque["grosor"],
        })

    return resultado


def getListCoordenadas(grupoCapa, indice, archivo=RUTA_ARCHIVO_DEFECTO):
    """
    Regresa la lista de coordenadas [(x, y), ...] de la capa identificada
    por 'indice' dentro del grupoCapa dado. El 'indice' es el mismo que
    entrega getListCapaPorGrupoCapa.
    """
    entrada = _obtener_entrada_cache(archivo)
    if entrada is None:
        return []

    if grupoCapa not in entrada["sheet_names"]:
        mensaje.error(f"El grupoCapa '{grupoCapa}' no existe en '{archivo}'.")
        return []

    bloques = _obtener_bloques_hoja(entrada, grupoCapa, archivo)

    if indice < 0 or indice >= len(bloques):
        mensaje.error(
            f"Indice {indice} fuera de rango para grupoCapa '{grupoCapa}' "
            f"en '{archivo}' (hay {len(bloques)} capa(s))."
        )
        return []

    coordenadas = bloques[indice]["coordenadas"]
    if not coordenadas:
        mensaje.advertencia(
            f"GrupoCapa '{grupoCapa}' en '{archivo}', indice {indice}: no tiene coordenadas."
        )

    return coordenadas