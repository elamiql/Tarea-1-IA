import heapq
from ..utils import reconstruir_camino, vecinos_validos
from ..heuristicas import manhattan

def A_star(grid, inicio, fin, costo_fn=None):
    if costo_fn is None:
        costo_fn = lambda actual, vecino: 1  # costo parejo por defecto

    contador = 0
    frontera = [(manhattan(inicio, fin), contador, inicio)]  # heap: (f, desempate, nodo)
    padre = {}
    costo_g = {inicio: 0}

    while frontera:
        actual = heapq.heappop(frontera)[2]  # saca el de MENOR f(n)

        if actual == fin:
            return reconstruir_camino(padre, fin)

        for vecino in vecinos_validos(grid, actual):
            nuevo_g = costo_g[actual] + costo_fn(actual, vecino)
            if vecino not in costo_g or nuevo_g < costo_g[vecino]:
                costo_g[vecino] = nuevo_g
                f = nuevo_g + manhattan(vecino, fin)
                contador += 1
                heapq.heappush(frontera, (f, contador, vecino))
                padre[vecino] = actual

    return None