import numpy as np

from src.mapas.map_generator import generar_mapa
from src.benchmark.runner import elegir_origen_fuego, K_FUEGO
from src.simulacion.fuego import calcular_turno_quema_salida
from src.algoritmos.no_informada.bfs import BFS
from src.visualizacion.visualizador_simulacion import VisualizadorSimulacion


seed = 42
tipo_mapa = "abierto"

rng = np.random.default_rng(seed)

grid, salida, spawns = generar_mapa(tipo_mapa, ancho=50, alto=50, n_spawns=20, seed=seed)

origen_fuego = elegir_origen_fuego(grid, salida, rng)

turno_quema_salida = calcular_turno_quema_salida(grid, [origen_fuego], salida, K_FUEGO)
max_turnos = turno_quema_salida + 1

visualizador = VisualizadorSimulacion(grid, spawns, salida, [origen_fuego], max_turnos, K_FUEGO, n_snapshots=8)

visualizador.generar_historial(BFS)
visualizador.mostrar("BFS · Mapa abierto · Seed 42")