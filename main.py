# main.py
# Este es el archivo que se ejecuta para correr el programa (python main.py).
# Aquí solo se juntan las piezas de los otros archivos, no dibuja nada por sí solo.
# Lo que hace, en orden:
#   1. Crea el objeto que dibuja y el que reproduce la animación.
#   2. Calcula UN solo offset (desplazamiento) usando las coordenadas de
#      capas.xlsx y de fotogramas.xlsx juntas, para que todo quede alineado.
#   3. Abre la ventana y crea el panel de controles (Play/Pause, FPS y
#      corrección X/Y).
#   4. Corre el loop principal. En cada vuelta dibuja:
#        a) el fotograma que toca de fotogramas.xlsx (fondo animado; si está
#           en pausa se dibuja el mismo sin avanzar)
#        b) todas las capas de capas.xlsx encima (imagen estática)
#        c) el panel de controles encima de todo
#      La corrección X/Y y los FPS se leen del panel en cada vuelta, por eso
#      se pueden cambiar mientras el programa corre.
#
# No hace falta saber los nombres de las hojas de los Excel, se detectan solos.

# Módulo que maneja la ventana y el loop principal
import windows
# Clase que dibuja las capas (relleno y bordes)
from dibujar import Dibujar
# Clase que reproduce los fotogramas como animación
from animar import Animar
# Clase del panel de controles
from interfaz import Interfaz

# Ancho de la ventana en píxeles
ANCHO_VENTANA = 1500
# Alto de la ventana en píxeles
ALTO_VENTANA = 1000
# Texto de la barra de título de la ventana
TITULO_VENTANA = "Dibujo de Capas"
# Color de fondo de la ventana (blanco, en hexadecimal)
COLOR_FONDO = "#DDDDDD"
# Fotogramas por segundo con los que arranca la animación
FPS_INICIAL = 8

# Archivo Excel de la imagen estática
ARCHIVO_CAPAS = "capas.xlsx"
# Archivo Excel de la animación (cada hoja es un fotograma)
ARCHIVO_FOTOGRAMAS = "fotogramas.xlsx"

# Valores iniciales del ajuste manual de posición. Se pueden cambiar en vivo
# desde el panel una vez que el programa está corriendo.
# Corrimiento inicial en X (horizontal)
CORRECCION_X_INICIAL = -350.0
# Corrimiento inicial en Y (vertical)
CORRECCION_Y_INICIAL = -400.0


# Función principal: arma todo y arranca el programa
def main():
    # Crea el objeto que dibuja las capas en pantalla
    dibujador = Dibujar()
    # Crea el objeto de la animación. Recibe el mismo dibujador para reutilizarlo
    animador = Animar(dibujador, archivo=ARCHIVO_FOTOGRAMAS)

    # Se calcula UN solo offset con las coordenadas de los dos archivos juntos
    # (la imagen estática y todos los fotogramas). Así comparten el mismo
    # sistema de coordenadas y la imagen estática no se desalinea del fondo animado.
    # Junta todas las coordenadas de capas.xlsx
    coordenadas_estaticas = dibujador.obtenerTodasLasCoordenadas(archivo=ARCHIVO_CAPAS)
    # Junta todas las coordenadas de todos los fotogramas
    coordenadas_animadas = animador.obtenerTodasLasCoordenadas()
    # Une las dos listas en una sola
    todas_coordenadas = coordenadas_estaticas + coordenadas_animadas
    # Calcula el offset con un margen de 40 píxeles alrededor del dibujo
    dibujador.calcularOffsetDesdeCoordenadas(todas_coordenadas, margen=40)

    # Abre la ventana con el tamaño, título y color de fondo definidos arriba.
    # Si no se pudo abrir, se sale de la función y el programa termina.
    if not windows.inicializar(ancho=ANCHO_VENTANA, alto=ALTO_VENTANA,
                                titulo=TITULO_VENTANA, colorFondo=COLOR_FONDO):
        return

    # Crea el panel de controles
    interfaz = Interfaz(
        # La ventana de glfw, para poder leer el mouse y el teclado
        ventanaGLFW=windows.obtenerVentanaGLFW(),
        # Función que da el tamaño actual de la ventana (para pegar el panel a la derecha)
        obtenerTamanoVentana=windows.obtenerTamano,
        # FPS con los que arranca el panel
        fpsInicial=FPS_INICIAL,
        # Corrección X con la que arranca el panel
        correccionXInicial=CORRECCION_X_INICIAL,
        # Corrección Y con la que arranca el panel
        correccionYInicial=CORRECCION_Y_INICIAL,
    )

    # Función que dibuja UN frame completo (sin el panel). windows.ejecutar la
    # llama en cada vuelta del loop.
    def dibujarFrame():
        # Lee la corrección X/Y que tiene el panel en este momento y se la pasa al dibujador
        dibujador.establecerCorreccion(interfaz.obtenerCorreccionX(), interfaz.obtenerCorreccionY())
        # Dibuja el fondo animado. Si el panel está en pausa no avanza al siguiente fotograma
        animador.dibujarFotogramaActual(avanzar=not interfaz.estaPausado())
        # Dibuja la imagen estática encima del fondo
        dibujador.dibujarTodosLosGrupos(archivo=ARCHIVO_CAPAS)

    # Arranca el loop principal. No termina hasta que se cierre la ventana.
    windows.ejecutar(
        # Función que dibuja cada frame
        dibujarFrame,
        # Se le pasa la función (sin paréntesis) para que lea el FPS del panel en vivo
        fpsObjetivo=interfaz.obtenerFPS,
        # Función que dibuja el panel, se llama después del dibujo para quedar encima
        funcionUI=interfaz.dibujar,
        # Función que revisa mouse y teclado del panel en cada vuelta
        funcionEventosUI=interfaz.procesarEventos,
    )

    # Cuando la ventana se cierra, se cierra también la interfaz
    interfaz.cerrar()


# Esto solo se cumple si se ejecuta este archivo directamente (python main.py),
# no si otro archivo lo importa
if __name__ == "__main__":
    # Arranca el programa
    main()
