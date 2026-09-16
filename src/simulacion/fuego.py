DIRECCIONES = [(1, 0), (-1, 0), (0, 1), (0, -1)]

def calcular_fuego_por_turno(grid, origenes_fuego, max_turnos, k):
    """
    Precalcula qué celdas están quemadas en cada turno, ya que la propagación
    NO depende de los agentes (es un cronograma fijo, calculable una sola vez).

    grid: mapa base (0=libre, 1=muro), el fuego no avanza sobre muros
    origenes_fuego: lista de celdas (x, y) donde empieza el incendio
    max_turnos: hasta qué turno precalcular
    k: cada cuántos turnos se propaga a las celdas adyacentes

    Devuelve: dict {turno: set(celdas_quemadas_hasta_ese_turno)}
    """
    alto, ancho = grid.shape
    quemado = set(origenes_fuego)
    frontera = list(origenes_fuego)
    fuego_por_turno = {}

    for t in range(max_turnos):
        if t > 0 and t % k == 0:
            nueva_frontera = []
            for (x, y) in frontera:
                for dx, dy in DIRECCIONES:
                    nx, ny = x + dx, y + dy
                    if (0 <= nx < ancho and 0 <= ny < alto
                            and grid[ny, nx] == 0 and (nx, ny) not in quemado):
                        quemado.add((nx, ny))
                        nueva_frontera.append((nx, ny))
            frontera = nueva_frontera

        fuego_por_turno[t] = set(quemado)

    return fuego_por_turno