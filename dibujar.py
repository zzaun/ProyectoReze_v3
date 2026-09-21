# dibujar.py
#
# Clase Dibujar: tiene toda la lógica para dibujar en pantalla las capas que
# lee lectorcapas.py.
#
# Reglas:
#   - TIPO = "BACKGROUND" -> se dibuja como RELLENO (polígono sólido).
#   - TIPO = "LINE"       -> se dibuja como BORDE (línea abierta: NO se une
#                            el último punto con el primero).
#   - Relleno y borde son métodos separados (dibujarRelleno y dibujarBorde)
#     para poder usarlos y ajustarlos por separado.
#   - Las capas se dibujan en el orden en que aparecen en la hoja del Excel
#     (el mismo que entrega lectorcapas.getListCapaPorGrupoCapa), no en orden
#     alfabético.
#   - Transformación de coordenadas: X solo se traslada (se le suma el
#     offset). Y se INVIERTE (cambio de signo) y luego se traslada. Esto es
#     porque el Excel usa Y hacia arriba (cartesiano) y la pantalla usa Y hacia
#     abajo. Una simple suma no puede voltear el eje, hace falta el cambio de
#     signo. Ver Dibujar._transformar().

# Funciones y constantes de OpenGL que se usan para dibujar
from OpenGL.GL import (
    glBegin, glEnd, glVertex2f, glColor4f, glLineWidth,
    GL_POLYGON, GL_LINE_STRIP,
)

# Para convertir los colores del Excel a un formato que entienda OpenGL
import color
# Para leer capas y coordenadas del Excel
import lectorcapas
# Para imprimir avisos en la consola
import mensaje

# Grosor mínimo que puede tener una línea, en píxeles
GROSOR_MINIMO = 1.0
# Margen (en píxeles) que se deja alrededor del dibujo al calcular el offset
# automático, si no se indica otro
MARGEN_AUTO_OFFSET = 20.0


# Clase que dibuja las capas en pantalla
class Dibujar:
    # Constructor: se ejecuta al crear un objeto Dibujar.
    # offsetX y offsetY: traslación que se le suma a cada coordenada.
    # correccionX y correccionY: ajuste manual extra encima del offset.
    def __init__(self, offsetX=0.0, offsetY=0.0, correccionX=0.0, correccionY=0.0):
        # Guarda el offset en X
        self.offsetX = offsetX
        # Guarda el offset en Y
        self.offsetY = offsetY
        # La corrección manual se suma POR ENCIMA del offset automático. Sirve
        # para mover todo el dibujo en X/Y a ojo, sin afectar el cálculo de
        # calcularOffsetDesdeCoordenadas().
        self.correccionX = correccionX
        self.correccionY = correccionY

    # establecerOffset(offsetX, offsetY): fija a mano el offset (traslación)
    # que se suma a cada coordenada antes de dibujarla
    def establecerOffset(self, offsetX, offsetY):
        # Guarda el nuevo offset en X
        self.offsetX = offsetX
        # Guarda el nuevo offset en Y
        self.offsetY = offsetY

    # establecerCorreccion(correccionX, correccionY): fija la corrección
    # manual. Se suma encima del offset (automático o manual) y mueve todo el
    # dibujo sin recalcular el offset. Sirve para afinar la posición a ojo
    # mientras se ve el resultado.
    def establecerCorreccion(self, correccionX, correccionY):
        # Guarda la nueva corrección en X
        self.correccionX = correccionX
        # Guarda la nueva corrección en Y
        self.correccionY = correccionY

    # calcularOffsetDesdeCoordenadas(todasCoordenadas, margen): calcula solo el
    # offset para que todo el dibujo quede dentro de la ventana, con 'margen'
    # píxeles de espacio.
    #
    # Ojo con el eje Y: en el Excel Y crece hacia arriba y en la ventana crece
    # hacia abajo. Una suma no puede corregir eso (solo mueve, no voltea). Por
    # eso X se calcula con una resta directa (los dos sistemas van en el mismo
    # sentido), pero en Y se usa el MAYOR valor y no el menor: en el Excel el
    # punto más alto del dibujo es el de mayor Y, y ese debe quedar cerca del
    # borde de arriba de la pantalla. Ver _transformar() para la fórmula.
    #
    # Esto no toca correccionX ni correccionY, esas se aplican aparte.
    def calcularOffsetDesdeCoordenadas(self, todasCoordenadas, margen=MARGEN_AUTO_OFFSET):
        # Si la lista está vacía no hay nada que calcular: avisa y deja el offset en (0, 0)
        if not todasCoordenadas:
            mensaje.advertencia("No hay coordenadas para calcular el offset, se deja en (0, 0).")
            self.offsetX, self.offsetY = 0.0, 0.0
            return self.offsetX, self.offsetY

        # Lista con todas las X de todos los puntos
        xs = [x for x, y in todasCoordenadas]
        # Lista con todas las Y de todos los puntos
        ys = [y for x, y in todasCoordenadas]
        # Se necesita la X más pequeña (el punto más a la izquierda) y la Y más grande (el punto más alto)
        min_x, max_y = min(xs), max(ys)

        # Offset en X: hace que el punto más a la izquierda quede a 'margen' píxeles del borde
        self.offsetX = margen - min_x
        # Offset en Y: como después Y se invierte, el punto más alto termina a 'margen' píxeles del borde de arriba
        self.offsetY = margen + max_y
        # Regresa los dos offsets calculados
        return self.offsetX, self.offsetY

    # _transformar(x, y): convierte una coordenada del Excel (Y hacia arriba) a
    # una de pantalla (Y hacia abajo).
    # X: se le suma offsetX y la corrección manual correccionX.
    # Y: se le cambia el signo, se le suma offsetY y la corrección manual
    #    correccionY. La corrección siempre se suma al final, después del offset.
    def _transformar(self, x, y):
        # X de pantalla: la X del Excel + offset + corrección
        sx = x + self.offsetX + self.correccionX
        # Y de pantalla: la Y del Excel con el signo cambiado + offset + corrección
        sy = -y + self.offsetY + self.correccionY
        # Regresa la coordenada ya convertida
        return sx, sy

    # dibujarRelleno(coordenadas, colorValor): dibuja las coordenadas como un
    # polígono sólido relleno
    def dibujarRelleno(self, coordenadas, colorValor):
        # Si no hay puntos, avisa y se sale sin dibujar
        if not coordenadas:
            mensaje.advertencia("dibujarRelleno: no hay coordenadas, no se dibuja nada.")
            return

        # Convierte el color del Excel a sus cuatro valores (rojo, verde, azul, alfa)
        r, g, b, a = color.obtenerColorOpenGL(colorValor)
        # Le dice a OpenGL que dibuje con ese color
        glColor4f(r, g, b, a)

        # Empieza a dibujar un polígono relleno
        glBegin(GL_POLYGON)
        # Recorre cada punto de la lista
        for x, y in coordenadas:
            # Convierte el punto de coordenadas del Excel a coordenadas de pantalla
            sx, sy = self._transformar(x, y)
            # Agrega ese punto como vértice del polígono
            glVertex2f(sx, sy)
        # Termina el polígono
        glEnd()

    # dibujarBorde(coordenadas, colorValor, grosor): dibuja las coordenadas como
    # una línea ABIERTA (borde): une los puntos en orden pero NO regresa del
    # último punto al primero
    def dibujarBorde(self, coordenadas, colorValor, grosor):
        # Si no hay puntos, avisa y se sale sin dibujar
        if not coordenadas:
            mensaje.advertencia("dibujarBorde: no hay coordenadas, no se dibuja nada.")
            return

        # Convierte el color a sus cuatro valores
        r, g, b, a = color.obtenerColorOpenGL(colorValor)
        # Le dice a OpenGL que dibuje con ese color
        glColor4f(r, g, b, a)

        # Intenta convertir el grosor a número decimal
        try:
            ancho_linea = float(grosor)
        # Si no se puede (viene vacío o con letras), usa el grosor mínimo
        except (TypeError, ValueError):
            ancho_linea = GROSOR_MINIMO
        # Fija el grosor de la línea. max() evita que sea menor al mínimo.
        glLineWidth(max(GROSOR_MINIMO, ancho_linea))

        # Empieza a dibujar una línea que va pasando por cada punto, sin cerrarse
        glBegin(GL_LINE_STRIP)
        # Recorre cada punto de la lista
        for x, y in coordenadas:
            # Convierte el punto a coordenadas de pantalla
            sx, sy = self._transformar(x, y)
            # Agrega el punto a la línea
            glVertex2f(sx, sy)
        # Termina la línea
        glEnd()

    # dibujarCapa(infoCapa, coordenadas, colorOverride, grosorOverride): dibuja
    # una sola capa según su TIPO:
    #   BACKGROUND -> dibujarRelleno()
    #   LINE       -> dibujarBorde()
    #
    # colorOverride y grosorOverride sirven para cambiar el color o el grosor que
    # trae la capa del Excel mientras el programa corre, sin tocar
    # lectorcapas.py. Si se dejan en None se usa lo que trae infoCapa.
    def dibujarCapa(self, infoCapa, coordenadas, colorOverride=None, grosorOverride=None):
        # Nombre de la capa (si no tiene, "SIN_NOMBRE"); se usa en los avisos
        nombreCapa = infoCapa.get("nombreCapa", "SIN_NOMBRE")
        # Tipo de la capa, sin espacios y en mayúsculas. El "or ''" evita error si viene vacío (None).
        tipo = (infoCapa.get("tipo") or "").strip().upper()
        # Color: si hay override se usa ese, si no el de la capa
        colorValor = colorOverride if colorOverride is not None else infoCapa.get("color")
        # Grosor: si hay override se usa ese, si no el de la capa
        grosorValor = grosorOverride if grosorOverride is not None else infoCapa.get("grosor")

        # Si la capa no tiene puntos, avisa y la salta
        if not coordenadas:
            mensaje.advertencia(f"Capa '{nombreCapa}' no tiene coordenadas, se omite.")
            return

        # Si es BACKGROUND se dibuja con relleno
        if tipo == "BACKGROUND":
            self.dibujarRelleno(coordenadas, colorValor)
        # Si es LINE se dibuja solo el borde
        elif tipo == "LINE":
            self.dibujarBorde(coordenadas, colorValor, grosorValor)
        # Si es otro tipo, avisa y la dibuja como BACKGROUND
        else:
            mensaje.advertencia(
                f"Capa '{nombreCapa}': tipo desconocido '{tipo}', se dibuja como BACKGROUND."
            )
            self.dibujarRelleno(coordenadas, colorValor)

    # dibujarGrupo(grupoCapa, archivo): dibuja todas las capas de un grupoCapa
    # (una hoja), en el orden en que aparecen en el Excel, usando lectorcapas.py
    # para obtener la información y las coordenadas.
    #
    # 'archivo' permite usar este método con capas.xlsx, con fotogramas.xlsx
    # (donde cada hoja es un fotograma) o con cualquier otro Excel con el mismo formato.
    def dibujarGrupo(self, grupoCapa, archivo=lectorcapas.RUTA_ARCHIVO_DEFECTO):
        # Pide la lista de capas de la hoja
        capas = lectorcapas.getListCapaPorGrupoCapa(grupoCapa, archivo=archivo)
        # Recorre las capas en orden
        for infoCapa in capas:
            # Pide las coordenadas de esta capa usando su índice interno
            coordenadas = lectorcapas.getListCoordenadas(grupoCapa, infoCapa["indice"], archivo=archivo)
            # Dibuja la capa
            self.dibujarCapa(infoCapa, coordenadas)

    # dibujarTodosLosGrupos(archivo): dibuja TODOS los grupoCapa (todas las
    # hojas) del archivo, uno encima del otro, en el orden en que aparecen.
    # Es la forma automática: no hace falta saber los nombres de las hojas.
    def dibujarTodosLosGrupos(self, archivo=lectorcapas.RUTA_ARCHIVO_DEFECTO):
        # Pide la lista con los nombres de todas las hojas
        grupos = lectorcapas.getListGruposCapas(archivo=archivo)
        # Recorre las hojas en orden
        for grupoCapa in grupos:
            # Dibuja todas las capas de esa hoja
            self.dibujarGrupo(grupoCapa, archivo=archivo)

    # obtenerTodasLasCoordenadas(grupoCapa, archivo): junta en una sola lista
    # todas las coordenadas. Sirve para calcular el offset automático.
    # Si se pasa 'grupoCapa', junta solo las de esa hoja.
    # Si se deja en None, junta las de TODAS las hojas del archivo, para que el
    # offset deje visible el dibujo completo.
    def obtenerTodasLasCoordenadas(self, grupoCapa=None, archivo=lectorcapas.RUTA_ARCHIVO_DEFECTO):
        # Aquí se van juntando todas las coordenadas
        todas = []

        # Si se pidió una hoja en concreto, solo se recorre esa
        if grupoCapa is not None:
            grupos_a_recorrer = [grupoCapa]
        # Si no, se recorren todas las hojas del archivo
        else:
            grupos_a_recorrer = lectorcapas.getListGruposCapas(archivo=archivo)

        # Recorre cada hoja
        for grupo in grupos_a_recorrer:
            # Pide las capas de la hoja
            capas = lectorcapas.getListCapaPorGrupoCapa(grupo, archivo=archivo)
            # Recorre cada capa
            for infoCapa in capas:
                # Pide las coordenadas de la capa
                coordenadas = lectorcapas.getListCoordenadas(grupo, infoCapa["indice"], archivo=archivo)
                # Las agrega a la lista general (extend agrega todos los elementos de una lista)
                todas.extend(coordenadas)

        # Regresa la lista con todas las coordenadas
        return todas
