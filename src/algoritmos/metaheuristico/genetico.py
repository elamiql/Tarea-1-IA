import numpy as np

from .constantes import MOVIMIENTOS
from .operadores import (generar_secuencia, cruza_secuencia, mutar_secuencia, seleccion_torneo)
from .simulacion_genetica import (calcular_distancias_salida, simular_agente, combinar_trazas, simular_grupo)
from .evaluacion import (fitness, construir_contexto_base, evaluar_traza_con_contexto, evaluar_poblacion)


__all__ = [
    "MOVIMIENTOS",
    "calcular_distancias_salida",
    "generar_secuencia",
    "cruza_secuencia",
    "mutar_secuencia",
    "seleccion_torneo",
    "simular_agente",
    "combinar_trazas",
    "simular_grupo",
    "fitness",
    "construir_contexto_base",
    "evaluar_traza_con_contexto",
    "evaluar_poblacion",
    "algoritmo_genetico",
]


def algoritmo_genetico(
    grid,
    spawns,
    salida,
    fuego_por_turno,
    largo,
    generaciones=50,
    tam_poblacion=20,
    prob_mutacion=0.1,
    k_torneo=3,
    elitismo=True,
    tipo_congestion="cuadratico",
    factor_congestion=1.0,
    seed=None
):
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
        return [], simular_grupo(
            [],
            grid,
            [],
            salida,
            fuego_por_turno,
            tipo_congestion,
            factor_congestion
        )

    poblaciones = [
        [
            generar_secuencia(largo, rng)
            for _ in range(tam_poblacion)
        ]
        for _ in range(n_agentes)
    ]

    mejores = [
        list(poblaciones[i][0])
        for i in range(n_agentes)
    ]

    trazas_mejores = [
        simular_agente(
            mejores[i],
            grid,
            spawns[i],
            salida,
            fuego_por_turno,
            distancias_salida
        )
        for i in range(n_agentes)
    ]

    for _ in range(generaciones):
        for i in range(n_agentes):
            poblacion_actual = poblaciones[i]

            fitnesses = evaluar_poblacion(
                poblacion_actual,
                i,
                mejores,
                grid,
                spawns,
                salida,
                fuego_por_turno,
                tipo_congestion,
                factor_congestion,
                trazas_mejores,
                distancias_salida
            )

            mejor_idx = max(
                range(tam_poblacion),
                key=lambda j: fitnesses[j]
            )

            mejor_individuo = list(
                poblacion_actual[mejor_idx]
            )

            nueva_poblacion = []

            if elitismo:
                nueva_poblacion.append(
                    list(mejor_individuo)
                )

            while len(nueva_poblacion) < tam_poblacion:
                padre1 = seleccion_torneo(
                    poblacion_actual,
                    fitnesses,
                    k_torneo,
                    rng
                )

                padre2 = seleccion_torneo(
                    poblacion_actual,
                    fitnesses,
                    k_torneo,
                    rng
                )

                hijo = cruza_secuencia(
                    padre1,
                    padre2,
                    rng
                )

                mutar_secuencia(
                    hijo,
                    prob_mutacion,
                    rng
                )

                nueva_poblacion.append(hijo)

            poblaciones[i] = nueva_poblacion
            mejores[i] = mejor_individuo

            trazas_mejores[i] = simular_agente(
                mejor_individuo,
                grid,
                spawns[i],
                salida,
                fuego_por_turno,
                distancias_salida
            )

    for i in range(n_agentes):
        poblacion_actual = poblaciones[i]

        fitnesses = evaluar_poblacion(
            poblacion_actual,
            i,
            mejores,
            grid,
            spawns,
            salida,
            fuego_por_turno,
            tipo_congestion,
            factor_congestion,
            trazas_mejores,
            distancias_salida
        )

        mejor_idx = max(
            range(tam_poblacion),
            key=lambda j: fitnesses[j]
        )

        mejores[i] = list(
            poblacion_actual[mejor_idx]
        )

        trazas_mejores[i] = simular_agente(
            mejores[i],
            grid,
            spawns[i],
            salida,
            fuego_por_turno,
            distancias_salida
        )

    resultado_final = simular_grupo(
        mejores,
        grid,
        spawns,
        salida,
        fuego_por_turno,
        tipo_congestion,
        factor_congestion,
        distancias_salida
    )

    return mejores, resultado_final