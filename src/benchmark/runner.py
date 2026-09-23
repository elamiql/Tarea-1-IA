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


def elegir_origen_fuego(grid, salida, rng):
    """Celda libre lejos de la salida, para que el incendio no nazca pegado a la puerta."""
    alto, ancho = grid.shape
    libres = [(x, y) for y in range(alto) for x in range(ancho)
              if grid[y, x] == 0 and (x, y) != salida]
    libres.sort(key=lambda c: abs(c[0] - salida[0]) + abs(c[1] - salida[1]), reverse=True)
    top = libres[:max(1, len(libres) // 3)]
    return top[int(rng.integers(len(top)))]


def correr_una_iteracion(tipo_mapa, nombre_algo, seed, ancho=30, alto=30, n_spawns=20,
                          max_turnos=150, k_fuego=5, largo_genetico=60,
                          generaciones_genetico=100, tam_poblacion_genetico=40):
    rng = np.random.default_rng(seed)

    grid, salida, spawns = generar_mapa(tipo_mapa, ancho=ancho, alto=alto,
                                         n_spawns=n_spawns, seed=seed)
    origen_fuego = elegir_origen_fuego(grid, salida, rng)

    if nombre_algo == "Genetico":
        fuego_por_turno = calcular_fuego_por_turno(grid, [origen_fuego], largo_genetico, k_fuego)
        _, resultado = algoritmo_genetico(
            grid, spawns, salida, fuego_por_turno, largo=largo_genetico,
            generaciones=generaciones_genetico, tam_poblacion=tam_poblacion_genetico, seed=seed
        )
    else:
        algo, usa_costo_fn = next((a, c) for n, a, c in ALGORITMOS_PATHFINDING if n == nombre_algo)
        resultado = simular(algo, grid, spawns, salida, [origen_fuego],
                             max_turnos, k_fuego, usa_costo_fn=usa_costo_fn)

    return dict(mapa=tipo_mapa, algoritmo=nombre_algo, seed=seed, **resultado)


def correr_benchmark(n_iteraciones=100, **kwargs):
    nombres_algo = [n for n, _, _ in ALGORITMOS_PATHFINDING] + ["Genetico"]
    resultados = []
    total = len(TIPOS_MAPA) * len(nombres_algo) * n_iteraciones
    contador = 0

    for tipo_mapa in TIPOS_MAPA:
        for nombre_algo in nombres_algo:
            for i in range(n_iteraciones):
                contador += 1
                t0 = time.time()
                r = correr_una_iteracion(tipo_mapa, nombre_algo, seed=i, **kwargs)
                r["tiempo_seg"] = time.time() - t0
                resultados.append(r)
                print(f"[{contador}/{total}] {tipo_mapa:15s} {nombre_algo:8s} "
                      f"seed={i:3d} sobrevivientes={r['sobrevivientes']}/{r['n_agentes']} "
                      f"turnos={r['turnos_ultimo']} costo_congestion={r['costo_congestion']:.1f} "
                      f"({r['tiempo_seg']:.2f}s)")

    return resultados


def guardar_csv(resultados, path):
    if not resultados:
        return
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=resultados[0].keys())
        writer.writeheader()
        writer.writerows(resultados)