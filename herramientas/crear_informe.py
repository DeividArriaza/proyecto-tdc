"""Genera el informe editable. Las mediciones y definiciones se leen del repo."""
from pathlib import Path
import csv
import json
import sys
import xml.etree.ElementTree as ET
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from simulador import cargar_maquina


def main():
    salida = RAIZ / 'output'
    salida.mkdir(exist_ok=True)
    datos = json.loads((RAIZ / 'entrega.json').read_text(encoding='utf-8'))
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    sec.top_margin = sec.bottom_margin = Inches(0.85)
    sec.left_margin = sec.right_margin = Inches(0.85)
    sec.footer_distance = Inches(0.35)
    for nombre, tam in [('Normal', 11), ('Title', 26), ('Subtitle', 14), ('Heading 1', 14), ('Heading 2', 12)]:
        st = doc.styles[nombre]
        st.font.name = 'Arial'
        st.font.size = Pt(tam)
        st.font.color.rgb = RGBColor(0, 0, 0)
        st.paragraph_format.space_after = Pt(8)
        st.paragraph_format.line_spacing = 1.12
    doc.styles['Normal'].paragraph_format.widow_control = True
    for nombre in ['Heading 1', 'Heading 2']:
        doc.styles[nombre].paragraph_format.space_before = Pt(10)
        doc.styles[nombre].font.bold = True
    code_style = doc.styles.add_style('Código', 1)
    code_style.font.name = 'Consolas'
    code_style.font.size = Pt(9)
    code_style.paragraph_format.space_after = Pt(0)
    code_style.paragraph_format.line_spacing = 1
    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = footer.add_run('Proyecto 3 | ')
    r.font.size = Pt(9)
    fld = OxmlElement('w:fldSimple')
    fld.set(qn('w:instr'), 'PAGE')
    footer._p.append(fld)
    doc.core_properties.title = 'Simulador de máquinas de Turing'
    doc.core_properties.subject = 'Proyecto 3 de Teoría de la Computación CC2019'
    doc.core_properties.author = '; '.join(x['nombre'] for x in datos['integrantes'])

    def p(texto, bold=False):
        para = doc.add_paragraph()
        para.add_run(texto).bold = bold
        return para

    def h(texto, nivel=1):
        doc.add_heading(texto, nivel)

    def nueva(texto):
        doc.add_page_break()
        h(texto)

    def codigo(texto):
        for linea in texto.strip('\n').splitlines():
            doc.add_paragraph(linea, style='Código')
        doc.add_paragraph().paragraph_format.space_after = Pt(2)

    def tabla(encabezados, filas, widths=None):
        t = doc.add_table(rows=1, cols=len(encabezados))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        if widths:
            for c, w in zip(t.columns, widths):
                c.width = Inches(w)
        for c, texto in zip(t.rows[0].cells, encabezados):
            c.text = texto
        rep = OxmlElement('w:tblHeader')
        t.rows[0]._tr.get_or_add_trPr().append(rep)
        for fila in filas:
            for c, text in zip(t.add_row().cells, fila):
                c.text = str(text)
        for i, row in enumerate(t.rows):
            props = row._tr.get_or_add_trPr()
            cant = OxmlElement('w:cantSplit')
            props.append(cant)
            for j, c in enumerate(row.cells):
                if widths:
                    c.width = Inches(widths[j])
                c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                tcPr = c._tc.get_or_add_tcPr()
                shade = OxmlElement('w:shd')
                shade.set(qn('w:fill'), '17324D' if i == 0 else 'F1F4F7' if i % 2 == 0 else 'FFFFFF')
                tcPr.append(shade)
                margins = OxmlElement('w:tcMar')
                for side in ['top', 'left', 'bottom', 'right']:
                    el = OxmlElement('w:' + side)
                    el.set(qn('w:w'), '100')
                    el.set(qn('w:type'), 'dxa')
                    margins.append(el)
                tcPr.append(margins)
                borders = OxmlElement('w:tcBorders')
                for side in ['top', 'left', 'bottom', 'right']:
                    el = OxmlElement('w:' + side)
                    el.set(qn('w:val'), 'single')
                    el.set(qn('w:sz'), '4')
                    el.set(qn('w:color'), 'D9D9D9')
                    borders.append(el)
                tcPr.append(borders)
                for para in c.paragraphs:
                    para.paragraph_format.space_after = Pt(2)
                    para.paragraph_format.line_spacing = 1.05
                    for run in para.runs:
                        run.font.size = Pt(9.5)
                        if i == 0:
                            run.font.bold = True
                            run.font.color.rgb = RGBColor(255, 255, 255)
        doc.add_paragraph().paragraph_format.space_after = Pt(2)
        return t

    def figura(nombre, ancho, titulo):
        para = doc.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        para.add_run().add_picture(str(RAIZ / nombre), width=Inches(ancho))
        para.paragraph_format.keep_with_next = True
        cap = doc.add_paragraph(titulo)
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in cap.runs:
            run.italic = True
            run.font.size = Pt(9)

    # Portada
    for texto in ['UNIVERSIDAD DEL VALLE DE GUATEMALA', 'Teoría de la Computación CC2019', 'Sección 30 | Semestre 2 de 2026']:
        para = p(texto)
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p('')
    para = doc.add_paragraph('Simulador de máquinas de Turing', style='Title')
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para = doc.add_paragraph('Proyecto 3', style='Subtitle')
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p('')
    p('Docente: Tomás Gálvez P.').alignment = WD_ALIGN_PARAGRAPH.CENTER
    for integrante in datos['integrantes']:
        p(f'{integrante["nombre"]} | Carné {integrante["carne"]}').alignment = WD_ALIGN_PARAGRAPH.CENTER
    p(datos['fecha']).alignment = WD_ALIGN_PARAGRAPH.CENTER
    p('')
    p('Simulación determinista de una cinta con especificaciones YAML, trazas completas y análisis experimental de crecimiento.').alignment = WD_ALIGN_PARAGRAPH.CENTER

    nueva('Índice')
    doc.paragraphs[-1].style = doc.styles['Subtitle']
    toc = OxmlElement('w:fldSimple')
    toc.set(qn('w:instr'), 'TOC \\o "1-1" \\h \\z \\u')
    doc.add_paragraph()._p.append(toc)

    nueva('1 Introducción y objetivos')
    p('El proyecto implementa un simulador de máquinas de Turing deterministas de una cinta, con un cabezal que puede desplazarse hacia ambos lados. A partir de una definición YAML y una entrada, el programa construye la configuración inicial, aplica cada transición y registra la computación completa hasta la parada o la cancelación solicitada por el usuario [1].')
    p('El simulador permite observar cómo las operaciones locales de lectura, escritura y desplazamiento producen una transformación global de la cinta. Su resultado principal es una implementación que separa la definición de la máquina, el motor de ejecución y las interfaces. Esta separación facilita tanto las pruebas como la explicación del funcionamiento.')
    h('1.1 Objetivo general', 2)
    p('Desarrollar y documentar un simulador capaz de ejecutar cualquier máquina determinista que cumpla la sintaxis de cuádruplas definida, conservando todas las descripciones instantáneas y mostrando el contenido de la cinta al finalizar.')
    h('1.2 Objetivos específicos', 2)
    for texto in ['Validar estados, alfabeto, blanco y transiciones antes de ejecutar.', 'Representar una cinta extensible en índices positivos y negativos sin una longitud máxima fijada por el programa.', 'Ofrecer ejecución paso a paso, continua, pausa, cancelación y exportación de la traza.', 'Comprobar dos algoritmos de ejemplo y explicar su crecimiento asintótico con mediciones reproducibles.']:
        p('• ' + texto)
    h('1.3 Fundamento y alcance', 2)
    p('Una configuración queda determinada por el estado, la posición del cabezal y el contenido de la cinta. La función de transición es parcial: cuando no existe una regla aplicable, la máquina se detiene. La parada no implica aceptación o rechazo porque el formato del proyecto no exige conjuntos de estados finales. Tampoco se interpreta el contenido como una cantidad unaria.')
    p('Las limitaciones prácticas son los recursos de la computadora. El programa no establece un máximo de estados, reglas, pasos o celdas. La cancelación permite interrumpir una máquina que no termina, sin afirmar que se ha decidido el problema general de la parada.')

    nueva('2 Especificación de la máquina en YAML')
    p('YAML permite expresar listas y mapas legibles [2]. Cada archivo contiene una única clave raíz mt. El lector usa BaseLoader de PyYAML y conserva los escalares como texto; de ese modo, 0 o yes pueden ser símbolos sin convertirse implícitamente en números o valores booleanos [3].')
    tabla(['Campo', 'Requisito', 'Significado'], [
        ['estados', 'Obligatorio', 'Lista no vacía de estados distintos.'],
        ['alfabeto', 'Obligatorio', 'Lista no vacía de símbolos distintos; entrada y cinta comparten alfabeto.'],
        ['estado_inicial', 'Obligatorio', 'Estado perteneciente a estados.'],
        ['transiciones', 'Obligatorio', 'Lista de cuádruplas; puede ser [].'],
        ['blanco', 'Opcional', 'Símbolo blanco; B si se omite. Debe pertenecer al alfabeto.'],
        ['nombre y descripcion', 'Opcionales', 'Textos descriptivos de la máquina.'],
    ], [1.3, 1.1, 4.3])
    codigo('''mt:
  nombre: Ejemplo mínimo
  estados: [q0, q1]
  alfabeto: [a, b, B]
  blanco: B
  estado_inicial: q0
  transiciones:
    - q0 a b q1
    - q1 b R q0''')
    p('Los estados y símbolos son cadenas no vacías. La forma textual de la cuádrupla separa sus cuatro elementos por espacios. Para símbolos que contienen espacios o caracteres especiales se utiliza la forma de lista YAML:')
    codigo("    - [q0, '#', R, q1]")
    p('El uso de una lista también evita que # se interprete como comentario YAML. La modalidad de entrada JSON permite utilizar símbolos de varios caracteres sin imponer un alfabeto unario.')

    nueva('3 Semántica y convenciones de salida')
    h('3.1 Cuádruplas', 2)
    p('Cada transición tiene la forma (estado, lectura, operación, siguiente estado). La operación L mueve una celda a la izquierda y R una a la derecha, conservando el símbolo. Cualquier otra operación que represente un símbolo del alfabeto lo escribe en la celda actual sin mover el cabezal. Después se actualiza el estado y se incrementa el contador en uno.')
    p('El prefijo W: fuerza una escritura: W:R escribe el símbolo R en vez de mover el cabezal; W:W:a escribe el símbolo W:a. Esta convención elimina la ambigüedad sin excluir esos símbolos del alfabeto. Una operación que escribe y después desplaza requiere dos cuádruplas y, por tanto, dos pasos.')
    h('3.2 Blanco y configuración inicial', 2)
    p('Los ejemplos usan B como blanco. La entrada ocupa las posiciones 0 a n − 1 y el cabezal comienza en 0. Para la entrada vacía, la celda 0 contiene blanco. Las posiciones que no se almacenan explícitamente también contienen blanco. El cabezal puede llegar a cualquier índice entero que los recursos disponibles permitan representar.')
    h('3.3 Descripciones instantáneas', 2)
    p('Se registra la DI 0 y una DI después de cada transición. Cada registro incluye paso, estado, cabezal, índice izquierdo y la secuencia completa del intervalo que contiene la entrada original y todas las posiciones visitadas. Fuera de ese intervalo hay blancos implícitos. La notación textual [s] identifica la celda bajo el cabezal; el JSONL conserva los símbolos de manera inequívoca.')
    h('3.4 Extracción del resultado', 2)
    p('Al detenerse, se presenta la lista de símbolos entre la primera y la última celda no blanca. Los blancos interiores se conservan; una cinta completamente blanca produce []. La concatenación se ofrece como una segunda representación. Los blancos exteriores, el estado y el cabezal siguen disponibles en la DI final. Esta convención no transforma números ni elimina separadores o marcadores.')
    p('Una ejecución cancelada informa contenido parcial y cancelada=true. No se presenta como una computación concluida. Pausar permite continuar; cancelar requiere preparar una nueva simulación si se desea volver a comenzar.')

    nueva('4 Diseño e implementación')
    p('El código se organiza en módulos con responsabilidades específicas. El modelo validado es inmutable; las transiciones se consultan mediante un diccionario cuya clave es el par (estado, símbolo leído). La cinta es otro diccionario, de índices enteros a símbolos, y conserva únicamente las celdas no blancas.')
    tabla(['Archivo', 'Responsabilidad'], [
        ['simulador/modelo.py', 'Lectura YAML, validación defensiva y definición de la máquina.'],
        ['simulador/motor.py', 'Estado de ejecución, cinta, aplicación de una regla, DI y resultado.'],
        ['simulador/interfaz.py', 'Interfaz Tkinter, controles de ejecución y traza en disco.'],
        ['simulador/__main__.py', 'Argumentos de terminal, ejecución y arranque de la interfaz.'],
        ['tests/test_simulador.py', 'Pruebas del motor, lector, ejemplos y terminal.'],
        ['herramientas/medir.py', 'Mediciones reproducibles del número de pasos y tamaño de la traza.'],
    ], [2.35, 4.35])
    h('4.1 Ejecución y capacidad de respuesta', 2)
    p('La interfaz usa Tkinter [4]. La ejecución rápida trabaja por lotes breves de aproximadamente ocho milisegundos y devuelve el control al ciclo de eventos. Este intervalo regula el refresco de la interfaz; no limita la cantidad de pasos de la máquina. La animación lenta permite revisar cada transición.')
    h('4.2 Registro de la computación', 2)
    p('La traza se escribe de manera incremental en un archivo temporal JSONL UTF-8. La ventana conserva las últimas 200 DI y abrevia líneas extensas, mientras el archivo contiene todas las configuraciones completas. Esta decisión reduce la memoria de la interfaz sin truncar la computación registrada. Exportar copia la traza hasta el paso actual o, después de la parada, la traza completa con su resumen final.')
    h('4.3 Validación defensiva', 2)
    p('Se rechazan archivos ilegibles, YAML mal formado, claves repetidas, campos desconocidos, estados o símbolos inexistentes, listas duplicadas, transiciones con un número incorrecto de elementos y dos reglas para el mismo par de lectura. Las entradas también se verifican contra el alfabeto. Las etiquetas YAML no se usan para construir objetos Python ejecutables.')

    nueva('5 Diagrama de flujo de la simulación')
    figura('output/figuras/flujo_simulacion.png', 6.3, 'Figura 1. Flujo desde la lectura del YAML hasta la parada o cancelación.')

    nueva('6 Manual de instalación y uso')
    h('6.1 Instalación', 2)
    p('Se requiere Python 3.11 o superior con Tkinter. Desde la carpeta del repositorio, instale la dependencia y abra la aplicación. En Linux y macOS sustituya py por python3; algunas distribuciones Linux requieren python3-tk.')
    codigo('py -m pip install -r requirements.txt\npy -m simulador')
    h('6.2 Operación de la interfaz', 2)
    for texto in ['1. Abra un archivo mediante Abrir YAML, use Cargar ruta o seleccione un ejemplo.', '2. Escriba la entrada y pulse Preparar / reiniciar; esto registra la configuración inicial.', '3. Use Un paso o Ejecutar. Desmarque Animación lenta para acelerar la ejecución.', '4. Use Pausar para continuar después o Cancelar para terminar con contenido parcial.', '5. Pulse Exportar traza para guardar las configuraciones en formato JSONL.']:
        p(texto)
    figura('evidencia/capturas/02_adn_paso_08.png', 6.5, 'Figura 2. Ejecución real del complemento de ADN al finalizar en ocho pasos.')

    nueva('7 Manual de terminal y lectura de la traza')
    p('Para cambiar la entrada en la interfaz, prepare una nueva simulación. El campo visible no modifica una ejecución ya preparada. Para la entrada vacía deje el campo sin texto; para símbolos compuestos use Lista JSON de símbolos, por ejemplo, ["A", "C"].')
    codigo('''py -m simulador ejemplos/complemento_adn.yaml ACGT --traza adn.jsonl
py -m simulador ejemplos/duplicacion_ternaria.yaml abc --traza dup.jsonl
py -m simulador ejemplos/duplicacion_ternaria.yaml ""
py -m simulador ejemplos/bucle_cancelable.yaml''')
    p('Por defecto, la terminal muestra todas las DI y el resumen final. Ctrl+C cancela la ejecución. El argumento --resumen omite las DI de la pantalla si el usuario así lo solicita; --traza sigue registrándolas cuando se proporciona. La opción --tokens recibe una lista JSON y permite separar símbolos de varios caracteres. La ayuda completa se obtiene con py -m simulador --help.')
    tabla(['Código de salida', 'Significado'], [['0', 'La máquina se detuvo por ausencia de regla.'], ['2', 'Error de archivo, especificación, entrada o almacenamiento.'], ['130', 'Cancelación por el usuario mediante Ctrl+C.']], [1.5, 5.2])
    h('7.1 Formato JSONL', 2)
    p('Cada línea del archivo es un objeto JSON independiente. Las líneas tipo=di contienen paso, estado, cabezal, izquierda y celdas. La posición izquierda + j corresponde al elemento j de la lista de celdas. La última línea tipo=resultado incluye el estado de parada, el contador, el contenido y las banderas detenida y cancelada.')
    codigo('''{"tipo":"di","paso":0,"estado":"q0","cabezal":0,
 "izquierda":0,"celdas":["A","C","G","T"]}
{"tipo":"resultado","estado":"q0","pasos":8,"cabezal":4,
 "cancelada":false,"detenida":true,
 "simbolos":["T","G","C","A"],"texto":"TGCA"}''')
    p('El ejemplo anterior muestra la primera y la última línea de la ejecución ACGT; el archivo real también contiene las nueve DI de los pasos 0 a 8. No se omiten configuraciones intermedias en el JSONL.')
    h('7.2 Errores frecuentes', 2)
    p('Si un símbolo no está declarado, agréguelo al alfabeto o corrija la entrada. Si el archivo contiene # como lectura, utilice una lista YAML con el símbolo entre comillas. Si dos reglas comparten estado y lectura, elimine la ambigüedad. Si una ejecución parece no terminar, pause para inspeccionar o cancele; no se aplica una parada automática.')

    nueva('8 Primera máquina complemento de ADN')
    p('La máquina recibe una palabra sobre {A, C, G, T} y produce su complemento: A ↔ T y C ↔ G. Recorre la entrada de izquierda a derecha. El estado q0 escribe el complemento y qm mueve el cabezal una posición; al llegar al blanco en q0 no existe regla y termina.')
    codigo((RAIZ / 'ejemplos/complemento_adn.yaml').read_text(encoding='utf-8'))
    tabla(['Entrada', 'Resultado', 'Pasos'], [['vacía', 'vacía', 0], ['A', 'T', 2], ['ACGT', 'TGCA', 8], ['GATTACA', 'CTAATGT', 14]], [2, 3.2, 1.5])
    p('Invariante: al comenzar una iteración en q0 y posición i, las celdas anteriores a i contienen el complemento del prefijo leído y las restantes conservan la entrada. La escritura y el movimiento mantienen esta propiedad. Después de n iteraciones toda la palabra está transformada y el cabezal se encuentra en n.')

    nueva('9 Segunda máquina duplicación ternaria')
    mt = cargar_maquina(RAIZ / 'ejemplos/duplicacion_ternaria.yaml')
    p(f'La máquina transforma w en w#w para w ∈ {{a, b, c}}*. Tiene {len(mt.estados)} estados y {len(mt.transiciones)} reglas. La definición completa se incluye en los anexos y en ejemplos/duplicacion_ternaria.yaml. El separador # y los marcadores X, Y, Z pertenecen al mismo alfabeto de entrada y cinta; el dominio del algoritmo se restringe a las palabras originales sobre a, b y c.')
    tabla(['Fase', 'Comportamiento'], [['Preparación', 'Recorre w, escribe # en el primer blanco y vuelve a la posición 0.'], ['Selección', 'Salta X, Y, Z y marca el siguiente símbolo sin copiar.'], ['Copia', 'El estado recuerda el símbolo; recorre hasta el blanco derecho y lo escribe.'], ['Retorno', 'Regresa hasta el blanco izquierdo y reinicia la selección.'], ['Restauración', 'Al encontrar #, restaura los marcadores de derecha a izquierda.']], [1.4, 5.3])
    traza = [json.loads(x) for x in (RAIZ / 'evidencia/duplicacion_abc.jsonl').read_text(encoding='utf-8').splitlines()]
    tabla(['Paso', 'Estado', 'Cabezal', 'Celdas de la DI'], [[r['paso'], r['estado'], r['cabezal'], ' '.join(r['celdas'])] for r in traza if r['tipo'] == 'di' and r['paso'] in [0, 25, 61]], [0.6, 1, 0.9, 4.2])
    p('La tabla selecciona tres DI de la ejecución de abc. El archivo JSONL contiene las 62 configuraciones, incluida la inicial. El cabezal final queda en −1 y no existe una transición para el blanco en qlim.')
    p('Invariante: después de k copias, los primeros k símbolos originales están marcados y a la derecha de # aparece exactamente el prefijo de longitud k de w. El estado de copia conserva el símbolo seleccionado. Al completar n copias, la restauración recupera la palabra original sin alterar la copia.')
    tabla(['Entrada', 'Resultado', 'Pasos'], [['vacía', '#', 4], ['a', 'a#a', 17], ['ab', 'ab#ab', 36], ['abc', 'abc#abc', 61]], [2, 3.2, 1.5])

    nueva('10 Pruebas y resultados')
    xml = ET.parse(RAIZ / 'evidencia/pruebas.xml').getroot()
    suites = list(xml.iter('testsuite'))
    total = sum(int(s.get('tests', 0)) for s in suites)
    fallos = sum(int(s.get('failures', 0)) + int(s.get('errors', 0)) for s in suites)
    p(f'La ejecución de pytest registró {total} casos de prueba y {fallos} fallos o errores. Se verificaron por comparación las 364 palabras ternarias de longitud 0 a 5: en cada ejecución se comprobó el resultado w#w, la posición final del cabezal y el conteo exacto de pasos. Las evidencias JUnit y las trazas originales se conservan en evidencia/.')
    tabla(['Área', 'Verificación realizada'], [['Resultados de ejemplos', 'Complementos conocidos y duplicación exhaustiva hasta longitud cinco.'], ['Cuádruplas', 'Escritura sin movimiento, borrado y símbolos L/R como datos.'], ['Entradas', 'Cadena vacía, símbolos compuestos, espacios y símbolos no declarados.'], ['YAML', 'Campos faltantes, duplicados, transiciones ambiguas y símbolos/estados desconocidos.'], ['Cinta y cancelación', '15001 pasos hacia cada sentido sin un límite del motor y cancelación explícita.'], ['Traza', 'Todas las DI 0 a 8 y el resultado de ACGT, con las celdas correctas.'], ['Interfaz real', 'Preparación, pasos, parada y cancelación con capturas y JSONL de respaldo.']], [1.6, 5.1])
    p('El presupuesto de 10000 pasos empleado por el arnés de pruebas de los ejemplos sirve para detectar regresiones; no está presente en el motor ni en la interfaz. Las pruebas de desplazamiento ejecutan más de 15000 pasos expresamente.')
    h('10.1 Reproducción', 2)
    codigo('py -m pip install pytest\npy -m pytest -q\npy herramientas/medir.py')
    p('Las mediciones evalúan longitudes de 0 a 64 y acumulan tanto transiciones como celdas materializadas en las DI. No se presenta una medición de tiempo de pared como prueba de complejidad; el conteo de operaciones explica el crecimiento sin depender de la velocidad de la computadora.')
    p('La revisión local se realizó en Windows con Python 3.14. La configuración de GitHub Actions incluye Python 3.11 a 3.14 para las pruebas de motor y terminal. El estado remoto del flujo puede consultarse en la pestaña Actions del repositorio.')

    nueva('11 Análisis de complejidad')
    p('Sea n la longitud de una entrada válida del algoritmo de ejemplo y T(n) el número de cuádruplas ejecutadas. Se usa un modelo RAM de costo unitario y acceso esperado constante a diccionarios. El tamaño de la máquina se considera fijo para cada ejemplo. La carga y validación tienen costo esperado O(|Q| + |Γ| + |δ|) en elementos de especificación, aparte de la lectura del texto.')
    h('11.1 Complemento de ADN', 2)
    p('Cada símbolo requiere una escritura y un movimiento: T(n) = 2n. La inicialización y el resultado agregan O(n + 1), por lo que el motor completo tarda Θ(n + 1). La cinta ocupa O(n + 1) espacio. Para n ≥ 1, todas las DI tienen n celdas salvo la última, que incluye el blanco de la posición n; se serializan 2n² + n + 1 celdas. Con traza completa, el simulador tarda Θ((n + 1)²) y produce ese orden de volumen en disco.')
    h('11.2 Duplicación ternaria', 2)
    p('La preparación consume 2n + 3 pasos. La copia número k, para 1 ≤ k ≤ n, consume 2n + 2k + 4 pasos: selección de marcadores, escritura, búsqueda del extremo y retorno. La restauración consume 3n + 1. En consecuencia:')
    codigo('T(n) = (2n + 3) + sumatorio[k=1..n](2n + 2k + 4) + (3n + 1)\n     = 3n² + 10n + 4')
    p('El motor tarda Θ((n + 1)²) y usa O(n + 1) espacio. La amplitud final visitada es 2n + 2, incluidos los blancos de los extremos. Durante una fracción constante de las Θ(n²) transiciones, la DI ocupa Θ(n) celdas; por ello el registro íntegro requiere Θ((n + 1)³) tiempo y volumen en disco.')
    tabla(['n', 'Pasos ADN', 'Pasos duplicación', 'Celdas de traza duplicación'], [[4, 8, 92, 750], [8, 16, 276, 3972], [16, 32, 932, 25024], [32, 64, 3396, 175736], [64, 128, 12932, 1313000]], [0.5, 1.3, 1.8, 3.1])
    p('La RAM no almacena toda la historia: conserva la cinta, una DI temporal y una ventana de texto acotada. Para estos ejemplos su uso es O(n + 1), además de la definición. En un análisis por bits hay que contar el tamaño de índices, contadores y símbolos; los campos numéricos JSON agregan O(T(n) log(T(n) + n + 1)) bytes, dominados asintóticamente por las celdas de estos dos ejemplos con alfabetos fijos.')

    nueva('12 Conclusiones y referencias')
    h('12.1 Conclusiones', 2)
    p('La implementación reproduce las operaciones de una máquina determinista de una cinta y mantiene el estado, el cabezal y el contenido de forma explícita. La ausencia de una transición es la condición de parada, mientras que la cancelación se informa por separado. Las pruebas verifican tanto los resultados como las convenciones de escritura y desplazamiento.')
    p('Los dos ejemplos muestran costos distintos: un recorrido de complemento requiere 2n cuádruplas y la copia mediante recorridos repetidos requiere 3n² + 10n + 4. Conservar la computación completa tiene un costo adicional: el simulador debe materializar cada configuración, lo que eleva el crecimiento a cuadrático y cúbico, respectivamente.')
    h('12.2 Recomendaciones de uso', 2)
    p('Para estudiar una transición conviene usar el modo paso a paso. En entradas largas, la ejecución rápida y la exportación JSONL permiten consultar toda la historia fuera de la ventana. Antes de cargar una máquina nueva se deben revisar sus invariantes y el significado del resultado; una parada fuera del dominio previsto por su algoritmo no equivale a una respuesta correcta para ese algoritmo.')
    h('12.3 Recursos de entrega', 2)
    p('Repositorio de código: ' + datos['repositorio'])
    if datos['youtube_url']:
        p('Video de YouTube no listado: ' + datos['youtube_url'])
    else:
        p('Video demostrativo y subtítulos: video/presentacion.mp4 y video/subtitulos.srt, incluidos con el proyecto.')
    h('12.4 Referencias', 2)
    for texto in [
        '[1] Universidad del Valle de Guatemala. (2026). Proyecto 3. Teoría de la Computación CC2019, sección 30. Enunciado del curso.',
        '[2] YAML Language Development Team. (2021). YAML Ain’t Markup Language, versión 1.2.2. https://yaml.org/spec/1.2.2/',
        '[3] PyYAML. (s. f.). PyYAML Documentation. https://pyyaml.org/wiki/PyYAMLDocumentation',
        '[4] Python Software Foundation. (s. f.). tkinter — Python interface to Tcl/Tk. https://docs.python.org/3.14/library/tkinter.html',
    ]:
        p(texto)

    lineas = (RAIZ / 'ejemplos/duplicacion_ternaria.yaml').read_text(encoding='utf-8').splitlines()
    nueva('Anexo A Definición de la duplicación ternaria')
    p('La siguiente especificación coincide con el archivo ejecutado en las pruebas. Cada fila define una única escritura o un único movimiento.')
    codigo('\n'.join(lineas[:37]))
    nueva('Anexo A Continuación de las transiciones')
    codigo('\n'.join(lineas[37:]))
    h('Anexo B Bucle auxiliar para cancelación', 2)
    codigo((RAIZ / 'ejemplos/bucle_cancelable.yaml').read_text(encoding='utf-8'))
    p('Este archivo no sustituye las dos máquinas de ejemplo. Su única regla desplaza el cabezal hacia la izquierda sobre blancos para demostrar que el usuario puede cancelar una computación que no se detiene por sí sola.')

    path = salida / 'Informe_Proyecto_3.docx'
    for raiz in [doc._element, doc.styles.element]:
        for borde in list(raiz.xpath('.//w:pBdr')):
            borde.getparent().remove(borde)
    doc.save(path)
    print(path)


if __name__ == '__main__':
    main()
