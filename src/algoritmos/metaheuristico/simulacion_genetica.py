from collections import deque

import numpy as np

from ...simulacion.congestion import costo_congestion_turno
from .constantes import MOVIMIENTOS


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

            if (
                0 <= nx < ancho
                and 0 <= ny < alto
                and grid[ny, nx] == 0
                and distancias[ny, nx] == -1
            ):
                distancias[ny, nx] = distancias[y, x] + 1
                cola.append((nx, ny))

    return distancias


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

        if (
            0 <= nx < ancho
            and 0 <= ny < alto
            and grid[ny, nx] == 0
            and (nx, ny) not in quemado
        ):
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

    turnos_validos = [
        traza["turno_evacuacion"]
        for traza in trazas
        if traza["turno_evacuacion"] is not None
    ]

    if turnos_validos:
        turnos_ultimo = max(turnos_validos)
    else:
        turnos_ultimo = None

    costo_total = 0.0

    for t in range(largo):
        ocupacion = {}

        for traza in trazas:
            pos = traza["ocupacion"][t]

            if pos is not None:
                ocupacion[pos] = ocupacion.get(pos, 0) + 1

        costo_total += costo_congestion_turno(
            ocupacion,
            tipo_congestion,
            factor_congestion
        )

    if trazas:
        progreso_promedio = (
            sum(traza["progreso"] for traza in trazas) / len(trazas)
        )
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


def simular_grupo(
    plan_conjunto,
    grid,
    spawns,
    salida,
    fuego_por_turno,
    tipo_congestion="cuadratico",
    factor_congestion=1.0,
    distancias_salida=None
):
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
        simular_agente(
            plan_conjunto[i],
            grid,
            spawns[i],
            salida,
            fuego_por_turno,
            distancias_salida
        )
        for i in range(n_agentes)
    ]

    return combinar_trazas(
        trazas,
        largo,
        tipo_congestion,
        factor_congestion
    )