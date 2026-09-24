import sys

from src.benchmark.csv_utils import cargar_resultados_csv, guardar_resumen_csv
from src.benchmark.graficos import generar_graficos
from src.benchmark.metricas import resumir_resultados
from src.benchmark.runner import correr_benchmark


def main():
    if len(sys.argv) < 3:
        print("Uso:")
        print("python ejecutar_benchmark.py <iteraciones> <nombre>")
        print()
        print("Ejemplo:")
        print("python ejecutar_benchmark.py 5 smoke")
        return

    n_iteraciones = int(sys.argv[1])
    nombre = sys.argv[2]

    path_raw = f"resultados/{nombre}.csv"
    path_resumen = f"resultados/{nombre}_resumen.csv"
    carpeta_graficos = f"graficos/{nombre}"

    print(f"Iteraciones por combinación: {n_iteraciones}")
    print(f"CSV crudo: {path_raw}")
    print(f"CSV procesado: {path_resumen}")
    print()

    correr_benchmark(n_iteraciones=n_iteraciones, path_csv=path_raw)

    resultados = cargar_resultados_csv(path_raw)
    resumen = resumir_resultados(resultados)

    guardar_resumen_csv(resumen, path_resumen)
    generar_graficos(path_raw, carpeta_graficos)

    print()
    print("Benchmark completado.")
    print(f"Resultados crudos: {path_raw}")
    print(f"Resumen procesado: {path_resumen}")
    print(f"Graficos: {carpeta_graficos}")


if __name__ == "__main__":
    main()