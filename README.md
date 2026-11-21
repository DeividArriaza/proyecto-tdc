# Simulador de máquinas de Turing

Proyecto 3 de Teoría de la Computación, CC2019, sección 30, Universidad del Valle de Guatemala. Simula máquinas deterministas de una cinta y un cabezal, extensible hacia ambos lados, definidas en YAML mediante cuádruplas.

[Informe PDF](output/Informe_Proyecto_3.pdf) · [Informe editable](output/Informe_Proyecto_3.docx) · [Video MP4](video/presentacion.mp4) · [Subtítulos](video/subtitulos.srt)

## Instalación

Requiere Python 3.11 o superior con Tkinter. La aplicación solo depende de PyYAML. Desde la carpeta del repositorio:

```powershell
py -m pip install -r requirements.txt
py -m simulador
```

En Linux/macOS use `python3` en lugar de `py`. Algunas distribuciones Linux requieren instalar `python3-tk`. En Windows también puede abrir `ejecutar.bat` después de instalar las dependencias.

## Uso de la interfaz

1. Abra un archivo YAML o seleccione uno de los dos ejemplos incluidos.
2. Escriba la entrada. Deje el campo vacío para representar la cadena vacía.
3. Pulse **Preparar / reiniciar**. Esto crea una simulación nueva y registra la DI inicial.
4. Pulse **Un paso** o **Ejecutar**. Puede desmarcar la animación lenta para acelerar la ejecución.
5. Use **Pausar** para continuar después; **Cancelar** finaliza la ejecución como cancelada y presenta contenido parcial.
6. Use **Exportar traza** para guardar las DI y el resultado en JSONL. Durante una ejecución, exporta la traza hasta ese momento; al detenerse, incluye el resultado final.

La celda coloreada contiene el cabezal. Los índices pueden ser negativos. La cinta visible sigue al cabezal; esa ventana no limita la cinta simulada. La vista de texto conserva las últimas 200 DI y abrevia líneas largas; el archivo temporal conserva todas las DI completas, sin esa abreviación. Los registros temporales se llaman `turing_*.jsonl` en la carpeta temporal del sistema y permanecen disponibles tras cerrar la aplicación.

Al cambiar la entrada, pulse **Preparar / reiniciar** antes de comenzar una simulación nueva. La entrada visible no modifica una simulación ya preparada.

## Uso por terminal

```powershell
py -m simulador ejemplos/complemento_adn.yaml ACGT --traza adn.jsonl
py -m simulador ejemplos/duplicacion_ternaria.yaml abc --traza duplicacion.jsonl
py -m simulador ejemplos/duplicacion_ternaria.yaml ""
py -m simulador ejemplos/bucle_cancelable.yaml
```

La terminal muestra la DI inicial y cada configuración posterior. `Ctrl+C` cancela una ejecución. Los códigos de salida son 0 (parada normal), 2 (entrada, archivo o especificación inválidos) y 130 (cancelación). No existe límite automático de pasos. `--resumen` omite las DI de la pantalla por decisión del usuario; si se proporciona `--traza`, el archivo sigue registrándolas todas.

Para símbolos de varios caracteres o espacios, use una lista de símbolos JSON:

```powershell
py -m simulador ejemplos/complemento_adn.yaml --tokens '["A","C","G","T"]'
```

En la interfaz marque **Lista JSON de símbolos**. En PowerShell 5.1 puede ser necesario escapar las comillas internas al pasar JSON a programas nativos; la interfaz evita ese problema.

## Sintaxis YAML

```yaml
mt:
  nombre: Ejemplo mínimo
  estados: [q0, q1]
  alfabeto: [a, b, B]
  blanco: B
  estado_inicial: q0
  transiciones:
    - q0 a b q1
    - q1 b R q0
```

La cuádrupla se interpreta como `estado lectura operación siguiente_estado`:

- `R` mueve una celda a la derecha; `L`, una a la izquierda. No escriben.
- Un símbolo del alfabeto escribe ese símbolo sin mover el cabezal.
- `W:símbolo` fuerza una escritura y elimina ambigüedades: `W:R` escribe el símbolo `R` y `W:W:a` escribe `W:a`.
- Cada cuádrupla consume un paso. Una escritura y un desplazamiento necesitan dos reglas.
- Si no existe regla para el estado y símbolo actuales, la máquina se detiene. No se presupone aceptación o rechazo.

También se admite una cuádrupla como lista YAML. Es la forma necesaria para símbolos con espacios, comillas o `#`:

```yaml
    - [q0, '#', R, q1]
```

`estados`, `alfabeto`, `estado_inicial` y `transiciones` son obligatorios. `nombre`, `descripcion` y `blanco` son opcionales. El blanco predeterminado es `B` y debe pertenecer al alfabeto. `transiciones: []` es válido. Se rechazan estados/símbolos desconocidos, claves duplicadas, campos desconocidos, listas repetidas y reglas duplicadas para el mismo par de lectura.

Los escalares se leen como texto, incluso números o palabras como `yes`; el lector no construye objetos Python desde etiquetas YAML. Para evitar confusiones entre lectura y escritura se recomienda usar comillas alrededor de símbolos especiales. El alfabeto de entrada y de cinta es el mismo. La cadena normal se separa por puntos de código Unicode; la modalidad JSON conserva exactamente cada símbolo de la lista. Los estados y los símbolos son cadenas no vacías. No hay un máximo predefinido de estados, reglas o longitud.

## Configuraciones y resultado

La entrada comienza en la posición 0 y el cabezal empieza en esa posición, incluso para la entrada vacía. La cinta guarda únicamente celdas no blancas en un diccionario de índices enteros.

Cada DI registra paso, estado, índice del cabezal, índice izquierdo y todas las celdas del intervalo que contiene la entrada original y todas las posiciones visitadas. Fuera de ese intervalo se sobreentienden blancos infinitos. En pantalla, `[s]` identifica la celda leída. JSONL conserva los símbolos sin ambigüedad, aunque su representación textual contenga corchetes.

El resultado es la lista ordenada de símbolos entre los extremos no blancos de la cinta final; conserva los blancos interiores. Si toda la cinta está en blanco, es `[]`. También se ofrece su concatenación como texto. Los blancos exteriores y el cabezal siguen constando en la DI final. No se interpreta la salida como número unario ni se borran separadores o marcadores de la máquina. Una cancelación produce contenido parcial, no un resultado final calculado.

## Ejemplos y complejidad

| Máquina | Dominio del ejemplo | Entrada | Resultado | Pasos |
|---|---|---|---|---:|
| Complemento de ADN | `{A,C,G,T}*` | `ACGT` | `TGCA` | 8 |
| Duplicación ternaria | `{a,b,c}*` | `abc` | `abc#abc` | 61 |
| Complemento de ADN | `{A,C,G,T}*` | vacía | vacía | 0 |
| Duplicación ternaria | `{a,b,c}*` | vacía | `#` | 4 |

Para una longitud `n`, el complemento ejecuta `2n` cuádruplas y la duplicación ejecuta `3n² + 10n + 4`. Con diccionarios de acceso esperado constante, el motor tarda respectivamente Θ(n + 1) y Θ((n + 1)²), usando O(n + 1) celdas.

**El simulador completo con traza tiene otro costo:** cada DI materializa Θ(n + 1) celdas. Por ello, registrar todas las configuraciones cuesta Θ((n + 1)²) para ADN y Θ((n + 1)³) para duplicación, medido en celdas serializadas y bajo el modelo de símbolos y enteros de costo unitario. Los campos numéricos JSON agregan O(T(n) log(T(n) + n + 1)) bytes, dominados por las celdas en estos ejemplos con alfabetos fijos. La traza se escribe en disco y no se conserva íntegra en RAM.

Los dominios anteriores describen los algoritmos de ejemplo, no una restricción del simulador. Cualquier palabra del alfabeto declarado puede cargarse; fuera del dominio del algoritmo, una parada sin regla no certifica un resultado de ese algoritmo.

## Pruebas y evidencia

```powershell
py -m pip install pytest
py -m pytest -q
py herramientas/medir.py
```

Las pruebas incluyen las 364 palabras ternarias de longitud 0 a 5, resultados conocidos, conteo exacto de pasos, blancos interiores, cinta en ambos sentidos, más de 15000 pasos sin parada automática, validación defensiva y trazas completas. El presupuesto de 10000 pasos de una prueba de ejemplos pertenece exclusivamente al arnés de pruebas; no existe en el simulador.

`evidencia/` contiene trazas reales, mediciones CSV/JSON y resultados JUnit. GitHub Actions ejecuta las pruebas del motor y terminal en Python 3.11, 3.12, 3.13 y 3.14; la revisión de interfaz se realiza en Windows.

## Organización

```text
simulador/modelo.py       Lectura YAML, tipos y validación
simulador/motor.py        Cinta, transición, configuraciones y resultado
simulador/interfaz.py     Interfaz de escritorio y registro en disco
simulador/__main__.py     Terminal y arranque de escritorio
ejemplos/                Dos máquinas y un bucle auxiliar
tests/                   Pruebas automáticas
herramientas/            Mediciones, informe y producción del video
evidencia/               Resultados reproducibles y capturas reales
output/                  Informe editable y PDF
video/                   Video, narración, subtítulos y guía
```

## Entrega académica

El informe y la presentación se encuentran en `output/` y `video/`. La presentación producida automáticamente utiliza narración sintética: la participación personal de todos los integrantes debe incorporarse antes de entregarla si así lo exige el docente. La disponibilidad de los ejemplos debe confirmarse y registrarse en el [registro del curso](https://uvggt-my.sharepoint.com/:x:/g/personal/tgalvez_uvg_edu_gt/cQq9_Hpdem0ARqBUyerGce4sEgUCLh8Rhmv7xhr_PR0rMYlEXg).

Repositorio: https://github.com/DeividArriaza/proyecto-tdc

## Fuentes técnicas

- Enunciado del Proyecto 3, CC2019, UVG, semestre 2 de 2026.
- [Especificación YAML](https://yaml.org/spec/1.2.2/).
- [Documentación de PyYAML](https://pyyaml.org/wiki/PyYAMLDocumentation).
- [Documentación de Tkinter](https://docs.python.org/3/library/tkinter.html).
