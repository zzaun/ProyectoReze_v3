"""
dibujar.py

Clase Dibujar: contiene toda la logica para dibujar en pantalla las
capas leidas por lectorcapas.py.

Reglas de negocio acordadas:
    - TIPO = "BACKGROUND"  -> se dibuja como RELLENO (poligono solido).
    - TIPO = "LINE"        -> se dibuja como BORDE (polilinea abierta,
                               NO se conecta el ultimo punto con el
                               primero).
    - El relleno y el borde son metodos separados (dibujarRelleno /
      dibujarBorde), para poder usarlos y ajustarlos de forma
      independiente.
    - El dibujo se hace en orden lineal: el orden en que las capas
      aparecen en la hoja de excel (el mismo que entrega
      lectorcapas.getListCapaPorGrupoCapa), no orden alfabetico.
    - Transformacion de coordenadas: X se traslada (suma). Y se
      INVIERTE (signo negativo) y luego se traslada, porque el excel
      usa convencion cartesiana (Y hacia arriba) y la pantalla usa
      convencion de pantalla (Y hacia abajo) -- son orientaciones
      opuestas, y solo una inversion de signo puede convertir una en
      la otra (una simple suma no alcanza). Ver Dibujar._transformar().
"""

from OpenGL.GL import (
    glBegin, glEnd, glVertex2f, glColor4f, glLineWidth,
    GL_POLYGON, GL_LINE_STRIP,
)

import color
import lectorcapas
import mensaje

GROSOR_MINIMO = 1.0
MARGEN_AUTO_OFFSET = 20.0


class Dibujar:
    def __init__(self, offsetX=0.0, offsetY=0.0, correccionX=0.0, correccionY=0.0):
        self.offsetX = offsetX
        self.offsetY = offsetY
        # Correccion manual: se suma POR ENCIMA del offset automatico,
        # para ajustar fino la posicion del dibujo (mover todo en X/Y)
        # sin afectar el calculo de calcularOffsetDesdeCoordenadas().
        self.correccionX = correccionX
        self.correccionY = correccionY

    def establecerOffset(self, offsetX, offsetY):
        """Fija manualmente el offset (traslacion) que se suma a cada
        coordenada antes de dibujarla."""
        self.offsetX = offsetX
        self.offsetY = offsetY

    def establecerCorreccion(self, correccionX, correccionY):
        """
        Fija CORRECCION_X y CORRECCION_Y: un ajuste manual adicional que
        se suma encima del offset (automatico o manual), para mover el
        dibujo completo en pantalla sin recalcular el offset. Util para
        afinar la posicion a ojo mientras se ve el resultado.
        """
        self.correccionX = correccionX
        self.correccionY = correccionY

    def calcularOffsetDesdeCoordenadas(self, todasCoordenadas, margen=MARGEN_AUTO_OFFSET):
        """
        Calcula automaticamente el offset para que el conjunto de
        coordenadas dado quede dentro del area visible, con 'margen'
        pixeles de espacio.

        IMPORTANTE sobre el eje Y: los datos del excel usan convencion
        CARTESIANA (Y crece hacia arriba), mientras que la ventana usa
        convencion de PANTALLA (Y crece hacia abajo). Estas dos
        convenciones tienen orientacion opuesta, y una simple suma NO
        puede corregir eso (solo traslada, no invierte el eje). Por eso
        X se sigue calculando con una resta directa (misma orientacion
        en ambos sistemas), pero Y se calcula distinto: se usa el
        maximo (no el minimo), porque en cartesiano el punto "mas
        arriba" del dibujo es el de mayor Y, y ese debe terminar cerca
        del margen superior de la pantalla (Y de pantalla pequeño).
        Ver _transformar() para la formula completa.

        Nota: esto NO toca correccionX/correccionY; esos se aplican
        aparte, encima de este resultado.
        """
        if not todasCoordenadas:
            mensaje.advertencia("No hay coordenadas para calcular el offset, se deja en (0, 0).")
            self.offsetX, self.offsetY = 0.0, 0.0
            return self.offsetX, self.offsetY

        xs = [x for x, y in todasCoordenadas]
        ys = [y for x, y in todasCoordenadas]
        min_x, max_y = min(xs), max(ys)

        self.offsetX = margen - min_x
        self.offsetY = margen + max_y
        return self.offsetX, self.offsetY

    def _transformar(self, x, y):
        """
        Convierte una coordenada del excel (cartesiana, Y hacia arriba)
        a una coordenada de pantalla (Y hacia abajo).

        X: se traslada con offsetX, mas el ajuste manual correccionX.
        Y: se invierte el signo, se traslada con offsetY, mas el ajuste
        manual correccionY. La correccion se suma SIEMPRE al final,
        despues del offset automatico u manual.
        """
        sx = x + self.offsetX + self.correccionX
        sy = -y + self.offsetY + self.correccionY
        return sx, sy

    def dibujarRelleno(self, coordenadas, colorValor):
        """Dibuja 'coordenadas' como un poligono solido relleno."""
        if not coordenadas:
            mensaje.advertencia("dibujarRelleno: no hay coordenadas, no se dibuja nada.")
            return

        r, g, b, a = color.obtenerColorOpenGL(colorValor)
        glColor4f(r, g, b, a)

        glBegin(GL_POLYGON)
        for x, y in coordenadas:
            sx, sy = self._transformar(x, y)
            glVertex2f(sx, sy)
        glEnd()

    def dibujarBorde(self, coordenadas, colorValor, grosor):
        """
        Dibuja 'coordenadas' como una polilinea ABIERTA (borde): conecta
        los puntos en orden, pero NO regresa del ultimo punto al
        primero.
        """
        if not coordenadas:
            mensaje.advertencia("dibujarBorde: no hay coordenadas, no se dibuja nada.")
            return

        r, g, b, a = color.obtenerColorOpenGL(colorValor)
        glColor4f(r, g, b, a)

        try:
            ancho_linea = float(grosor)
        except (TypeError, ValueError):
            ancho_linea = GROSOR_MINIMO
        glLineWidth(max(GROSOR_MINIMO, ancho_linea))

        glBegin(GL_LINE_STRIP)
        for x, y in coordenadas:
            sx, sy = self._transformar(x, y)
            glVertex2f(sx, sy)
        glEnd()

    def dibujarCapa(self, infoCapa, coordenadas, colorOverride=None, grosorOverride=None):
        """
        Dibuja una sola capa segun su TIPO:
            BACKGROUND -> dibujarRelleno()
            LINE       -> dibujarBorde()

        'colorOverride' / 'grosorOverride' permiten sobreescribir, en
        tiempo de ejecucion, el color/grosor que trae la capa desde el
        excel, sin modificar lectorcapas.py. Si se dejan en None, se usa
        lo que traiga 'infoCapa'.
        """
        nombreCapa = infoCapa.get("nombreCapa", "SIN_NOMBRE")
        tipo = (infoCapa.get("tipo") or "").strip().upper()
        colorValor = colorOverride if colorOverride is not None else infoCapa.get("color")
        grosorValor = grosorOverride if grosorOverride is not None else infoCapa.get("grosor")

        if not coordenadas:
            mensaje.advertencia(f"Capa '{nombreCapa}' no tiene coordenadas, se omite.")
            return

        if tipo == "BACKGROUND":
            self.dibujarRelleno(coordenadas, colorValor)
        elif tipo == "LINE":
            self.dibujarBorde(coordenadas, colorValor, grosorValor)
        else:
            mensaje.advertencia(
                f"Capa '{nombreCapa}': tipo desconocido '{tipo}', se dibuja como BACKGROUND."
            )
            self.dibujarRelleno(coordenadas, colorValor)

    def dibujarGrupo(self, grupoCapa, archivo=lectorcapas.RUTA_ARCHIVO_DEFECTO):
        """
        Dibuja todas las capas de un grupoCapa (hoja), en el orden
        lineal en que aparecen en el excel (no alfabetico), usando
        lectorcapas.py para obtener la informacion y las coordenadas.

        'archivo' permite reutilizar este metodo tanto para capas.xlsx
        como para fotogramas.xlsx (donde cada hoja es un fotograma) o
        cualquier otro archivo con el mismo formato.
        """
        capas = lectorcapas.getListCapaPorGrupoCapa(grupoCapa, archivo=archivo)
        for infoCapa in capas:
            coordenadas = lectorcapas.getListCoordenadas(grupoCapa, infoCapa["indice"], archivo=archivo)
            self.dibujarCapa(infoCapa, coordenadas)

    def dibujarTodosLosGrupos(self, archivo=lectorcapas.RUTA_ARCHIVO_DEFECTO):
        """
        Dibuja TODOS los grupoCapa (todas las hojas) de 'archivo', uno
        encima del otro, en el orden en que aparecen dentro del archivo
        (el mismo orden que entrega lectorcapas.getListGruposCapas()).

        Esta es la forma "automatica": no requiere saber de antemano
        los nombres de las hojas.
        """
        grupos = lectorcapas.getListGruposCapas(archivo=archivo)
        for grupoCapa in grupos:
            self.dibujarGrupo(grupoCapa, archivo=archivo)

    def obtenerTodasLasCoordenadas(self, grupoCapa=None, archivo=lectorcapas.RUTA_ARCHIVO_DEFECTO):
        """
        Utilidad para calcular el offset automatico: junta en una sola
        lista todas las coordenadas.

        Si se pasa 'grupoCapa', junta solo las de esa hoja.
        Si se deja en None (por defecto), junta las de TODOS los
        grupoCapa de 'archivo', para que el offset calculado deje
        visible el dibujo completo (todas las hojas superpuestas).
        """
        todas = []

        if grupoCapa is not None:
            grupos_a_recorrer = [grupoCapa]
        else:
            grupos_a_recorrer = lectorcapas.getListGruposCapas(archivo=archivo)

        for grupo in grupos_a_recorrer:
            capas = lectorcapas.getListCapaPorGrupoCapa(grupo, archivo=archivo)
            for infoCapa in capas:
                coordenadas = lectorcapas.getListCoordenadas(grupo, infoCapa["indice"], archivo=archivo)
                todas.extend(coordenadas)

        return todas