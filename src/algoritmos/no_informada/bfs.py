from collections import deque
from ..utils import vecinos_validos, reconstruir_camino

def BFS(grid, inicio, fin):
    queue = [inicio]
    visitados = {inicio}
    padre = {}

    while queue:
        s = queue.pop(0)

        if s == fin:
            return reconstruir_camino(padre, fin)

        for vecino in vecinos_validos(grid, s):
            if vecino not in visitados:
                visitados.add(vecino)
                padre[vecino] = s
                queue.append(vecino)
    return None