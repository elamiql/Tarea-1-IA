import csv
import time

import numpy as np

from src.mapas.map_generator import generar_mapa
from src.simulacion.entorno import simular
from src.simulacion.fuego import calcular_fuego_por_turno, calcular_turno_quema_salida
from src.algoritmos.no_informada.bfs import BFS
from src.algoritmos.no_informada.dfs import DFS
from src.algoritmos.informada.a_star import A_star
from src.algoritmos.informada.greedy_best_first import greedy_best_first
from src.algoritmos.metaheuristico.genetico import algoritmo_genetico
from src.benchmark.csv_utils import cargar_claves_completadas, guardar_resultado_incremental

# Configuracion oficial de los experimentos
ANCHO_MAPA = 50
ALTO_MAPA = 50
N_AGENTES = 45

K_FUEGO = 5

GENERACIONES_GENETICO = 100
TAM_POBLACION_GENETICO = 40
PROB_MUTACION_GENETICO = 0.02

N_ITERACIONES_BENCHMARK = 100

ALGORITMOS_PATHFINDING = [
    ("BFS", BFS, False),
    ("DFS", DFS, False),
    ("A*", A_star, True),
    ("Greedy", greedy_best_first, False),
]

TIPOS_MAPA = ["cuello_botella", "laberinto", "abierto"]

SEEDS_PRUEBA = [7, 19, 42, 73, 91]


def elegir_origen_fuego(grid, salida, rng):
    """Celda libre lejos de la salida, para que el incendio no nazca pegado a la puerta."""
    alto, ancho = grid.shape

    libres = [
        (x, y)
        for y in range(alto)
        for x in range(ancho)
        if grid[y, x] == 0 and (x, y) != salida
    ]

    if not libres:
        raise ValueError("No existen celdas libres para colocar fuego")

    libres.sort(
        key=lambda c: abs(c[0] - salida[0]) + abs(c[1] - salida[1]),
        reverse=True
    )

    cantidad_top = max(1, len(libres) // 3)
    top = libres[:cantidad_top]

    return top[int(rng.integers(len(top)))]


def correr_una_iteracion(
    tipo_mapa,
    nombre_algo,
    seed,
    ancho=ANCHO_MAPA,
    alto=ALTO_MAPA,
    n_spawns=N_AGENTES,
    k_fuego=K_FUEGO,
    generaciones_genetico=GENERACIONES_GENETICO,
    tam_poblacion_genetico=TAM_POBLACION_GENETICO,
    prob_mutacion_genetico=PROB_MUTACION_GENETICO):

    rng = np.random.default_rng(seed)

    grid, salida, spawns = generar_mapa(
        tipo_mapa,
        ancho=ancho,
        alto=alto,
        n_spawns=n_spawns,
        seed=seed
    )

    origen_fuego = elegir_origen_fuego(grid, salida, rng)

    turno_quema_salida = calcular_turno_quema_salida(
        grid,
        [origen_fuego],
        salida,
        k_fuego
    )

    if turno_quema_salida is None:
        raise RuntimeError(
            f"El fuego no puede alcanzar la salida en "
            f"mapa={tipo_mapa}, seed={seed}"
        )

    # +1 porque range(max_turnos) no incluye el extremo.
    # Si la salida se quema en t=185, necesitamos simular 0..185.
    max_turnos = turno_quema_salida + 1

    inicio_algoritmo = time.perf_counter()

    if nombre_algo == "Genetico":
        fuego_por_turno = calcular_fuego_por_turno(
            grid,
            [origen_fuego],
            max_turnos,
            k_fuego
        )

        _, resultado = algoritmo_genetico(
            grid,
            spawns,
            salida,
            fuego_por_turno,
            largo=max_turnos,
            generaciones=generaciones_genetico,
            tam_poblacion=tam_poblacion_genetico,
            prob_mutacion=prob_mutacion_genetico,
            seed=seed
        )

    else:
        algoritmo, usa_costo_fn = next(
            (algoritmo, usa_costo_fn)
            for nombre, algoritmo, usa_costo_fn in ALGORITMOS_PATHFINDING
            if nombre == nombre_algo
        )

        resultado = simular(
            algoritmo,
            grid,
            spawns,
            salida,
            [origen_fuego],
            max_turnos,
            k_fuego,
            usa_costo_fn=usa_costo_fn
        )

    tiempo_algoritmo = time.perf_counter() - inicio_algoritmo

    return {
        "mapa": tipo_mapa,
        "algoritmo": nombre_algo,
        "seed": seed,
        "ancho": ancho,
        "alto": alto,
        "n_spawns": n_spawns,
        "turno_quema_salida": turno_quema_salida,
        "max_turnos": max_turnos,
        "evacuados": resultado["evacuados"],
        "muertos": resultado["muertos"],
        "n_agentes": resultado["n_agentes"],
        "turnos_ultimo": resultado["turnos_ultimo"],
        "costo_congestion": resultado["costo_congestion"],
        "tiempo_algoritmo_seg": tiempo_algoritmo,
    }

def correr_benchmark(n_iteraciones=N_ITERACIONES_BENCHMARK, path_csv=None, **kwargs):
    nombres_algoritmos = [nombre for nombre, _, _ in ALGORITMOS_PATHFINDING]
    nombres_algoritmos.append("Genetico")

    resultados = []

    if path_csv is not None:
        completadas = cargar_claves_completadas(path_csv)
    else:
        completadas = set()

    total = len(TIPOS_MAPA) * len(nombres_algoritmos) * n_iteraciones
    contador = 0

    for tipo_mapa in TIPOS_MAPA:
        for nombre_algo in nombres_algoritmos:
            for seed in range(n_iteraciones):
                contador += 1
                clave = (tipo_mapa, nombre_algo, seed)

                if clave in completadas:
                    print(
                        f"[{contador}/{total}] "
                        f"{tipo_mapa:15s} "
                        f"{nombre_algo:8s} "
                        f"seed={seed:3d} "
                        f"YA COMPLETADO"
                    )
                    continue

                inicio_total = time.perf_counter()

                resultado = correr_una_iteracion(tipo_mapa, nombre_algo, seed=seed, **kwargs)

                tiempo_total = time.perf_counter() - inicio_total
                resultado["tiempo_total_seg"] = tiempo_total

                resultados.append(resultado)

                if path_csv is not None:
                    guardar_resultado_incremental(resultado, path_csv)
                    completadas.add(clave)

                print(
                    f"[{contador}/{total}] "
                    f"{tipo_mapa:15s} "
                    f"{nombre_algo:8s} "
                    f"seed={seed:3d} "
                    f"evacuados={resultado['evacuados']}/{resultado['n_agentes']} "
                    f"muertos={resultado['muertos']} "
                    f"turnos={resultado['turnos_ultimo']} "
                    f"quema_salida={resultado['turno_quema_salida']} "
                    f"congestion={resultado['costo_congestion']:.1f} "
                    f"alg={resultado['tiempo_algoritmo_seg']:.2f}s "
                    f"total={resultado['tiempo_total_seg']:.2f}s"
                )

    return resultados

def probar_genetico_seeds(seeds=None):
    if seeds is None:
        seeds = SEEDS_PRUEBA

    resultados = []

    total = len(TIPOS_MAPA) * len(seeds)
    contador = 0

    print("\nPRUEBA GENETICO - MULTIPLES SEEDS")
    print(f"Seeds: {seeds}")
    print(f"Total ejecuciones: {total}\n")

    for tipo_mapa in TIPOS_MAPA:
        print(f"=== {tipo_mapa.upper()} ===")

        for seed in seeds:
            contador += 1

            resultado = correr_una_iteracion(
                tipo_mapa,
                "Genetico",
                seed
            )

            resultados.append(resultado)

            print(
                f"[{contador}/{total}] "
                f"seed={seed:3d} "
                f"evacuados={resultado['evacuados']}/{resultado['n_agentes']} "
                f"muertos={resultado['muertos']} "
                f"turnos={resultado['turnos_ultimo']} "
                f"quema_salida={resultado['turno_quema_salida']} "
                f"congestion={resultado['costo_congestion']:.1f} "
                f"tiempo={resultado['tiempo_algoritmo_seg']:.2f}s"
            )

        print()

    print("=== RESUMEN ===")

    for tipo_mapa in TIPOS_MAPA:
        datos = [
            resultado
            for resultado in resultados
            if resultado["mapa"] == tipo_mapa
        ]

        promedio_evacuados = sum(
            resultado["evacuados"]
            for resultado in datos
        ) / len(datos)

        promedio_muertos = sum(
            resultado["muertos"]
            for resultado in datos
        ) / len(datos)

        turnos_validos = [
            resultado["turnos_ultimo"]
            for resultado in datos
            if resultado["turnos_ultimo"] is not None
        ]

        if turnos_validos:
            promedio_turnos = sum(turnos_validos) / len(turnos_validos)
            texto_turnos = f"{promedio_turnos:.2f}"
        else:
            promedio_turnos = None
            texto_turnos = "N/A"

        promedio_congestion = sum(
            resultado["costo_congestion"]
            for resultado in datos
        ) / len(datos)

        promedio_tiempo = sum(
            resultado["tiempo_algoritmo_seg"]
            for resultado in datos
        ) / len(datos)

        minimo_evacuados = min(
            resultado["evacuados"]
            for resultado in datos
        )

        maximo_evacuados = max(
            resultado["evacuados"]
            for resultado in datos
        )

        print(
            f"{tipo_mapa:15s} "
            f"evacuados={promedio_evacuados:.2f}/20 "
            f"rango=[{minimo_evacuados}, {maximo_evacuados}] "
            f"muertos={promedio_muertos:.2f} "
            f"turnos={texto_turnos} "
            f"congestion={promedio_congestion:.2f} "
            f"tiempo={promedio_tiempo:.2f}s"
        )

    return resultados


def guardar_csv(resultados, path):
    if not resultados:
        return

    with open(path, "w", newline="") as archivo:
        writer = csv.DictWriter(
            archivo,
            fieldnames=resultados[0].keys()
        )
        writer.writeheader()
        writer.writerows(resultados)


if __name__ == "__main__":
    resultados = probar_genetico_seeds()