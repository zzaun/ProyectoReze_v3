"""
interfaz.py

Panel de control minimalista, fijo en el costado derecho de la
ventana, construido a mano con glfw + PyOpenGL puro (sin librerias de
UI externas -- ver el historial del proyecto: tanto pyimgui como
imgui-bundle resultaron incompatibles con este entorno).

Incluye:
    - Boton Play / Pause (pausa SOLO la animacion de fotogramas.xlsx)
    - Input numerico de FPS
    - Inputs numericos de CORRECCION_X y CORRECCION_Y

Como OpenGL/glfw no traen texto ni widgets, esto se resuelve con:
    - Una fuente de pixeles 5x7 hecha a mano (solo los caracteres que
      se usan: digitos, '.', '-', y las letras de las etiquetas), 
      dibujada con rectangulos (GL_QUADS).
    - Botones e inputs como rectangulos, con deteccion de click por
      "polling" (comparar la posicion del mouse contra cada rectangulo
      cada frame), igual que se hizo con ESC en windows.py.
    - Los inputs de texto usan glfw.set_char_callback (para capturar
      los caracteres tecleados) y polling de BACKSPACE/ENTER (para
      borrar / confirmar).
"""

import glfw
from OpenGL.GL import (
    glBegin, glEnd, glVertex2f, glColor3f, glColor4f,
    GL_QUADS, GL_LINE_LOOP,
)

import mensaje

ANCHO_PANEL = 260
COLOR_FONDO_PANEL = (0.12, 0.12, 0.12, 0.95)
COLOR_TEXTO = (0.95, 0.95, 0.95)
COLOR_BOTON = (0.25, 0.45, 0.85)
COLOR_BOTON_HOVER = (0.32, 0.55, 0.95)
COLOR_CAJA = (0.20, 0.20, 0.20)
COLOR_CAJA_ENFOCADA = (0.28, 0.28, 0.35)
COLOR_BORDE_ENFOCADO = (0.40, 0.70, 1.0)

FPS_MINIMO = 0.1
FPS_MAXIMO = 240.0

MARGEN = 15
ALTO_BOTON = 32
ALTO_CAJA = 26
ALTO_ETIQUETA = 16
ESPACIADO = 8

# --- Fuente de pixeles 5x7 (solo los caracteres usados en esta interfaz) ---
_FUENTE = {
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "N": ["10001", "11001", "10101", "10101", "10011", "10001", "10001"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
}
_ANCHO_GLIFO = 5
_ALTO_GLIFO = 7


def _dibujar_rectangulo(x, y, ancho, alto, color, relleno=True):
    if len(color) == 3:
        glColor3f(*color)
    else:
        glColor4f(*color)
    glBegin(GL_QUADS if relleno else GL_LINE_LOOP)
    glVertex2f(x, y)
    glVertex2f(x + ancho, y)
    glVertex2f(x + ancho, y + alto)
    glVertex2f(x, y + alto)
    glEnd()


def _dibujar_texto(x, y, texto, escala=2, color=COLOR_TEXTO):
    """Dibuja 'texto' empezando en (x, y) (esquina superior izquierda),
    usando la fuente de pixeles 5x7. Caracteres no soportados se
    dibujan como espacio."""
    glColor3f(*color)
    cursor_x = x
    for caracter in texto.upper():
        filas = _FUENTE.get(caracter, _FUENTE[" "])
        for fila_idx, fila in enumerate(filas):
            for col_idx, bit in enumerate(fila):
                if bit == "1":
                    px = cursor_x + col_idx * escala
                    py = y + fila_idx * escala
                    glBegin(GL_QUADS)
                    glVertex2f(px, py)
                    glVertex2f(px + escala, py)
                    glVertex2f(px + escala, py + escala)
                    glVertex2f(px, py + escala)
                    glEnd()
        cursor_x += (_ANCHO_GLIFO + 1) * escala


def _ancho_texto(texto, escala=2):
    return len(texto) * (_ANCHO_GLIFO + 1) * escala


def _punto_dentro_de_rect(px, py, rect):
    x, y, ancho, alto = rect
    return x <= px <= x + ancho and y <= py <= y + alto


def _formatear_numero(valor):
    """Muestra enteros sin decimales (ej. '30') y el resto con 2
    decimales (ej. '-15.50'), para que no se vea '30.00' innecesario."""
    if valor == int(valor):
        return str(int(valor))
    return f"{valor:.2f}"


class _CampoNumerico:
    """Un input de texto para un solo valor numerico (usado para FPS,
    CORRECCION_X y CORRECCION_Y)."""

    def __init__(self, valorInicial):
        self.valor = float(valorInicial)
        self.textoEditando = None  # None = no enfocado
        self.rect = (0, 0, 0, 0)  # se actualiza cada frame en dibujar()

    def enfocar(self):
        self.textoEditando = _formatear_numero(self.valor)

    def confirmar(self):
        """Intenta convertir el texto escrito a numero. Si no es un
        numero valido, se descarta el cambio (se queda con el valor
        anterior) y se avisa por mensaje.py."""
        if self.textoEditando is not None and self.textoEditando not in ("", "-", "."):
            try:
                self.valor = float(self.textoEditando)
            except ValueError:
                mensaje.advertencia(f"'{self.textoEditando}' no es un numero valido, se descarta.")
        self.textoEditando = None

    def texto_mostrado(self):
        return self.textoEditando if self.textoEditando is not None else _formatear_numero(self.valor)


class Interfaz:
    def __init__(self, ventanaGLFW, obtenerTamanoVentana,
                 fpsInicial=1.0, correccionXInicial=0.0, correccionYInicial=0.0):
        self._ventana = ventanaGLFW
        self._obtenerTamanoVentana = obtenerTamanoVentana

        self.pausado = False
        self._campoFPS = _CampoNumerico(fpsInicial)
        self._campoCorreccionX = _CampoNumerico(correccionXInicial)
        self._campoCorreccionY = _CampoNumerico(correccionYInicial)
        self._campos = {
            "fps": self._campoFPS,
            "cx": self._campoCorreccionX,
            "cy": self._campoCorreccionY,
        }
        self._campoEnfocado = None  # None, "fps", "cx" o "cy"

        self._botonRect = (0, 0, 0, 0)
        self._mousePresionadoAntes = False
        self._backspaceAntes = False
        self._enterAntes = False

        glfw.set_char_callback(ventanaGLFW, self._callback_char)

        mensaje.info("Interfaz inicializada (dibujada a mano, sin dependencias externas).")

    # --- Getters usados por main.py / windows.py en cada frame ---

    def estaPausado(self):
        return self.pausado

    def obtenerFPS(self):
        return self._campoFPS.valor

    def obtenerCorreccionX(self):
        return self._campoCorreccionX.valor

    def obtenerCorreccionY(self):
        return self._campoCorreccionY.valor

    # --- Entrada de texto (glfw char callback) ---

    def _callback_char(self, ventana, codepoint):
        if self._campoEnfocado is None:
            return
        caracter = chr(codepoint)
        if caracter in "0123456789.-":
            campo = self._campos[self._campoEnfocado]
            campo.textoEditando += caracter

    # --- Hook para windows.ejecutar(): logica de entrada (mouse/teclado) ---

    def procesarEventos(self):
        """
        Revisa mouse y teclado por 'polling' (igual que el ESC en
        windows.py): click del mouse, BACKSPACE y ENTER. Debe llamarse
        una vez por frame, despues de glfw.poll_events().
        """
        mouse_x, mouse_y = glfw.get_cursor_pos(self._ventana)
        mouse_presionado = glfw.get_mouse_button(self._ventana, glfw.MOUSE_BUTTON_LEFT) == glfw.PRESS
        click_este_frame = mouse_presionado and not self._mousePresionadoAntes
        self._mousePresionadoAntes = mouse_presionado

        if click_este_frame:
            if _punto_dentro_de_rect(mouse_x, mouse_y, self._botonRect):
                self.pausado = not self.pausado
                self._enfocar_campo(None)
            else:
                clic_en_algun_campo = False
                for nombre, campo in self._campos.items():
                    if _punto_dentro_de_rect(mouse_x, mouse_y, campo.rect):
                        self._enfocar_campo(nombre)
                        clic_en_algun_campo = True
                        break
                if not clic_en_algun_campo:
                    self._enfocar_campo(None)  # click afuera: confirma y desenfoca

        if self._campoEnfocado is not None:
            backspace_presionado = glfw.get_key(self._ventana, glfw.KEY_BACKSPACE) == glfw.PRESS
            if backspace_presionado and not self._backspaceAntes:
                campo = self._campos[self._campoEnfocado]
                campo.textoEditando = campo.textoEditando[:-1]
            self._backspaceAntes = backspace_presionado

            enter_presionado = (
                glfw.get_key(self._ventana, glfw.KEY_ENTER) == glfw.PRESS
                or glfw.get_key(self._ventana, glfw.KEY_KP_ENTER) == glfw.PRESS
            )
            if enter_presionado and not self._enterAntes:
                self._enfocar_campo(None)
            self._enterAntes = enter_presionado

        # FPS: se recorta al rango permitido apenas cambia.
        self._campoFPS.valor = max(FPS_MINIMO, min(FPS_MAXIMO, self._campoFPS.valor))

    def _enfocar_campo(self, nombre):
        """Cambia el campo enfocado, confirmando (convirtiendo a
        numero) el que se estaba editando antes, si habia uno."""
        if self._campoEnfocado is not None:
            self._campos[self._campoEnfocado].confirmar()
        self._campoEnfocado = nombre
        if nombre is not None:
            self._campos[nombre].enfocar()

    # --- Hook para windows.ejecutar(): dibujo del panel ---

    def dibujar(self):
        """Dibuja el panel completo. Debe llamarse una vez por frame,
        DESPUES de dibujar la escena (para quedar encima)."""
        ancho_ventana, alto_ventana = self._obtenerTamanoVentana()
        panel_x = max(0, ancho_ventana - ANCHO_PANEL)

        _dibujar_rectangulo(panel_x, 0, ANCHO_PANEL, alto_ventana, COLOR_FONDO_PANEL)

        x = panel_x + MARGEN
        ancho_util = ANCHO_PANEL - 2 * MARGEN
        y = MARGEN

        _dibujar_texto(x, y, "CONTROLES", escala=2)
        y += ALTO_ETIQUETA + ESPACIADO * 2

        # --- Boton Play/Pause ---
        self._botonRect = (x, y, ancho_util, ALTO_BOTON)
        mouse_x, mouse_y = glfw.get_cursor_pos(self._ventana)
        con_hover = _punto_dentro_de_rect(mouse_x, mouse_y, self._botonRect)
        _dibujar_rectangulo(x, y, ancho_util, ALTO_BOTON,
                             COLOR_BOTON_HOVER if con_hover else COLOR_BOTON)
        etiqueta_boton = "PAUSE" if not self.pausado else "PLAY"
        texto_x = x + (ancho_util - _ancho_texto(etiqueta_boton, escala=2)) / 2
        texto_y = y + (ALTO_BOTON - _ALTO_GLIFO * 2) / 2
        _dibujar_texto(texto_x, texto_y, etiqueta_boton, escala=2)
        y += ALTO_BOTON + ESPACIADO * 2

        # --- Campos numericos ---
        y = self._dibujar_campo(x, y, ancho_util, "FPS", self._campoFPS, "fps")
        y = self._dibujar_campo(x, y, ancho_util, "CORRECCION X", self._campoCorreccionX, "cx")
        y = self._dibujar_campo(x, y, ancho_util, "CORRECCION Y", self._campoCorreccionY, "cy")

    def _dibujar_campo(self, x, y, ancho, etiqueta, campo, nombre):
        _dibujar_texto(x, y, etiqueta, escala=1)
        y += ALTO_ETIQUETA

        campo.rect = (x, y, ancho, ALTO_CAJA)
        enfocado = self._campoEnfocado == nombre
        _dibujar_rectangulo(x, y, ancho, ALTO_CAJA,
                             COLOR_CAJA_ENFOCADA if enfocado else COLOR_CAJA)
        if enfocado:
            _dibujar_rectangulo(x, y, ancho, ALTO_CAJA, COLOR_BORDE_ENFOCADO, relleno=False)

        texto = campo.texto_mostrado()
        _dibujar_texto(x + 6, y + (ALTO_CAJA - _ALTO_GLIFO * 2) / 2, texto, escala=2)

        return y + ALTO_CAJA + ESPACIADO * 2

    def cerrar(self):
        """No hay recursos externos que liberar (sin dependencias de
        terceros); se deja por simetria con el resto del proyecto."""
        pass