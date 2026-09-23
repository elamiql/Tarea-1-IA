import csv
import time
import numpy as np

from src.mapas.map_generator import generar_mapa
from src.simulacion.entorno import simular
from src.simulacion.fuego import calcular_fuego_por_turno
from src.algoritmos.no_informada.bfs import BFS
from src.algoritmos.no_informada.dfs import DFS
from src.algoritmos.informada.a_star import A_star
from src.algoritmos.informada.greedy_best_first import greedy_best_first
from src.algoritmos.metaheuristico.genetico import algoritmo_genetico


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

    libres.sort(key=lambda c: abs(c[0] - salida[0]) + abs(c[1] - salida[1]), reverse=True)

    cantidad_top = max(1, len(libres) // 3)
    top = libres[:cantidad_top]

    return top[int(rng.integers(len(top)))]


def correr_una_iteracion(tipo_mapa, nombre_algo, seed, ancho=50, alto=50, n_spawns=20,
                          max_turnos=150, k_fuego=5, largo_genetico=None,
                          generaciones_genetico=100, tam_poblacion_genetico=40,
                          prob_mutacion_genetico=0.02):

    rng = np.random.default_rng(seed)

    grid, salida, spawns = generar_mapa(
        tipo_mapa,
        ancho=ancho,
        alto=alto,
        n_spawns=n_spawns,
        seed=seed
    )

    origen_fuego = elegir_origen_fuego(grid, salida, rng)

    inicio_algoritmo = time.perf_counter()

    if nombre_algo == "Genetico":
        if largo_genetico is None:
            largo_genetico = max_turnos

        fuego_por_turno = calcular_fuego_por_turno(grid, [origen_fuego], largo_genetico, k_fuego)

        _, resultado = algoritmo_genetico(
            grid,
            spawns,
            salida,
            fuego_por_turno,
            largo=largo_genetico,
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
        "max_turnos": max_turnos,
        "evacuados": resultado["evacuados"],
        "muertos": resultado["muertos"],
        "n_agentes": resultado["n_agentes"],
        "turnos_ultimo": resultado["turnos_ultimo"],
        "costo_congestion": resultado["costo_congestion"],
        "tiempo_algoritmo_seg": tiempo_algoritmo,
    }


def correr_benchmark(n_iteraciones=100, **kwargs):
    nombres_algoritmos = [nombre for nombre, _, _ in ALGORITMOS_PATHFINDING]
    nombres_algoritmos.append("Genetico")

    resultados = []

    total = len(TIPOS_MAPA) * len(nombres_algoritmos) * n_iteraciones
    contador = 0

    for tipo_mapa in TIPOS_MAPA:
        for nombre_algo in nombres_algoritmos:
            for i in range(n_iteraciones):
                contador += 1

                inicio_total = time.perf_counter()

                resultado = correr_una_iteracion(tipo_mapa, nombre_algo, seed=i, **kwargs)

                tiempo_total = time.perf_counter() - inicio_total

                resultado["tiempo_total_seg"] = tiempo_total
                resultados.append(resultado)

                print(
                    f"[{contador}/{total}] "
                    f"{tipo_mapa:15s} "
                    f"{nombre_algo:8s} "
                    f"seed={i:3d} "
                    f"evacuados={resultado['evacuados']}/{resultado['n_agentes']} "
                    f"muertos={resultado['muertos']} "
                    f"turnos={resultado['turnos_ultimo']} "
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

            resultado = correr_una_iteracion(tipo_mapa, "Genetico", seed)

            resultados.append(resultado)

            print(
                f"[{contador}/{total}] "
                f"seed={seed:3d} "
                f"evacuados={resultado['evacuados']}/{resultado['n_agentes']} "
                f"muertos={resultado['muertos']} "
                f"turnos={resultado['turnos_ultimo']} "
                f"congestion={resultado['costo_congestion']:.1f} "
                f"tiempo={resultado['tiempo_algoritmo_seg']:.2f}s"
            )

        print()

    print("=== RESUMEN ===")

    for tipo_mapa in TIPOS_MAPA:
        datos = [resultado for resultado in resultados if resultado["mapa"] == tipo_mapa]

        promedio_evacuados = sum(resultado["evacuados"] for resultado in datos) / len(datos)
        promedio_muertos = sum(resultado["muertos"] for resultado in datos) / len(datos)
        promedio_turnos = sum(resultado["turnos_ultimo"] for resultado in datos) / len(datos)
        promedio_congestion = sum(resultado["costo_congestion"] for resultado in datos) / len(datos)
        promedio_tiempo = sum(resultado["tiempo_algoritmo_seg"] for resultado in datos) / len(datos)

        minimo_evacuados = min(resultado["evacuados"] for resultado in datos)
        maximo_evacuados = max(resultado["evacuados"] for resultado in datos)

        print(
            f"{tipo_mapa:15s} "
            f"evacuados={promedio_evacuados:.2f}/20 "
            f"rango=[{minimo_evacuados}, {maximo_evacuados}] "
            f"muertos={promedio_muertos:.2f} "
            f"turnos={promedio_turnos:.2f} "
            f"congestion={promedio_congestion:.2f} "
            f"tiempo={promedio_tiempo:.2f}s"
        )

    return resultados


def guardar_csv(resultados, path):
    if not resultados:
        return

    with open(path, "w", newline="") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=resultados[0].keys())
        writer.writeheader()
        writer.writerows(resultados)


if __name__ == "__main__":
    resultados = probar_genetico_seeds()