# main.py
# Este es el punto de entrada del programa. Su unico trabajo es
# inicializar todas las piezas (ventana, dibujo, animacion, interfaz,
# audio) y conectarlas entre si. No tiene logica propia de dibujo ni
# de audio: eso vive en cada archivo correspondiente.
# En cada refresco de pantalla se hace, en este orden: 1) se aplica la
# correccion de posicion vigente, 2) se revisa si hay que pausar o
# reproducir un efecto de sonido, 3) se dibuja el fondo animado, 4) se
# dibuja encima la imagen estatica, 5) se dibuja el panel de interfaz.
# No hace falta saber de antemano los nombres de las hojas de ningun
# archivo excel: se detectan solos. Al arrancar, se imprime en consola
# la lista de fotogramas con su indice, para saber que numero poner en
# EFECTOS_POR_FOTOGRAMA sin tener que contar las hojas a mano.

# Importamos windows.py, que maneja la ventana y el loop principal.
import windows
# Importamos la clase Dibujar, que sabe dibujar capas en pantalla.
from dibujar import Dibujar
# Importamos la clase Animar, que recorre los fotogramas de la animacion.
from animar import Animar
# Importamos la clase Interfaz, que dibuja el panel de control.
from interfaz import Interfaz
# Importamos la clase Audio, que maneja musica y efectos de sonido.
from audio import Audio
# Importamos la clase Ruido, que dibuja la textura de ruido tipo papel.
from ruido import Ruido
# Importamos mensaje.py para imprimir la lista de fotogramas al arrancar.
import mensaje

# Ancho de la ventana, en pixeles.
ANCHO_VENTANA = 1500
# Alto de la ventana, en pixeles.
ALTO_VENTANA = 1000
# Texto que aparece en la barra de titulo de la ventana.
TITULO_VENTANA = "Dibujo de Capas"
# Color de fondo de la ventana (blanco).
COLOR_FONDO = "#FFFFFF"
# FPS con el que arranca el programa (se puede cambiar despues desde la interfaz).
FPS_INICIAL = 12.0

# Nombre del archivo excel con la imagen estatica.
ARCHIVO_CAPAS = "capas.xlsx"
# Nombre del archivo excel con los fotogramas de la animacion.
ARCHIVO_FOTOGRAMAS = "fotogramas.xlsx"
# Nombre del archivo de musica de fondo. Si no existe, audio.py avisa
# el error en consola y el programa sigue funcionando sin musica.
ARCHIVO_MUSICA = "ChainsawMan_TheMovie_RezeArc.mp3"

# Valores iniciales del ajuste manual de posicion (despues se pueden
# cambiar en vivo desde el panel de interfaz).
CORRECCION_X_INICIAL = -50.0
CORRECCION_Y_INICIAL = -70.0
# Volumen inicial de musica y efectos (0.0 = silencio, 1.0 = maximo).
VOLUMEN_INICIAL = 0.25

# Aqui se decide que efecto de sonido suena en cada fotograma.
# La llave es el indice INTERNO del fotograma (empieza en 0, y se
# reinicia solo cada vez que la animacion vuelve a empezar). El valor
# es el nombre del efecto, tal como esta guardado en audio.py ("click",
# "encendido" o "explosion"). Para saber que numero de indice le toca a
# cada fotograma, revisa la lista que se imprime en consola al arrancar
# el programa (dice "Fotograma N: 'NombreDeLaHoja'" por cada uno).
# Ejemplo: en el fotograma numero 2 suena un click; en el numero 5
# suena el encendido del mechero; en el numero 6 suena la explosion.
EFECTOS_POR_FOTOGRAMA = {
    2: "click",
    3: "encendido",
    4: "explosion",
}


# Funcion principal del programa. Arma todas las piezas y arranca el loop.
def main():
    # Creamos el objeto que sabe dibujar capas.
    dibujador = Dibujar()
    # Creamos el objeto que maneja la animacion, usando el mismo dibujador.
    animador = Animar(dibujador, archivo=ARCHIVO_FOTOGRAMAS)

    # Pedimos la lista de fotogramas (hojas de fotogramas.xlsx) y la
    # imprimimos con su indice, para saber que numero usar en
    # EFECTOS_POR_FOTOGRAMA sin tener que contar las hojas a mano.
    lista_fotogramas = animador.obtenerListaFotogramas()
    # Recorremos la lista junto con su posicion (empezando en 0).
    for indice, nombre in enumerate(lista_fotogramas):
        mensaje.info(f"Fotograma {indice}: '{nombre}'")

    # Juntamos las coordenadas de la imagen estatica...
    coordenadas_estaticas = dibujador.obtenerTodasLasCoordenadas(archivo=ARCHIVO_CAPAS)
    # ...y las coordenadas de todos los fotogramas de la animacion...
    coordenadas_animadas = animador.obtenerTodasLasCoordenadas()
    # ...en una sola lista, para calcular UN solo offset que sirva para ambos.
    todas_coordenadas = coordenadas_estaticas + coordenadas_animadas
    # Calculamos el offset (con 40 pixeles de margen) para que todo se vea dentro de la ventana.
    dibujador.calcularOffsetDesdeCoordenadas(todas_coordenadas, margen=40)

    # Creamos la ventana. Si falla (por ejemplo, no hay pantalla disponible), se cancela todo.
    if not windows.inicializar(ancho=ANCHO_VENTANA, alto=ALTO_VENTANA,
                                titulo=TITULO_VENTANA, colorFondo=COLOR_FONDO):
        # Si inicializar() regreso False, no seguimos con el resto del programa.
        return

    # Creamos el panel de interfaz, dandole el handle de la ventana ya creada.
    interfaz = Interfaz(
        ventanaGLFW=windows.obtenerVentanaGLFW(),
        obtenerTamanoVentana=windows.obtenerTamano,
        fpsInicial=FPS_INICIAL,
        correccionXInicial=CORRECCION_X_INICIAL,
        correccionYInicial=CORRECCION_Y_INICIAL,
        volumenInicial=VOLUMEN_INICIAL,
    )

    # Creamos el objeto de ruido (textura de papel), usando el tamano
    # real de la ventana para esparcir los puntitos en toda esa area.
    ancho_real, alto_real = windows.obtenerTamano()
    ruido = Ruido(ancho_real, alto_real)

    # Creamos el objeto de audio (esto ya genera los efectos sinteticos
    # y prepara el mixer, listo para usarse).
    audio = Audio()
    # Dejamos el volumen inicial en el mismo que se le dio a la interfaz.
    audio.establecerVolumen(VOLUMEN_INICIAL)
    # Arrancamos la musica de fondo en loop infinito, desde ya.
    audio.reproducirMusicaLoop(ARCHIVO_MUSICA)

    # Guardamos aqui el ultimo fotograma que se mostro, para saber
    # cuando CAMBIA de fotograma (y no repetir un efecto de sonido en
    # cada refresco de pantalla si la animacion esta en pausa).
    indice_anterior_mostrado = None
    # Guardamos aqui si la animacion ya estaba pausada en el frame
    # anterior, para saber cuando el usuario ACABA de darle Play o Pause.
    pausado_anterior = False
    # Guardamos aqui el ultimo volumen aplicado, para solo llamar a
    # establecerVolumen() cuando de verdad cambia (no en cada frame).
    volumen_anterior = VOLUMEN_INICIAL

    # Esta funcion se llama una vez por cada refresco de pantalla, y
    # dibuja todo lo que debe verse en ese frame.
    def dibujarFrame():
        # nonlocal deja usar y modificar las variables de main() aqui adentro.
        nonlocal indice_anterior_mostrado, pausado_anterior, volumen_anterior

        # Revisamos el estado actual del boton Play/Pause.
        pausado_actual = interfaz.estaPausado()
        # Si el estado de pausa CAMBIO desde el frame anterior...
        if pausado_actual != pausado_anterior:
            # ...y ahora esta pausado, pausamos tambien la musica.
            if pausado_actual:
                audio.pausarMusica()
            # ...y si ya no esta pausado, reanudamos la musica.
            else:
                audio.reanudarMusica()
            # Actualizamos el estado guardado, para la siguiente comparacion.
            pausado_anterior = pausado_actual

        # Revisamos el volumen actual del panel de interfaz.
        volumen_actual = interfaz.obtenerVolumen()
        # Si el volumen CAMBIO desde el frame anterior, lo aplicamos.
        if volumen_actual != volumen_anterior:
            audio.establecerVolumen(volumen_actual)
            volumen_anterior = volumen_actual

        # Vemos que fotograma le toca mostrar a la animacion en este frame.
        indice_actual = animador.indiceFotogramaActual
        # Si ese fotograma es distinto al que se mostro la vez pasada
        # (o sea, de verdad avanzamos, no estamos repitiendo por pausa)...
        if indice_actual != indice_anterior_mostrado:
            # ...y ademas ese indice tiene un efecto de sonido asignado...
            if indice_actual in EFECTOS_POR_FOTOGRAMA:
                # ...lo reproducimos.
                audio.reproducirEfecto(EFECTOS_POR_FOTOGRAMA[indice_actual])
        # Guardamos el indice actual, para comparar en el siguiente frame.
        indice_anterior_mostrado = indice_actual

        # Aplicamos la correccion de posicion vigente (puede cambiar en vivo desde la interfaz).
        dibujador.establecerCorreccion(interfaz.obtenerCorreccionX(), interfaz.obtenerCorreccionY())
        # Dibujamos el fondo animado. Si esta pausado, se redibuja el mismo fotograma sin avanzar.
        animador.dibujarFotogramaActual(avanzar=not pausado_actual)
        # Dibujamos encima la imagen estatica (todas las hojas de capas.xlsx).
        dibujador.dibujarTodosLosGrupos(archivo=ARCHIVO_CAPAS)
        # Dibujamos la textura de ruido (papel) encima de todo lo anterior.
        # El panel de interfaz se sigue dibujando despues de esto (via
        # funcionUI en windows.ejecutar), asi que el ruido no lo tapa.
        ruido.dibujar()

    # Arrancamos el loop principal de la ventana, pasandole:
    windows.ejecutar(
        dibujarFrame,                          # que dibujar en cada frame,
        fpsObjetivo=interfaz.obtenerFPS,        # el FPS (leido en vivo desde la interfaz),
        funcionUI=interfaz.dibujar,             # como dibujar el panel encima,
        funcionEventosUI=interfaz.procesarEventos,  # y como procesar clicks/teclado del panel.
    )

    # Cuando el loop termina (se cerro la ventana), liberamos la interfaz.
    interfaz.cerrar()


# Esto hace que main() solo se ejecute si corremos este archivo
# directamente (y no si alguien mas lo importa).
if __name__ == "__main__":
    main()