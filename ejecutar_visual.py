import argparse
import sys
from pathlib import Path

import numpy as np

from src.algoritmos.informada.a_star import A_star
from src.algoritmos.informada.greedy_best_first import greedy_best_first
from src.algoritmos.metaheuristico.genetico import algoritmo_genetico
from src.algoritmos.no_informada.bfs import BFS
from src.algoritmos.no_informada.dfs import DFS
from src.benchmark.runner import (
    ALTO_MAPA,
    ANCHO_MAPA,
    GENERACIONES_GENETICO,
    K_FUEGO,
    N_AGENTES,
    PROB_MUTACION_GENETICO,
    TAM_POBLACION_GENETICO,
    elegir_origen_fuego,
)
from src.mapas.map_generator import generar_mapa
from src.simulacion.fuego import calcular_fuego_por_turno, calcular_turno_quema_salida
from src.visualizacion.visualizador_simulacion import VisualizadorSimulacion


MAPAS = ("cuello_botella", "laberinto", "abierto")
ALGORITMOS = {
    "BFS": (BFS, False),
    "DFS": (DFS, False),
    "A*": (A_star, True),
    "Greedy": (greedy_best_first, False),
    "Genetico": (None, False),
}


def _elegir_opcion(etiqueta, opciones, predeterminado):
    print(f"\n{etiqueta}:")
    for indice, opcion in enumerate(opciones, start=1):
        marca = " (predeterminado)" if opcion == predeterminado else ""
        print(f"  {indice}. {opcion}{marca}")

    while True:
        respuesta = input("> ").strip()
        if not respuesta:
            return predeterminado
        if respuesta.isdigit() and 1 <= int(respuesta) <= len(opciones):
            return opciones[int(respuesta) - 1]
        if respuesta in opciones:
            return respuesta
        print("Opcion invalida; escribe el numero o el nombre exacto.")


def _leer_entero(etiqueta, predeterminado, minimo=0):
    while True:
        respuesta = input(f"{etiqueta} [{predeterminado}]: ").strip()
        if not respuesta:
            return predeterminado
        try:
            valor = int(respuesta)
        except ValueError:
            print("Debe ser un numero entero.")
            continue
        if valor < minimo:
            print(f"Debe ser mayor o igual que {minimo}.")
            continue
        return valor


def _completar_interactivo(args):
    selectores = (args.mapa, args.algoritmo, args.seed, args.agentes)
    if not sys.stdin.isatty() or any(valor is not None for valor in selectores):
        return args

    print("Modo visual de evacuacion")
    args.mapa = _elegir_opcion("Tipo de mapa", MAPAS, "abierto")
    args.algoritmo = _elegir_opcion("Algoritmo", tuple(ALGORITMOS), "BFS")
    args.seed = _leer_entero("Seed", 42)
    args.agentes = _leer_entero("Cantidad de agentes", N_AGENTES, minimo=1)
    return args


def construir_parser():
    parser = argparse.ArgumentParser(
        description="Ejecuta una simulacion y permite navegar 8 snapshots representativos."
    )
    parser.add_argument("--mapa", choices=MAPAS)
    parser.add_argument("--algoritmo", choices=tuple(ALGORITMOS))
    parser.add_argument("--seed", type=int)
    parser.add_argument("--agentes", type=int)
    parser.add_argument("--ancho", type=int, default=ANCHO_MAPA)
    parser.add_argument("--alto", type=int, default=ALTO_MAPA)
    parser.add_argument("--snapshots", type=int, default=8)
    parser.add_argument("--generaciones", type=int, default=GENERACIONES_GENETICO)
    parser.add_argument("--poblacion", type=int, default=TAM_POBLACION_GENETICO)
    parser.add_argument("--mutacion", type=float, default=PROB_MUTACION_GENETICO)
    parser.add_argument("--guardar", type=Path, help="Carpeta opcional donde guardar los PNG.")
    parser.add_argument("--exportar-gif", type=Path, help="Ruta opcional para exportar la animacion.")
    parser.add_argument("--fps", type=int, default=24, help="Cuadros por segundo del GIF.")
    parser.add_argument("--salto", type=int, default=1, help="Exporta uno de cada N turnos.")
    parser.add_argument("--no-mostrar", action="store_true", help="No abre la ventana; util para pruebas.")
    return parser


def ejecutar(args):
    tipo_mapa = args.mapa or "abierto"
    nombre_algoritmo = args.algoritmo or "BFS"
    seed = 42 if args.seed is None else args.seed
    n_agentes = N_AGENTES if args.agentes is None else args.agentes

    if n_agentes <= 0:
        raise ValueError("La cantidad de agentes debe ser mayor que 0.")
    if args.ancho < 10 or args.alto < 10:
        raise ValueError("El ancho y el alto deben ser al menos 10.")
    if args.snapshots <= 0:
        raise ValueError("La cantidad de snapshots debe ser mayor que 0.")
    if args.generaciones <= 0 or args.poblacion <= 0:
        raise ValueError("Generaciones y poblacion deben ser mayores que 0.")
    if not 0 <= args.mutacion <= 1:
        raise ValueError("La mutacion debe estar entre 0 y 1.")
    if args.fps <= 0 or args.salto <= 0:
        raise ValueError("fps y salto deben ser mayores que 0.")

    rng = np.random.default_rng(seed)
    grid, salida, spawns = generar_mapa(
        tipo_mapa,
        ancho=args.ancho,
        alto=args.alto,
        n_spawns=n_agentes,
        seed=seed,
    )
    origen_fuego = elegir_origen_fuego(grid, salida, rng)
    turno_quema_salida = calcular_turno_quema_salida(
        grid, [origen_fuego], salida, K_FUEGO
    )
    if turno_quema_salida is None:
        raise RuntimeError("El fuego no puede alcanzar la salida en el escenario generado.")

    max_turnos = turno_quema_salida + 1
    visualizador = VisualizadorSimulacion(
        grid,
        spawns,
        salida,
        [origen_fuego],
        max_turnos,
        K_FUEGO,
        n_snapshots=args.snapshots,
    )

    if nombre_algoritmo == "Genetico":
        fuego_por_turno = calcular_fuego_por_turno(
            grid, [origen_fuego], max_turnos, K_FUEGO
        )
        planes, _ = algoritmo_genetico(
            grid,
            spawns,
            salida,
            fuego_por_turno,
            largo=max_turnos,
            generaciones=args.generaciones,
            tam_poblacion=args.poblacion,
            prob_mutacion=args.mutacion,
            seed=seed,
        )
        snapshots = visualizador.generar_historial_genetico(planes)
    else:
        algoritmo, usa_costo_fn = ALGORITMOS[nombre_algoritmo]
        snapshots = visualizador.generar_historial(algoritmo, usa_costo_fn=usa_costo_fn)

    titulo = (
        f"{nombre_algoritmo} · {tipo_mapa} · Seed {seed} · "
        f"{n_agentes} agentes"
    )
    visualizador.titulo = titulo

    print(f"Mapa: {tipo_mapa}")
    print(f"Algoritmo: {nombre_algoritmo}")
    print(f"Seed: {seed}")
    print(f"Agentes: {n_agentes}")
    print(f"Horizonte: {max_turnos} turnos")
    print(f"Snapshots: {len(snapshots)} (turnos {[s['turno'] for s in snapshots]})")

    if args.guardar is not None:
        carpeta = visualizador.guardar_snapshots(args.guardar, prefijo="snapshot")
        print(f"Snapshots guardados en: {carpeta.resolve()}")

    if args.exportar_gif is not None:
        ruta_gif = visualizador.guardar_animacion(
            args.exportar_gif,
            fps=args.fps,
            salto=args.salto,
        )
        print(f"Animacion guardada en: {ruta_gif.resolve()}")

    if not args.no_mostrar:
        print("Controles: espacio=reproducir/pausar, flechas=navegar, M=cambiar vista.")
        visualizador.mostrar(titulo)

    return visualizador


def main():
    args = _completar_interactivo(construir_parser().parse_args())
    ejecutar(args)


if __name__ == "__main__":
    main()
