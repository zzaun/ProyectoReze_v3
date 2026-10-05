# Dibujo de Capas

Programa en Python 3 que lee "capas" de dibujo desde archivos Excel y las renderiza en una ventana con OpenGL (via `glfw` + `PyOpenGL`),
incluyendo animación por fotogramas, un panel de control en pantalla, y audio (música de fondo en loop + efectos sintéticos por fotograma).

## Requisitos

```bash
pip install pandas openpyxl glfw PyOpenGL pygame numpy
```

> **Nota sobre Linux/Wayland:** la interfaz (`interfaz.py`) está dibujada a mano con OpenGL puro (sin `pyimgui` ni `imgui-bundle`),
> porque ambas librerías presentaron problemas de compatibilidad binaria en entornos Wayland sin X11. No hace falta ninguna
> dependencia adicional para la interfaz.
>
> `numpy` casi seguro ya está instalada porque `pandas` la necesita, pero no está de más pedirla explícita (la usa `audio.py` para
> generar los efectos de sonido sintéticos).

## Estructura del proyecto

| Archivo | Responsabilidad |
|---|---|
| `main.py` | Punto de entrada. Solo inicializa y conecta todas las piezas. |
| `windows.py` | Ventana, contexto OpenGL, loop principal, control de FPS. |
| `lectorcapas.py` | Lee `capas.xlsx` / `fotogramas.xlsx` (o cualquier excel con el mismo formato), con cache y recarga automática si el archivo cambia en disco. |
| `color.py` | Convierte colores en formatos muy variados (hex, `rgb(...)`, nombres, etc.) a un formato usable por OpenGL, con alta tolerancia a errores. |
| `mensaje.py` | Único responsable de imprimir información relevante en consola (info, advertencias, errores). |
| `dibujar.py` | Clase `Dibujar`: toda la lógica de dibujo (relleno, borde, transformación de coordenadas, corrección de posición). |
| `animar.py` | Clase `Animar`: reproduce `fotogramas.xlsx` como una animación en loop, reutilizando `dibujar.py`. |
| `interfaz.py` | Panel de control minimalista (Play/Pause, FPS, Corrección X/Y), dibujado a mano con OpenGL puro. |
| `audio.py` | Clase `Audio`: música de fondo en loop infinito, y efectos de sonido generados por código (sin archivos), disparados en fotogramas específicos. |
| `capas.xlsx` | Datos de la imagen estática (capas fijas). |
| `fotogramas.xlsx` | Datos de la animación (cada hoja = un fotograma). |

## Formato del Excel (`capas.xlsx` y `fotogramas.xlsx`)

Cada **hoja** es un `grupoCapa` (o un `fotograma`, según el archivo).
Dentro de una hoja, los datos van en bloques apilados verticalmente:

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
- `TIPO=LINE` → la capa se dibuja como **borde** (polilínea abierta, no se cierra).
- El orden de dibujo es el orden **lineal** en que aparecen las capas/hojas en el archivo (no alfabético).
- Si falta `TIPO`, `COLOR` o `GROSOR`, se usan valores por defecto (`BACKGROUND`, negro, el grosor máximo), y se avisa por consola.
- Los nombres de capa se pueden repetir dentro de una misma hoja; internamente se identifican por un índice (no visible en el excel).

## Audio

- **Música de fondo**: se reproduce en loop infinito desde que arranca el programa. El archivo se indica en `main.py` con la constante `ARCHIVO_MUSICA` (por defecto `"musica.mp3"`). Si ese archivo no existe, se muestra un error en consola y el programa sigue funcionando sin música (no se detiene).
- **Efectos por fotograma**: `audio.py` genera dos efectos de sonido directamente por código (sin archivos externos), usando `numpy`: `"click"` y `"encendido"` (varios clicks cortos simulando un mechero). Suenan estilo retro/sintético, no son grabaciones.
- La asociación entre fotograma y efecto se define en `main.py`, en el diccionario `EFECTOS_POR_FOTOGRAMA`, usando el **índice interno** del fotograma (empieza en 0, se reinicia solo cada vez que la animación vuelve a empezar):

```python
EFECTOS_POR_FOTOGRAMA = {
    2: "click",
    5: "encendido",
}
```

- El botón **Pause** del panel de interfaz también pausa la música de fondo (se reanuda junto con **Play**).

## Cómo correr

```bash
python main.py
```

Esto abre una ventana con:

- El fondo animado de `fotogramas.xlsx` (un fotograma nuevo por refresco de pantalla, en loop), con sus efectos de sonido asociados.
- La imagen estática de `capas.xlsx` dibujada encima.
- Música de fondo en loop.
- Un panel de control fijo en el borde derecho con:
  - **Play / Pause**: pausa la animación y la música (lo estático se sigue actualizando).
  - **FPS**: cambia la tasa de refresco en vivo.
  - **Corrección X / Corrección Y**: mueve todo el dibujo en pantalla en vivo, sin recalcular el centrado automático.
- `ESC` cierra la ventana.

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