import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.lines import Line2D
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.colors import ListedColormap
from matplotlib.widgets import Button, Slider
from pathlib import Path

from src.simulacion.entorno import Agente, combinar_obstaculos, camino_bloqueado, costo_fn_congestion
from src.simulacion.fuego import calcular_fuego_por_turno
from src.algoritmos.metaheuristico.constantes import MOVIMIENTOS

FPS_ANIMACION_BASE = 24

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
        ruta_proyecto = Path(__file__).resolve().parents[2]
        self.imagen_fuego = mpimg.imread(ruta_proyecto / "assets" / "fire.png")
        self.historial = []
        self.snapshots = []

        self.indice_snapshot = 0
        self.modo = "snapshots"
        self.reproduciendo = False
        self.velocidad = 1.0
        self._actualizando_slider = False
        self.titulo = "Simulacion"

        self.fig = None
        self.ax = None
        self.boton_anterior = None
        self.boton_siguiente = None
        self.boton_reproducir = None
        self.boton_modo = None
        self.slider_tiempo = None
        self.slider_velocidad = None
        self.temporizador = None

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

    def generar_historial_genetico(self, plan_conjunto):
        """Genera estados visuales para las secuencias producidas por el genetico."""
        if len(plan_conjunto) != len(self.spawns):
            raise ValueError("Debe existir una secuencia por agente.")

        if not plan_conjunto:
            self.historial = []
            self.snapshots = []
            return self.snapshots

        if any(len(secuencia) < self.max_turnos for secuencia in plan_conjunto):
            raise ValueError("Cada secuencia debe cubrir todos los turnos de la simulacion.")

        movimientos_validos = set(MOVIMIENTOS)
        if any(movimiento not in movimientos_validos for secuencia in plan_conjunto for movimiento in secuencia):
            raise ValueError("El plan genetico contiene un movimiento no valido.")

        fuego_por_turno = calcular_fuego_por_turno(
            self.grid, self.origenes_fuego, self.max_turnos, self.k_fuego
        )
        agentes = [Agente(i, pos) for i, pos in enumerate(self.spawns)]
        muertes_acumuladas = {}
        alto, ancho = self.grid.shape

        self.historial = []

        for t in range(self.max_turnos):
            quemado = fuego_por_turno.get(t, set())

            if self.salida in quemado:
                for agente in agentes:
                    if agente.vivo and not agente.evacuado:
                        agente.vivo = False
                        self._registrar_muerte(muertes_acumuladas, agente.pos)
                self._guardar_estado(t, quemado, agentes, muertes_acumuladas)
                break

            for agente in agentes:
                if not agente.vivo or agente.evacuado:
                    continue

                if agente.pos in quemado:
                    agente.vivo = False
                    self._registrar_muerte(muertes_acumuladas, agente.pos)
                    continue

                dx, dy = plan_conjunto[agente.id][t]
                nx = agente.pos[0] + dx
                ny = agente.pos[1] + dy

                if (
                    0 <= nx < ancho
                    and 0 <= ny < alto
                    and self.grid[ny, nx] == 0
                    and (nx, ny) not in quemado
                ):
                    agente.pos = (nx, ny)

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

    def _estados_activos(self):
        if self.modo == "animacion":
            return self.historial
        return self.snapshots

    def _indice_turno_mas_cercano(self, estados, turno):
        return min(
            range(len(estados)),
            key=lambda indice: abs(estados[indice]["turno"] - turno)
        )

    def mostrar(self, titulo="Simulacion"):
        if not self.snapshots:
            raise RuntimeError("Primero debes generar el historial.")

        self.titulo = titulo
        self.modo = "snapshots"
        self.indice_snapshot = 0
        self.reproduciendo = False

        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        plt.subplots_adjust(bottom=0.25, top=0.90)

        eje_tiempo = self.fig.add_axes([0.12, 0.15, 0.76, 0.035])
        eje_modo = self.fig.add_axes([0.06, 0.055, 0.20, 0.055])
        eje_anterior = self.fig.add_axes([0.30, 0.055, 0.08, 0.055])
        eje_reproducir = self.fig.add_axes([0.40, 0.055, 0.15, 0.055])
        eje_siguiente = self.fig.add_axes([0.57, 0.055, 0.08, 0.055])
        eje_velocidad = self.fig.add_axes([0.72, 0.065, 0.20, 0.03])

        self.slider_tiempo = Slider(
            eje_tiempo,
            "Posicion",
            0,
            max(0, len(self.snapshots) - 1),
            valinit=0,
            valstep=1,
        )
        self.boton_modo = Button(eje_modo, "Vista: 8 snapshots")
        self.boton_anterior = Button(eje_anterior, "Anterior")
        self.boton_reproducir = Button(eje_reproducir, "Reproducir")
        self.boton_siguiente = Button(eje_siguiente, "Siguiente")
        self.slider_velocidad = Slider(
            eje_velocidad,
            "Velocidad",
            0.25,
            4.0,
            valinit=1.0,
            valstep=0.25,
            valfmt="%1.2fx",
        )

        self.slider_tiempo.on_changed(self._slider_cambiado)
        self.slider_velocidad.on_changed(self._velocidad_cambiada)
        self.boton_modo.on_clicked(self._cambiar_modo)
        self.boton_anterior.on_clicked(self._anterior)
        self.boton_reproducir.on_clicked(self._alternar_reproduccion)
        self.boton_siguiente.on_clicked(self._siguiente)

        self.fig.canvas.mpl_connect("key_press_event", self._tecla_presionada)
        self.fig.canvas.mpl_connect("close_event", self._cerrar)

        self.temporizador = self.fig.canvas.new_timer(
            interval=round(1000 / FPS_ANIMACION_BASE)
        )
        self.temporizador.add_callback(self._avanzar_reproduccion)

        self.fig.text(
            0.5,
            0.015,
            "Espacio: reproducir/pausar · ←/→: navegar · M/Tab: cambiar vista · Inicio/Fin: saltar",
            ha="center",
            fontsize=8,
            color="#555555",
        )

        self._dibujar_actual()

        plt.show()

    def _dibujar_actual(self):
        estados = self._estados_activos()
        self.indice_snapshot = min(self.indice_snapshot, len(estados) - 1)
        snapshot = estados[self.indice_snapshot]

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

        if self.modo == "animacion":
            mascara_fuego = np.zeros_like(self.grid, dtype=float)
            for x, y in snapshot["quemado"]:
                mascara_fuego[y, x] = 1.0

            cmap_fuego = ListedColormap([
                (0.0, 0.0, 0.0, 0.0),
                (1.0, 0.18, 0.02, 0.58),
            ])
            self.ax.imshow(
                mascara_fuego,
                cmap=cmap_fuego,
                interpolation="none",
                vmin=0,
                vmax=1,
                origin="upper",
                zorder=5,
            )
        else:
            for x, y in snapshot["quemado"]:
                imagen = OffsetImage(self.imagen_fuego, zoom=0.20, alpha=0.55)
                fuego = AnnotationBbox(imagen, (x, y), frameon=False, pad=0, zorder=7)
                self.ax.add_artist(fuego)

        cantidad_vivos = len(snapshot["agentes_vivos"])
        estado_salida = "ACTIVA" if snapshot["salida_activa"] else "QUEMADA"

        if self.modo == "animacion":
            texto_posicion = (
                f"Turno {snapshot['turno']} · "
                f"Frame {self.indice_snapshot + 1}/{len(estados)}"
            )
        else:
            texto_posicion = (
                f"Snapshot {self.indice_snapshot + 1}/{len(estados)} · "
                f"Turno {snapshot['turno']}"
            )

        self.ax.set_title(
            f"{self.titulo}\n"
            f"{texto_posicion}\n"
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

        if self.slider_tiempo is not None:
            self._actualizando_slider = True
            self.slider_tiempo.valmax = max(0, len(estados) - 1)
            self.slider_tiempo.ax.set_xlim(0, max(1, len(estados) - 1))
            self.slider_tiempo.set_val(self.indice_snapshot)
            self._actualizando_slider = False

        self.fig.canvas.draw_idle()

    def _anterior(self, _):
        self._pausar()
        if self.indice_snapshot > 0:
            self.indice_snapshot -= 1
            self._dibujar_actual()

    def _siguiente(self, _):
        self._pausar()
        if self.indice_snapshot < len(self._estados_activos()) - 1:
            self.indice_snapshot += 1
            self._dibujar_actual()

    def _slider_cambiado(self, valor):
        if self._actualizando_slider:
            return

        self._pausar()
        nuevo_indice = int(round(valor))
        nuevo_indice = min(nuevo_indice, len(self._estados_activos()) - 1)

        if nuevo_indice != self.indice_snapshot:
            self.indice_snapshot = nuevo_indice
            self._dibujar_actual()

    def _velocidad_cambiada(self, valor):
        self.velocidad = float(valor)
        if self.temporizador is not None:
            intervalo_base = 1000 / FPS_ANIMACION_BASE
            self.temporizador.interval = max(
                25,
                round(intervalo_base / self.velocidad),
            )

    def _cambiar_modo(self, _):
        self._pausar()
        turno_actual = self._estados_activos()[self.indice_snapshot]["turno"]
        self.modo = "animacion" if self.modo == "snapshots" else "snapshots"
        estados = self._estados_activos()
        self.indice_snapshot = self._indice_turno_mas_cercano(estados, turno_actual)
        self._dibujar_actual()

    def _alternar_reproduccion(self, _):
        if self.reproduciendo:
            self._pausar()
            return

        if self.modo == "snapshots":
            turno_actual = self.snapshots[self.indice_snapshot]["turno"]
            self.modo = "animacion"
            self.indice_snapshot = self._indice_turno_mas_cercano(
                self.historial, turno_actual
            )

        if self.indice_snapshot >= len(self.historial) - 1:
            self.indice_snapshot = 0

        self.reproduciendo = True
        self.boton_reproducir.label.set_text("Pausar")
        self.temporizador.start()
        self._dibujar_actual()

    def _avanzar_reproduccion(self):
        if not self.reproduciendo:
            return

        if self.indice_snapshot >= len(self.historial) - 1:
            self._pausar()
            return

        self.indice_snapshot += 1
        self._dibujar_actual()

    def _pausar(self):
        self.reproduciendo = False
        if self.temporizador is not None:
            self.temporizador.stop()
        if self.boton_reproducir is not None:
            self.boton_reproducir.label.set_text("Reproducir")

    def _cerrar(self, _):
        self._pausar()

    def _tecla_presionada(self, evento):
        if evento.key == "left":
            self._anterior(None)
        elif evento.key == "right":
            self._siguiente(None)
        elif evento.key in (" ", "space"):
            self._alternar_reproduccion(None)
        elif evento.key == "home":
            self._pausar()
            self.indice_snapshot = 0
            self._dibujar_actual()
        elif evento.key == "end":
            self._pausar()
            self.indice_snapshot = len(self._estados_activos()) - 1
            self._dibujar_actual()
        elif evento.key in ("m", "tab"):
            self._cambiar_modo(None)

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
        puede_siguiente = self.indice_snapshot < len(self._estados_activos()) - 1

        self.boton_anterior.set_active(puede_anterior)
        self.boton_siguiente.set_active(puede_siguiente)

        self.boton_anterior.label.set_color("black" if puede_anterior else "gray")
        self.boton_siguiente.label.set_color("black" if puede_siguiente else "gray")

        if self.boton_modo is not None:
            etiqueta = (
                "Vista: turno a turno"
                if self.modo == "animacion"
                else f"Vista: {len(self.snapshots)} snapshots"
            )
            self.boton_modo.label.set_text(etiqueta)

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
        boton_reproducir_original = self.boton_reproducir
        boton_modo_original = self.boton_modo
        slider_tiempo_original = self.slider_tiempo
        slider_velocidad_original = self.slider_velocidad
        modo_original = self.modo

        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        self.ax.set_position([0.15, 0.18, 0.70, 0.70])

        self.boton_anterior = None
        self.boton_siguiente = None
        self.boton_reproducir = None
        self.boton_modo = None
        self.slider_tiempo = None
        self.slider_velocidad = None
        self.modo = "snapshots"

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
        self.boton_reproducir = boton_reproducir_original
        self.boton_modo = boton_modo_original
        self.slider_tiempo = slider_tiempo_original
        self.slider_velocidad = slider_velocidad_original
        self.modo = modo_original
        self.indice_snapshot = indice_original

        return carpeta

    def guardar_animacion(self, ruta="resultados/animacion.gif", fps=24, salto=1):
        """Exporta el historial turno a turno como GIF sin alterar la simulacion."""
        if not self.historial:
            raise RuntimeError("Primero debes generar el historial.")
        if fps <= 0:
            raise ValueError("fps debe ser mayor que 0.")
        if salto <= 0:
            raise ValueError("salto debe ser mayor que 0.")

        ruta = Path(ruta)
        if ruta.suffix.lower() != ".gif":
            ruta = ruta.with_suffix(".gif")
        ruta.parent.mkdir(parents=True, exist_ok=True)

        indice_original = self.indice_snapshot
        modo_original = self.modo
        fig_original = self.fig
        ax_original = self.ax
        controles_originales = (
            self.boton_anterior,
            self.boton_siguiente,
            self.boton_reproducir,
            self.boton_modo,
            self.slider_tiempo,
            self.slider_velocidad,
        )

        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        self.ax.set_position([0.08, 0.08, 0.84, 0.82])
        self.boton_anterior = None
        self.boton_siguiente = None
        self.boton_reproducir = None
        self.boton_modo = None
        self.slider_tiempo = None
        self.slider_velocidad = None
        self.modo = "animacion"

        frames = list(range(0, len(self.historial), salto))
        if frames[-1] != len(self.historial) - 1:
            frames.append(len(self.historial) - 1)

        def actualizar(indice):
            self.indice_snapshot = indice
            self._dibujar_actual()
            return []

        animacion = FuncAnimation(
            self.fig,
            actualizar,
            frames=frames,
            interval=1000 / fps,
            blit=False,
            repeat=False,
        )
        animacion.save(ruta, writer=PillowWriter(fps=fps), dpi=100)
        plt.close(self.fig)

        self.fig = fig_original
        self.ax = ax_original
        (
            self.boton_anterior,
            self.boton_siguiente,
            self.boton_reproducir,
            self.boton_modo,
            self.slider_tiempo,
            self.slider_velocidad,
        ) = controles_originales
        self.modo = modo_original
        self.indice_snapshot = indice_original

        return ruta
