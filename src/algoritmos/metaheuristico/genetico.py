import numpy as np

from ...simulacion.congestion import costo_congestion_turno


MOVIMIENTOS = [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]

def generar_secuencia(largo, rng):
    """Una secuencia random de movimientos para 1 agente."""
    idx = rng.integers(0, len(MOVIMIENTOS), size=largo)
    return [MOVIMIENTOS[i] for i in idx]


def cruza_secuencia(p1, p2, rng):
    """Cruza de 1 punto entre dos secuencias del mismo largo."""
    largo = len(p1)
    if largo < 2:
        return list(p1)
    punto = int(rng.integers(1, largo))
    return p1[:punto] + p2[punto:]


def mutar_secuencia(secuencia, prob_mutacion, rng):
    """Muta in-place: cada gen tiene prob_mutacion de cambiar a un movimiento random."""
    for t in range(len(secuencia)):
        if rng.random() < prob_mutacion:
            secuencia[t] = MOVIMIENTOS[int(rng.integers(len(MOVIMIENTOS)))]


def seleccion_torneo(poblacion, fitnesses, k, rng):
    """Elige k individuos al azar y devuelve el de mejor fitness."""
    participantes = rng.choice(len(poblacion), size=min(k, len(poblacion)), replace=False)
    mejor_idx = max(participantes, key=lambda i: fitnesses[i])
    return poblacion[mejor_idx]


# simulación conjunta (fitness real)

def simular_grupo(plan_conjunto, grid, spawns, salida, fuego_por_turno,
                   tipo_congestion="cuadratico", factor_congestion=1.0):
    """
    Ejecuta el plan de TODOS los agentes turno a turno (movimiento + fuego +
    congestión real), y devuelve las métricas resultantes.

    plan_conjunto: lista de secuencias, una por agente (mismo orden que spawns)
    fuego_por_turno: dict {turno: set(celdas_quemadas)}, precalculado y fijo
    """
    alto, ancho = grid.shape
    n_agentes = len(spawns)
    largo = len(plan_conjunto[0])

    posiciones = list(spawns)
    vivos = [True] * n_agentes
    evacuados = [False] * n_agentes
    turno_evacuacion = [None] * n_agentes
    costo_total = 0.0

    for t in range(largo):
        quemado = fuego_por_turno.get(t, set())

        # el fuego mata ANTES de que el agente se mueva este turno
        for i, pos in enumerate(posiciones):
            if vivos[i] and not evacuados[i] and pos in quemado:
                vivos[i] = False

        nuevas_posiciones = list(posiciones)
        for i, pos in enumerate(posiciones):
            if not vivos[i] or evacuados[i]:
                continue
            dx, dy = plan_conjunto[i][t]
            nx, ny = pos[0] + dx, pos[1] + dy
            # "reparación": movimiento inválido (muro/borde) = se queda quieto
            if 0 <= nx < ancho and 0 <= ny < alto and grid[ny, nx] == 0:
                nuevas_posiciones[i] = (nx, ny)

        # congestión real: cuántos agentes vivos y no evacuados comparten celda
        ocupacion = {}
        for i, pos in enumerate(nuevas_posiciones):
            if vivos[i] and not evacuados[i]:
                ocupacion[pos] = ocupacion.get(pos, 0) + 1
        costo_total += costo_congestion_turno(ocupacion, tipo_congestion, factor_congestion)

        posiciones = nuevas_posiciones
        for i, pos in enumerate(posiciones):
            if vivos[i] and not evacuados[i] and pos == salida:
                evacuados[i] = True
                turno_evacuacion[i] = t

    sobrevivientes = sum(evacuados)
    turnos_validos = [t for t in turno_evacuacion if t is not None]
    turnos_ultimo = max(turnos_validos) if turnos_validos else largo

    return dict(
        sobrevivientes=sobrevivientes,
        n_agentes=n_agentes,
        turnos_ultimo=turnos_ultimo,
        costo_congestion=costo_total,
    )


def fitness(resultado, w_sobrevivencia=100.0, w_turnos=1.0, w_congestion=0.1):
    return (resultado["sobrevivientes"] * w_sobrevivencia
            - resultado["turnos_ultimo"] * w_turnos
            - resultado["costo_congestion"] * w_congestion)


# coevolución cooperativa (1 población por agente)

def algoritmo_genetico(grid, spawns, salida, fuego_por_turno, largo,
                        generaciones=50, tam_poblacion=20, prob_mutacion=0.1,
                        k_torneo=3, elitismo=True, tipo_congestion="cuadratico",
                        factor_congestion=1.0, seed=None):
    """
    Evoluciona una secuencia de movimientos por agente. Cada candidato de un
    agente se evalúa insertándolo en el plan conjunto (junto al mejor actual
    de los demás agentes) y simulando el grupo completo de verdad — así el
    fitness refleja congestión real, no una estimación.

    Devuelve: (mejores, resultado_final)
      mejores: lista de secuencias, una por agente (el plan final)
      resultado_final: métricas de simular_grupo(mejores, ...)
    """
    rng = np.random.default_rng(seed)
    n_agentes = len(spawns)

    poblaciones = [
        [generar_secuencia(largo, rng) for _ in range(tam_poblacion)]
        for _ in range(n_agentes)
    ]
    mejores = [poblaciones[i][0] for i in range(n_agentes)]

    for _ in range(generaciones):
        for i in range(n_agentes):
            fitnesses = []
            for candidato in poblaciones[i]:
                plan_conjunto = list(mejores)
                plan_conjunto[i] = candidato

                resultado = simular_grupo(plan_conjunto, grid, spawns, salida,
                                           fuego_por_turno, tipo_congestion, factor_congestion)
                fitnesses.append(fitness(resultado))

            nueva_poblacion = []
            if elitismo:
                mejor_idx_actual = max(range(tam_poblacion), key=lambda j: fitnesses[j])
                nueva_poblacion.append(list(poblaciones[i][mejor_idx_actual]))

            while len(nueva_poblacion) < tam_poblacion:
                p1 = seleccion_torneo(poblaciones[i], fitnesses, k_torneo, rng)
                p2 = seleccion_torneo(poblaciones[i], fitnesses, k_torneo, rng)
                hijo = cruza_secuencia(p1, p2, rng)
                mutar_secuencia(hijo, prob_mutacion, rng)
                nueva_poblacion.append(hijo)

            poblaciones[i] = nueva_poblacion
            mejor_idx = max(range(tam_poblacion), key=lambda j: fitnesses[j])
            mejores[i] = poblaciones[i][mejor_idx]

    resultado_final = simular_grupo(mejores, grid, spawns, salida,
                                     fuego_por_turno, tipo_congestion, factor_congestion)
    return mejores, resultado_final