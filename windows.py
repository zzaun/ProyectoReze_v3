"""
windows.py

Se encarga de todo lo relacionado a la ventana:
    - Inicializar glfw y crear el contexto OpenGL.
    - Configurar una proyeccion ortografica en PIXELES ABSOLUTOS: 1 unidad
      de coordenada siempre equivale a 1 pixel en pantalla, sin importar
      el tamano de la ventana. Si la ventana crece, simplemente se ve mas
      lienzo (mas area visible), nunca se estira el dibujo.
    - El origen (0, 0) esta en la esquina superior izquierda, con el eje Y
      creciendo hacia ABAJO (convencion de pixeles de pantalla). La
      conversion entre este sistema y el sistema de coordenadas de los
      datos del excel (que puede ser cartesiano) es responsabilidad de
      dibujar.py, no de este modulo.
    - Correr el loop principal: procesar eventos, limpiar pantalla,
      invocar la funcion de dibujo que se le pase, intercambiar buffers
      y controlar la tasa de refresco manualmente con time.sleep().
"""

import time

import glfw
from OpenGL.GL import (
    glClear, glClearColor, glViewport, glMatrixMode, glLoadIdentity,
    glOrtho, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT,
    GL_PROJECTION, GL_MODELVIEW,
)

import color
import mensaje

ANCHO_DEFECTO = 1000
ALTO_DEFECTO = 1000
TITULO_DEFECTO = "Dibujo de Capas"
FPS_DEFECTO = 1
COLOR_FONDO_DEFECTO = "#FFFFFF"

_ventana = None
_ancho_actual = ANCHO_DEFECTO
_alto_actual = ALTO_DEFECTO


def _configurar_proyeccion_absoluta(ancho, alto):
    """
    Establece la proyeccion ortografica de forma que las coordenadas que
    se dibujen sean pixeles absolutos: (0,0) arriba-izquierda, Y crece
    hacia abajo, y 1 unidad = 1 pixel siempre, sin escalar segun el
    tamano de la ventana.
    """
    glViewport(0, 0, ancho, alto)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    # left, right, bottom, top, near, far
    # bottom > top intencionalmente: hace que Y crezca hacia abajo.
    glOrtho(0, ancho, alto, 0, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def _callback_framebuffer_size(ventana_glfw, ancho, alto):
    global _ancho_actual, _alto_actual
    # Cuando alto/ancho llegan en 0 (por ejemplo al minimizar), se ignora
    # para no romper la proyeccion.
    if ancho <= 0 or alto <= 0:
        return
    _ancho_actual = ancho
    _alto_actual = alto
    _configurar_proyeccion_absoluta(ancho, alto)


def establecerColorFondo(valorColor):
    """
    Cambia el color de fondo de la ventana. Acepta cualquier formato
    tolerado por color.py (hex, rgb(...), nombre, etc.). Puede llamarse
    tanto antes como despues de inicializar()/durante la ejecucion.
    """
    r, g, b, a = color.obtenerColorOpenGL(valorColor)
    glClearColor(r, g, b, a)


def inicializar(ancho=ANCHO_DEFECTO, alto=ALTO_DEFECTO, titulo=TITULO_DEFECTO,
                 pantalla_completa=False, colorFondo=COLOR_FONDO_DEFECTO):
    """
    Crea la ventana y el contexto OpenGL. Debe llamarse una sola vez,
    antes de ejecutar() y antes de cualquier comando de dibujo.

    Regresa True si la inicializacion fue exitosa, False en caso
    contrario.
    """
    global _ventana, _ancho_actual, _alto_actual

    if not glfw.init():
        mensaje.error("No se pudo inicializar glfw.")
        return False

    monitor = None
    if pantalla_completa:
        monitor = glfw.get_primary_monitor()
        modo_video = glfw.get_video_mode(monitor)
        ancho, alto = modo_video.size.width, modo_video.size.height

    _ventana = glfw.create_window(ancho, alto, titulo, monitor, None)
    if not _ventana:
        mensaje.error("No se pudo crear la ventana.")
        glfw.terminate()
        return False

    glfw.make_context_current(_ventana)

    # Desactivamos vsync: la tasa de refresco la controlamos nosotros a
    # mano en ejecutar(), con time.sleep().
    glfw.swap_interval(0)

    glfw.set_framebuffer_size_callback(_ventana, _callback_framebuffer_size)
    # Nota: NO registramos un callback de teclado aqui (glfw.set_key_callback).
    # ESC se revisa por "polling" dentro de ejecutar() en vez de por
    # callback, para dejar ese callback libre para pyimgui (interfaz.py),
    # que necesita instalar los suyos propios para que los inputs de
    # texto funcionen. Si ambos registraran un callback de teclado, el
    # segundo pisaria al primero.

    # El tamano real del framebuffer puede diferir del solicitado (por
    # ejemplo en pantallas con escalado/HiDPI), asi que se toma el real.
    ancho_real, alto_real = glfw.get_framebuffer_size(_ventana)
    _ancho_actual, _alto_actual = ancho_real, alto_real

    establecerColorFondo(colorFondo)
    _configurar_proyeccion_absoluta(ancho_real, alto_real)

    mensaje.info(f"Ventana inicializada ({ancho_real}x{alto_real}).")
    return True


def obtenerTamano():
    """Regresa (ancho, alto) actuales de la ventana, en pixeles."""
    return _ancho_actual, _alto_actual


def obtenerVentanaGLFW():
    """
    Regresa el handle nativo de la ventana de glfw. Pensado para que
    interfaz.py pueda engancharle pyimgui (GlfwRenderer necesita este
    handle). El resto del proyecto no deberia necesitarlo.
    """
    return _ventana


def ejecutar(funcionDibujo, fpsObjetivo=FPS_DEFECTO, funcionUI=None, funcionEventosUI=None):
    """
    Corre el loop principal hasta que el usuario cierre la ventana (o
    presione ESC). En cada vuelta:
        1. Procesa eventos (resize, etc.)
        2. Si se paso 'funcionEventosUI', la llama (por ejemplo, para
           que pyimgui procese mouse/teclado).
        3. Revisa si se presiono ESC (por polling, no por callback) y
           cierra la ventana si es asi.
        4. Limpia la pantalla.
        5. Llama a funcionDibujo() (sin argumentos): todo el dibujo de
           ese frame (animacion + estatico).
        6. Si se paso 'funcionUI', la llama DESPUES del dibujo (encima):
           pensada para dibujar un panel de interfaz (ej. con pyimgui).
        7. Intercambia los buffers (muestra lo dibujado).
        8. Duerme hasta el momento en que debe ocurrir el siguiente
           frame, segun el FPS objetivo vigente EN ESE MOMENTO.

    'fpsObjetivo' puede ser:
        - un numero fijo (comportamiento de siempre), o
        - una funcion sin argumentos que regresa el FPS actual (por
          ejemplo interfaz.obtenerFPS), para poder cambiarlo en vivo
          desde la interfaz sin reiniciar el loop.

    Control de tiempo: se mantiene un "reloj objetivo" que avanza
    'duracion_frame_objetivo' en cada vuelta (recalculado cada vez por
    si el FPS cambio). Si el programa se atrasa mas de un frame
    completo (por una pausa larga, trabajo pesado, etc.), el reloj se
    resincroniza al tiempo actual en vez de intentar "alcanzar" el
    atraso de golpe (evita una rafaga de frames sin dormir nada).

    'funcionDibujo', 'funcionUI' y 'funcionEventosUI' se pasan como
    parametros para no acoplar windows.py a dibujar.py ni a pyimgui:
    windows.py solo necesita algo invocable.
    """
    if _ventana is None:
        mensaje.error("La ventana no ha sido inicializada. Llama a inicializar() primero.")
        return

    def _fps_actual():
        return fpsObjetivo() if callable(fpsObjetivo) else fpsObjetivo

    tiempo_objetivo_siguiente = time.perf_counter()

    while not glfw.window_should_close(_ventana):
        glfw.poll_events()

        if funcionEventosUI is not None:
            try:
                funcionEventosUI()
            except Exception as e:
                mensaje.error(f"Error procesando eventos de interfaz: {e}")

        if glfw.get_key(_ventana, glfw.KEY_ESCAPE) == glfw.PRESS:
            glfw.set_window_should_close(_ventana, True)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        try:
            funcionDibujo()
        except Exception as e:
            mensaje.error(f"Error dentro de la funcion de dibujo: {e}")

        if funcionUI is not None:
            try:
                funcionUI()
            except Exception as e:
                mensaje.error(f"Error dentro de la funcion de interfaz: {e}")

        glfw.swap_buffers(_ventana)

        fps = _fps_actual()
        duracion_frame_objetivo = 1.0 / fps if fps and fps > 0 else 0.0

        if duracion_frame_objetivo > 0:
            ahora = time.perf_counter()
            # Si nos atrasamos mas de un frame completo, resincroniza en
            # vez de intentar recuperar el atraso de golpe.
            if tiempo_objetivo_siguiente < ahora - duracion_frame_objetivo:
                tiempo_objetivo_siguiente = ahora

            tiempo_objetivo_siguiente += duracion_frame_objetivo
            tiempo_restante = tiempo_objetivo_siguiente - time.perf_counter()
            if tiempo_restante > 0:
                time.sleep(tiempo_restante)
        else:
            tiempo_objetivo_siguiente = time.perf_counter()

    cerrar()


def cerrar():
    """Cierra la ventana y libera los recursos de glfw."""
    global _ventana
    if _ventana is not None:
        glfw.destroy_window(_ventana)
        _ventana = None
    glfw.terminate()
    mensaje.info("Ventana cerrada.")