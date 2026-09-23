from collections import deque


DIRECCIONES = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def validar_fuego(grid, origenes_fuego, k):
    if k <= 0:
        raise ValueError("k debe ser mayor que 0")

    alto, ancho = grid.shape

    for x, y in origenes_fuego:
        if not (0 <= x < ancho and 0 <= y < alto):
            raise ValueError(f"Origen del fuego fuera del mapa: {(x, y)}")

        if grid[y, x] != 0:
            raise ValueError(f"El origen del fuego está sobre un muro: {(x, y)}")


def calcular_turno_quema_salida(grid, origenes_fuego, salida, k):
    """
    Calcula el turno exacto en que el fuego alcanza la salida.

    El fuego comienza en los origenes en el turno 0 y avanza una celda
    ortogonal cada k turnos.

    Devuelve None si la salida no es alcanzable por el fuego.
    """
    validar_fuego(grid, origenes_fuego, k)

    alto, ancho = grid.shape
    sx, sy = salida

    if not (0 <= sx < ancho and 0 <= sy < alto):
        raise ValueError(f"Salida fuera del mapa: {salida}")

    if grid[sy, sx] != 0:
        raise ValueError("La salida debe estar en una celda transitable.")

    if not origenes_fuego:
        return None

    distancias = {}
    cola = deque()

    for origen in origenes_fuego:
        if origen not in distancias:
            distancias[origen] = 0
            cola.append(origen)

    while cola:
        x, y = cola.popleft()
        distancia = distancias[(x, y)]

        if (x, y) == salida:
            return distancia * k

        for dx, dy in DIRECCIONES:
            nx = x + dx
            ny = y + dy
            vecino = (nx, ny)

            if (
                0 <= nx < ancho
                and 0 <= ny < alto
                and grid[ny, nx] == 0
                and vecino not in distancias
            ):
                distancias[vecino] = distancia + 1
                cola.append(vecino)

    return None


def calcular_fuego_por_turno(grid, origenes_fuego, max_turnos, k):
    """
    Precalcula qué celdas están quemadas en cada turno, ya que la propagación
    NO depende de los agentes.

    grid: mapa base (0=libre, 1=muro)
    origenes_fuego: celdas (x, y) donde empieza el incendio
    max_turnos: cantidad de turnos a precalcular
    k: cada cuantos turnos se propaga a las celdas adyacentes

    Devuelve:
        dict {turno: set(celdas_quemadas_hasta_ese_turno)}
    """
    if max_turnos <= 0:
        raise ValueError("max_turnos debe ser mayor que 0")

    validar_fuego(grid, origenes_fuego, k)

    alto, ancho = grid.shape

    quemado = set(origenes_fuego)
    frontera = list(origenes_fuego)
    fuego_por_turno = {}

    for t in range(max_turnos):
        if t > 0 and t % k == 0:
            nueva_frontera = []

            for x, y in frontera:
                for dx, dy in DIRECCIONES:
                    nx = x + dx
                    ny = y + dy

                    if (
                        0 <= nx < ancho
                        and 0 <= ny < alto
                        and grid[ny, nx] == 0
                        and (nx, ny) not in quemado
                    ):
                        quemado.add((nx, ny))
                        nueva_frontera.append((nx, ny))

            frontera = nueva_frontera

        fuego_por_turno[t] = set(quemado)

    return fuego_por_turno