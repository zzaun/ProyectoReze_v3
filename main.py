"""
main.py

Punto de entrada del programa. Solo inicializa:
    - Crea la ventana (windows.py)
    - Calcula UN offset combinado (usando las coordenadas de capas.xlsx
      Y de fotogramas.xlsx juntas), para que todo comparta el mismo
      sistema de coordenadas y nada se desalinee entre si.
    - Crea la interfaz (interfaz.py): panel fijo con Play/Pause, FPS,
      CORRECCION_X y CORRECCION_Y.
    - Ejecuta el loop principal. En cada refresco de pantalla:
        1) aplica la CORRECCION_X/Y vigente (puede cambiar en vivo
           desde la interfaz)
        2) dibuja el fotograma que le toca de fotogramas.xlsx (fondo
           animado; si esta en Pause, se redibuja el mismo fotograma
           sin avanzar)
        3) dibuja encima TODOS los grupoCapa de capas.xlsx (imagen
           estatica)
        4) dibuja el panel de interfaz encima de todo
    El FPS del loop tambien se lee en vivo desde la interfaz.

No es necesario conocer de antemano los nombres de las hojas de
ninguno de los dos archivos excel: se detectan automaticamente.
"""

import windows
from dibujar import Dibujar
from animar import Animar
from interfaz import Interfaz

ANCHO_VENTANA = 1500
ALTO_VENTANA = 1000
TITULO_VENTANA = "Dibujo de Capas"
COLOR_FONDO = "#FFFFFF"
FPS_INICIAL = 15

ARCHIVO_CAPAS = "capas.xlsx"
ARCHIVO_FOTOGRAMAS = "fotogramas.xlsx"

# Valores iniciales del ajuste manual de posicion (se pueden cambiar en
# vivo desde el panel de interfaz una vez corriendo).
CORRECCION_X_INICIAL = 0.0
CORRECCION_Y_INICIAL = -200.0


def main():
    dibujador = Dibujar()
    animador = Animar(dibujador, archivo=ARCHIVO_FOTOGRAMAS)

    # Offset UNICO, calculado con las coordenadas de AMBOS archivos
    # juntos (estatico + todos los fotogramas de la animacion), para
    # que compartan el mismo sistema de coordenadas y la imagen
    # estatica no quede desalineada respecto al fondo animado.
    coordenadas_estaticas = dibujador.obtenerTodasLasCoordenadas(archivo=ARCHIVO_CAPAS)
    coordenadas_animadas = animador.obtenerTodasLasCoordenadas()
    todas_coordenadas = coordenadas_estaticas + coordenadas_animadas
    dibujador.calcularOffsetDesdeCoordenadas(todas_coordenadas, margen=40)

    if not windows.inicializar(ancho=ANCHO_VENTANA, alto=ALTO_VENTANA,
                                titulo=TITULO_VENTANA, colorFondo=COLOR_FONDO):
        return

    interfaz = Interfaz(
        ventanaGLFW=windows.obtenerVentanaGLFW(),
        obtenerTamanoVentana=windows.obtenerTamano,
        fpsInicial=FPS_INICIAL,
        correccionXInicial=CORRECCION_X_INICIAL,
        correccionYInicial=CORRECCION_Y_INICIAL,
    )

    def dibujarFrame():
        dibujador.establecerCorreccion(interfaz.obtenerCorreccionX(), interfaz.obtenerCorreccionY())
        animador.dibujarFotogramaActual(avanzar=not interfaz.estaPausado())  # fondo animado
        dibujador.dibujarTodosLosGrupos(archivo=ARCHIVO_CAPAS)               # estatico encima

    windows.ejecutar(
        dibujarFrame,
        fpsObjetivo=interfaz.obtenerFPS,       # FPS en vivo, leido desde la interfaz
        funcionUI=interfaz.dibujar,
        funcionEventosUI=interfaz.procesarEventos,
    )

    interfaz.cerrar()


if __name__ == "__main__":
    main()