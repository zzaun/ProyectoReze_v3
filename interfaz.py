# interfaz.py
#
# Panel de controles sencillo, fijo en el lado derecho de la ventana. Está
# hecho a mano con glfw + PyOpenGL, sin librerías de interfaz externas (las
# que se probaron, pyimgui e imgui-bundle, no funcionaron en este entorno).
#
# Tiene:
#   - Botón Play / Pause (pausa SOLO la animación de fotogramas.xlsx)
#   - Campo numérico de FPS
#   - Campos numéricos de CORRECCION X y CORRECCION Y
#
# OpenGL y glfw no traen texto ni botones, así que se resuelve así:
#   - Una fuente de píxeles de 5x7 hecha a mano (solo los caracteres que se
#     usan: dígitos, '.', '-' y las letras de las etiquetas), dibujada con
#     rectángulos (GL_QUADS).
#   - Botones y campos son rectángulos. Los clics se detectan por "polling":
#     en cada frame se compara la posición del mouse con cada rectángulo (igual
#     que se hizo con ESC en windows.py).
#   - Los campos de texto usan glfw.set_char_callback para recibir las teclas
#     que se escriben, y polling para BACKSPACE (borrar) y ENTER (confirmar).

# Para leer mouse y teclado
import glfw
# Funciones y constantes de OpenGL que se usan para dibujar el panel
from OpenGL.GL import (
    glBegin, glEnd, glVertex2f, glColor3f, glColor4f,
    GL_QUADS, GL_LINE_LOOP,
)

# Para imprimir avisos en la consola
import mensaje

# Ancho del panel en píxeles
ANCHO_PANEL = 260
# Color de fondo del panel: (rojo, verde, azul, alfa), gris oscuro casi opaco
COLOR_FONDO_PANEL = (0.12, 0.12, 0.12, 0.95)
# Color del texto: casi blanco
COLOR_TEXTO = (0.95, 0.95, 0.95)
# Color del botón Play/Pause: azul
COLOR_BOTON = (0.25, 0.45, 0.85)
# Color del botón cuando el mouse está encima: azul más claro
COLOR_BOTON_HOVER = (0.32, 0.55, 0.95)
# Color de las cajas de texto: gris
COLOR_CAJA = (0.20, 0.20, 0.20)
# Color de la caja de texto que se está editando
COLOR_CAJA_ENFOCADA = (0.28, 0.28, 0.35)
# Color del borde de la caja que se está editando: azul claro
COLOR_BORDE_ENFOCADO = (0.40, 0.70, 1.0)

# FPS más bajo que se permite en el campo de FPS
FPS_MINIMO = 0.1
# FPS más alto que se permite en el campo de FPS
FPS_MAXIMO = 240.0

# Espacio entre el borde del panel y su contenido
MARGEN = 15
# Alto del botón en píxeles
ALTO_BOTON = 32
# Alto de las cajas de texto en píxeles
ALTO_CAJA = 26
# Alto que se reserva para el texto de cada etiqueta
ALTO_ETIQUETA = 16
# Espacio vertical entre elementos
ESPACIADO = 8

# Fuente de píxeles 5x7 hecha a mano. Cada carácter es una lista de 7 textos
# (las filas) de 5 caracteres (las columnas). Un "1" es un píxel pintado y un
# "0" es un píxel vacío. Por ejemplo, la "I" es:
#   11111
#   00100
#   00100
#   00100
#   00100
#   00100
#   11111
# Todos los caracteres siguen el mismo patrón, por eso solo se explica aquí.
# Solo están los caracteres que usa el panel; cualquier otro se dibuja como espacio.
_FUENTE = {
    # Dígitos
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
    # Punto y guion (para escribir decimales y números negativos)
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    # Letras
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
    # Espacio (todo vacío)
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
}
# Ancho de cada carácter en píxeles de la fuente (5 columnas)
_ANCHO_GLIFO = 5
# Alto de cada carácter en píxeles de la fuente (7 filas)
_ALTO_GLIFO = 7


# _dibujar_rectangulo(x, y, ancho, alto, color, relleno): dibuja un rectángulo
# cuya esquina superior izquierda está en (x, y). Si relleno es True se dibuja
# sólido, si es False solo se dibuja el borde.
def _dibujar_rectangulo(x, y, ancho, alto, color, relleno=True):
    # Si el color trae 3 valores (sin alfa) se usa glColor3f
    if len(color) == 3:
        glColor3f(*color)
    # Si trae 4 valores (con alfa) se usa glColor4f
    else:
        glColor4f(*color)
    # GL_QUADS dibuja un cuadrilátero relleno, GL_LINE_LOOP dibuja solo su contorno
    glBegin(GL_QUADS if relleno else GL_LINE_LOOP)
    # Las cuatro esquinas, en orden: arriba-izquierda, arriba-derecha, abajo-derecha y abajo-izquierda
    glVertex2f(x, y)
    glVertex2f(x + ancho, y)
    glVertex2f(x + ancho, y + alto)
    glVertex2f(x, y + alto)
    # Termina el rectángulo
    glEnd()


# _dibujar_texto(x, y, texto, escala, color): dibuja el texto empezando en
# (x, y) (esquina superior izquierda) con la fuente de píxeles 5x7. Los
# caracteres que no estén en la fuente se dibujan como espacio. 'escala' es
# cuántos píxeles de pantalla mide cada píxel de la fuente.
def _dibujar_texto(x, y, texto, escala=2, color=COLOR_TEXTO):
    # Pone el color del texto
    glColor3f(*color)
    # Posición horizontal donde va el siguiente carácter
    cursor_x = x
    # Recorre cada carácter del texto (en mayúsculas, porque la fuente solo tiene mayúsculas)
    for caracter in texto.upper():
        # Busca sus filas en la fuente. Si no existe, usa las del espacio.
        filas = _FUENTE.get(caracter, _FUENTE[" "])
        # Recorre las 7 filas (enumerate da el número de fila y su texto)
        for fila_idx, fila in enumerate(filas):
            # Recorre las 5 columnas de esa fila
            for col_idx, bit in enumerate(fila):
                # Solo se dibuja donde hay un "1"
                if bit == "1":
                    # Posición en pantalla de este píxel de la fuente
                    px = cursor_x + col_idx * escala
                    py = y + fila_idx * escala
                    # Dibuja un cuadrito de tamaño 'escala' con sus cuatro esquinas
                    glBegin(GL_QUADS)
                    glVertex2f(px, py)
                    glVertex2f(px + escala, py)
                    glVertex2f(px + escala, py + escala)
                    glVertex2f(px, py + escala)
                    glEnd()
        # Mueve el cursor a la derecha para el siguiente carácter (el ancho del carácter + 1 de separación)
        cursor_x += (_ANCHO_GLIFO + 1) * escala


# _ancho_texto(texto, escala): regresa cuántos píxeles de ancho ocupa el texto
# con esa escala. Se usa para centrar el texto del botón.
def _ancho_texto(texto, escala=2):
    # Cantidad de caracteres por lo que mide cada uno (con su separación)
    return len(texto) * (_ANCHO_GLIFO + 1) * escala


# _punto_dentro_de_rect(px, py, rect): dice si el punto (px, py) está dentro de
# un rectángulo. rect es (x, y, ancho, alto).
def _punto_dentro_de_rect(px, py, rect):
    # Separa los cuatro datos del rectángulo
    x, y, ancho, alto = rect
    # True solo si el punto está entre los bordes izquierdo/derecho y arriba/abajo
    return x <= px <= x + ancho and y <= py <= y + alto


# _formatear_numero(valor): muestra los enteros sin decimales (ej. "30") y los
# demás con 2 decimales (ej. "-15.50"), para que no se vea "30.00" de más
def _formatear_numero(valor):
    # Si el número es igual a su parte entera, no tiene decimales
    if valor == int(valor):
        # Lo muestra como entero
        return str(int(valor))
    # Si tiene decimales, los muestra con 2 dígitos
    return f"{valor:.2f}"


# Clase de una caja de texto donde se escribe un solo número. Se usa para FPS,
# CORRECCION X y CORRECCION Y.
class _CampoNumerico:
    # Constructor: recibe el valor con el que empieza el campo
    def __init__(self, valorInicial):
        # Valor numérico actual del campo
        self.valor = float(valorInicial)
        # Texto que se está escribiendo. None significa que el campo no se está editando.
        self.textoEditando = None
        # Rectángulo (x, y, ancho, alto) que ocupa el campo en pantalla. Se
        # actualiza en cada frame cuando se dibuja.
        self.rect = (0, 0, 0, 0)

    # enfocar(): el usuario hizo clic en el campo y empieza a editarlo
    def enfocar(self):
        # El texto a editar empieza siendo el valor actual
        self.textoEditando = _formatear_numero(self.valor)

    # confirmar(): intenta convertir lo escrito a número. Si no es un número
    # válido, se descarta el cambio (queda el valor anterior) y se avisa por
    # mensaje.py.
    def confirmar(self):
        # Solo si se estaba editando y el texto no está vacío ni es solo "-" o "."
        if self.textoEditando is not None and self.textoEditando not in ("", "-", "."):
            # Intenta convertir el texto a número
            try:
                self.valor = float(self.textoEditando)
            # Si no se puede (por ejemplo "1.2.3"), avisa y deja el valor anterior
            except ValueError:
                mensaje.advertencia(f"'{self.textoEditando}' no es un numero valido, se descarta.")
        # Termina la edición
        self.textoEditando = None

    # texto_mostrado(): regresa el texto que se debe ver en la caja
    def texto_mostrado(self):
        # Si se está editando, muestra lo que se va escribiendo; si no, el valor ya formateado
        return self.textoEditando if self.textoEditando is not None else _formatear_numero(self.valor)


# Clase del panel completo: botón, campos, dibujo y lectura de mouse/teclado
class Interfaz:
    # Constructor: recibe la ventana de glfw, una función que da el tamaño de la
    # ventana y los valores iniciales de FPS y de las correcciones.
    def __init__(self, ventanaGLFW, obtenerTamanoVentana,
                 fpsInicial=1.0, correccionXInicial=0.0, correccionYInicial=0.0):
        # Guarda la ventana para poder leer mouse y teclado
        self._ventana = ventanaGLFW
        # Guarda la función que da el tamaño actual de la ventana
        self._obtenerTamanoVentana = obtenerTamanoVentana

        # Indica si la animación está en pausa (empieza reproduciéndose)
        self.pausado = False
        # Campo de FPS
        self._campoFPS = _CampoNumerico(fpsInicial)
        # Campo de corrección X
        self._campoCorreccionX = _CampoNumerico(correccionXInicial)
        # Campo de corrección Y
        self._campoCorreccionY = _CampoNumerico(correccionYInicial)
        # Diccionario para encontrar cada campo por su nombre corto
        self._campos = {
            "fps": self._campoFPS,
            "cx": self._campoCorreccionX,
            "cy": self._campoCorreccionY,
        }
        # Nombre del campo que se está editando: None, "fps", "cx" o "cy"
        self._campoEnfocado = None

        # Rectángulo del botón (se actualiza en cada frame al dibujar)
        self._botonRect = (0, 0, 0, 0)
        # Los tres siguientes recuerdan si el mouse, BACKSPACE y ENTER estaban
        # presionados en el frame anterior. Sirven para detectar solo el
        # momento en que se presionan y no repetir la acción mientras se mantienen.
        self._mousePresionadoAntes = False
        self._backspaceAntes = False
        self._enterAntes = False

        # Registra la función que glfw llama cada vez que se teclea un carácter
        glfw.set_char_callback(ventanaGLFW, self._callback_char)

        # Avisa por consola que la interfaz quedó lista
        mensaje.info("Interfaz inicializada (dibujada a mano, sin dependencias externas).")

    # --- Getters: funciones que main.py y windows.py llaman en cada frame ---

    # Regresa True si la animación está en pausa
    def estaPausado(self):
        return self.pausado

    # Regresa los FPS que tiene el campo de FPS
    def obtenerFPS(self):
        return self._campoFPS.valor

    # Regresa la corrección X que tiene el campo
    def obtenerCorreccionX(self):
        return self._campoCorreccionX.valor

    # Regresa la corrección Y que tiene el campo
    def obtenerCorreccionY(self):
        return self._campoCorreccionY.valor

    # --- Entrada de texto (callback de caracteres de glfw) ---

    # _callback_char(ventana, codepoint): glfw la llama sola cada vez que el
    # usuario escribe un carácter. codepoint es el número del carácter.
    def _callback_char(self, ventana, codepoint):
        # Si ningún campo está siendo editado, se ignora lo que se teclee
        if self._campoEnfocado is None:
            return
        # Convierte el número del carácter a texto
        caracter = chr(codepoint)
        # Solo se aceptan dígitos, punto y guion
        if caracter in "0123456789.-":
            # Busca el campo que se está editando
            campo = self._campos[self._campoEnfocado]
            # Agrega el carácter al final de lo escrito
            campo.textoEditando += caracter

    # --- Lógica de mouse y teclado (windows.ejecutar la llama en cada vuelta) ---

    # procesarEventos(): revisa por polling el clic del mouse, BACKSPACE y ENTER.
    # Se llama una vez por frame, después de glfw.poll_events().
    def procesarEventos(self):
        # Posición actual del mouse en la ventana
        mouse_x, mouse_y = glfw.get_cursor_pos(self._ventana)
        # True si el botón izquierdo del mouse está presionado ahora
        mouse_presionado = glfw.get_mouse_button(self._ventana, glfw.MOUSE_BUTTON_LEFT) == glfw.PRESS
        # Es un clic nuevo solo si ahora está presionado y en el frame anterior no
        click_este_frame = mouse_presionado and not self._mousePresionadoAntes
        # Guarda el estado actual para comparar en el siguiente frame
        self._mousePresionadoAntes = mouse_presionado

        # Solo se hace algo si hubo un clic nuevo
        if click_este_frame:
            # Si el clic fue sobre el botón, cambia entre pausa y play
            if _punto_dentro_de_rect(mouse_x, mouse_y, self._botonRect):
                # not invierte el valor: True pasa a False y False a True
                self.pausado = not self.pausado
                # Quita el foco de cualquier campo (y confirma lo que se estaba escribiendo)
                self._enfocar_campo(None)
            # Si no fue en el botón, se revisa si fue en algún campo
            else:
                # Empieza asumiendo que el clic no cayó en ningún campo
                clic_en_algun_campo = False
                # Revisa los campos uno por uno
                for nombre, campo in self._campos.items():
                    # Si el clic cayó dentro de este campo
                    if _punto_dentro_de_rect(mouse_x, mouse_y, campo.rect):
                        # Le da el foco a este campo
                        self._enfocar_campo(nombre)
                        # Anota que sí cayó en un campo
                        clic_en_algun_campo = True
                        # Ya no hace falta revisar los demás
                        break
                # Si el clic no cayó en ningún campo, se quita el foco
                if not clic_en_algun_campo:
                    # Clic afuera: confirma lo escrito y quita el foco
                    self._enfocar_campo(None)

        # Las teclas solo importan si hay un campo siendo editado
        if self._campoEnfocado is not None:
            # True si BACKSPACE está presionado ahora
            backspace_presionado = glfw.get_key(self._ventana, glfw.KEY_BACKSPACE) == glfw.PRESS
            # Solo actúa en el momento en que se presiona (no mientras se mantiene)
            if backspace_presionado and not self._backspaceAntes:
                # Busca el campo que se está editando
                campo = self._campos[self._campoEnfocado]
                # Borra el último carácter escrito
                campo.textoEditando = campo.textoEditando[:-1]
            # Guarda el estado para el siguiente frame
            self._backspaceAntes = backspace_presionado

            # True si se presiona ENTER o el ENTER del teclado numérico
            enter_presionado = (
                glfw.get_key(self._ventana, glfw.KEY_ENTER) == glfw.PRESS
                or glfw.get_key(self._ventana, glfw.KEY_KP_ENTER) == glfw.PRESS
            )
            # Solo actúa en el momento en que se presiona
            if enter_presionado and not self._enterAntes:
                # Confirma lo escrito y quita el foco
                self._enfocar_campo(None)
            # Guarda el estado para el siguiente frame
            self._enterAntes = enter_presionado

        # Los FPS se limitan al rango permitido en cuanto cambian:
        # min() evita que pase del máximo y max() evita que baje del mínimo.
        self._campoFPS.valor = max(FPS_MINIMO, min(FPS_MAXIMO, self._campoFPS.valor))

    # _enfocar_campo(nombre): cambia el campo que se está editando. Antes
    # confirma (convierte a número) el que se estaba editando, si había uno.
    # nombre puede ser "fps", "cx", "cy" o None (ninguno).
    def _enfocar_campo(self, nombre):
        # Si había un campo en edición, se confirma lo que se escribió
        if self._campoEnfocado is not None:
            self._campos[self._campoEnfocado].confirmar()
        # Guarda cuál es el nuevo campo enfocado
        self._campoEnfocado = nombre
        # Si es un campo (no None), empieza su edición
        if nombre is not None:
            self._campos[nombre].enfocar()

    # --- Dibujo del panel (windows.ejecutar lo llama en cada vuelta) ---

    # dibujar(): dibuja el panel completo. Se llama una vez por frame, DESPUÉS
    # de dibujar la escena, para que quede encima.
    def dibujar(self):
        # Tamaño actual de la ventana
        ancho_ventana, alto_ventana = self._obtenerTamanoVentana()
        # Posición X donde empieza el panel: pegado al borde derecho (nunca menor a 0)
        panel_x = max(0, ancho_ventana - ANCHO_PANEL)

        # Dibuja el fondo del panel, de arriba a abajo de la ventana
        _dibujar_rectangulo(panel_x, 0, ANCHO_PANEL, alto_ventana, COLOR_FONDO_PANEL)

        # X donde empieza el contenido (con margen desde el borde del panel)
        x = panel_x + MARGEN
        # Ancho disponible para el contenido (el panel menos los márgenes de los dos lados)
        ancho_util = ANCHO_PANEL - 2 * MARGEN
        # Y donde va el siguiente elemento. Empieza arriba, con margen. Va bajando conforme se dibuja.
        y = MARGEN

        # Título del panel
        _dibujar_texto(x, y, "CONTROLES", escala=2)
        # Baja la posición para dejar espacio debajo del título
        y += ALTO_ETIQUETA + ESPACIADO * 2

        # --- Botón Play/Pause ---
        # Guarda el rectángulo del botón para detectar clics en procesarEventos()
        self._botonRect = (x, y, ancho_util, ALTO_BOTON)
        # Posición del mouse, para saber si está encima del botón
        mouse_x, mouse_y = glfw.get_cursor_pos(self._ventana)
        # True si el mouse está sobre el botón
        con_hover = _punto_dentro_de_rect(mouse_x, mouse_y, self._botonRect)
        # Dibuja el botón, con el color claro si el mouse está encima
        _dibujar_rectangulo(x, y, ancho_util, ALTO_BOTON,
                             COLOR_BOTON_HOVER if con_hover else COLOR_BOTON)
        # El botón dice PAUSE mientras se reproduce y PLAY cuando está en pausa
        etiqueta_boton = "PAUSE" if not self.pausado else "PLAY"
        # X para centrar el texto horizontalmente dentro del botón
        texto_x = x + (ancho_util - _ancho_texto(etiqueta_boton, escala=2)) / 2
        # Y para centrar el texto verticalmente dentro del botón
        texto_y = y + (ALTO_BOTON - _ALTO_GLIFO * 2) / 2
        # Dibuja el texto del botón
        _dibujar_texto(texto_x, texto_y, etiqueta_boton, escala=2)
        # Baja la posición para dejar espacio debajo del botón
        y += ALTO_BOTON + ESPACIADO * 2

        # --- Campos numéricos ---
        # Cada llamada dibuja un campo y regresa la Y donde va el siguiente
        y = self._dibujar_campo(x, y, ancho_util, "FPS", self._campoFPS, "fps")
        y = self._dibujar_campo(x, y, ancho_util, "CORRECCION X", self._campoCorreccionX, "cx")
        y = self._dibujar_campo(x, y, ancho_util, "CORRECCION Y", self._campoCorreccionY, "cy")

    # _dibujar_campo(x, y, ancho, etiqueta, campo, nombre): dibuja un campo
    # numérico con su etiqueta encima. Regresa la Y donde debe ir el siguiente
    # elemento.
    def _dibujar_campo(self, x, y, ancho, etiqueta, campo, nombre):
        # Dibuja la etiqueta (texto pequeño) encima de la caja
        _dibujar_texto(x, y, etiqueta, escala=1)
        # Baja para dejar el espacio de la etiqueta
        y += ALTO_ETIQUETA

        # Guarda el rectángulo de la caja para detectar clics en procesarEventos()
        campo.rect = (x, y, ancho, ALTO_CAJA)
        # True si este campo es el que se está editando
        enfocado = self._campoEnfocado == nombre
        # Dibuja la caja, con otro color si se está editando
        _dibujar_rectangulo(x, y, ancho, ALTO_CAJA,
                             COLOR_CAJA_ENFOCADA if enfocado else COLOR_CAJA)
        # Si se está editando, le dibuja además un borde de color
        if enfocado:
            _dibujar_rectangulo(x, y, ancho, ALTO_CAJA, COLOR_BORDE_ENFOCADO, relleno=False)

        # Texto que se debe ver en la caja (lo que se escribe o el valor actual)
        texto = campo.texto_mostrado()
        # Lo dibuja dentro de la caja: 6 píxeles desde la izquierda y centrado verticalmente
        _dibujar_texto(x + 6, y + (ALTO_CAJA - _ALTO_GLIFO * 2) / 2, texto, escala=2)

        # Regresa la Y donde termina este campo más el espacio para el siguiente
        return y + ALTO_CAJA + ESPACIADO * 2

    # cerrar(): no hay recursos externos que liberar (no se usan librerías de
    # terceros). Se deja por orden, para que sea igual que el resto del proyecto.
    def cerrar(self):
        # pass significa "no hacer nada"
        pass
