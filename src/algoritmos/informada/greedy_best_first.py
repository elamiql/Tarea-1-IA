import heapq
from ..utils import vecinos_validos, reconstruir_camino
from ..heuristicas import manhattan


def greedy_best_first(grid, inicio, fin):
    contador = 0
    frontera = [(manhattan(inicio, fin), contador, inicio)]
    visitados = {inicio}
    padre = {}

    while frontera:
        actual = heapq.heappop(frontera)[2]

        if actual == fin:
            return reconstruir_camino(padre, fin)

        for vecino in vecinos_validos(grid, actual):
            if vecino not in visitados:
                visitados.add(vecino)
                padre[vecino] = actual
                contador += 1
                heapq.heappush(frontera, (manhattan(vecino, fin), contador, vecino))

    return None