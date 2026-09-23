import numpy as np
from collections import deque

from ...simulacion.congestion import costo_celda, costo_congestion_turno


MOVIMIENTOS = [
    (0, 0),
    (1, 0),
    (-1, 0),
    (0, 1),
    (0, -1),
]


def calcular_distancias_salida(grid, salida):
    alto, ancho = grid.shape
    sx, sy = salida

    if not (0 <= sx < ancho and 0 <= sy < alto):
        raise ValueError("La salida esta fuera del mapa.")

    if grid[sy, sx] != 0:
        raise ValueError("La salida debe estar en una celda transitable.")

    distancias = np.full((alto, ancho), -1, dtype=int)
    distancias[sy, sx] = 0

    cola = deque([salida])

    while cola:
        x, y = cola.popleft()

        for dx, dy in MOVIMIENTOS[1:]:
            nx = x + dx
            ny = y + dy

            if 0 <= nx < ancho and 0 <= ny < alto and grid[ny, nx] == 0 and distancias[ny, nx] == -1:
                distancias[ny, nx] = distancias[y, x] + 1
                cola.append((nx, ny))

    return distancias


def generar_secuencia(largo, rng):
    if largo <= 0:
        raise ValueError("largo debe ser mayor que 0.")

    indices = rng.integers(0, len(MOVIMIENTOS), size=largo)

    return [MOVIMIENTOS[i] for i in indices]


def cruza_secuencia(p1, p2, rng):
    if len(p1) != len(p2):
        raise ValueError("Los padres deben tener el mismo largo.")

    largo = len(p1)

    if largo < 2:
        return list(p1)

    punto = int(rng.integers(1, largo))

    return p1[:punto] + p2[punto:]


def mutar_secuencia(secuencia, prob_mutacion, rng):
    if not 0 <= prob_mutacion <= 1:
        raise ValueError("prob_mutacion debe estar entre 0 y 1.")

    for t in range(len(secuencia)):
        if rng.random() < prob_mutacion:
            secuencia[t] = MOVIMIENTOS[int(rng.integers(len(MOVIMIENTOS)))]


def seleccion_torneo(poblacion, fitnesses, k, rng):
    if len(poblacion) != len(fitnesses):
        raise ValueError("poblacion y fitnesses deben tener el mismo largo.")

    if len(poblacion) == 0:
        raise ValueError("La poblacion no puede estar vacia.")

    if k <= 0:
        raise ValueError("k debe ser mayor que 0.")

    participantes = rng.choice(len(poblacion), size=min(k, len(poblacion)), replace=False)
    mejor_idx = max(participantes, key=lambda i: fitnesses[i])

    return poblacion[mejor_idx]


def simular_agente(secuencia, grid, spawn, salida, fuego_por_turno, distancias_salida):
    largo = len(secuencia)
    alto, ancho = grid.shape

    pos = spawn
    vivo = True
    evacuado = False
    turno_evacuacion = None

    ocupacion_por_turno = [None] * largo

    distancia_inicial = distancias_salida[spawn[1], spawn[0]]

    if distancia_inicial < 0:
        mejor_distancia = None
    else:
        mejor_distancia = distancia_inicial

    for t in range(largo):
        quemado = fuego_por_turno.get(t, set())

        # Si la unica salida se quema, cualquier agente
        # que siga dentro queda atrapado y se considera baja.
        if salida in quemado:
            vivo = False
            break

        # Si el fuego alcanza directamente al agente, muere.
        if pos in quemado:
            vivo = False
            break

        dx, dy = secuencia[t]

        nx = pos[0] + dx
        ny = pos[1] + dy

        if 0 <= nx < ancho and 0 <= ny < alto and grid[ny, nx] == 0 and (nx, ny) not in quemado:
            pos = (nx, ny)

        ocupacion_por_turno[t] = pos

        distancia_actual = distancias_salida[pos[1], pos[0]]

        if distancia_actual >= 0:
            if mejor_distancia is None or distancia_actual < mejor_distancia:
                mejor_distancia = distancia_actual

        if pos == salida:
            evacuado = True
            turno_evacuacion = t
            mejor_distancia = 0
            break

    if distancia_inicial <= 0:
        progreso = 1.0
    elif mejor_distancia is None:
        progreso = 0.0
    else:
        progreso = (distancia_inicial - mejor_distancia) / distancia_inicial
        progreso = max(0.0, min(1.0, progreso))

    return {
        "evacuado": evacuado,
        "muerto": not vivo,
        "turno_evacuacion": turno_evacuacion,
        "ocupacion": ocupacion_por_turno,
        "progreso": progreso,
    }


def combinar_trazas(trazas, largo, tipo_congestion="cuadratico", factor_congestion=1.0):
    cantidad_evacuados = sum(traza["evacuado"] for traza in trazas)
    cantidad_muertos = sum(traza["muerto"] for traza in trazas)

    turnos_validos = [traza["turno_evacuacion"] for traza in trazas if traza["turno_evacuacion"] is not None]

    if turnos_validos:
        turnos_ultimo = max(turnos_validos)
    else:
        turnos_ultimo = largo

    costo_total = 0.0

    for t in range(largo):
        ocupacion = {}

        for traza in trazas:
            pos = traza["ocupacion"][t]

            if pos is not None:
                ocupacion[pos] = ocupacion.get(pos, 0) + 1

        costo_total += costo_congestion_turno(ocupacion, tipo_congestion, factor_congestion)

    if trazas:
        progreso_promedio = sum(traza["progreso"] for traza in trazas) / len(trazas)
    else:
        progreso_promedio = 0.0

    return {
        "sobrevivientes": cantidad_evacuados,
        "evacuados": cantidad_evacuados,
        "muertos": cantidad_muertos,
        "n_agentes": len(trazas),
        "turnos_ultimo": turnos_ultimo,
        "costo_congestion": costo_total,
        "progreso_promedio": progreso_promedio,
        "horizonte": largo,
    }


def simular_grupo(plan_conjunto, grid, spawns, salida, fuego_por_turno, tipo_congestion="cuadratico", factor_congestion=1.0, distancias_salida=None):
    n_agentes = len(spawns)

    if n_agentes == 0:
        return {
            "sobrevivientes": 0,
            "evacuados": 0,
            "muertos": 0,
            "n_agentes": 0,
            "turnos_ultimo": 0,
            "costo_congestion": 0.0,
            "progreso_promedio": 0.0,
            "horizonte": 0,
        }

    if len(plan_conjunto) != n_agentes:
        raise ValueError("Debe existir una secuencia por agente.")

    largo = len(plan_conjunto[0])

    if largo == 0:
        raise ValueError("Las secuencias no pueden estar vacias.")

    for secuencia in plan_conjunto:
        if len(secuencia) != largo:
            raise ValueError("Todas las secuencias deben tener el mismo largo.")

    if distancias_salida is None:
        distancias_salida = calcular_distancias_salida(grid, salida)

    trazas = [
        simular_agente(plan_conjunto[i], grid, spawns[i], salida, fuego_por_turno, distancias_salida)
        for i in range(n_agentes)
    ]

    return combinar_trazas(trazas, largo, tipo_congestion, factor_congestion)


def fitness(resultado):
    evacuados = resultado["sobrevivientes"]
    muertos = resultado["muertos"]
    n_agentes = resultado["n_agentes"]
    turnos_ultimo = resultado["turnos_ultimo"]
    costo_congestion = resultado["costo_congestion"]
    progreso = resultado["progreso_promedio"]
    horizonte = resultado["horizonte"]

    if n_agentes == 0:
        return 0.0

    if horizonte > 0:
        rapidez = 1.0 - min(turnos_ultimo / horizonte, 1.0)
    else:
        rapidez = 0.0

    descongestion = 1.0 / (1.0 + costo_congestion)

    penalizacion_muerte = 120.0
    recompensa_evacuacion = n_agentes * penalizacion_muerte + 120.0

    return (
        evacuados * recompensa_evacuacion
        - muertos * penalizacion_muerte
        + rapidez * 10.0
        + descongestion
        + progreso * 100.0
    )


def construir_contexto_base(trazas_mejores, indice_agente, largo, tipo_congestion, factor_congestion):
    ocupacion_base = [{} for _ in range(largo)]
    costos_base = [0.0] * largo

    evacuados_base = 0
    muertos_base = 0
    progreso_total = 0.0
    turnos_evacuacion_base = []

    for i, traza in enumerate(trazas_mejores):
        if i == indice_agente:
            continue

        if traza["evacuado"]:
            evacuados_base += 1

        if traza["muerto"]:
            muertos_base += 1

        progreso_total += traza["progreso"]

        if traza["turno_evacuacion"] is not None:
            turnos_evacuacion_base.append(traza["turno_evacuacion"])

        for t in range(largo):
            pos = traza["ocupacion"][t]

            if pos is not None:
                ocupacion_base[t][pos] = ocupacion_base[t].get(pos, 0) + 1

    for t in range(largo):
        costos_base[t] = costo_congestion_turno(ocupacion_base[t], tipo_congestion, factor_congestion)

    if turnos_evacuacion_base:
        turno_ultimo_base = max(turnos_evacuacion_base)
    else:
        turno_ultimo_base = None

    return {
        "ocupacion": ocupacion_base,
        "costos": costos_base,
        "evacuados": evacuados_base,
        "muertos": muertos_base,
        "progreso_total": progreso_total,
        "turno_ultimo": turno_ultimo_base,
        "n_agentes": len(trazas_mejores),
    }


def evaluar_traza_con_contexto(traza, contexto, largo, tipo_congestion, factor_congestion):
    cantidad_evacuados = contexto["evacuados"] + int(traza["evacuado"])
    cantidad_muertos = contexto["muertos"] + int(traza["muerto"])

    turno_candidato = traza["turno_evacuacion"]
    turno_base = contexto["turno_ultimo"]

    if turno_base is None and turno_candidato is None:
        turnos_ultimo = largo
    elif turno_base is None:
        turnos_ultimo = turno_candidato
    elif turno_candidato is None:
        turnos_ultimo = turno_base
    else:
        turnos_ultimo = max(turno_base, turno_candidato)

    costo_total = 0.0

    for t in range(largo):
        costo_turno = contexto["costos"][t]
        pos = traza["ocupacion"][t]

        if pos is not None:
            cantidad_actual = contexto["ocupacion"][t].get(pos, 0)

            costo_anterior = costo_celda(cantidad_actual, tipo_congestion, factor_congestion)
            costo_nuevo = costo_celda(cantidad_actual + 1, tipo_congestion, factor_congestion)

            costo_turno += costo_nuevo - costo_anterior

        costo_total += costo_turno

    progreso_promedio = (contexto["progreso_total"] + traza["progreso"]) / contexto["n_agentes"]

    return {
        "sobrevivientes": cantidad_evacuados,
        "evacuados": cantidad_evacuados,
        "muertos": cantidad_muertos,
        "n_agentes": contexto["n_agentes"],
        "turnos_ultimo": turnos_ultimo,
        "costo_congestion": costo_total,
        "progreso_promedio": progreso_promedio,
        "horizonte": largo,
    }


def evaluar_poblacion(poblacion, indice_agente, mejores, grid, spawns, salida, fuego_por_turno, tipo_congestion, factor_congestion, trazas_mejores=None, distancias_salida=None):
    if len(mejores) != len(spawns):
        raise ValueError("Debe existir un mejor individuo por agente.")

    largo = len(mejores[0])

    if distancias_salida is None:
        distancias_salida = calcular_distancias_salida(grid, salida)

    if trazas_mejores is None:
        trazas_mejores = [
            simular_agente(mejores[i], grid, spawns[i], salida, fuego_por_turno, distancias_salida)
            for i in range(len(spawns))
        ]

    contexto = construir_contexto_base(trazas_mejores, indice_agente, largo, tipo_congestion, factor_congestion)

    fitnesses = []
    cache = {}

    for candidato in poblacion:
        clave = tuple(candidato)

        if clave not in cache:
            traza = simular_agente(candidato, grid, spawns[indice_agente], salida, fuego_por_turno, distancias_salida)
            resultado = evaluar_traza_con_contexto(traza, contexto, largo, tipo_congestion, factor_congestion)
            cache[clave] = fitness(resultado)

        fitnesses.append(cache[clave])

    return fitnesses


def algoritmo_genetico(grid, spawns, salida, fuego_por_turno, largo, generaciones=50, tam_poblacion=20, prob_mutacion=0.1, k_torneo=3, elitismo=True, tipo_congestion="cuadratico", factor_congestion=1.0, seed=None):
    if largo <= 0:
        raise ValueError("largo debe ser mayor que 0.")

    if generaciones <= 0:
        raise ValueError("generaciones debe ser mayor que 0.")

    if tam_poblacion <= 0:
        raise ValueError("tam_poblacion debe ser mayor que 0.")

    if k_torneo <= 0:
        raise ValueError("k debe ser mayor que 0.")

    if not 0 <= prob_mutacion <= 1:
        raise ValueError("prob_mutacion debe estar entre 0 y 1.")

    rng = np.random.default_rng(seed)
    distancias_salida = calcular_distancias_salida(grid, salida)
    n_agentes = len(spawns)

    if n_agentes == 0:
        return [], simular_grupo([], grid, [], salida, fuego_por_turno, tipo_congestion, factor_congestion)

    poblaciones = [
        [generar_secuencia(largo, rng) for _ in range(tam_poblacion)]
        for _ in range(n_agentes)
    ]

    mejores = [list(poblaciones[i][0]) for i in range(n_agentes)]

    trazas_mejores = [
        simular_agente(mejores[i], grid, spawns[i], salida, fuego_por_turno, distancias_salida)
        for i in range(n_agentes)
    ]

    for _ in range(generaciones):
        for i in range(n_agentes):
            poblacion_actual = poblaciones[i]

            fitnesses = evaluar_poblacion(
                poblacion_actual, i, mejores, grid, spawns, salida, fuego_por_turno,
                tipo_congestion, factor_congestion, trazas_mejores, distancias_salida
            )

            mejor_idx = max(range(tam_poblacion), key=lambda j: fitnesses[j])
            mejor_individuo = list(poblacion_actual[mejor_idx])

            nueva_poblacion = []

            if elitismo:
                nueva_poblacion.append(list(mejor_individuo))

            while len(nueva_poblacion) < tam_poblacion:
                padre1 = seleccion_torneo(poblacion_actual, fitnesses, k_torneo, rng)
                padre2 = seleccion_torneo(poblacion_actual, fitnesses, k_torneo, rng)

                hijo = cruza_secuencia(padre1, padre2, rng)
                mutar_secuencia(hijo, prob_mutacion, rng)

                nueva_poblacion.append(hijo)

            poblaciones[i] = nueva_poblacion
            mejores[i] = mejor_individuo
            trazas_mejores[i] = simular_agente(mejor_individuo, grid, spawns[i], salida, fuego_por_turno, distancias_salida)

    for i in range(n_agentes):
        poblacion_actual = poblaciones[i]

        fitnesses = evaluar_poblacion(
            poblacion_actual, i, mejores, grid, spawns, salida, fuego_por_turno,
            tipo_congestion, factor_congestion, trazas_mejores, distancias_salida
        )

        mejor_idx = max(range(tam_poblacion), key=lambda j: fitnesses[j])

        mejores[i] = list(poblacion_actual[mejor_idx])
        trazas_mejores[i] = simular_agente(mejores[i], grid, spawns[i], salida, fuego_por_turno, distancias_salida)

    resultado_final = simular_grupo(mejores, grid, spawns, salida, fuego_por_turno, tipo_congestion, factor_congestion, distancias_salida)

    return mejores, resultado_final