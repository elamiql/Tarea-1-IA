def costo_celda(n_agentes, tipo="cuadratico", factor=1.0):
    """
    Costo de congestión de UNA celda según cuántos agentes la ocupan
    simultáneamente. Sin penalización si es 0 o 1 agente (tráfico normal);
    el costo crece con el EXCESO de agentes (n_agentes - 1).
    """
    if n_agentes <= 1:
        return 0.0

    exceso = n_agentes - 1
    if tipo == "lineal":
        return factor * exceso
    elif tipo == "cuadratico":
        return factor * (exceso ** 2)
    elif tipo == "exponencial":
        return factor * (2 ** exceso - 1)
    else:
        raise ValueError(f"tipo debe ser 'lineal', 'cuadratico' o 'exponencial', llegó '{tipo}'")


def costo_congestion_turno(ocupacion, tipo="cuadratico", factor=1.0):
    """
    ocupacion: dict {celda: n_agentes_en_esa_celda_este_turno}
    Devuelve el costo total de congestión de ese turno (suma sobre todas las celdas).
    """
    return sum(costo_celda(n, tipo, factor) for n in ocupacion.values())