import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

from matplotlib.lines import Line2D
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.colors import ListedColormap
from matplotlib.widgets import Button
from pathlib import Path

from src.simulacion.entorno import Agente, combinar_obstaculos, camino_bloqueado, costo_fn_congestion
from src.simulacion.fuego import calcular_fuego_por_turno


class VisualizadorSimulacion:
    def __init__(self, grid, spawns, salida, origenes_fuego, max_turnos, k_fuego, n_snapshots=8):
        if n_snapshots <= 0:
            raise ValueError("n_snapshots debe ser mayor que 0.")

        self.grid = grid
        self.spawns = list(spawns)
        self.salida = salida
        self.origenes_fuego = list(origenes_fuego)
        self.max_turnos = max_turnos
        self.k_fuego = k_fuego
        self.n_snapshots = n_snapshots
        self.imagen_fuego = mpimg.imread("assets/fire.png")
        self.historial = []
        self.snapshots = []

        self.indice_snapshot = 0
        self.titulo = "Simulacion"

        self.fig = None
        self.ax = None
        self.boton_anterior = None
        self.boton_siguiente = None

    def generar_historial(self, algoritmo, usa_costo_fn=False):
        fuego_por_turno = calcular_fuego_por_turno(
            self.grid, self.origenes_fuego, self.max_turnos, self.k_fuego
        )

        agentes = [Agente(i, pos) for i, pos in enumerate(self.spawns)]

        ocupacion_previa = {}
        muertes_acumuladas = {}

        self.historial = []

        for t in range(self.max_turnos):
            quemado = fuego_por_turno.get(t, set())
            fuego_recien_avanzo = t > 0 and t % self.k_fuego == 0

            if self.salida in quemado:
                for agente in agentes:
                    if agente.vivo and not agente.evacuado:
                        agente.vivo = False
                        self._registrar_muerte(muertes_acumuladas, agente.pos)

                self._guardar_estado(t, quemado, agentes, muertes_acumuladas)
                break

            for agente in agentes:
                if agente.vivo and not agente.evacuado and agente.pos in quemado:
                    agente.vivo = False
                    self._registrar_muerte(muertes_acumuladas, agente.pos)

            vivos_activos = [
                agente
                for agente in agentes
                if agente.vivo and not agente.evacuado
            ]

            if not vivos_activos:
                self._guardar_estado(t, quemado, agentes, muertes_acumuladas)
                break

            grid_efectivo = combinar_obstaculos(self.grid, quemado)

            for agente in vivos_activos:
                necesita_plan = (
                    agente.camino is None
                    or t == 0
                    or fuego_recien_avanzo
                    or camino_bloqueado(agente.camino, agente.idx, quemado)
                )

                if not necesita_plan:
                    continue

                if usa_costo_fn:
                    costo_fn = costo_fn_congestion(ocupacion_previa)
                    nuevo_camino = algoritmo(grid_efectivo, agente.pos, self.salida, costo_fn)
                else:
                    nuevo_camino = algoritmo(grid_efectivo, agente.pos, self.salida)

                agente.camino = nuevo_camino
                agente.idx = 0

            siguientes = {}

            for agente in vivos_activos:
                if agente.camino and agente.idx + 1 < len(agente.camino):
                    siguientes[agente.id] = agente.camino[agente.idx + 1]
                else:
                    siguientes[agente.id] = agente.pos

            ocupacion = {}

            for pos in siguientes.values():
                ocupacion[pos] = ocupacion.get(pos, 0) + 1

            ocupacion_previa = ocupacion

            for agente in vivos_activos:
                nueva_pos = siguientes[agente.id]

                if nueva_pos != agente.pos:
                    agente.pos = nueva_pos
                    agente.idx += 1

                if agente.pos == self.salida:
                    agente.evacuado = True
                    agente.turno_evacuacion = t

            self._guardar_estado(t, quemado, agentes, muertes_acumuladas)

            if all(agente.evacuado or not agente.vivo for agente in agentes):
                break

        self._seleccionar_snapshots()

        return self.snapshots

    def _registrar_muerte(self, muertes, posicion):
        muertes[posicion] = muertes.get(posicion, 0) + 1

    def _guardar_estado(self, turno, quemado, agentes, muertes_acumuladas):
        posiciones_vivos = [
            agente.pos
            for agente in agentes
            if agente.vivo and not agente.evacuado
        ]

        evacuados = sum(1 for agente in agentes if agente.evacuado)
        muertos = sum(1 for agente in agentes if not agente.vivo)

        self.historial.append({
            "turno": turno,
            "quemado": set(quemado),
            "agentes_vivos": posiciones_vivos,
            "muertes": dict(muertes_acumuladas),
            "evacuados": evacuados,
            "muertos": muertos,
            "salida_activa": self.salida not in quemado,
        })

    def _seleccionar_snapshots(self):
        if not self.historial:
            self.snapshots = []
            return

        cantidad = min(self.n_snapshots, len(self.historial))
        indices = np.linspace(0, len(self.historial) - 1, cantidad, dtype=int)
        indices = np.unique(indices)

        self.snapshots = [self.historial[i] for i in indices]
        self.indice_snapshot = 0

    def mostrar(self, titulo="Simulacion"):
        if not self.snapshots:
            raise RuntimeError("Primero debes generar el historial.")

        self.titulo = titulo

        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        plt.subplots_adjust(bottom=0.15, top=0.90)

        eje_anterior = self.fig.add_axes([0.33, 0.04, 0.12, 0.06])
        eje_siguiente = self.fig.add_axes([0.55, 0.04, 0.12, 0.06])

        self.boton_anterior = Button(eje_anterior, "←")
        self.boton_siguiente = Button(eje_siguiente, "→")

        self.boton_anterior.on_clicked(self._anterior)
        self.boton_siguiente.on_clicked(self._siguiente)

        self.fig.canvas.mpl_connect("key_press_event", self._tecla_presionada)

        self._dibujar_actual()

        plt.show()

    def _dibujar_actual(self):
        snapshot = self.snapshots[self.indice_snapshot]

        self.ax.clear()

        cmap = ListedColormap(["white", "#444444"])

        self.ax.imshow(
            self.grid,
            cmap=cmap,
            interpolation="none",
            vmin=0,
            vmax=1,
            origin="upper"
        )

        sx, sy = self.salida

        self.ax.scatter(
            sx,
            sy,
            s=130,
            marker="s",
            c="limegreen",
            edgecolors="black",
            linewidths=1,
            zorder=4
        )

        for x, y in self.origenes_fuego:
            self.ax.scatter(x, y, s=90, marker="o", facecolors="none", edgecolors="darkorange", linewidths=1.5, zorder=10)

        if snapshot["agentes_vivos"]:
            xs = [pos[0] for pos in snapshot["agentes_vivos"]]
            ys = [pos[1] for pos in snapshot["agentes_vivos"]]

            self.ax.scatter(
                xs,
                ys,
                s=55,
                marker="o",
                c="dodgerblue",
                edgecolors="black",
                linewidths=0.5,
                zorder=6
            )

        for (x, y), cantidad in snapshot["muertes"].items():
            self.ax.scatter(x, y, s=85, marker="x", c="black", linewidths=2, zorder=8)

            if cantidad > 1:
                self.ax.text(
                    x + 0.25,
                    y - 0.25,
                    str(cantidad),
                    fontsize=8,
                    fontweight="bold",
                    color="black",
                    zorder=9
                )

        for x, y in snapshot["quemado"]:
            imagen = OffsetImage(self.imagen_fuego, zoom=0.20, alpha=0.55)
            fuego = AnnotationBbox(imagen, (x, y), frameon=False, pad=0, zorder=7)
            self.ax.add_artist(fuego)

        cantidad_vivos = len(snapshot["agentes_vivos"])
        estado_salida = "ACTIVA" if snapshot["salida_activa"] else "QUEMADA"

        self.ax.set_title(
            f"{self.titulo}\n"
            f"Snapshot {self.indice_snapshot + 1}/{len(self.snapshots)} · Turno {snapshot['turno']}\n"
            f"Vivos: {cantidad_vivos} · Evacuados: {snapshot['evacuados']} · "
            f"Muertos: {snapshot['muertos']} · Salida: {estado_salida}",
            fontsize=11
        )

        alto, ancho = self.grid.shape

        self.ax.set_xlim(-0.5, ancho - 0.5)
        self.ax.set_ylim(alto - 0.5, -0.5)

        self.ax.set_xticks([])
        self.ax.set_yticks([])

        self._dibujar_leyenda()
        self._actualizar_botones()
        
        self.fig.canvas.draw_idle()

    def _anterior(self, _):
        if self.indice_snapshot > 0:
            self.indice_snapshot -= 1
            self._dibujar_actual()

    def _siguiente(self, _):
        if self.indice_snapshot < len(self.snapshots) - 1:
            self.indice_snapshot += 1
            self._dibujar_actual()

    def _tecla_presionada(self, evento):
        if evento.key == "left":
            self._anterior(None)
        elif evento.key == "right":
            self._siguiente(None)

    def _dibujar_leyenda(self):
        elementos = [
            Line2D([0], [0], marker="o", color="none", markerfacecolor="dodgerblue", markeredgecolor="black", markersize=7, label="Agente vivo"),
            Line2D([0], [0], marker="s", color="none", markerfacecolor="limegreen", markeredgecolor="black", markersize=7, label="Salida"),
            Line2D([0], [0], marker="x", color="black", markersize=7, linewidth=0, markeredgewidth=2, label="Muerte"),
            Line2D([0], [0], marker="o", color="none", markerfacecolor="orangered", markersize=7, label="Fuego"),
            Line2D([0], [0], marker="o", color="none", markerfacecolor="none", markeredgecolor="darkorange", markersize=7, label="Origen fuego"),
        ]

        self.ax.legend(handles=elementos, loc="lower center", bbox_to_anchor=(0.5, -0.10), ncol=5, frameon=False, fontsize=8)

    def _actualizar_botones(self):
        if self.boton_anterior is None or self.boton_siguiente is None:
            return

        puede_anterior = self.indice_snapshot > 0
        puede_siguiente = self.indice_snapshot < len(self.snapshots) - 1

        self.boton_anterior.set_active(puede_anterior)
        self.boton_siguiente.set_active(puede_siguiente)

        self.boton_anterior.label.set_color("black" if puede_anterior else "gray")
        self.boton_siguiente.label.set_color("black" if puede_siguiente else "gray")

    def guardar_snapshots(self, carpeta="resultados/snapshots", prefijo="snapshot"):
        if not self.snapshots:
            raise RuntimeError("Primero debes generar el historial.")

        carpeta = Path(carpeta)
        carpeta.mkdir(parents=True, exist_ok=True)

        indice_original = self.indice_snapshot

        fig_original = self.fig
        ax_original = self.ax
        boton_anterior_original = self.boton_anterior
        boton_siguiente_original = self.boton_siguiente

        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        self.ax.set_position([0.15, 0.18, 0.70, 0.70])

        self.boton_anterior = None
        self.boton_siguiente = None

        for i in range(len(self.snapshots)):
            self.indice_snapshot = i
            self._dibujar_actual()

            snapshot = self.snapshots[i]
            turno = snapshot["turno"]

            nombre = carpeta / f"{prefijo}_{i + 1:02d}_turno_{turno}.png"
            self.fig.savefig(nombre, dpi=200, bbox_inches="tight")

        plt.close(self.fig)

        self.fig = fig_original
        self.ax = ax_original
        self.boton_anterior = boton_anterior_original
        self.boton_siguiente = boton_siguiente_original
        self.indice_snapshot = indice_original

        return carpeta