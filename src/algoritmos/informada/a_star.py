import heapq

from ..heuristicas import manhattan
from ..utils import reconstruir_camino, vecinos_validos

def A_star(grid, inicio, fin, costo_fn=None):
    if costo_fn is None:
        def costo_fn(actual, vecino):
            return 1

    contador = 0
    frontera = [(manhattan(inicio, fin), contador, inicio)]
    padre = {}
    costo_g = {inicio: 0}

    while frontera:
        _, _, actual = heapq.heappop(frontera)

        if actual == fin:
            return reconstruir_camino(padre, fin)

        for vecino in vecinos_validos(grid, actual):
            costo_movimiento = costo_fn(actual, vecino)

            if costo_movimiento <= 0:
                raise ValueError("El costo de movimiento debe ser mayor que 0.")

            nuevo_g = costo_g[actual] + costo_movimiento

            if vecino not in costo_g or nuevo_g < costo_g[vecino]:
                costo_g[vecino] = nuevo_g
                padre[vecino] = actual

                f = nuevo_g + manhattan(vecino, fin)
                contador += 1

                heapq.heappush(
                    frontera,
                    (f, contador, vecino)
                )

    return None