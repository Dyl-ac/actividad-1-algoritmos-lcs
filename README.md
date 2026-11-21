# Actividad 1 · Comparación de algoritmos LCS

Tres implementaciones en Python para calcular una subsecuencia común más larga: recursión directa, Hirschberg y programación dinámica tabular.

## Ejecución

Con Python 3.10 o posterior y sin dependencias externas:

```sh
python experimento.py
```

El comando ejecuta las pruebas y repite las mediciones sobre 22 parejas de cadenas. Se realizan 198 ejecuciones en procesos separados. Los datos de entrada están en `datasets/` y las mediciones originales en `resultados/`. Al repetir el experimento se actualiza esa carpeta.

La recursión directa dispone de un límite de 1,5 segundos de CPU por proceso. Las interrupciones se registran como tales y el pico de memoria incluye el intérprete de Python.
