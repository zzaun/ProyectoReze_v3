# ruido.py
# Este archivo le agrega una textura de "ruido de papel" encima de
# toda la imagen: puntitos sueltos, grises, semitransparentes,
# esparcidos por la pantalla. No usa ninguna imagen ni textura: todo
# se genera por codigo con numeros aleatorios.
# Para que se vea como "grano" vivo (tipo pelicula antigua) en vez de
# puntos fijos pegados en la pantalla, se generan varios patrones
# distintos desde el inicio, y se van mostrando uno distinto en cada
# refresco de pantalla, en loop (igual que animar.py hace con los
# fotogramas de la animacion).

# Importamos random para generar las posiciones y transparencias al azar.
import random

# Importamos las funciones de OpenGL que necesitamos para dibujar los
# puntitos y para que se vean transparentes (blend).
from OpenGL.GL import (
    glBegin, glEnd, glVertex2f, glColor4f,
    glEnable, glBlendFunc,
    GL_QUADS, GL_BLEND, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
)

# Cuantos patrones distintos de ruido se generan (entre mas, menos se
# nota que se repiten en loop).
NUMERO_PATRONES = 500
# Cuantos puntitos tiene cada patron.
PUNTOS_POR_PATRON = 5000
# Tamano de cada puntito, en pixeles.
TAMANO_PUNTO = 2.0
# Que tan transparente es, como maximo, cada puntito (0 = invisible, 1 = solido).
# Se deja bajo a proposito, para que se sienta como textura y no tape el dibujo.
OPACIDAD_MAXIMA = 0.25


# Clase Ruido: genera los patrones de puntos y los va mostrando en
# loop, uno por cada refresco de pantalla.
class Ruido:

    # Al crear el objeto, se generan todos los patrones de una vez
    # (ancho y alto son el tamano de la ventana, para saber en que
    # area esparcir los puntos).
    def __init__(self, ancho, alto, numeroPatrones=NUMERO_PATRONES, puntosPorPatron=PUNTOS_POR_PATRON):
        # Guardamos el tamano que se uso para generar los patrones.
        self._ancho = ancho
        self._alto = alto
        # Aqui guardamos la lista de patrones ya generados.
        self._patrones = []
        # Generamos cada patron, uno por uno.
        for _ in range(numeroPatrones):
            self._patrones.append(self._generarUnPatron(ancho, alto, puntosPorPatron))
        # Indice del patron que toca mostrar ahorita (empieza en el primero).
        self._indiceActual = 0

    # Genera UN patron: una lista de puntitos, cada uno con su
    # posicion, su tono de gris, y su transparencia, todos al azar.
    def _generarUnPatron(self, ancho, alto, cantidad):
        patron = []
        # Repetimos "cantidad" veces, una por cada puntito del patron.
        for _ in range(cantidad):
            # Posicion al azar dentro del area de la ventana.
            x = random.uniform(0, ancho)
            y = random.uniform(0, alto)
            # Tono de gris al azar: unos puntos mas claros, otros mas oscuros
            # (el papel real tiene motas de los dos tipos, no solo oscuras).
            gris = random.uniform(0.0, 1.0)
            # Transparencia al azar, entre casi invisible y OPACIDAD_MAXIMA.
            alfa = random.uniform(0.02, OPACIDAD_MAXIMA)
            # Guardamos este puntito en el patron.
            patron.append((x, y, gris, alfa))
        # Regresamos el patron completo ya armado.
        return patron

    # Dibuja el patron que le toca a este frame, y avanza al siguiente
    # (con loop: al pasar del ultimo, vuelve al primero). Debe llamarse
    # una vez por cada refresco de pantalla, DESPUES de dibujar la
    # escena, para que quede encima.
    def dibujar(self):
        # Activamos la mezcla de transparencia (necesaria para que el
        # cuarto numero de glColor4f, el alfa, funcione). Volver a
        # llamar esto cada frame no causa ningun problema.
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Tomamos el patron que le toca mostrar en este frame.
        patron = self._patrones[self._indiceActual]
        # Dibujamos cada puntito del patron como un cuadrito pequeno.
        for x, y, gris, alfa in patron:
            # El color es el mismo numero de gris en rojo, verde y azul
            # (asi se ve gris puro, ni mas rojo ni mas azul), y el alfa
            # es la transparencia de ese puntito.
            glColor4f(gris, gris, gris, alfa)
            glBegin(GL_QUADS)
            glVertex2f(x, y)
            glVertex2f(x + TAMANO_PUNTO, y)
            glVertex2f(x + TAMANO_PUNTO, y + TAMANO_PUNTO)
            glVertex2f(x, y + TAMANO_PUNTO)
            glEnd()

        # Avanzamos al siguiente patron, volviendo al primero si ya
        # llegamos al final (esto es lo que hace que se sienta "en loop").
        self._indiceActual = (self._indiceActual + 1) % len(self._patrones)