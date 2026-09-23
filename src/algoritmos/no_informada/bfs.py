from collections import deque
from ..utils import vecinos_validos, reconstruir_camino

def BFS(grid, inicio, fin):
    queue = deque([inicio])
    visitados = {inicio}
    padre = {}

    while queue:
        actual = queue.popleft()

        if actual == fin:
            return reconstruir_camino(padre, fin)

        for vecino in vecinos_validos(grid, actual):
            if vecino not in visitados:
                visitados.add(vecino)
                padre[vecino] = actual
                queue.append(vecino)

    return None