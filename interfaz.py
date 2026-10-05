# interfaz.py
# Panel de control minimalista, fijo en el costado derecho de la
# ventana, hecho a mano con glfw + PyOpenGL puro (sin librerias de UI
# externas: tanto pyimgui como imgui-bundle resultaron incompatibles
# con este entorno, por eso se construyo asi).
#
# Incluye:
#   - Boton Play / Pause (pausa la animacion y la musica de fondo)
#   - Input numerico de FPS
#   - Inputs numericos de CORRECCION_X y CORRECCION_Y
#   - Input numerico de VOLUMEN (musica + efectos de sonido)
#
# Como OpenGL/glfw no traen texto ni widgets, esto se resuelve con una
# fuente de pixeles 5x7 hecha a mano, botones/inputs como rectangulos,
# deteccion de click por "polling" (comparar el mouse contra cada
# rectangulo cada frame), y glfw.set_char_callback para capturar lo
# que se teclea dentro de un input enfocado.

# Importamos glfw para leer mouse/teclado directamente.
import glfw
# Importamos las funciones de OpenGL que usamos para dibujar rectangulos y texto.
from OpenGL.GL import (
    glBegin, glEnd, glVertex2f, glColor3f, glColor4f,
    GL_QUADS, GL_LINE_LOOP,
)

# Importamos mensaje.py para avisar en consola si algo no se puede inicializar.
import mensaje

# Ancho fijo del panel, en pixeles.
ANCHO_PANEL = 260
# Color de fondo del panel (gris oscuro, casi opaco).
COLOR_FONDO_PANEL = (0.12, 0.12, 0.12, 0.95)
# Color del texto normal.
COLOR_TEXTO = (0.95, 0.95, 0.95)
# Color del boton Play/Pause.
COLOR_BOTON = (0.25, 0.45, 0.85)
# Color del boton cuando el mouse esta encima (hover).
COLOR_BOTON_HOVER = (0.32, 0.55, 0.95)
# Color de fondo de una caja de texto normal.
COLOR_CAJA = (0.20, 0.20, 0.20)
# Color de fondo de una caja de texto cuando esta enfocada (se esta editando).
COLOR_CAJA_ENFOCADA = (0.28, 0.28, 0.35)
# Color del borde de una caja enfocada.
COLOR_BORDE_ENFOCADO = (0.40, 0.70, 1.0)

# Rango permitido para el valor de FPS.
FPS_MINIMO = 0.1
FPS_MAXIMO = 240.0

# Rango permitido para el volumen (0 = silencio, 1 = volumen maximo).
VOLUMEN_MINIMO = 0.0
VOLUMEN_MAXIMO = 1.0

# Medidas de layout del panel, todas en pixeles.
MARGEN = 15
ALTO_BOTON = 32
ALTO_CAJA = 26
ALTO_ETIQUETA = 16
ESPACIADO = 8

# Fuente de pixeles 5x7: cada caracter es una lista de 7 filas, cada
# fila un texto de 5 caracteres ('1' = pixel encendido, '0' = apagado).
# Solo se definen los caracteres que esta interfaz realmente usa.
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
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
}
# Ancho de cada glifo, en "pixeles" de la fuente.
_ANCHO_GLIFO = 5
# Alto de cada glifo, en "pixeles" de la fuente.
_ALTO_GLIFO = 7


# Dibuja un rectangulo relleno (o solo el borde, si relleno=False).
def _dibujar_rectangulo(x, y, ancho, alto, color, relleno=True):
    # Si el color tiene 3 numeros, es RGB; si tiene 4, es RGBA (con transparencia).
    if len(color) == 3:
        glColor3f(*color)
    else:
        glColor4f(*color)
    # GL_QUADS dibuja un rectangulo relleno; GL_LINE_LOOP solo el contorno.
    glBegin(GL_QUADS if relleno else GL_LINE_LOOP)
    glVertex2f(x, y)
    glVertex2f(x + ancho, y)
    glVertex2f(x + ancho, y + alto)
    glVertex2f(x, y + alto)
    glEnd()


# Dibuja un texto empezando en (x, y), usando la fuente de pixeles.
def _dibujar_texto(x, y, texto, escala=2, color=COLOR_TEXTO):
    glColor3f(*color)
    # cursor_x va avanzando a la derecha conforme dibujamos cada letra.
    cursor_x = x
    # Recorremos cada caracter del texto (en mayusculas, la fuente solo tiene mayusculas).
    for caracter in texto.upper():
        # Buscamos el dibujo del caracter; si no existe, usamos un espacio en blanco.
        filas = _FUENTE.get(caracter, _FUENTE[" "])
        # Recorremos cada fila del glifo (de arriba hacia abajo).
        for fila_idx, fila in enumerate(filas):
            # Recorremos cada columna de esa fila.
            for col_idx, bit in enumerate(fila):
                # Si el pixel esta encendido ('1'), dibujamos un cuadradito ahi.
                if bit == "1":
                    px = cursor_x + col_idx * escala
                    py = y + fila_idx * escala
                    glBegin(GL_QUADS)
                    glVertex2f(px, py)
                    glVertex2f(px + escala, py)
                    glVertex2f(px + escala, py + escala)
                    glVertex2f(px, py + escala)
                    glEnd()
        # Avanzamos el cursor para la siguiente letra (5 columnas + 1 de espacio).
        cursor_x += (_ANCHO_GLIFO + 1) * escala


# Calcula cuanto espacio (en pixeles) ocupa un texto al dibujarse, sin dibujarlo.
def _ancho_texto(texto, escala=2):
    return len(texto) * (_ANCHO_GLIFO + 1) * escala


# Revisa si el punto (px, py) cae dentro de un rectangulo (x, y, ancho, alto).
def _punto_dentro_de_rect(px, py, rect):
    x, y, ancho, alto = rect
    return x <= px <= x + ancho and y <= py <= y + alto


# Convierte un numero a texto para mostrarlo: sin decimales si es
# entero (ej. '30'), con 2 decimales si no lo es (ej. '-15.50').
def _formatear_numero(valor):
    if valor == int(valor):
        return str(int(valor))
    return f"{valor:.2f}"


# Representa un input de texto para UN solo valor numerico (se usa
# para FPS, CORRECCION_X, CORRECCION_Y y VOLUMEN).
class _CampoNumerico:

    # Al crear el campo, se le da su valor inicial.
    def __init__(self, valorInicial):
        # El valor numerico "de verdad" (el que usa el resto del programa).
        self.valor = float(valorInicial)
        # El texto que se esta escribiendo mientras el campo esta enfocado.
        # None significa que el campo no esta enfocado ahorita.
        self.textoEditando = None
        # El rectangulo donde se dibuja este campo (se recalcula cada frame).
        self.rect = (0, 0, 0, 0)

    # Se llama cuando el usuario hace click en este campo: empieza a editarlo.
    def enfocar(self):
        self.textoEditando = _formatear_numero(self.valor)

    # Se llama cuando se deja de editar este campo (Enter o click afuera):
    # intenta convertir el texto escrito a numero.
    def confirmar(self):
        # Si lo que quedo escrito no es un numero valido, se descarta el cambio.
        if self.textoEditando is not None and self.textoEditando not in ("", "-", "."):
            try:
                self.valor = float(self.textoEditando)
            except ValueError:
                mensaje.advertencia(f"'{self.textoEditando}' no es un numero valido, se descarta.")
        # Al confirmar, dejamos de estar en modo edicion.
        self.textoEditando = None

    # Regresa el texto que debe mostrarse ahorita en el campo (lo que se
    # esta escribiendo, o el valor actual si no se esta editando).
    def texto_mostrado(self):
        return self.textoEditando if self.textoEditando is not None else _formatear_numero(self.valor)


# Clase principal: agrupa todo el panel de interfaz.
class Interfaz:

    # Se ejecuta al crear la interfaz. Prepara los campos y conecta el
    # callback de teclado con glfw.
    def __init__(self, ventanaGLFW, obtenerTamanoVentana,
                 fpsInicial=1.0, correccionXInicial=0.0, correccionYInicial=0.0,
                 volumenInicial=1.0):
        # Guardamos el handle de la ventana, para leer mouse/teclado.
        self._ventana = ventanaGLFW
        # Guardamos la funcion que nos dice el tamano actual de la ventana.
        self._obtenerTamanoVentana = obtenerTamanoVentana

        # Estado de Play/Pause (False = reproduciendo, True = pausado).
        self.pausado = False
        # Creamos cada campo numerico con su valor inicial.
        self._campoFPS = _CampoNumerico(fpsInicial)
        self._campoCorreccionX = _CampoNumerico(correccionXInicial)
        self._campoCorreccionY = _CampoNumerico(correccionYInicial)
        self._campoVolumen = _CampoNumerico(volumenInicial)
        # Diccionario para poder buscar un campo por su nombre corto.
        self._campos = {
            "fps": self._campoFPS,
            "cx": self._campoCorreccionX,
            "cy": self._campoCorreccionY,
            "vol": self._campoVolumen,
        }
        # Nombre del campo que esta enfocado ahorita (None = ninguno).
        self._campoEnfocado = None

        # Rectangulo del boton Play/Pause (se recalcula cada frame).
        self._botonRect = (0, 0, 0, 0)
        # Guardamos el estado del mouse/teclado del frame anterior, para
        # detectar el momento EXACTO en que se presiona algo (no cada
        # frame que se mantiene presionado).
        self._mousePresionadoAntes = False
        self._backspaceAntes = False
        self._enterAntes = False

        # Le decimos a glfw que nos avise cada vez que se teclea un caracter.
        glfw.set_char_callback(ventanaGLFW, self._callback_char)

        mensaje.info("Interfaz inicializada (dibujada a mano, sin dependencias externas).")

    # --- Getters usados por main.py en cada frame ---

    # Regresa si la animacion esta pausada.
    def estaPausado(self):
        return self.pausado

    # Regresa el FPS actual configurado en el panel.
    def obtenerFPS(self):
        return self._campoFPS.valor

    # Regresa la correccion de posicion en X.
    def obtenerCorreccionX(self):
        return self._campoCorreccionX.valor

    # Regresa la correccion de posicion en Y.
    def obtenerCorreccionY(self):
        return self._campoCorreccionY.valor

    # Regresa el volumen actual configurado en el panel (0.0 a 1.0).
    def obtenerVolumen(self):
        return self._campoVolumen.valor

    # --- Entrada de texto (glfw lo llama solo cuando se teclea algo) ---

    # Se ejecuta cada vez que se teclea un caracter en la ventana.
    def _callback_char(self, ventana, codepoint):
        # Si no hay ningun campo enfocado, no hacemos nada con lo tecleado.
        if self._campoEnfocado is None:
            return
        # Convertimos el codigo de caracter a texto real.
        caracter = chr(codepoint)
        # Solo aceptamos digitos, punto y guion (numeros validos).
        if caracter in "0123456789.-":
            campo = self._campos[self._campoEnfocado]
            campo.textoEditando += caracter

    # --- Logica de entrada (mouse/teclado), se llama una vez por frame ---

    # Revisa clicks del mouse y teclas especiales (BACKSPACE, ENTER).
    # Debe llamarse despues de glfw.poll_events().
    def procesarEventos(self):
        # Posicion actual del mouse.
        mouse_x, mouse_y = glfw.get_cursor_pos(self._ventana)
        # Si el boton izquierdo esta presionado ahorita.
        mouse_presionado = glfw.get_mouse_button(self._ventana, glfw.MOUSE_BUTTON_LEFT) == glfw.PRESS
        # Un "click" cuenta solo en el instante en que se presiona (no mientras se mantiene).
        click_este_frame = mouse_presionado and not self._mousePresionadoAntes
        self._mousePresionadoAntes = mouse_presionado

        if click_este_frame:
            # Si el click fue sobre el boton Play/Pause, cambiamos el estado.
            if _punto_dentro_de_rect(mouse_x, mouse_y, self._botonRect):
                self.pausado = not self.pausado
                self._enfocar_campo(None)
            else:
                # Si no fue el boton, revisamos si fue sobre algun campo numerico.
                clic_en_algun_campo = False
                for nombre, campo in self._campos.items():
                    if _punto_dentro_de_rect(mouse_x, mouse_y, campo.rect):
                        self._enfocar_campo(nombre)
                        clic_en_algun_campo = True
                        break
                # Si el click fue afuera de todo, confirmamos y desenfocamos.
                if not clic_en_algun_campo:
                    self._enfocar_campo(None)

        # Si hay un campo enfocado, revisamos BACKSPACE y ENTER.
        if self._campoEnfocado is not None:
            backspace_presionado = glfw.get_key(self._ventana, glfw.KEY_BACKSPACE) == glfw.PRESS
            # Igual que con el click: solo contamos el instante en que se presiona.
            if backspace_presionado and not self._backspaceAntes:
                campo = self._campos[self._campoEnfocado]
                campo.textoEditando = campo.textoEditando[:-1]
            self._backspaceAntes = backspace_presionado

            enter_presionado = (
                glfw.get_key(self._ventana, glfw.KEY_ENTER) == glfw.PRESS
                or glfw.get_key(self._ventana, glfw.KEY_KP_ENTER) == glfw.PRESS
            )
            if enter_presionado and not self._enterAntes:
                # ENTER confirma el campo y lo desenfoca.
                self._enfocar_campo(None)
            self._enterAntes = enter_presionado

        # El FPS se recorta al rango permitido apenas cambia.
        self._campoFPS.valor = max(FPS_MINIMO, min(FPS_MAXIMO, self._campoFPS.valor))
        # El volumen se recorta entre 0.0 y 1.0 apenas cambia.
        self._campoVolumen.valor = max(VOLUMEN_MINIMO, min(VOLUMEN_MAXIMO, self._campoVolumen.valor))

    # Cambia cual campo esta enfocado. Antes de cambiar, confirma (convierte
    # a numero) el que se estaba editando, si habia uno.
    def _enfocar_campo(self, nombre):
        if self._campoEnfocado is not None:
            self._campos[self._campoEnfocado].confirmar()
        self._campoEnfocado = nombre
        if nombre is not None:
            self._campos[nombre].enfocar()

    # --- Dibujo del panel, se llama una vez por frame, encima de la escena ---

    # Dibuja el panel completo: fondo, boton, y los 4 campos numericos.
    def dibujar(self):
        # Tamano actual de la ventana, para saber donde queda el borde derecho.
        ancho_ventana, alto_ventana = self._obtenerTamanoVentana()
        panel_x = max(0, ancho_ventana - ANCHO_PANEL)

        # Fondo del panel: un rectangulo solido de alto completo.
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

        # --- Campos numericos, uno debajo del otro ---
        y = self._dibujar_campo(x, y, ancho_util, "FPS", self._campoFPS, "fps")
        y = self._dibujar_campo(x, y, ancho_util, "CORRECCION X", self._campoCorreccionX, "cx")
        y = self._dibujar_campo(x, y, ancho_util, "CORRECCION Y", self._campoCorreccionY, "cy")
        y = self._dibujar_campo(x, y, ancho_util, "VOLUMEN", self._campoVolumen, "vol")

    # Dibuja un campo individual (etiqueta + caja de texto), y regresa la
    # posicion Y donde debe empezar el siguiente campo.
    def _dibujar_campo(self, x, y, ancho, etiqueta, campo, nombre):
        _dibujar_texto(x, y, etiqueta, escala=1)
        y += ALTO_ETIQUETA

        campo.rect = (x, y, ancho, ALTO_CAJA)
        enfocado = self._campoEnfocado == nombre
        _dibujar_rectangulo(x, y, ancho, ALTO_CAJA,
                             COLOR_CAJA_ENFOCADA if enfocado else COLOR_CAJA)
        # Si esta enfocado, le dibujamos un borde de color encima para que se note.
        if enfocado:
            _dibujar_rectangulo(x, y, ancho, ALTO_CAJA, COLOR_BORDE_ENFOCADO, relleno=False)

        texto = campo.texto_mostrado()
        _dibujar_texto(x + 6, y + (ALTO_CAJA - _ALTO_GLIFO * 2) / 2, texto, escala=2)

        return y + ALTO_CAJA + ESPACIADO * 2

    # No hay recursos externos que liberar (sin dependencias de
    # terceros), se deja este metodo por simetria con el resto del proyecto.
    def cerrar(self):
        pass