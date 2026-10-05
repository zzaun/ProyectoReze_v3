# audio.py
# Este archivo se encarga de todo el sonido del programa.
# Hace dos cosas: reproducir musica de fondo en loop infinito, y
# reproducir efectos cortos generados por codigo (sin archivos de
# audio), para usarse cuando la animacion llega a un fotograma
# especifico.
# Usa pygame solo para el mixer de audio (no se abre ninguna ventana de
# pygame, solo se usa la parte de sonido).
# Los efectos se generan una sola vez al iniciar (con numpy) y se
# guardan en memoria, para que al reproducirlos no haya que calcular
# nada de nuevo (eso evita retrasos al dispararlos).

# Importamos pygame, que es quien realmente reproduce el audio.
import pygame

# Importamos numpy, que usamos para construir las ondas de sonido a mano.
import numpy as np

# Importamos mensaje.py para avisar en consola si algo falla.
import mensaje

# Frecuencia de muestreo del audio (muestras por segundo). 44100 es el
# estandar de calidad de CD, por eso se usa aqui tambien.
FRECUENCIA_MUESTREO = 44100

# Duracion del efecto "click", en segundos.
DURACION_CLICK = 0.03

# Duracion total del efecto "encendido" (varios clicks seguidos), en segundos.
DURACION_ENCENDIDO = 0.3

# Duracion del efecto "explosion", en segundos.
DURACION_EXPLOSION = 0.5


# Genera un arreglo de numeros (una "onda") de ruido blanco con una
# caida rapida de volumen al final, para que suene como un click seco.
# 'duracion' es en segundos. Regresa un arreglo de numeros flotantes
# entre -1 y 1 (todavia no es un sonido reproducible).
def _generarOndaClick(duracion):
    # Calculamos cuantas muestras (numeros) necesitamos para esa duracion.
    numero_muestras = int(FRECUENCIA_MUESTREO * duracion)
    # Generamos ruido blanco: numeros aleatorios entre -1 y 1.
    ruido = np.random.uniform(-1.0, 1.0, numero_muestras)
    # Creamos una "rampa" de tiempo de 0 a 1, para construir la caida de volumen.
    tiempo = np.linspace(0.0, 1.0, numero_muestras)
    # La envolvente hace que el sonido empiece fuerte y baje rapido a
    # casi silencio (como un chasquido), usando una exponencial negativa.
    envolvente = np.exp(-tiempo * 18.0)
    # Multiplicamos el ruido por la envolvente: eso le da la forma de "click".
    onda = ruido * envolvente
    # Aplicamos un filtro muy simple (diferencia entre muestras vecinas)
    # para resaltar el golpe inicial y que suene mas "metalico" y menos
    # como un soplido sordo.
    onda_filtrada = np.diff(onda, prepend=onda[0])
    # Regresamos la onda ya lista, en escala -1 a 1.
    return onda_filtrada / (np.max(np.abs(onda_filtrada)) + 1e-9)


# Genera la onda completa del efecto "encendido tipo mechero": son
# varios clicks cortos seguidos, simulando la ruedita de un mechero,
# con pequenos silencios entre cada uno.
def _generarOndaEncendido():
    # Lista donde vamos a ir pegando cada pedazo (clicks y silencios).
    pedazos = []
    # Generamos 4 "chispazos" seguidos, como la ruedita de un mechero.
    for indice in range(4):
        # Cada chispazo es un click corto (mas corto que el click normal).
        pedazos.append(_generarOndaClick(0.015))
        # Entre cada chispazo metemos un silencio breve (puros ceros).
        silencio = np.zeros(int(FRECUENCIA_MUESTREO * 0.03))
        pedazos.append(silencio)
    # Unimos todos los pedazos en una sola onda larga.
    onda = np.concatenate(pedazos)
    # Si la onda nos quedo mas corta que DURACION_ENCENDIDO, la rellenamos
    # con silencio al final para que siempre dure lo mismo.
    muestras_objetivo = int(FRECUENCIA_MUESTREO * DURACION_ENCENDIDO)
    if len(onda) < muestras_objetivo:
        relleno = np.zeros(muestras_objetivo - len(onda))
        onda = np.concatenate([onda, relleno])
    # Regresamos la onda final.
    return onda


# Genera la onda del efecto "explosion": una mezcla de ruido crudo (el
# "crack" seco del golpe inicial) y un retumbo grave (el mismo ruido,
# pero suavizado para que suene bajo y no agudo), con una caida de
# volumen larga para que se sienta como un boom, no como un click.
def _generarOndaExplosion():
    # Calculamos cuantas muestras necesitamos para la duracion pedida.
    numero_muestras = int(FRECUENCIA_MUESTREO * DURACION_EXPLOSION)
    # Ruido blanco: la base de todo el efecto.
    ruido = np.random.uniform(-1.0, 1.0, numero_muestras)

    # Para el retumbo grave, suavizamos el ruido a mano (un filtro simple
    # de "promedio que se va moviendo"): entre mas chico alpha, mas grave
    # suena, porque los cambios bruscos del ruido se van emparejando.
    alpha = 0.05
    retumbo = np.zeros(numero_muestras)
    valor_anterior = 0.0
    # Recorremos muestra por muestra porque cada una depende de la anterior.
    for indice in range(numero_muestras):
        valor_anterior = alpha * ruido[indice] + (1.0 - alpha) * valor_anterior
        retumbo[indice] = valor_anterior
    # Normalizamos el retumbo para que use todo el rango de -1 a 1.
    retumbo = retumbo / (np.max(np.abs(retumbo)) + 1e-9)

    # Armamos una rampa de tiempo de 0 a 1, para la envolvente de volumen.
    tiempo = np.linspace(0.0, 1.0, numero_muestras)
    # Caida de volumen mas lenta que la del click, para que la explosion dure mas.
    envolvente = np.exp(-tiempo * 4.0)

    # Mezclamos el ruido crudo (el golpe seco inicial) con el retumbo
    # grave (el cuerpo del sonido), y le aplicamos la envolvente encima.
    mezcla = (ruido * 0.5 + retumbo * 0.8) * envolvente
    # Normalizamos el resultado final para que use todo el rango de -1 a 1.
    return mezcla / (np.max(np.abs(mezcla)) + 1e-9)


# Convierte una onda (numeros flotantes entre -1 y 1) en un objeto de
# sonido que pygame puede reproducir.
def _ondaASonidoPygame(onda):
    # pygame espera numeros enteros de 16 bits, no decimales, asi que
    # escalamos la onda al rango completo de un entero de 16 bits.
    onda_entera = np.int16(onda * 32767)
    # El mixer de audio lo configuramos en estereo (2 canales), asi que
    # duplicamos la misma onda en ambos canales (izquierdo y derecho).
    onda_estereo = np.column_stack((onda_entera, onda_entera))
    # Pygame necesita el arreglo "contiguo" en memoria para leerlo bien.
    onda_estereo = np.ascontiguousarray(onda_estereo)
    # Creamos y regresamos el sonido ya listo para reproducirse.
    return pygame.sndarray.make_sound(onda_estereo)


# Clase Audio: agrupa todo el manejo de musica y efectos de sonido.
class Audio:

    # Se ejecuta al crear un objeto Audio. Prepara el mixer de pygame y
    # genera los efectos sinteticos una sola vez.
    def __init__(self):
        # Intentamos iniciar el mixer de audio de pygame.
        try:
            # frequency: calidad del audio. size=-16: enteros de 16 bits con signo.
            # channels=2: estereo. Debe coincidir con como armamos las ondas arriba.
            pygame.mixer.init(frequency=FRECUENCIA_MUESTREO, size=-16, channels=2)
            # Guardamos si se pudo iniciar correctamente, para no tronar despues.
            self._disponible = True
        except Exception as error:
            # Si no hay dispositivo de audio o algo falla, avisamos pero
            # dejamos seguir el programa sin sonido (no debe tronar todo
            # el programa solo porque el audio no funciono).
            mensaje.error(f"No se pudo iniciar el audio: {error}")
            self._disponible = False

        # Diccionario donde guardamos los efectos ya generados, listos
        # para reproducirse sin esperar (nombre del efecto -> sonido).
        self._efectos = {}

        # Si el audio si quedo disponible, generamos los efectos de una vez.
        if self._disponible:
            # Generamos el efecto "click" y lo guardamos.
            self._efectos["click"] = _ondaASonidoPygame(_generarOndaClick(DURACION_CLICK))
            # Generamos el efecto "encendido" y lo guardamos.
            self._efectos["encendido"] = _ondaASonidoPygame(_generarOndaEncendido())
            # Generamos el efecto "explosion" y lo guardamos.
            self._efectos["explosion"] = _ondaASonidoPygame(_generarOndaExplosion())
            # Avisamos en consola que ya quedo listo.
            mensaje.info("Audio inicializado (musica + efectos sinteticos: click, encendido, explosion).")

    # Reproduce un archivo de musica en loop infinito (se repite para
    # siempre hasta que se llame detenerMusica()).
    def reproducirMusicaLoop(self, archivo):
        # Si el audio no esta disponible, no hacemos nada (evita errores).
        if not self._disponible:
            return
        # Intentamos cargar y reproducir el archivo.
        try:
            # Cargamos el archivo de musica indicado.
            pygame.mixer.music.load(archivo)
            # Lo reproducimos con loops=-1, que en pygame significa "para siempre".
            pygame.mixer.music.play(loops=-1)
        except Exception as error:
            # Si el archivo no existe o esta corrupto, avisamos y seguimos.
            mensaje.error(f"No se pudo reproducir la musica '{archivo}': {error}")

    # Detiene la musica de fondo por completo.
    def detenerMusica(self):
        # Si no hay audio disponible, no hacemos nada.
        if not self._disponible:
            return
        # Detenemos la musica.
        pygame.mixer.music.stop()

    # Pausa la musica de fondo (se puede reanudar despues desde el mismo punto).
    def pausarMusica(self):
        # Si no hay audio disponible, no hacemos nada.
        if not self._disponible:
            return
        # Pausamos la musica.
        pygame.mixer.music.pause()

    # Reanuda la musica de fondo justo donde se habia quedado.
    def reanudarMusica(self):
        # Si no hay audio disponible, no hacemos nada.
        if not self._disponible:
            return
        # Reanudamos la musica.
        pygame.mixer.music.unpause()

    # Cambia el volumen de la musica Y de todos los efectos de sonido a
    # la vez. 'valor' va de 0.0 (silencio) a 1.0 (volumen maximo); si
    # llega un numero fuera de ese rango, se recorta automaticamente.
    def establecerVolumen(self, valor):
        # Si no hay audio disponible, no hacemos nada.
        if not self._disponible:
            return
        # Nos aseguramos de que el valor quede entre 0.0 y 1.0.
        volumen = max(0.0, min(1.0, valor))
        # Cambiamos el volumen de la musica de fondo.
        pygame.mixer.music.set_volume(volumen)
        # Cambiamos el volumen de cada efecto ya generado (click, encendido, explosion).
        for sonido in self._efectos.values():
            sonido.set_volume(volumen)

    # Reproduce un efecto ya generado, por su nombre ("click",
    # "encendido" o "explosion"). No bloquea el programa: solo lo manda
    # a sonar y sigue de inmediato.
    def reproducirEfecto(self, nombre):
        # Si no hay audio disponible, no hacemos nada.
        if not self._disponible:
            return
        # Buscamos el efecto en el diccionario de efectos ya generados.
        sonido = self._efectos.get(nombre)
        # Si no existe un efecto con ese nombre, avisamos y no hacemos nada.
        if sonido is None:
            mensaje.advertencia(f"No existe el efecto de sonido '{nombre}'.")
            return
        # Lo reproducimos. pygame automaticamente busca un canal libre,
        # asi que si ya hay otro efecto sonando, no se cortan entre si.
        sonido.play()