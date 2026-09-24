from collections import defaultdict
import math


def promedio(valores):
    if not valores:
        return 0.0

    return sum(valores) / len(valores)


def desviacion_estandar(valores):
    if len(valores) < 2:
        return 0.0

    media = promedio(valores)
    suma = sum((valor - media) ** 2 for valor in valores)

    return math.sqrt(suma / (len(valores) - 1))


def minimo(valores):
    if not valores:
        return None

    return min(valores)


def maximo(valores):
    if not valores:
        return None

    return max(valores)


def resumir_resultados(resultados):
    grupos = defaultdict(list)

    for resultado in resultados:
        clave = (resultado["mapa"], resultado["algoritmo"])
        grupos[clave].append(resultado)

    resumen = []

    for (mapa, algoritmo), grupo in grupos.items():
        evacuados = [r["evacuados"] for r in grupo]
        muertos = [r["muertos"] for r in grupo]
        turnos = [r["turnos_ultimo"] for r in grupo if r["turnos_ultimo"] is not None]
        congestion = [r["costo_congestion"] for r in grupo]
        tiempos = [r["tiempo_algoritmo_seg"] for r in grupo]

        tasas_supervivencia = [
            r["evacuados"] / r["n_agentes"]
            for r in grupo
            if r["n_agentes"] > 0
        ]

        turnos_promedio = promedio(turnos) if turnos else None
        turnos_std = desviacion_estandar(turnos) if turnos else None

        resumen.append({
            "mapa": mapa,
            "algoritmo": algoritmo,
            "n": len(grupo),

            "tasa_supervivencia_promedio": promedio(tasas_supervivencia),
            "tasa_supervivencia_std": desviacion_estandar(tasas_supervivencia),

            "evacuados_promedio": promedio(evacuados),
            "evacuados_std": desviacion_estandar(evacuados),

            "muertos_promedio": promedio(muertos),
            "muertos_std": desviacion_estandar(muertos),

            "turnos_promedio": turnos_promedio,
            "turnos_std": turnos_std,
            "turnos_min": minimo(turnos),
            "turnos_max": maximo(turnos),

            "ejecuciones_con_evacuados": len(turnos),
            "ejecuciones_sin_evacuados": len(grupo) - len(turnos),

            "congestion_promedio": promedio(congestion),
            "congestion_std": desviacion_estandar(congestion),

            "tiempo_algoritmo_promedio": promedio(tiempos),
            "tiempo_algoritmo_std": desviacion_estandar(tiempos),
        })

    return resumen