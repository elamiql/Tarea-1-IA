from ..utils import reconstruir_camino, vecinos_validos

def DFS(grid, inicio, fin):
    pila = [inicio]
    visitados = {inicio}
    padre = {}

    while pila:
        actual = pila.pop()

        if actual == fin:
            return reconstruir_camino(padre, fin)

        for vecino in vecinos_validos(grid, actual):
            if vecino not in visitados:
                visitados.add(vecino)
                padre[vecino] = actual
                pila.append(vecino)
    return None