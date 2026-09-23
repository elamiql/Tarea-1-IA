from src.benchmark.runner import correr_benchmark, guardar_csv


if __name__ == "__main__":
    resultados = correr_benchmark(n_iteraciones=1)
    guardar_csv(resultados, "resultados/raw/prueba.csv")