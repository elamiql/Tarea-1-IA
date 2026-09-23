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

def resumir_resultados(resultados):
    grupos = defaultdict(list)

    for resultado in resultados:
        clave = (resultado["mapa"], resultado["algoritmo"])

        grupos[clave].append(resultado)

    resumen = []

    for (mapa, algoritmo), grupo in grupos.items():
        evacuados = [r["evacuados"] for r in grupo]

        muertos = [r["muertos"] for r in grupo]

        turnos = [
            r["turnos_ultimo"] for r in grupo]

        congestion = [r["costo_congestion"] for r in grupo]

        tiempos = [r["tiempo_algoritmo_seg"] for r in grupo]

        n_agentes = grupo[0]["n_agentes"]

        tasa_evacuacion = [r["evacuados"] / n_agentes for r in grupo]

        resumen.append({
            "mapa": mapa,
            "algoritmo": algoritmo,
            "n": len(grupo),
            "evacuados_promedio": promedio(evacuados),
            "evacuados_std": desviacion_estandar(evacuados),
            "muertos_promedio": promedio(muertos),
            "turnos_promedio": promedio(turnos),
            "turnos_std": desviacion_estandar(turnos),
            "congestion_promedio": promedio(congestion),
            "congestion_std": desviacion_estandar(congestion),
            "tiempo_algoritmo_promedio": promedio(tiempos),
            "tiempo_algoritmo_std": desviacion_estandar(tiempos),
            "tasa_evacuacion_promedio": promedio(
                tasa_evacuacion
            ),
        })

    return resumen