from ...simulacion.congestion import costo_celda, costo_congestion_turno
from .simulacion_genetica import calcular_distancias_salida, simular_agente


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

    if turnos_ultimo is None or horizonte <= 0:
        rapidez = 0.0
    else:
        rapidez = 1.0 - min(turnos_ultimo / horizonte, 1.0)

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


def construir_contexto_base(
    trazas_mejores,
    indice_agente,
    largo,
    tipo_congestion,
    factor_congestion
):
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
        costos_base[t] = costo_congestion_turno(
            ocupacion_base[t],
            tipo_congestion,
            factor_congestion
        )

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


def evaluar_traza_con_contexto(
    traza,
    contexto,
    largo,
    tipo_congestion,
    factor_congestion
):
    cantidad_evacuados = contexto["evacuados"] + int(traza["evacuado"])
    cantidad_muertos = contexto["muertos"] + int(traza["muerto"])

    turno_candidato = traza["turno_evacuacion"]
    turno_base = contexto["turno_ultimo"]

    if turno_base is None and turno_candidato is None:
        turnos_ultimo = None
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

            costo_anterior = costo_celda(
                cantidad_actual,
                tipo_congestion,
                factor_congestion
            )

            costo_nuevo = costo_celda(
                cantidad_actual + 1,
                tipo_congestion,
                factor_congestion
            )

            costo_turno += costo_nuevo - costo_anterior

        costo_total += costo_turno

    progreso_promedio = (
        contexto["progreso_total"] + traza["progreso"]
    ) / contexto["n_agentes"]

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


def evaluar_poblacion(
    poblacion,
    indice_agente,
    mejores,
    grid,
    spawns,
    salida,
    fuego_por_turno,
    tipo_congestion,
    factor_congestion,
    trazas_mejores=None,
    distancias_salida=None
):
    if len(mejores) != len(spawns):
        raise ValueError("Debe existir un mejor individuo por agente.")

    largo = len(mejores[0])

    if distancias_salida is None:
        distancias_salida = calcular_distancias_salida(grid, salida)

    if trazas_mejores is None:
        trazas_mejores = [
            simular_agente(
                mejores[i],
                grid,
                spawns[i],
                salida,
                fuego_por_turno,
                distancias_salida
            )
            for i in range(len(spawns))
        ]

    contexto = construir_contexto_base(
        trazas_mejores,
        indice_agente,
        largo,
        tipo_congestion,
        factor_congestion
    )

    fitnesses = []
    cache = {}

    for candidato in poblacion:
        clave = tuple(candidato)

        if clave not in cache:
            traza = simular_agente(
                candidato,
                grid,
                spawns[indice_agente],
                salida,
                fuego_por_turno,
                distancias_salida
            )

            resultado = evaluar_traza_con_contexto(
                traza,
                contexto,
                largo,
                tipo_congestion,
                factor_congestion
            )

            cache[clave] = fitness(resultado)

        fitnesses.append(cache[clave])

    return fitnesses