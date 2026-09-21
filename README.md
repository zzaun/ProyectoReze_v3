# ProyectoReze v3

Proyecto en Python que lee un archivo de Excel (`capas.xlsx`) y dibuja sus capas gráficamente utilizando **OpenGL y GLFW**.

## Características

* Detecta automáticamente las hojas de `capas.xlsx`.
* Cada hoja representa un grupo de capas.
* Lee capas, colores, grosor y coordenadas.
* Soporta dos tipos de dibujo:

  * `BACKGROUND`: polígono relleno.
  * `LINE`: línea abierta.
* Calcula automáticamente un offset para mostrar el dibujo.
* Soporta diferentes formatos de color.

## Estructura

```text
ProyectoReze v3/
├── main.py
├── mensaje.py
├── color.py
├── lectorcapas.py
├── windows.py
├── dibujar.py
├── capas.xlsx
└── README.md
```

## Requisitos

Es necesario tener instalado **Python 3**.

### Descargar e instalar las librerías

Instala las librerías necesarias con el siguiente comando:

```bash
pip install pandas openpyxl PyOpenGL glfw
```

Las librerías utilizadas son:

* **Pandas:** lectura del archivo Excel.
* **OpenPyXL:** soporte para archivos `.xlsx`.
* **PyOpenGL:** funciones gráficas de OpenGL.
* **GLFW:** creación y administración de la ventana.

## Ejecutar

Desde la carpeta del proyecto ejecuta:

```bash
python3 main.py
```

Presiona **ESC** o cierra la ventana para terminar el programa.

## Formato de `capas.xlsx`

Cada hoja puede contener varias capas:

```text
CAPA      Nombre
TIPO      BACKGROUND o LINE
COLOR     #FF0000
GROSOR    5

X         Y
10        20
30        40
50        60
```

## Módulos

* **main.py:** inicia el programa.
* **lectorcapas.py:** lee `capas.xlsx`.
* **dibujar.py:** dibuja las capas.
* **windows.py:** administra la ventana y OpenGL.
* **color.py:** convierte colores a formato OpenGL.
* **mensaje.py:** muestra mensajes de información, advertencias y errores.
