DIRECCIONES = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def vecinos_validos(grid, pos):
    """Vecinos ortogonales dentro del grid y transitables (grid == 0)."""
    x, y = pos
    alto, ancho = grid.shape
    for dx, dy in DIRECCIONES:
        nx, ny = x + dx, y + dy
        if 0 <= nx < ancho and 0 <= ny < alto and grid[ny, nx] == 0:
            yield (nx, ny)


def reconstruir_camino(padre, fin):
    """Sigue el diccionario padre desde fin hasta el inicio y da vuelta la lista."""
    camino = [fin]
    while camino[-1] in padre:
        camino.append(padre[camino[-1]])
    camino.reverse()
    return camino