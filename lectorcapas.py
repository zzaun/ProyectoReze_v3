# lectorcapas.py
#
# Lee la información de los Excel con formato de "capas" (usando pandas) y la
# entrega con tres funciones:
#
#   getListGruposCapas(archivo=RUTA_ARCHIVO_DEFECTO)
#   getListCapaPorGrupoCapa(grupoCapa, archivo=RUTA_ARCHIVO_DEFECTO)
#   getListCoordenadas(grupoCapa, indice, archivo=RUTA_ARCHIVO_DEFECTO)
#
# El parámetro 'archivo' permite usar el mismo lector con capas.xlsx (imagen
# estática), con fotogramas.xlsx (animación: cada hoja es un fotograma) o con
# cualquier otro Excel con el mismo formato. Si no se indica, se usa capas.xlsx.
#
# Estructura que se espera dentro de cada hoja (grupoCapa / fotograma):
#   CAPA    <nombre>
#   TIPO    <tipo>
#   COLOR   <color>
#   GROSOR  <número>
#   X       Y
#   <x1>    <y1>
#   <x2>    <y2>
#   ...
#   CAPA    <siguiente capa>
#   ...
#
# Una misma hoja puede tener varias capas con el mismo nombre. Por eso
# getListCapaPorGrupoCapa agrega un "indice" interno (no existe en el Excel)
# que identifica cada bloque sin confundirlos. Respeta el orden en que
# aparecen en la hoja, que es el mismo orden en que se dibujan.
#
# CACHÉ CON RECARGA AUTOMÁTICA:
# Cada archivo leído se guarda en memoria junto con su fecha de modificación.
# En cada llamada se compara esa fecha con la fecha actual del archivo en
# disco (es una operación muy barata, no lee el Excel). Si no cambió, se usa
# lo que ya está en memoria. Si cambió (por ejemplo, editaste y guardaste el
# Excel con el programa corriendo), se vuelve a leer solo. Así se ven los
# cambios en vivo sin reiniciar y sin releer el archivo en cada frame.

# os sirve para preguntarle al sistema la fecha de modificación de un archivo
import os

# pandas sirve para leer los Excel (se le llama "pd" para escribir menos)
import pandas as pd

# Para imprimir avisos y errores en la consola
import mensaje

# Archivo que se usa si no se indica otro
RUTA_ARCHIVO_DEFECTO = "capas.xlsx"

# Color que se usa si la capa no trae COLOR (negro)
COLOR_DEFECTO = "#000000"
# Grosor que se usa si la capa no trae GROSOR
GROSOR_DEFECTO = 10
# Tipo que se usa si la capa no trae TIPO
TIPO_DEFECTO = "BACKGROUND"

# Palabras que se buscan en la primera columna del Excel para saber qué es
# cada fila. Se comparan en mayúsculas.
# Marca el inicio de una capa nueva
_ETIQUETA_CAPA = "CAPA"
# Fila con el tipo de la capa
_ETIQUETA_TIPO = "TIPO"
# Fila con el color de la capa
_ETIQUETA_COLOR = "COLOR"
# Fila con el grosor de la capa
_ETIQUETA_GROSOR = "GROSOR"
# Fila de encabezado "X | Y" que antecede a las coordenadas
_ETIQUETA_HEADER_X = "X"

# Caché: guarda lo que ya se leyó de cada archivo. Es un diccionario con esta forma:
#   { ruta_archivo: {"mtime": fecha de modificación, "excel_file": el Excel abierto,
#                    "sheet_names": [nombres de hojas], "bloques": {hoja: [...]}} }
_cache = {}


# _normalizar_texto(valor): convierte el valor de una celda a texto limpio.
# Regresa None si la celda está vacía o es NaN (el "vacío" de pandas).
def _normalizar_texto(valor):
    # Si no hay valor, regresa None
    if valor is None:
        return None
    # Si es un decimal que es NaN (celda vacía en pandas), regresa None
    if isinstance(valor, float) and pd.isna(valor):
        return None
    # Lo convierte a texto y le quita los espacios de los lados
    texto = str(valor).strip()
    # Si quedó vacío regresa None, si no, el texto
    return texto if texto != "" else None


# _es_etiqueta(valor, etiqueta): dice si la celda contiene esa etiqueta
# (por ejemplo "CAPA"), sin importar mayúsculas ni espacios
def _es_etiqueta(valor, etiqueta):
    # Limpia el texto de la celda
    texto = _normalizar_texto(valor)
    # True solo si hay texto y, en mayúsculas, es igual a la etiqueta
    return texto is not None and texto.upper() == etiqueta


# _obtener_mtime(archivo): regresa la fecha de última modificación del archivo,
# o None si el archivo no existe o no se puede consultar
def _obtener_mtime(archivo):
    # Intenta pedirle la fecha al sistema
    try:
        return os.path.getmtime(archivo)
    # Si falla (por ejemplo, no existe el archivo), regresa None
    except OSError:
        return None


# _obtener_entrada_cache(archivo): regresa lo guardado en la caché para el
# archivo. Lo carga (o lo recarga) si es la primera vez que se pide o si el
# archivo cambió en disco. Regresa None si no se pudo abrir.
def _obtener_entrada_cache(archivo):
    # Fecha de modificación actual del archivo
    mtime_actual = _obtener_mtime(archivo)
    # Si no se pudo obtener, el archivo no existe: avisa y borra lo que hubiera en la caché
    if mtime_actual is None:
        mensaje.error(f"No se encontro el archivo '{archivo}'.")
        _cache.pop(archivo, None)
        return None

    # Busca si ya hay algo guardado de este archivo
    entrada = _cache.get(archivo)
    # Si ya estaba y la fecha es la misma, el archivo no cambió: se usa lo guardado
    if entrada is not None and entrada["mtime"] == mtime_actual:
        return entrada

    # Si llega aquí, hay que leer el Excel (primera vez o cambió). Intenta abrirlo.
    try:
        excel_file = pd.ExcelFile(archivo)
    # Si falla, avisa, borra lo que hubiera en la caché y regresa None
    except Exception as e:
        mensaje.error(f"No se pudo abrir '{archivo}': {e}")
        _cache.pop(archivo, None)
        return None

    # Arma la entrada nueva de la caché
    entrada = {
        # Fecha de modificación que tenía el archivo al leerlo
        "mtime": mtime_actual,
        # El Excel ya abierto
        "excel_file": excel_file,
        # Nombres de todas las hojas, en orden
        "sheet_names": excel_file.sheet_names,
        # Aquí se irán guardando las hojas ya procesadas (empieza vacío)
        "bloques": {},
    }
    # La guarda en la caché
    _cache[archivo] = entrada
    # Avisa por consola que el archivo se cargó
    mensaje.info(f"'{archivo}' cargado/recargado ({len(entrada['sheet_names'])} hoja(s)).")
    # Regresa la entrada
    return entrada


# _obtener_bloques_hoja(entrada, hoja, archivo): regresa los bloques (capas) ya
# procesados de una hoja. Usa la caché: cada hoja se procesa una sola vez.
def _obtener_bloques_hoja(entrada, hoja, archivo):
    # Si esta hoja ya se procesó antes, regresa lo guardado
    if hoja in entrada["bloques"]:
        return entrada["bloques"][hoja]

    # Intenta leer la hoja como tabla. header=None significa que la primera fila NO es encabezado.
    try:
        df = pd.read_excel(entrada["excel_file"], sheet_name=hoja, header=None)
    # Si falla, avisa y regresa una lista vacía
    except Exception as e:
        mensaje.error(f"No se pudo leer la hoja '{hoja}' de '{archivo}': {e}")
        return []

    # Convierte la tabla en una lista de bloques (capas)
    bloques = _parsear_bloques_hoja(df, hoja)
    # Guarda el resultado en la caché para no repetir el trabajo
    entrada["bloques"][hoja] = bloques
    # Regresa los bloques
    return bloques


# _valor_celda(df, fila, columna): regresa el valor de una celda, o None si
# esa posición no existe en la tabla
def _valor_celda(df, fila, columna):
    # Si la fila o la columna se pasan del tamaño de la tabla, regresa None
    if fila >= len(df.index) or columna >= len(df.columns):
        return None
    # iat lee una celda por su posición (número de fila y número de columna)
    return df.iat[fila, columna]


# _parsear_bloques_hoja(df, hoja_nombre): recorre la tabla de una hoja y regresa
# una lista de bloques (uno por capa), en el mismo orden que la hoja. Cada
# bloque es un diccionario así:
#   {
#       "nombreCapa": texto,
#       "tipo": texto,
#       "color": texto,
#       "grosor": número,
#       "coordenadas": [(x, y), ...],
#   }
def _parsear_bloques_hoja(df, hoja_nombre):
    # Lista donde se van agregando los bloques
    bloques = []
    # Bloque que se está llenando en este momento (todavía no hay ninguno)
    bloque_actual = None
    # Cantidad de filas de la hoja
    total_filas = len(df.index)

    # Recorre la hoja fila por fila
    for fila in range(total_filas):
        # Valor de la primera columna (donde van las etiquetas o la X)
        col_a = _valor_celda(df, fila, 0)
        # Valor de la segunda columna (donde van los datos o la Y)
        col_b = _valor_celda(df, fila, 1)

        # Si la fila dice "CAPA", empieza una capa nueva
        if _es_etiqueta(col_a, _ETIQUETA_CAPA):
            # El nombre de la capa está en la segunda columna
            nombre_capa = _normalizar_texto(col_b)
            # Si no tiene nombre, avisa y usa "SIN_NOMBRE" (fila + 1 porque en Excel se cuenta desde 1)
            if nombre_capa is None:
                mensaje.advertencia(
                    f"Hoja '{hoja_nombre}', fila {fila + 1}: 'CAPA' sin nombre, "
                    f"se usara 'SIN_NOMBRE'."
                )
                nombre_capa = "SIN_NOMBRE"

            # Crea el bloque nuevo. Tipo, color y grosor empiezan vacíos y se llenan con las filas siguientes.
            bloque_actual = {
                "nombreCapa": nombre_capa,
                "tipo": None,
                "color": None,
                "grosor": None,
                "coordenadas": [],
            }
            # Lo agrega a la lista de bloques
            bloques.append(bloque_actual)
            # Pasa a la siguiente fila
            continue

        # Si todavía no hay ninguna capa abierta, se ignora la fila
        if bloque_actual is None:
            continue

        # Si la fila dice "TIPO", guarda el tipo en el bloque
        if _es_etiqueta(col_a, _ETIQUETA_TIPO):
            bloque_actual["tipo"] = _normalizar_texto(col_b)
            continue

        # Si la fila dice "COLOR", guarda el color en el bloque
        if _es_etiqueta(col_a, _ETIQUETA_COLOR):
            bloque_actual["color"] = _normalizar_texto(col_b)
            continue

        # Si la fila dice "GROSOR", guarda el grosor como número
        if _es_etiqueta(col_a, _ETIQUETA_GROSOR):
            # Texto de la celda del grosor
            texto_grosor = _normalizar_texto(col_b)
            # Solo si la celda no está vacía
            if texto_grosor is not None:
                # Intenta convertirlo a número
                try:
                    bloque_actual["grosor"] = float(texto_grosor)
                # Si no es un número, avisa (el grosor queda vacío y luego se usa el de por defecto)
                except ValueError:
                    mensaje.advertencia(
                        f"Hoja '{hoja_nombre}', capa '{bloque_actual['nombreCapa']}': "
                        f"GROSOR invalido ('{texto_grosor}')."
                    )
            continue

        # Si la fila dice "X", es el encabezado "X | Y" y no trae datos
        if _es_etiqueta(col_a, _ETIQUETA_HEADER_X):
            continue

        # Si no es ninguna etiqueta conocida, se intenta leer como una fila de
        # coordenadas (x, y), siempre que las dos columnas tengan algo.
        # Texto de la primera columna (X)
        texto_a = _normalizar_texto(col_a)
        # Texto de la segunda columna (Y)
        texto_b = _normalizar_texto(col_b)
        # Solo si las dos columnas tienen datos
        if texto_a is not None and texto_b is not None:
            # Intenta convertir los dos a número
            try:
                # X como número
                x = float(texto_a)
                # Y como número
                y = float(texto_b)
                # Agrega el punto (x, y) a las coordenadas de la capa actual
                bloque_actual["coordenadas"].append((x, y))
            # Si alguno no es número, avisa y se omite la fila
            except ValueError:
                mensaje.advertencia(
                    f"Hoja '{hoja_nombre}', fila {fila + 1}: contenido no reconocido "
                    f"('{col_a}', '{col_b}'), se omite."
                )

    # Regresa todos los bloques encontrados
    return bloques


# _aplicar_defectos(hoja_nombre, bloque): si a la capa le falta TIPO, COLOR o
# GROSOR, le pone el valor por defecto y avisa por consola
def _aplicar_defectos(hoja_nombre, bloque):
    # Si no tiene tipo, avisa y le pone el de por defecto
    if bloque["tipo"] is None:
        mensaje.advertencia(
            f"Hoja '{hoja_nombre}', capa '{bloque['nombreCapa']}': TIPO no "
            f"especificado, se usara '{TIPO_DEFECTO}'."
        )
        bloque["tipo"] = TIPO_DEFECTO

    # Si no tiene color, avisa y le pone el de por defecto
    if bloque["color"] is None:
        mensaje.advertencia(
            f"Hoja '{hoja_nombre}', capa '{bloque['nombreCapa']}': COLOR no "
            f"especificado, se usara '{COLOR_DEFECTO}'."
        )
        bloque["color"] = COLOR_DEFECTO

    # Si no tiene grosor, avisa y le pone el de por defecto
    if bloque["grosor"] is None:
        mensaje.advertencia(
            f"Hoja '{hoja_nombre}', capa '{bloque['nombreCapa']}': GROSOR no "
            f"especificado, se usara el maximo ({GROSOR_DEFECTO})."
        )
        bloque["grosor"] = GROSOR_DEFECTO

    # Regresa el bloque ya completo
    return bloque


# getListGruposCapas(archivo): regresa la lista con los nombres de las hojas
# (grupoCapa o fotograma, según el archivo), en el orden en que aparecen
def getListGruposCapas(archivo=RUTA_ARCHIVO_DEFECTO):
    # Obtiene el archivo desde la caché (lo carga si hace falta)
    entrada = _obtener_entrada_cache(archivo)
    # Si no se pudo abrir, regresa una lista vacía
    if entrada is None:
        return []

    # Regresa los nombres de las hojas
    return entrada["sheet_names"]


# getListCapaPorGrupoCapa(grupoCapa, archivo): regresa la lista de capas de una
# hoja (grupoCapa), en orden de aparición. Cada elemento es un diccionario con:
#   indice, grupoCapa, nombreCapa, tipo, color, grosor
#
# 'indice' es solo interno (no existe en el Excel) y sirve para identificar
# cada capa cuando el nombre se repite dentro de la misma hoja.
def getListCapaPorGrupoCapa(grupoCapa, archivo=RUTA_ARCHIVO_DEFECTO):
    # Obtiene el archivo desde la caché
    entrada = _obtener_entrada_cache(archivo)
    # Si no se pudo abrir, regresa una lista vacía
    if entrada is None:
        return []

    # Si la hoja pedida no existe en el archivo, avisa y regresa una lista vacía
    if grupoCapa not in entrada["sheet_names"]:
        mensaje.error(f"El grupoCapa '{grupoCapa}' no existe en '{archivo}'.")
        return []

    # Obtiene los bloques (capas) de esa hoja
    bloques = _obtener_bloques_hoja(entrada, grupoCapa, archivo)

    # Aquí se arma la lista que se va a regresar
    resultado = []
    # enumerate da la posición (indice) y el bloque al mismo tiempo
    for indice, bloque in enumerate(bloques):
        # Completa con valores por defecto lo que le falte a la capa
        bloque = _aplicar_defectos(grupoCapa, bloque)
        # Agrega un diccionario con los datos de la capa (sin las coordenadas, esas se piden aparte)
        resultado.append({
            "indice": indice,
            "grupoCapa": grupoCapa,
            "nombreCapa": bloque["nombreCapa"],
            "tipo": bloque["tipo"],
            "color": bloque["color"],
            "grosor": bloque["grosor"],
        })

    # Regresa la lista de capas
    return resultado


# getListCoordenadas(grupoCapa, indice, archivo): regresa la lista de
# coordenadas [(x, y), ...] de la capa que tiene ese 'indice' dentro de la
# hoja. Es el mismo índice que da getListCapaPorGrupoCapa.
def getListCoordenadas(grupoCapa, indice, archivo=RUTA_ARCHIVO_DEFECTO):
    # Obtiene el archivo desde la caché
    entrada = _obtener_entrada_cache(archivo)
    # Si no se pudo abrir, regresa una lista vacía
    if entrada is None:
        return []

    # Si la hoja no existe, avisa y regresa una lista vacía
    if grupoCapa not in entrada["sheet_names"]:
        mensaje.error(f"El grupoCapa '{grupoCapa}' no existe en '{archivo}'.")
        return []

    # Obtiene los bloques de esa hoja
    bloques = _obtener_bloques_hoja(entrada, grupoCapa, archivo)

    # Si el índice no existe (es negativo o se pasa de la cantidad de capas), avisa y regresa una lista vacía
    if indice < 0 or indice >= len(bloques):
        mensaje.error(
            f"Indice {indice} fuera de rango para grupoCapa '{grupoCapa}' "
            f"en '{archivo}' (hay {len(bloques)} capa(s))."
        )
        return []

    # Toma las coordenadas del bloque que se pidió
    coordenadas = bloques[indice]["coordenadas"]
    # Si esa capa no tiene coordenadas, avisa (igual se regresa la lista vacía)
    if not coordenadas:
        mensaje.advertencia(
            f"GrupoCapa '{grupoCapa}' en '{archivo}', indice {indice}: no tiene coordenadas."
        )

    # Regresa las coordenadas
    return coordenadas
