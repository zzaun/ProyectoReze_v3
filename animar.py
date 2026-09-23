# animar.py
#
# Clase Animar: reproduce una animación a partir de un Excel con el mismo
# formato que capas.xlsx (bloques CAPA/TIPO/COLOR/GROSOR/X,Y), pero aquí cada
# HOJA es un FOTOGRAMA completo.
#
# No tiene lógica de dibujo propia: reutiliza la clase Dibujar y solo decide
# qué fotograma toca dibujar en cada momento.
#
# Reglas:
#   - Cada vez que se llama a dibujarFotogramaActual() se avanza una hoja
#     (normalmente una vez por vuelta del loop de windows.py).
#   - Al llegar al último fotograma se vuelve al primero (animación en loop).
#   - El offset de posición se calcula una sola vez con las coordenadas de
#     TODOS los fotogramas juntos, para que la imagen no salte de lugar
#     entre cuadros.

# Para leer las hojas, capas y coordenadas del Excel
import lectorcapas
# Para imprimir avisos en la consola
import mensaje


# Clase que maneja la animación por fotogramas
class Animar:
    # Constructor: se ejecuta al crear un objeto Animar.
    # dibujador: un objeto Dibujar que ya existe. Se reutiliza en vez de crear otro, para compartir el mismo offset con el resto del dibujo.
    # archivo: ruta del Excel con los fotogramas.
    def __init__(self, dibujador, archivo="fotogramas.xlsx"):
        # Guarda el dibujador para usarlo después
        self.dibujador = dibujador
        # Guarda la ruta del Excel de fotogramas
        self.archivo = archivo
        # Posición del fotograma que toca dibujar. Empieza en el primero (0)
        self.indiceFotogramaActual = 0

    # Regresa la lista con los nombres de los fotogramas (las hojas), en el
    # orden en que aparecen en el archivo. Es barato llamarla seguido porque
    # lectorcapas guarda el Excel en memoria y solo lo vuelve a leer si el
    # archivo cambió en disco.
    def obtenerListaFotogramas(self):
        # Pide a lectorcapas la lista de hojas del archivo
        return lectorcapas.getListGruposCapas(archivo=self.archivo)

    # Junta las coordenadas de TODOS los fotogramas del archivo. Sirve para
    # calcular el offset con dibujador.calcularOffsetDesdeCoordenadas(...)
    def obtenerTodasLasCoordenadas(self):
        # El dibujador ya sabe recorrer todas las hojas de un archivo
        return self.dibujador.obtenerTodasLasCoordenadas(archivo=self.archivo)

    # Vuelve al primer fotograma
    def reiniciar(self):
        # El índice 0 es el primer fotograma
        self.indiceFotogramaActual = 0

    # Dibuja el fotograma que toca en este momento.
    # avanzar=True (por defecto): después de dibujar pasa al siguiente
    #   fotograma. Al pasar del último vuelve al primero. Se llama una vez por
    #   vuelta del loop principal.
    # avanzar=False: vuelve a dibujar el MISMO fotograma sin avanzar. Así
    #   funciona el Pause: la animación se congela pero se sigue redibujando
    #   cada frame, y la corrección X/Y se puede seguir cambiando en vivo.
    def dibujarFotogramaActual(self, avanzar=True):
        # Pide la lista de fotogramas (hojas) del archivo
        fotogramas = self.obtenerListaFotogramas()

        # Si no hay ningún fotograma, avisa y se sale sin dibujar nada
        if not fotogramas:
            mensaje.advertencia(f"'{self.archivo}' no tiene fotogramas (hojas), no se dibuja nada.")
            return

        # Si el Excel cambió mientras el programa corría (le quitaron hojas),
        # el índice podría quedar fuera de rango. En ese caso se regresa al inicio.
        if self.indiceFotogramaActual >= len(fotogramas):
            self.indiceFotogramaActual = 0

        # Toma el nombre de la hoja que toca dibujar
        nombreFotograma = fotogramas[self.indiceFotogramaActual]
        # Dibuja todas las capas de esa hoja
        self.dibujador.dibujarGrupo(nombreFotograma, archivo=self.archivo)

        # Solo si no está en pausa se pasa al siguiente fotograma
        if avanzar:
            # Suma 1 al índice. El % (residuo) hace que después del último vuelva a 0
            self.indiceFotogramaActual = (self.indiceFotogramaActual + 1) % len(fotogramas)
