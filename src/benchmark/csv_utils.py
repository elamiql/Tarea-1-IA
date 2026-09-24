import csv
import os
from pathlib import Path


CAMPOS_RESULTADO = [
    "mapa",
    "algoritmo",
    "seed",
    "ancho",
    "alto",
    "n_spawns",
    "turno_quema_salida",
    "max_turnos",
    "evacuados",
    "muertos",
    "n_agentes",
    "turnos_ultimo",
    "costo_congestion",
    "tiempo_algoritmo_seg",
    "tiempo_total_seg",
]


CAMPOS_RESUMEN = [
    "mapa",
    "algoritmo",
    "n",
    "tasa_supervivencia_promedio",
    "tasa_supervivencia_std",
    "evacuados_promedio",
    "evacuados_std",
    "muertos_promedio",
    "muertos_std",
    "turnos_promedio",
    "turnos_std",
    "turnos_min",
    "turnos_max",
    "ejecuciones_con_evacuados",
    "ejecuciones_sin_evacuados",
    "congestion_promedio",
    "congestion_std",
    "tiempo_algoritmo_promedio",
    "tiempo_algoritmo_std",
]


def cargar_resultados_csv(path):
    resultados = []

    with open(path, newline="", encoding="utf-8-sig") as archivo:
        reader = csv.DictReader(archivo)

        for fila_original in reader:
            fila = {
                clave.strip(): valor.strip() if valor is not None else ""
                for clave, valor in fila_original.items()
            }

            resultados.append({
                "mapa": fila["mapa"],
                "algoritmo": fila["algoritmo"],
                "seed": int(fila["seed"]),
                "ancho": int(fila["ancho"]),
                "alto": int(fila["alto"]),
                "n_spawns": int(fila["n_spawns"]),
                "turno_quema_salida": int(fila["turno_quema_salida"]),
                "max_turnos": int(fila["max_turnos"]),
                "evacuados": int(fila["evacuados"]),
                "muertos": int(fila["muertos"]),
                "n_agentes": int(fila["n_agentes"]),
                "turnos_ultimo": int(fila["turnos_ultimo"]) if fila["turnos_ultimo"] else None,
                "costo_congestion": float(fila["costo_congestion"]),
                "tiempo_algoritmo_seg": float(fila["tiempo_algoritmo_seg"]),
                "tiempo_total_seg": float(fila["tiempo_total_seg"]),
            })

    return resultados


def cargar_claves_completadas(path):
    path = Path(path)

    if not path.exists() or path.stat().st_size == 0:
        return set()

    resultados = cargar_resultados_csv(path)

    return {
        (resultado["mapa"], resultado["algoritmo"], resultado["seed"])
        for resultado in resultados
    }


def guardar_resultado_incremental(resultado, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    escribir_header = not path.exists() or path.stat().st_size == 0

    with open(path, "a", newline="", encoding="utf-8") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=CAMPOS_RESULTADO)

        if escribir_header:
            writer.writeheader()

        fila = {campo: resultado.get(campo) for campo in CAMPOS_RESULTADO}
        writer.writerow(fila)

        archivo.flush()
        os.fsync(archivo.fileno())


def guardar_resumen_csv(resumen, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", newline="", encoding="utf-8") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=CAMPOS_RESUMEN)
        writer.writeheader()

        for resultado in resumen:
            fila = {campo: resultado.get(campo) for campo in CAMPOS_RESUMEN}
            writer.writerow(fila)