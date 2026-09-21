# ProyectoReze v3

# Dibujo de Capas

Programa en Python 3 que lee "capas" de dibujo desde archivos Excel y
las renderiza en una ventana con OpenGL (via `glfw` + `PyOpenGL`),
incluyendo animación por fotogramas y un panel de control en pantalla.

## Requisitos

```bash
pip install pandas openpyxl glfw PyOpenGL
```

> **Nota sobre Linux/Wayland:** este proyecto usa una interfaz de
> usuario dibujada a mano con OpenGL puro (sin `pyimgui` ni
> `imgui-bundle`), precisamente porque ambas librerías presentaron
> problemas de compatibilidad binaria en entornos Wayland sin X11.
> No hace falta ninguna dependencia adicional para la interfaz.

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

## Cómo correr

```bash
python main.py
```

Esto abre una ventana con:

- El fondo animado de `fotogramas.xlsx` (un fotograma nuevo por refresco de pantalla, en loop).
- La imagen estática de `capas.xlsx` dibujada encima.
- Un panel de control fijo en el borde derecho con:
  - **Play / Pause**: pausa solo la animación (lo estático se sigue actualizando).
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