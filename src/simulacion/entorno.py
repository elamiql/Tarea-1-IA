from .fuego import calcular_fuego_por_turno
from .congestion import costo_congestion_turno


class Agente:
    __slots__ = ("id", "pos", "vivo", "evacuado", "camino", "idx", "turno_evacuacion")

    def __init__(self, id_, pos):
        self.id = id_
        self.pos = pos
        self.vivo = True
        self.evacuado = False
        self.camino = None
        self.idx = 0
        self.turno_evacuacion = None


def combinar_obstaculos(grid, quemado):
    """Grid efectivo para planificar: muros originales + celdas quemadas."""
    grid_efectivo = grid.copy()

    for x, y in quemado:
        grid_efectivo[y, x] = 1

    return grid_efectivo


def camino_bloqueado(camino, idx, quemado):
    """Indica si el resto del camino pasa por una celda quemada."""
    if camino is None:
        return True

    return any(celda in quemado for celda in camino[idx:])


def costo_fn_congestion(ocupacion_previa, factor=5.0):
    """
    Costo extra para A* al moverse a una celda que estuvo congestionada
    el turno anterior.
    """

    def costo(actual, vecino):
        return 1 + factor * ocupacion_previa.get(vecino, 0)

    return costo


def simular(algoritmo, grid, spawns, salida, origenes_fuego, max_turnos, k_fuego,
            tipo_congestion="cuadratico", factor_congestion=1.0, usa_costo_fn=False):
    """
    Corre la evacuación completa para un algoritmo de pathfinding
    (BFS, DFS, A* o Greedy), replanificando cuando el fuego avanza
    o bloquea el camino actual.

    algoritmo: función (grid, inicio, fin) -> camino
               o (grid, inicio, fin, costo_fn) -> camino si usa_costo_fn=True.
    """

    if max_turnos <= 0:
        raise ValueError("max_turnos debe ser mayor que 0.")

    if k_fuego <= 0:
        raise ValueError("k_fuego debe ser mayor que 0.")

    alto, ancho = grid.shape

    if not (0 <= salida[0] < ancho and 0 <= salida[1] < alto):
        raise ValueError(f"Salida fuera del mapa: {salida}")

    if grid[salida[1], salida[0]] != 0:
        raise ValueError("La salida debe estar en una celda transitable.")

    for spawn in spawns:
        x, y = spawn

        if not (0 <= x < ancho and 0 <= y < alto):
            raise ValueError(f"Spawn fuera del mapa: {spawn}")

        if grid[y, x] != 0:
            raise ValueError(f"Spawn sobre un muro: {spawn}")

    fuego_por_turno = calcular_fuego_por_turno(grid, origenes_fuego, max_turnos, k_fuego)

    agentes = [Agente(i, pos) for i, pos in enumerate(spawns)]

    costo_congestion_total = 0.0
    ocupacion_previa = {}

    for t in range(max_turnos):
        quemado = fuego_por_turno.get(t, set())
        fuego_recien_avanzo = (t > 0 and t % k_fuego == 0)

        # Si la única salida queda consumida por el fuego,
        # todos los agentes que siguen dentro quedan atrapados.
        if salida in quemado:
            for agente in agentes:
                if agente.vivo and not agente.evacuado:
                    agente.vivo = False
            break

        # El fuego mata antes de replanificar o moverse.
        for agente in agentes:
            if agente.vivo and not agente.evacuado and agente.pos in quemado:
                agente.vivo = False

        vivos_activos = [agente for agente in agentes if agente.vivo and not agente.evacuado]

        if not vivos_activos:
            break

        grid_efectivo = combinar_obstaculos(grid, quemado)

        # Replanifica solo quien lo necesita.
        for agente in vivos_activos:
            necesita_plan = (
                agente.camino is None
                or t == 0
                or fuego_recien_avanzo
                or camino_bloqueado(agente.camino, agente.idx, quemado)
            )

            if not necesita_plan:
                continue

            if usa_costo_fn:
                nuevo_camino = algoritmo(grid_efectivo, agente.pos, salida, costo_fn_congestion(ocupacion_previa))
            else:
                nuevo_camino = algoritmo(grid_efectivo, agente.pos, salida)

            agente.camino = nuevo_camino
            agente.idx = 0

        # Decide la siguiente posición de cada agente activo.
        siguientes = {}

        for agente in vivos_activos:
            if agente.camino and agente.idx + 1 < len(agente.camino):
                siguientes[agente.id] = agente.camino[agente.idx + 1]
            else:
                siguientes[agente.id] = agente.pos

        # Calcula congestión del turno.
        ocupacion = {}

        for pos in siguientes.values():
            ocupacion[pos] = ocupacion.get(pos, 0) + 1

        costo_congestion_total += costo_congestion_turno(ocupacion, tipo_congestion, factor_congestion)
        ocupacion_previa = ocupacion

        # Aplica movimiento.
        for agente in vivos_activos:
            nueva_pos = siguientes[agente.id]

            if nueva_pos != agente.pos:
                agente.pos = nueva_pos
                agente.idx += 1

            if agente.pos == salida:
                agente.evacuado = True
                agente.turno_evacuacion = t

    evacuados = [agente for agente in agentes if agente.evacuado]
    cantidad_evacuados = len(evacuados)

    turnos_validos = [
        agente.turno_evacuacion
        for agente in evacuados
        if agente.turno_evacuacion is not None
    ]

    if turnos_validos:
        turnos_ultimo = max(turnos_validos)
    else:
        turnos_ultimo = None

    cantidad_vivos_no_evacuados = sum(
        1
        for agente in agentes
        if agente.vivo and not agente.evacuado
    )

    cantidad_muertos = len(agentes) - cantidad_evacuados - cantidad_vivos_no_evacuados

    return {
        "evacuados": cantidad_evacuados,
        "muertos": cantidad_muertos,
        "n_agentes": len(agentes),
        "turnos_ultimo": turnos_ultimo,
        "costo_congestion": costo_congestion_total,
    }