# ProyectoReze v3 – Dibujo de Capas

Proyecto de clase hecho en Python 3. Lee "capas" de dibujo desde archivos
Excel y las dibuja en una ventana con OpenGL (usando `glfw` + `PyOpenGL`).
Incluye una animación por fotogramas y un panel de control dibujado en la
propia ventana.

## Qué hace

- Lee la imagen estática desde `capas.xlsx`.
- Lee una animación desde `fotogramas.xlsx` (cada hoja es un fotograma) y la
  reproduce en loop como fondo.
- Dibuja la imagen estática encima de la animación.
- Muestra un panel a la derecha para pausar la animación, cambiar los FPS y
  mover el dibujo en pantalla, todo en vivo.
- Si editas y guardas un Excel mientras el programa corre, lo vuelve a leer
  solo y los cambios se ven sin reiniciar.

## Requisitos

- Python 3
- Estas librerías:

```bash
pip install pandas openpyxl glfw PyOpenGL
```

> **Nota sobre Linux/Wayland:** este proyecto usa una interfaz dibujada a mano
> con OpenGL puro (sin `pyimgui` ni `imgui-bundle`), porque ambas librerías
> dieron problemas de compatibilidad en entornos Wayland sin X11. No hace falta
> instalar nada más para la interfaz.

## Cómo correr

Desde la carpeta del proyecto (para que encuentre los archivos `.xlsx`):

```bash
python main.py
```

Se abre una ventana con:

- El fondo animado de `fotogramas.xlsx` (un fotograma nuevo por cada refresco
  de pantalla, en loop).
- La imagen estática de `capas.xlsx` dibujada encima.
- Un panel de control fijo en el borde derecho.
- `ESC` cierra la ventana.

### Panel de control

| Control | Qué hace |
|---|---|
| **PAUSE / PLAY** (botón) | Pausa o reanuda solo la animación. Lo demás se sigue redibujando, así que la corrección X/Y sigue funcionando en pausa. |
| **FPS** | Cambia la velocidad de refresco en vivo. Se limita entre 0.1 y 240. |
| **CORRECCION X** | Mueve todo el dibujo en horizontal, sin recalcular el centrado automático. |
| **CORRECCION Y** | Mueve todo el dibujo en vertical, sin recalcular el centrado automático. |

Cómo se usan los campos numéricos:

- Haz clic en un campo para editarlo. Solo acepta dígitos, `.` y `-`.
- `BACKSPACE` borra el último carácter.
- `ENTER` (o hacer clic fuera del campo) confirma el valor. Si lo escrito no
  es un número válido, se descarta y queda el valor anterior.

### Valores que se pueden cambiar en `main.py`

| Constante | Para qué sirve | Valor actual |
|---|---|---|
| `ANCHO_VENTANA` / `ALTO_VENTANA` | Tamaño de la ventana en píxeles | 1500 / 1000 |
| `TITULO_VENTANA` | Título de la ventana | `"Dibujo de Capas"` |
| `COLOR_FONDO` | Color de fondo | `"#FFFFFF"` |
| `FPS_INICIAL` | FPS con los que arranca la animación | 15 |
| `ARCHIVO_CAPAS` | Excel de la imagen estática | `"capas.xlsx"` |
| `ARCHIVO_FOTOGRAMAS` | Excel de la animación | `"fotogramas.xlsx"` |
| `CORRECCION_X_INICIAL` / `CORRECCION_Y_INICIAL` | Corrección con la que arranca el panel | 0.0 / -200.0 |

## Estructura del proyecto

| Archivo | Responsabilidad |
|---|---|
| `main.py` | Punto de entrada. Solo crea las piezas y las conecta. |
| `windows.py` | Ventana, contexto OpenGL, loop principal y control de FPS. |
| `lectorcapas.py` | Lee `capas.xlsx` / `fotogramas.xlsx` (o cualquier Excel con el mismo formato). Guarda lo leído en memoria y lo recarga solo si el archivo cambia en disco. |
| `color.py` | Convierte colores escritos de muchas formas (hex, `rgb(...)`, nombres, etc.) a un formato que entiende OpenGL. Tolera errores de escritura. |
| `mensaje.py` | Único responsable de imprimir en consola (info, advertencias y errores). |
| `dibujar.py` | Clase `Dibujar`: toda la lógica de dibujo (relleno, borde, conversión de coordenadas y corrección de posición). |
| `animar.py` | Clase `Animar`: reproduce `fotogramas.xlsx` como animación en loop, reutilizando `Dibujar`. |
| `interfaz.py` | Panel de control (Play/Pause, FPS, Corrección X/Y) dibujado a mano con OpenGL puro, con su propia fuente de píxeles. |
| `capas.xlsx` | Datos de la imagen estática (capas fijas). |
| `fotogramas.xlsx` | Datos de la animación (cada hoja es un fotograma). |
| `Reze.jpg` | Imagen incluida en el proyecto. El código no la carga. |

## Cómo funciona

1. `main.py` crea el `Dibujar` y el `Animar`.
2. Calcula **un solo offset** con las coordenadas de `capas.xlsx` y de todos los
   fotogramas juntos. Así todo comparte el mismo sistema de coordenadas y la
   imagen estática no se desalinea del fondo animado.
3. `windows.py` abre la ventana y `main.py` crea el panel (`Interfaz`).
4. `windows.py` corre el loop principal. En cada vuelta:
   1. Procesa los eventos del panel (mouse y teclado).
   2. Limpia la pantalla.
   3. Dibuja el fotograma que toca de la animación (si está en pausa, repite
      el mismo).
   4. Dibuja encima todas las capas de `capas.xlsx`.
   5. Dibuja el panel encima de todo.
   6. Espera lo necesario para respetar los FPS que tenga el panel en ese momento.

### Sistema de coordenadas

- La ventana usa **píxeles absolutos**: 1 unidad = 1 píxel. El origen `(0, 0)`
  está arriba a la izquierda y Y crece hacia **abajo**.
- Los datos del Excel usan Y hacia **arriba** (cartesiano). Por eso `dibujar.py`
  invierte el signo de Y y luego suma el offset y la corrección.
- La corrección X/Y del panel se suma al final, encima del offset automático.

## Formato del Excel (`capas.xlsx` y `fotogramas.xlsx`)

Cada **hoja** es un `grupoCapa` (o un `fotograma`, según el archivo). Dentro de
una hoja, los datos van en bloques apilados hacia abajo. Las etiquetas van en la
columna A y sus datos en la columna B:

```
CAPA     <nombre de la capa>
TIPO     BACKGROUND | LINE
COLOR    <color, en cualquier formato tolerado por color.py>
GROSOR   <numero>
X        Y
<x1>     <y1>
<x2>     <y2>
...
CAPA     <siguiente capa>
...
```

- `TIPO=BACKGROUND` → la capa se dibuja como **relleno** (polígono sólido).
- `TIPO=LINE` → la capa se dibuja como **borde** (línea abierta, no se une el
  último punto con el primero).
- El orden de dibujo es el orden **lineal** en que aparecen las capas y las
  hojas en el archivo (no alfabético).
- Si falta `TIPO`, `COLOR` o `GROSOR`, se usan valores por defecto
  (`BACKGROUND`, negro y grosor 10) y se avisa por consola.
- Lo que esté antes de la primera fila `CAPA` se ignora.
- Los nombres de capa se pueden repetir dentro de una misma hoja. Por dentro se
  identifican con un índice (que no aparece en el Excel).
- No hace falta conocer de antemano los nombres de las hojas, se detectan solos.

### Formatos de color aceptados

No importan mayúsculas ni espacios.

| Formato | Ejemplo |
|---|---|
| RGB decimal (0-255) | `255,0,0` o `(255, 0, 0)` |
| RGBA decimal | `255,0,0,128` |
| Estilo CSS | `rgb(255,0,0)` o `rgba(255,0,0,128)` |
| Hexadecimal | `#FF0000`, `FF0000`, `#F00`, `#FF000080` |
| Nombre | `rojo`, `red`, `negro`, `blanco`, `azul`, `verde`, `amarillo`, `gris`, `naranja`, `morado`, `transparente` (y sus nombres en inglés) |

Si el color no se puede entender, se avisa por consola y se usa negro.

## Comentarios en el código

Todo el código `.py` está comentado en español, con comentarios `#`: un
encabezado en cada archivo, otro en cada función o clase, y una explicación por
línea. Las partes que se repiten se explican una sola vez al inicio.

---

## Tutorial ssh

```bash
# 1. Generar una nueva clave SSH
ssh-keygen -t ed25519 -C "tu_correo@example.com"

# 2. Iniciar el agente SSH
eval "$(ssh-agent -s)"

# 3. Agregar la clave privada al agente
ssh-add ~/.ssh/id_ed25519

# 4. Mostrar la clave pública (para copiarla y pegarla en GitHub)
cat ~/.ssh/id_ed25519.pub

# 5. Probar la conexión con GitHub
ssh -T git@github.com
```
