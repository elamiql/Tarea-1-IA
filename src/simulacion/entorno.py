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
    """Grid 'efectivo' para planificar: muros originales + celdas quemadas."""
    grid_efectivo = grid.copy()
    for (x, y) in quemado:
        grid_efectivo[y, x] = 1
    return grid_efectivo


def camino_bloqueado(camino, idx, quemado):
    """¿El resto del camino desde idx en adelante pasa por una celda quemada?"""
    return any(celda in quemado for celda in camino[idx:])


def costo_fn_congestion(ocupacion_previa, factor=5.0):
    """
    Costo extra para A* al moverse a una celda que estuvo congestionada el
    turno anterior (estimación — la ocupación real de ESTE turno todavía
    no existe cuando A* está planificando).
    """
    def costo(actual, vecino):
        return 1 + factor * ocupacion_previa.get(vecino, 0)
    return costo


def simular(algoritmo, grid, spawns, salida, origenes_fuego, max_turnos, k_fuego,
            tipo_congestion="cuadratico", factor_congestion=1.0, usa_costo_fn=False):
    """
    Corre la evacuación completa para UN algoritmo de pathfinding
    (bfs, dfs, a_star o greedy_best_first), replanificando cuando el fuego
    avanza o bloquea el camino actual de algún agente.

    algoritmo: función (grid, inicio, fin) -> camino
               o (grid, inicio, fin, costo_fn) -> camino si usa_costo_fn=True (ej. A*)
    """
    fuego_por_turno = calcular_fuego_por_turno(grid, origenes_fuego, max_turnos, k_fuego)
    agentes = [Agente(i, pos) for i, pos in enumerate(spawns)]
    costo_congestion_total = 0.0
    ocupacion_previa = {}

    for t in range(max_turnos):
        quemado = fuego_por_turno.get(t, set())
        fuego_recien_avanzo = (t > 0 and t % k_fuego == 0)

        # el fuego mata ANTES de replanificar/moverse
        for agente in agentes:
            if agente.vivo and not agente.evacuado and agente.pos in quemado:
                agente.vivo = False

        vivos_activos = [a for a in agentes if a.vivo and not a.evacuado]
        if not vivos_activos:
            break

        grid_efectivo = combinar_obstaculos(grid, quemado)

        # replanifica solo quien lo necesita (no todos, todos los turnos)
        for agente in vivos_activos:
            necesita_plan = (
                agente.camino is None
                or t == 0
                or fuego_recien_avanzo
                or camino_bloqueado(agente.camino, agente.idx, quemado)
            )
            if necesita_plan:
                if usa_costo_fn:
                    nuevo_camino = algoritmo(grid_efectivo, agente.pos, salida,
                                              costo_fn_congestion(ocupacion_previa))
                else:
                    nuevo_camino = algoritmo(grid_efectivo, agente.pos, salida)

                agente.camino = nuevo_camino  # None si quedó sin ruta posible (atrapado)
                agente.idx = 0

        # decide la siguiente posición de cada agente activo
        siguientes = {}
        for agente in vivos_activos:
            if agente.camino and agente.idx + 1 < len(agente.camino):
                siguientes[agente.id] = agente.camino[agente.idx + 1]
            else:
                siguientes[agente.id] = agente.pos  # esperar / atrapado / ya llegó

        ocupacion = {}
        for pos in siguientes.values():
            ocupacion[pos] = ocupacion.get(pos, 0) + 1
        costo_congestion_total += costo_congestion_turno(ocupacion, tipo_congestion, factor_congestion)
        ocupacion_previa = ocupacion

        # aplica el movimiento
        for agente in vivos_activos:
            nueva_pos = siguientes[agente.id]
            if nueva_pos != agente.pos:
                agente.pos = nueva_pos
                agente.idx += 1
            if agente.pos == salida:
                agente.evacuado = True
                agente.turno_evacuacion = t

    evacuados = [a for a in agentes if a.evacuado]
    sobrevivientes = len(evacuados)
    turnos_validos = [a.turno_evacuacion for a in evacuados]
    turnos_ultimo = max(turnos_validos) if turnos_validos else max_turnos

    return dict(
        sobrevivientes=sobrevivientes,
        n_agentes=len(agentes),
        turnos_ultimo=turnos_ultimo,
        costo_congestion=costo_congestion_total,
    )