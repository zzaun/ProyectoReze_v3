# windows.py
#
# Se encarga de todo lo de la ventana:
#   - Inicia glfw y crea el contexto de OpenGL.
#   - Configura la proyección en PÍXELES ABSOLUTOS: 1 unidad de coordenada
#     siempre es 1 píxel en pantalla, sin importar el tamaño de la ventana. Si
#     la ventana crece se ve más lienzo, pero el dibujo nunca se estira.
#   - El origen (0, 0) está en la esquina superior izquierda y el eje Y crece
#     hacia ABAJO (como en las pantallas). Pasar de las coordenadas del Excel
#     (cartesianas) a las de pantalla lo hace dibujar.py, no este archivo.
#   - Corre el loop principal: procesa eventos, limpia la pantalla, llama a la
#     función de dibujo que le pasen, cambia los buffers y controla los FPS a
#     mano con time.sleep().

# Para medir el tiempo y hacer pausas (control de FPS)
import time

# Librería que abre la ventana y lee mouse y teclado
import glfw
# Funciones y constantes de OpenGL que se usan en este archivo
from OpenGL.GL import (
    glClear, glClearColor, glViewport, glMatrixMode, glLoadIdentity,
    glOrtho, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT,
    GL_PROJECTION, GL_MODELVIEW,
)

# Para convertir el color de fondo a un formato que entienda OpenGL
import color
# Para imprimir mensajes en la consola
import mensaje

# Ancho de ventana si no se indica otro
ANCHO_DEFECTO = 1000
# Alto de ventana si no se indica otro
ALTO_DEFECTO = 1000
# Título de ventana si no se indica otro
TITULO_DEFECTO = "Dibujo de Capas"
# FPS del loop si no se indica otro
FPS_DEFECTO = 1
# Color de fondo si no se indica otro (blanco)
COLOR_FONDO_DEFECTO = "#FFFFFF"

# Aquí se guarda la ventana de glfw. None significa que todavía no se crea.
# El guion bajo indica que es de uso interno de este archivo.
_ventana = None
# Ancho actual de la ventana en píxeles (se actualiza si cambia el tamaño)
_ancho_actual = ANCHO_DEFECTO
# Alto actual de la ventana en píxeles
_alto_actual = ALTO_DEFECTO


# _configurar_proyeccion_absoluta(ancho, alto): deja lista la proyección para
# que las coordenadas sean píxeles absolutos: (0,0) arriba a la izquierda, Y
# crece hacia abajo y 1 unidad = 1 píxel, sin escalar con el tamaño de la ventana.
def _configurar_proyeccion_absoluta(ancho, alto):
    # Le dice a OpenGL que use toda la ventana para dibujar
    glViewport(0, 0, ancho, alto)
    # Cambia a la matriz de proyección (la que define cómo se ve la escena)
    glMatrixMode(GL_PROJECTION)
    # La deja en su estado inicial, para no acumular cambios de antes
    glLoadIdentity()
    # Parámetros de glOrtho: izquierda, derecha, abajo, arriba, cerca, lejos.
    # "abajo" es mayor que "arriba" a propósito: así Y crece hacia abajo.
    glOrtho(0, ancho, alto, 0, -1, 1)
    # Regresa a la matriz de modelo, que es la que se usa para dibujar
    glMatrixMode(GL_MODELVIEW)
    # También la deja en su estado inicial
    glLoadIdentity()


# _callback_framebuffer_size(ventana_glfw, ancho, alto): glfw la llama sola
# cuando cambia el tamaño de la ventana (se registra en inicializar)
def _callback_framebuffer_size(ventana_glfw, ancho, alto):
    # global permite cambiar las variables de arriba desde dentro de la función
    global _ancho_actual, _alto_actual
    # Si el ancho o alto es 0 (pasa al minimizar) se ignora, para no romper la proyección
    if ancho <= 0 or alto <= 0:
        return
    # Guarda el nuevo ancho
    _ancho_actual = ancho
    # Guarda el nuevo alto
    _alto_actual = alto
    # Vuelve a configurar la proyección con el nuevo tamaño
    _configurar_proyeccion_absoluta(ancho, alto)


# establecerColorFondo(valorColor): cambia el color de fondo de la ventana.
# Acepta cualquier formato que entienda color.py (hex, rgb(...), nombre...).
# Se puede llamar antes o después de inicializar(), incluso con el programa corriendo.
def establecerColorFondo(valorColor):
    # Convierte el color a sus cuatro valores (rojo, verde, azul, alfa)
    r, g, b, a = color.obtenerColorOpenGL(valorColor)
    # Le dice a OpenGL con qué color limpiar la pantalla en cada frame
    glClearColor(r, g, b, a)


# inicializar(...): crea la ventana y el contexto de OpenGL. Se llama una sola
# vez, antes de ejecutar() y antes de cualquier dibujo. Regresa True si todo
# salió bien y False si algo falló.
def inicializar(ancho=ANCHO_DEFECTO, alto=ALTO_DEFECTO, titulo=TITULO_DEFECTO,
                 pantalla_completa=False, colorFondo=COLOR_FONDO_DEFECTO):
    # Para poder cambiar las variables globales de arriba
    global _ventana, _ancho_actual, _alto_actual

    # Inicia glfw. Si falla, avisa y regresa False
    if not glfw.init():
        mensaje.error("No se pudo inicializar glfw.")
        return False

    # None significa "ventana normal" (no pantalla completa)
    monitor = None
    # Si se pidió pantalla completa
    if pantalla_completa:
        # Busca el monitor principal
        monitor = glfw.get_primary_monitor()
        # Pide la resolución actual de ese monitor
        modo_video = glfw.get_video_mode(monitor)
        # El tamaño de la ventana pasa a ser el de la pantalla
        ancho, alto = modo_video.size.width, modo_video.size.height

    # Crea la ventana con el tamaño, título y monitor indicados
    _ventana = glfw.create_window(ancho, alto, titulo, monitor, None)
    # Si no se pudo crear, avisa, cierra glfw y regresa False
    if not _ventana:
        mensaje.error("No se pudo crear la ventana.")
        glfw.terminate()
        return False

    # Le dice a OpenGL que dibuje en esta ventana
    glfw.make_context_current(_ventana)

    # Se apaga el vsync (sincronía con el monitor): los FPS los controlamos
    # nosotros a mano en ejecutar() con time.sleep().
    glfw.swap_interval(0)

    # Registra la función que glfw llama cuando cambia el tamaño de la ventana
    glfw.set_framebuffer_size_callback(_ventana, _callback_framebuffer_size)
    # Nota: aquí NO se registra callback de teclado (glfw.set_key_callback).
    # ESC se revisa por "polling" (preguntándole a glfw en cada vuelta del
    # loop) dentro de ejecutar().

    # El tamaño real del área de dibujo puede ser distinto al pedido (por
    # ejemplo en pantallas con escalado), por eso se lee el real.
    ancho_real, alto_real = glfw.get_framebuffer_size(_ventana)
    # Guarda el tamaño real como el tamaño actual
    _ancho_actual, _alto_actual = ancho_real, alto_real

    # Pone el color de fondo
    establecerColorFondo(colorFondo)
    # Configura la proyección con el tamaño real
    _configurar_proyeccion_absoluta(ancho_real, alto_real)

    # Avisa por consola que todo salió bien
    mensaje.info(f"Ventana inicializada ({ancho_real}x{alto_real}).")
    return True


# obtenerTamano(): regresa (ancho, alto) actuales de la ventana en píxeles
def obtenerTamano():
    # Regresa las dos variables como una pareja
    return _ancho_actual, _alto_actual


# obtenerVentanaGLFW(): regresa la ventana de glfw. La usa interfaz.py para
# leer el mouse y el teclado. El resto del proyecto no debería necesitarla.
def obtenerVentanaGLFW():
    # Regresa la ventana guardada
    return _ventana


# ejecutar(...): corre el loop principal hasta que se cierre la ventana o se
# presione ESC. En cada vuelta hace esto:
#   1. Procesa eventos de la ventana (cambio de tamaño, etc.)
#   2. Si hay funcionEventosUI, la llama (para que el panel revise mouse y teclado)
#   3. Revisa si se presionó ESC y, si es así, marca la ventana para cerrarse
#   4. Limpia la pantalla
#   5. Llama a funcionDibujo() (sin argumentos): dibuja todo ese frame
#   6. Si hay funcionUI, la llama DESPUÉS del dibujo para que quede encima
#   7. Cambia los buffers (así se muestra lo dibujado)
#   8. Duerme hasta que toque el siguiente frame, según el FPS de ese momento
#
# fpsObjetivo puede ser un número fijo, o una función sin argumentos que
# regresa el FPS actual (como interfaz.obtenerFPS). Con la función, el FPS se
# puede cambiar en vivo sin reiniciar el loop.
#
# Control de tiempo: se lleva un "reloj objetivo" que avanza una duración de
# frame en cada vuelta. Si el programa se atrasa más de un frame completo, el
# reloj se sincroniza con el tiempo actual en vez de intentar recuperar todo el
# atraso de golpe (eso causaría una ráfaga de frames sin pausa).
#
# funcionDibujo, funcionUI y funcionEventosUI se reciben como parámetros para
# que windows.py no dependa de dibujar.py ni de interfaz.py. Solo necesita
# algo que se pueda llamar.
def ejecutar(funcionDibujo, fpsObjetivo=FPS_DEFECTO, funcionUI=None, funcionEventosUI=None):
    # Si la ventana no se creó, avisa y no hace nada
    if _ventana is None:
        mensaje.error("La ventana no ha sido inicializada. Llama a inicializar() primero.")
        return

    # Función interna que regresa el FPS de este momento.
    # callable() dice si fpsObjetivo es una función; si lo es se llama, si no, se usa el número.
    def _fps_actual():
        return fpsObjetivo() if callable(fpsObjetivo) else fpsObjetivo

    # Hora (en segundos) en la que debe empezar el siguiente frame. Arranca en "ahora".
    tiempo_objetivo_siguiente = time.perf_counter()

    # Se repite hasta que la ventana se marque para cerrar
    while not glfw.window_should_close(_ventana):
        # Procesa los eventos pendientes de la ventana (mouse, teclado, tamaño...)
        glfw.poll_events()

        # Si se pasó una función de eventos del panel, se ejecuta
        if funcionEventosUI is not None:
            # try/except: si esa función falla, se avisa y el programa no se cae
            try:
                funcionEventosUI()
            except Exception as e:
                mensaje.error(f"Error procesando eventos de interfaz: {e}")

        # Si se está presionando ESC, marca la ventana para cerrarse
        if glfw.get_key(_ventana, glfw.KEY_ESCAPE) == glfw.PRESS:
            glfw.set_window_should_close(_ventana, True)

        # Limpia la pantalla (con el color de fondo) para dibujar un frame nuevo
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Dibuja la escena. Si falla, se avisa y el loop sigue.
        try:
            funcionDibujo()
        except Exception as e:
            mensaje.error(f"Error dentro de la funcion de dibujo: {e}")

        # Si hay función del panel, se dibuja después de la escena para quedar encima
        if funcionUI is not None:
            # Igual que arriba: si falla, solo se avisa
            try:
                funcionUI()
            except Exception as e:
                mensaje.error(f"Error dentro de la funcion de interfaz: {e}")

        # Cambia los buffers: lo que se dibujó por detrás pasa a verse en pantalla
        glfw.swap_buffers(_ventana)

        # Lee el FPS actual (puede haber cambiado desde el panel)
        fps = _fps_actual()
        # Cuántos segundos debe durar cada frame. Si el FPS no es válido, queda en 0 (sin espera).
        duracion_frame_objetivo = 1.0 / fps if fps and fps > 0 else 0.0

        # Solo se espera si hay una duración de frame válida
        if duracion_frame_objetivo > 0:
            # Hora actual
            ahora = time.perf_counter()
            # Si el reloj objetivo quedó más de un frame atrasado, se sincroniza
            # con la hora actual para no intentar recuperar el atraso de golpe.
            if tiempo_objetivo_siguiente < ahora - duracion_frame_objetivo:
                tiempo_objetivo_siguiente = ahora

            # Adelanta el reloj objetivo un frame
            tiempo_objetivo_siguiente += duracion_frame_objetivo
            # Cuánto falta para llegar a esa hora
            tiempo_restante = tiempo_objetivo_siguiente - time.perf_counter()
            # Si todavía falta tiempo, duerme lo que falta
            if tiempo_restante > 0:
                time.sleep(tiempo_restante)
        # Si no hay FPS válido, no se espera y el reloj se pone en "ahora"
        else:
            tiempo_objetivo_siguiente = time.perf_counter()

    # Salió del loop (se cerró la ventana): libera todo
    cerrar()


# cerrar(): cierra la ventana y libera los recursos de glfw
def cerrar():
    # Para poder cambiar la variable global _ventana
    global _ventana
    # Solo si la ventana existe
    if _ventana is not None:
        # Destruye la ventana
        glfw.destroy_window(_ventana)
        # Deja la variable en None para indicar que ya no hay ventana
        _ventana = None
    # Cierra glfw por completo
    glfw.terminate()
    # Avisa por consola
    mensaje.info("Ventana cerrada.")
