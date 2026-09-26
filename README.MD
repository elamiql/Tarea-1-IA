# Tarea 1 IA: Escape de la Torre

Simulación multiagente de evacuación en una grilla dinámica con propagación de fuego y congestión. El proyecto compara BFS, DFS, A*, Greedy Best-First y un Algoritmo Genético en tres tipos de mapa.

**Integrante:** Agustín Salgado Espinoza  

## Contenido del repositorio

- Generación reproducible de mapas de `50 x 50` celdas mediante BSP.
- Escenarios `cuello_botella`, `laberinto` y `abierto`.
- Simulación de fuego, congestión, movimiento y replanificación.
- Algoritmos BFS, DFS, A* y Greedy Best-First.
- Algoritmo Genético con selección, cruce, mutación y elitismo.
- Benchmark automatizado con resultados en CSV y gráficos.
- Modo visual para ejecutar una simulación, reproducirla y navegar snapshots.
- Exportación de snapshots a PNG y de la animación completa a GIF.

## Requisitos e instalación

Se necesita Python 3.10 o superior.

### Windows (CMD)

```cmd
git clone https://github.com/elamiql/Tarea-1-IA.git
cd Tarea-1-IA
python -m pip install -r requirements.txt
```

### Linux

```bash
git clone https://github.com/elamiql/Tarea-1-IA.git
cd Tarea-1-IA
python -m pip install -r requirements.txt
```

Las dependencias utilizadas por el programa son NumPy y Matplotlib.

## Ejecutar el modo visual

La forma más simple de iniciar el programa es:

```bash
python main.py
```

El menú permite escoger el tipo de mapa, el algoritmo, la seed y la cantidad de agentes.

También se puede ejecutar directamente desde la terminal:

```bash
python ejecutar_visual.py --mapa laberinto --algoritmo "A*" --seed 42 --agentes 45
```

Opciones principales:

| Opción | Valores o descripción |
|---|---|
| `--mapa` | `cuello_botella`, `laberinto` o `abierto` |
| `--algoritmo` | `BFS`, `DFS`, `A*`, `Greedy` o `Genetico` |
| `--seed` | Entero utilizado para reproducir el escenario |
| `--agentes` | Cantidad de agentes de la simulación |
| `--snapshots` | Cantidad de estados representativos; por defecto, `8` |
| `--fps` | Velocidad de la animación exportada; por defecto, `24` |

El Algoritmo Genético acepta además sus parámetros principales:

```bash
python ejecutar_visual.py --mapa abierto --algoritmo Genetico --seed 42 --agentes 45 --poblacion 40 --generaciones 100 --mutacion 0.02
```

El Algoritmo Genético puede tardar considerablemente más que los algoritmos de búsqueda debido a la evaluación de poblaciones durante múltiples generaciones.

### Controles

- `Espacio`: reproducir o pausar.
- Flechas izquierda y derecha: avanzar o retroceder.
- `M` o `Tab`: alternar entre los snapshots representativos y todos los turnos.
- `Inicio` y `Fin`: ir al primer o último estado.
- Barra temporal: saltar a un instante específico.
- Selector de velocidad: cambiar la velocidad de reproducción.

La reproducción normal se muestra a 24 FPS.

### Guardar snapshots o exportar un GIF

```bash
python ejecutar_visual.py --mapa abierto --algoritmo BFS --seed 42 --agentes 45 --guardar resultados/snapshots
```

```bash
python ejecutar_visual.py --mapa abierto --algoritmo BFS --seed 42 --agentes 45 --exportar-gif resultados/evacuacion.gif --fps 24 --no-mostrar
```

## Ejecutar el benchmark

Uso general:

```bash
python ejecutar_benchmark.py <iteraciones> <nombre>
```

Ejemplo rápido para comprobar el funcionamiento:

```bash
python ejecutar_benchmark.py 1 smoke
```

Benchmark final utilizado en el informe:

```bash
python ejecutar_benchmark.py 120 final_45_agentes
```

La configuración final es:

| Parámetro | Valor |
|---|---:|
| Tamaño del mapa | `50 x 50` |
| Agentes | `45` |
| Frecuencia de propagación del fuego | `k = 5` |
| Tipos de mapa | `3` |
| Algoritmos | `5` |
| Seeds por combinación | `120` (`0` a `119`) |
| Población del Genético | `40` |
| Generaciones del Genético | `100` |
| Probabilidad de mutación | `0.02` |
| Total de simulaciones | `3 x 5 x 120 = 1800` |

Cada combinación mapa-algoritmo utiliza las mismas seeds para que la comparación sea reproducible. Los resultados se escriben incrementalmente: si una ejecución se interrumpe, el mismo comando continúa las combinaciones pendientes del CSV existente.

El benchmark completo, especialmente las ejecuciones del Algoritmo Genético, puede tardar varias horas según el equipo.

## Métricas del benchmark

Para cada ejecución se registran:

- **Tasa de supervivencia:** proporción de agentes que logran evacuar.
- **Agentes evacuados y muertos.**
- **Tiempo de evacuación:** turno en que evacúa el último superviviente.
- **Congestión acumulada:** suma de la congestión producida durante toda la simulación.
- **Tiempo del algoritmo y tiempo total de ejecución:** datos auxiliares de rendimiento del programa; no determinan la calidad de la solución.

Para cada combinación de mapa y algoritmo, el resumen calcula promedio y desviación estándar. En el tiempo de evacuación también informa mínimo y máximo. Las ejecuciones sin evacuados se contabilizan por separado y no se incluyen en esos estadísticos temporales.

Se generan tres gráficos:

1. Tasa de supervivencia por mapa y algoritmo.
2. Tiempo medio hasta la evacuación del último superviviente.
3. Congestión acumulada promedio.

## Archivos generados

Para un benchmark llamado `final_45_agentes`, se crean:

```text
resultados/final_45_agentes.csv
resultados/final_45_agentes_resumen.csv
graficos/final_45_agentes/supervivencia.png
graficos/final_45_agentes/turnos_evacuacion.png
graficos/final_45_agentes/congestion.png
```

## Estructura principal

```text
Tarea-1-IA/
├── assets/                         # Recursos gráficos utilizados por el visualizador
├── src/                            # Código fuente del proyecto
│   ├── algoritmos/                 # Implementaciones de los algoritmos evaluados
│   │   ├── informada/              # A* y Greedy Best-First
│   │   ├── metaheuristico/         # Algoritmo Genético y sus componentes
│   │   └── no_informada/           # BFS y DFS
│   ├── benchmark/                  # Ejecución, métricas, CSV y generación de gráficos
│   ├── mapas/                      # Generación procedural de los escenarios
│   ├── simulacion/                 # Entorno, propagación del fuego y congestión
│   └── visualizacion/              # Interfaz, reproducción, snapshots y exportación
├── resultados/                     # Resultados crudos y resúmenes en formato CSV
└── graficos/                       # Gráficos generados por el benchmark
```
```

La descripción teórica, las decisiones de modelado, la función de fitness y el análisis de resultados se encuentran en el informe de la tarea.