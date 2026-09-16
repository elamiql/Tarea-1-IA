from src.mapas.map_generator import PARAMS_TIPO, generar_mapa, mostrar_mapa

if __name__ == "__main__":
    for tipo in PARAMS_TIPO:
        grid, salida, spawns = generar_mapa(tipo, ancho=50, alto=50, seed=42)
        mostrar_mapa(grid, salida, spawns, titulo=tipo)

print(type(grid), grid.shape)