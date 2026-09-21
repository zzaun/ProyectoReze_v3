"""
animar.py

Clase Animar: reproduce una animacion a partir de un archivo excel con
el mismo formato que capas.xlsx (bloques CAPA/TIPO/COLOR/GROSOR/X,Y),
donde cada HOJA representa un FOTOGRAMA completo, en vez de un
grupoCapa estatico independiente.

No reimplementa logica de dibujo: reutiliza dibujar.Dibujar tal cual,
solo decide "que fotograma le toca dibujar en este momento".

Reglas acordadas:
    - Un fotograma nuevo por cada refresco de pantalla (un fotograma =
      una hoja; se avanza una hoja cada vez que se llama a
      dibujarFotogramaActual(), que normalmente se invoca una vez por
      vuelta del loop de windows.py).
    - Al llegar al ultimo fotograma, se vuelve al primero (animacion
      ciclica / loop).
    - El offset de posicion se calcula UNA vez, usando las coordenadas
      de TODOS los fotogramas juntos (no solo el actual), para que la
      imagen no salte de lugar entre cuadros.
"""

import lectorcapas
import mensaje


class Animar:
    def __init__(self, dibujador, archivo="fotogramas.xlsx"):
        """
        'dibujador' es una instancia de dibujar.Dibujar (se reutiliza,
        no se crea una nueva aqui, para poder compartir el mismo
        offset con el resto del dibujo si asi se desea).
        'archivo' es la ruta al excel de fotogramas.
        """
        self.dibujador = dibujador
        self.archivo = archivo
        self.indiceFotogramaActual = 0

    def obtenerListaFotogramas(self):
        """
        Regresa la lista de nombres de fotogramas (hojas), en el orden
        en que aparecen en el archivo. Gracias al cache de
        lectorcapas.py, esto es barato de llamar seguido: solo vuelve
        a leer el excel si detecta que cambio en disco.
        """
        return lectorcapas.getListGruposCapas(archivo=self.archivo)

    def obtenerTodasLasCoordenadas(self):
        """
        Utilidad para calcular el offset: junta las coordenadas de
        TODOS los fotogramas de self.archivo. Pensado para usarse junto
        con dibujador.calcularOffsetDesdeCoordenadas(...).
        """
        return self.dibujador.obtenerTodasLasCoordenadas(archivo=self.archivo)

    def reiniciar(self):
        """Vuelve al primer fotograma."""
        self.indiceFotogramaActual = 0

    def dibujarFotogramaActual(self, avanzar=True):
        """
        Dibuja el fotograma que le toca en este momento.

        Si 'avanzar' es True (por defecto), avanza el indice al
        siguiente fotograma despues de dibujar (con loop: al pasar del
        ultimo, vuelve al primero). Pensado para llamarse una vez por
        cada vuelta del loop principal.

        Si 'avanzar' es False, vuelve a dibujar el MISMO fotograma sin
        avanzar el indice -- esto es lo que implementa "Pause": la
        animacion se congela en el fotograma actual, pero se sigue
        redibujando cada frame (para que, por ejemplo, CORRECCION_X/Y
        sigan aplicandose en vivo aunque la animacion este pausada).
        """
        fotogramas = self.obtenerListaFotogramas()

        if not fotogramas:
            mensaje.advertencia(f"'{self.archivo}' no tiene fotogramas (hojas), no se dibuja nada.")
            return

        # Si el archivo cambio de tamano mientras corria (se agregaron
        # o quitaron hojas), el indice se recorta para no salirse de
        # rango.
        if self.indiceFotogramaActual >= len(fotogramas):
            self.indiceFotogramaActual = 0

        nombreFotograma = fotogramas[self.indiceFotogramaActual]
        self.dibujador.dibujarGrupo(nombreFotograma, archivo=self.archivo)

        if avanzar:
            self.indiceFotogramaActual = (self.indiceFotogramaActual + 1) % len(fotogramas)