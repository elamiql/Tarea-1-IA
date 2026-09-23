from .constantes import MOVIMIENTOS


def generar_secuencia(largo, rng):
    if largo <= 0:
        raise ValueError("largo debe ser mayor que 0.")

    indices = rng.integers(0, len(MOVIMIENTOS), size=largo)

    return [MOVIMIENTOS[i] for i in indices]


def cruza_secuencia(p1, p2, rng):
    if len(p1) != len(p2):
        raise ValueError("Los padres deben tener el mismo largo.")

    largo = len(p1)

    if largo < 2:
        return list(p1)

    punto = int(rng.integers(1, largo))

    return p1[:punto] + p2[punto:]


def mutar_secuencia(secuencia, prob_mutacion, rng):
    if not 0 <= prob_mutacion <= 1:
        raise ValueError("prob_mutacion debe estar entre 0 y 1.")

    for t in range(len(secuencia)):
        if rng.random() < prob_mutacion:
            secuencia[t] = MOVIMIENTOS[int(rng.integers(len(MOVIMIENTOS)))]


def seleccion_torneo(poblacion, fitnesses, k, rng):
    if len(poblacion) != len(fitnesses):
        raise ValueError("poblacion y fitnesses deben tener el mismo largo.")

    if len(poblacion) == 0:
        raise ValueError("La poblacion no puede estar vacia.")

    if k <= 0:
        raise ValueError("k debe ser mayor que 0.")

    participantes = rng.choice(
        len(poblacion),
        size=min(k, len(poblacion)),
        replace=False
    )

    mejor_idx = max(participantes, key=lambda i: fitnesses[i])

    return poblacion[mejor_idx]