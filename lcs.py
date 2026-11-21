"""Tres formas de obtener una subsecuencia común más larga, sin dependencias."""
from array import array
import sys


def lcs_recursiva(x: str, y: str) -> str:
    """Recursión directa sin caché. Guarda el mejor camino al llegar a una hoja."""
    sys.setrecursionlimit(max(sys.getrecursionlimit(), len(x) + len(y) + 200))
    camino = []
    mejor = []

    def visitar(i, j):
        nonlocal mejor
        if i == len(x) or j == len(y):
            if len(camino) > len(mejor):
                mejor = camino.copy()
            return
        if x[i] == y[j]:
            camino.append(x[i])
            visitar(i + 1, j + 1)
            camino.pop()
        else:
            visitar(i + 1, j)
            visitar(i, j + 1)

    visitar(0, 0)
    return ''.join(mejor)


def _fila(x, a, b, y, c, d, inversa=False):
    """Longitudes LCS para cada prefijo, con dos filas y rangos sin copias."""
    ancho = d - c
    previa = array('I', [0]) * (ancho + 1)
    actual = array('I', [0]) * (ancho + 1)
    indices = range(b - 1, a - 1, -1) if inversa else range(a, b)
    for i in indices:
        actual[0] = 0
        for k in range(1, ancho + 1):
            j = d - k if inversa else c + k - 1
            if x[i] == y[j]:
                actual[k] = previa[k - 1] + 1
            else:
                actual[k] = max(previa[k], actual[k - 1])
        previa, actual = actual, previa
    return previa


def lcs_hirschberg(x: str, y: str) -> str:
    """Divide y conquista con filas de PD para localizar el corte óptimo."""
    if len(x) < len(y):
        x, y = y, x
    resultado = []

    def resolver(a, b, c, d):
        if a == b or c == d:
            return
        if b - a == 1:
            for j in range(c, d):
                if x[a] == y[j]:
                    resultado.append(x[a])
                    break
            return
        medio = (a + b) // 2
        izquierda = _fila(x, a, medio, y, c, d)
        derecha = _fila(x, medio, b, y, c, d, inversa=True)
        ancho = d - c
        corte = max(range(ancho + 1), key=lambda k: izquierda[k] + derecha[ancho - k])
        del izquierda, derecha
        resolver(a, medio, c, c + corte)
        resolver(medio, b, c + corte, d)

    resolver(0, len(x), 0, len(y))
    return ''.join(resultado)


def lcs_tabular(x: str, y: str) -> str:
    """Tabla completa de longitudes y reconstrucción desde la última celda."""
    m, n = len(x), len(y)
    ancho = n + 1
    tabla = array('I', [0]) * ((m + 1) * ancho)
    for i in range(1, m + 1):
        fila, anterior = i * ancho, (i - 1) * ancho
        for j in range(1, n + 1):
            if x[i - 1] == y[j - 1]:
                tabla[fila + j] = tabla[anterior + j - 1] + 1
            else:
                tabla[fila + j] = max(tabla[anterior + j], tabla[fila + j - 1])
    salida = []
    i, j = m, n
    while i and j:
        if x[i - 1] == y[j - 1]:
            salida.append(x[i - 1])
            i -= 1
            j -= 1
        elif tabla[(i - 1) * ancho + j] >= tabla[i * ancho + j - 1]:
            i -= 1
        else:
            j -= 1
    return ''.join(reversed(salida))


def es_subsecuencia(candidata, cadena):
    posicion = 0
    for simbolo in cadena:
        if posicion < len(candidata) and candidata[posicion] == simbolo:
            posicion += 1
    return posicion == len(candidata)


VERSIONES = {'A': lcs_recursiva, 'B': lcs_hirschberg, 'C': lcs_tabular}
