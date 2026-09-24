import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from src.benchmark.metricas import resumir_resultados
from src.benchmark.csv_utils import cargar_resultados_csv


ALGORITMOS = ["BFS", "DFS", "A*", "Greedy", "Genetico"]
MAPAS = ["cuello_botella", "laberinto", "abierto"]

NOMBRES_MAPAS = {
    "cuello_botella": "Cuello de botella",
    "laberinto": "Laberinto",
    "abierto": "Abierto",
}


def indexar_resumen(resumen):
    return {(r["mapa"], r["algoritmo"]): r for r in resumen}


def configurar_eje(ax, titulo, ylabel):
    ax.set_title(titulo)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Algoritmo")
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)


def guardar_figura(fig, carpeta, nombre):
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)

    path = carpeta / nombre

    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)

    print(f"Guardado: {path}")


def grafico_supervivencia(resumen, carpeta):
    datos = indexar_resumen(resumen)

    x = np.arange(len(ALGORITMOS))
    ancho = 0.25

    fig, ax = plt.subplots(figsize=(10, 6))

    for i, mapa in enumerate(MAPAS):
        valores = [
            datos[(mapa, algoritmo)]["tasa_supervivencia_promedio"] * 100
            for algoritmo in ALGORITMOS
        ]

        desplazamiento = (i - 1) * ancho

        ax.bar(x + desplazamiento, valores, ancho, label=NOMBRES_MAPAS[mapa])

    configurar_eje(ax, "Tasa de supervivencia por algoritmo y tipo de mapa", "Supervivencia promedio (%)")

    ax.set_xticks(x)
    ax.set_xticklabels(ALGORITMOS)
    ax.set_ylim(0, 100)
    ax.legend()

    guardar_figura(fig, carpeta, "supervivencia.png")


def grafico_turnos(resumen, carpeta):
    datos = indexar_resumen(resumen)

    x = np.arange(len(ALGORITMOS))
    ancho = 0.25

    fig, ax = plt.subplots(figsize=(10, 6))

    for i, mapa in enumerate(MAPAS):
        promedios = []

        for algoritmo in ALGORITMOS:
            resultado = datos[(mapa, algoritmo)]

            promedio_turnos = resultado["turnos_promedio"]
            desviacion_turnos = resultado["turnos_std"]

            promedios.append(np.nan if promedio_turnos is None else promedio_turnos)

        desplazamiento = (i - 1) * ancho

        ax.bar(x + desplazamiento, promedios, ancho, label=NOMBRES_MAPAS[mapa])

    configurar_eje(
        ax,
        "Tiempo de evacuación por algoritmo y tipo de mapa",
        "Turnos hasta el último sobreviviente"
    )

    ax.set_xticks(x)
    ax.set_xticklabels(ALGORITMOS)
    ax.set_ylim(bottom=0)
    ax.legend()

    fig.text(
        0.5,
        0.01,
        "Solo se consideran ejecuciones en las que al menos un agente logró evacuar.",
        ha="center",
        fontsize=9
    )

    guardar_figura(fig, carpeta, "turnos_evacuacion.png")


def grafico_congestion(resumen, carpeta):
    datos = indexar_resumen(resumen)

    x = np.arange(len(ALGORITMOS))
    ancho = 0.25

    fig, ax = plt.subplots(figsize=(10, 6))

    for i, mapa in enumerate(MAPAS):
        promedios = [
            datos[(mapa, algoritmo)]["congestion_promedio"]
            for algoritmo in ALGORITMOS
        ]

        desplazamiento = (i - 1) * ancho

        ax.bar(x + desplazamiento, promedios, ancho, label=NOMBRES_MAPAS[mapa])

    configurar_eje(
        ax,
        "Congestión acumulada por algoritmo y tipo de mapa",
        "Costo de congestión"
    )

    ax.set_xticks(x)
    ax.set_xticklabels(ALGORITMOS)
    ax.set_ylim(bottom=0)
    ax.legend()

    guardar_figura(fig, carpeta, "congestion.png")


def generar_graficos(path_csv, carpeta="graficos"):
    resultados = cargar_resultados_csv(path_csv)
    resumen = resumir_resultados(resultados)

    grafico_supervivencia(resumen, carpeta)
    grafico_turnos(resumen, carpeta)
    grafico_congestion(resumen, carpeta)

    print("\nGráficos generados correctamente.")


if __name__ == "__main__":
    generar_graficos("benchmark_prueba.csv")