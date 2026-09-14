import numpy as np
import matplotlib.pyplot as plt


DIRECCIONES = [(1, 0), (-1, 0), (0, 1), (0, -1)]

# Parámetros por tipo de mapa
PARAMS_TIPO = {
    "cuello_botella": dict(n_iter=5, min_tam=4, margen_max=1, corredor_ancho=1, prob_pilar=0.05),
    "laberinto":       dict(n_iter=4, min_tam=5, margen_max=1, corredor_ancho=1, prob_pilar=0.15),
    "abierto":         dict(n_iter=2, min_tam=5, margen_max=1, corredor_ancho=5, prob_pilar=0.10),
}


class NodoBSP:
    __slots__ = ("x", "y", "w", "h", "izq", "der", "sala")

    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.izq = None
        self.der = None
        self.sala = None  # (x, y, w, h)

    def es_hoja(self):
        return self.izq is None and self.der is None

    def dividir(self, min_tam, rng):
        if not self.es_hoja():
            return False

        horizontal = rng.random() < 0.5
        if self.w > self.h * 1.25:
            horizontal = False
        elif self.h > self.w * 1.25:
            horizontal = True

        if horizontal:
            if self.h < min_tam * 2:
                return False
            split = int(rng.integers(min_tam, self.h - min_tam + 1))
            self.izq = NodoBSP(self.x, self.y, self.w, split)
            self.der = NodoBSP(self.x, self.y + split, self.w, self.h - split)
        else:
            if self.w < min_tam * 2:
                return False
            split = int(rng.integers(min_tam, self.w - min_tam + 1))
            self.izq = NodoBSP(self.x, self.y, split, self.h)
            self.der = NodoBSP(self.x + split, self.y, self.w - split, self.h)
        return True


def _dividir_bsp(ancho, alto, n_iter, min_tam, rng):
    raiz = NodoBSP(1, 1, ancho - 2, alto - 2)
    hojas = [raiz]
    for _ in range(n_iter):
        nuevas = []
        for nodo in hojas:
            if nodo.dividir(min_tam, rng):
                nuevas.append(nodo.izq)
                nuevas.append(nodo.der)
            else:
                nuevas.append(nodo)
        hojas = nuevas
    return raiz, hojas


def _asignar_salas(hojas, margen_max, rng):
    for hoja in hojas:
        mx = min(margen_max, max(0, hoja.w - 3))
        my = min(margen_max, max(0, hoja.h - 3))
        dx0 = int(rng.integers(0, mx + 1)) if mx > 0 else 0
        dy0 = int(rng.integers(0, my + 1)) if my > 0 else 0
        dx1 = int(rng.integers(0, mx + 1)) if mx > 0 else 0
        dy1 = int(rng.integers(0, my + 1)) if my > 0 else 0

        rx = hoja.x + dx0
        ry = hoja.y + dy0
        rw = max(2, hoja.w - dx0 - dx1)
        rh = max(2, hoja.h - dy0 - dy1)
        rw = min(rw, hoja.x + hoja.w - rx)
        rh = min(rh, hoja.y + hoja.h - ry)
        hoja.sala = (rx, ry, rw, rh)


def _tallar_salas(grid, hojas):
    for hoja in hojas:
        x, y, w, h = hoja.sala
        grid[y:y + h, x:x + w] = 0


def _carve_linea(grid, x0, x1, y, ancho_corredor):
    alto, ancho = grid.shape
    mitad = ancho_corredor // 2
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for m in range(-mitad, mitad + 1):
            yy = y + m
            if 0 <= yy < alto and 0 <= x < ancho:
                grid[yy, x] = 0


def _carve_columna(grid, y0, y1, x, ancho_corredor):
    alto, ancho = grid.shape
    mitad = ancho_corredor // 2
    for y in range(min(y0, y1), max(y0, y1) + 1):
        for m in range(-mitad, mitad + 1):
            xx = x + m
            if 0 <= xx < ancho and 0 <= y < alto:
                grid[y, xx] = 0


def _carve_corredor_l(grid, p1, p2, ancho_corredor, rng):
    x1, y1 = p1
    x2, y2 = p2
    if rng.random() < 0.5:
        _carve_linea(grid, x1, x2, y1, ancho_corredor)
        _carve_columna(grid, y1, y2, x2, ancho_corredor)
    else:
        _carve_columna(grid, y1, y2, x1, ancho_corredor)
        _carve_linea(grid, x1, x2, y2, ancho_corredor)


def _conectar_arbol(nodo, grid, ancho_corredor, rng):
    """Recorre el árbol BSP y conecta cada par de subárboles con un pasillo en L."""
    if nodo.es_hoja():
        x, y, w, h = nodo.sala
        return (x + w // 2, y + h // 2)

    p_izq = _conectar_arbol(nodo.izq, grid, ancho_corredor, rng)
    p_der = _conectar_arbol(nodo.der, grid, ancho_corredor, rng)
    _carve_corredor_l(grid, p_izq, p_der, ancho_corredor, rng)
    return p_izq


def _agregar_pilares(grid, hojas, prob, rng):
    """Agrega algunos obstáculos internos sueltos dentro de salas grandes (textura)."""
    for hoja in hojas:
        x, y, w, h = hoja.sala
        if w < 5 or h < 5:
            continue
        if rng.random() < prob:
            px = x + int(rng.integers(2, w - 2))
            py = y + int(rng.integers(2, h - 2))
            grid[py, px] = 1
            if rng.random() < 0.5:
                grid[py, min(px + 1, x + w - 2)] = 1


def _elegir_salida(grid, hojas, ancho, alto, rng):
    """Busca una sala que toque el borde exterior y abre una puerta hacia afuera."""
    candidatos = []
    for hoja in hojas:
        x, y, w, h = hoja.sala
        if x <= 2:
            candidatos.append(("izq", hoja))
        if x + w >= ancho - 3:
            candidatos.append(("der", hoja))
        if y <= 2:
            candidatos.append(("arriba", hoja))
        if y + h >= alto - 3:
            candidatos.append(("abajo", hoja))

    lado, hoja = candidatos[int(rng.integers(len(candidatos)))]
    x, y, w, h = hoja.sala

    if lado == "izq":
        py = y + int(rng.integers(0, h))
        salida = (0, py)
        _carve_linea(grid, 0, x, py, 1)
    elif lado == "der":
        py = y + int(rng.integers(0, h))
        salida = (ancho - 1, py)
        _carve_linea(grid, x + w - 1, ancho - 1, py, 1)
    elif lado == "arriba":
        px = x + int(rng.integers(0, w))
        salida = (px, 0)
        _carve_columna(grid, 0, y, px, 1)
    else:
        px = x + int(rng.integers(0, w))
        salida = (px, alto - 1)
        _carve_columna(grid, y + h - 1, alto - 1, px, 1)

    return salida


def _bfs_distancias(grid, origen):
    alto, ancho = grid.shape
    dist = np.full((alto, ancho), -1, dtype=int)
    ox, oy = origen
    if grid[oy, ox] == 1:
        return dist
    dist[oy, ox] = 0
    cola = [(ox, oy)]
    idx = 0
    while idx < len(cola):
        x, y = cola[idx]
        idx += 1
        for dx, dy in DIRECCIONES:
            nx, ny = x + dx, y + dy
            if 0 <= nx < ancho and 0 <= ny < alto and grid[ny, nx] == 0 and dist[ny, nx] == -1:
                dist[ny, nx] = dist[y, x] + 1
                cola.append((nx, ny))
    return dist


def _elegir_spawns(grid, salida, n, rng, umbral_lejania=0.5):
    """
    Elige n celdas de spawn: primero se queda con las más lejanas a la salida
    (el umbral_lejania% más alejado del mapa), y dentro de ese grupo las reparte
    con farthest-point sampling (cada nuevo spawn es el más lejano a los ya elegidos),
    para que no queden todos amontonados en el mismo rincón.
    """
    dist = _bfs_distancias(grid, salida)
    alto, ancho = grid.shape
    candidatos = [(x, y) for y in range(alto) for x in range(ancho) if dist[y, x] > 0]
    if not candidatos:
        return []

    candidatos.sort(key=lambda c: dist[c[1], c[0]], reverse=True)
    pool = candidatos[:max(n, int(len(candidatos) * umbral_lejania))]
    rng.shuffle(pool)

    elegidos = [pool.pop()]
    while len(elegidos) < n and pool:
        mejor_idx, _ = max(
            enumerate(pool),
            key=lambda ic: min(abs(ic[1][0] - e[0]) + abs(ic[1][1] - e[1]) for e in elegidos)
        )
        elegidos.append(pool.pop(mejor_idx))

    return elegidos[:n]


def generar_mapa(tipo, ancho=30, alto=30, n_spawns=40, seed=None, max_intentos=25):
    if tipo not in PARAMS_TIPO:
        raise ValueError(f"tipo debe ser uno de {list(PARAMS_TIPO)}")

    rng = np.random.default_rng(seed)
    p = PARAMS_TIPO[tipo]

    for _ in range(max_intentos):
        grid = np.ones((alto, ancho), dtype=int)
        raiz, hojas = _dividir_bsp(ancho, alto, p["n_iter"], p["min_tam"], rng)
        _asignar_salas(hojas, p["margen_max"], rng)
        _tallar_salas(grid, hojas)
        _conectar_arbol(raiz, grid, p["corredor_ancho"], rng)
        _agregar_pilares(grid, hojas, p["prob_pilar"], rng)

        salida = _elegir_salida(grid, hojas, ancho, alto, rng)
        spawns = _elegir_spawns(grid, salida, n_spawns, rng)

        if len(spawns) == n_spawns:
            return grid, salida, spawns

    raise RuntimeError(f"No se logró generar un mapa válido para tipo={tipo}")


def mostrar_mapa(grid, salida=None, spawns=None, titulo=""):
    plt.figure(figsize=(6, 6))
    plt.imshow(grid, cmap="gray_r")
    if salida:
        plt.scatter(*salida, c="red", s=80, marker="s", label="Salida")
    if spawns:
        xs, ys = zip(*spawns)
        plt.scatter(xs, ys, c="blue", s=40, label="Spawns")
    plt.title(titulo)
    plt.legend(loc="upper right", fontsize=8)
    plt.axis("off")
    plt.show()