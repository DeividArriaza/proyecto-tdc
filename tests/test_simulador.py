from itertools import product
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest
from simulador import ErrorEspecificacion, cargar_maquina, leer_yaml, Simulacion

RAIZ = Path(__file__).resolve().parents[1]


def ejecutar(nombre, entrada):
    sim = Simulacion(cargar_maquina(RAIZ / 'ejemplos' / nombre), entrada)
    # Límite exclusivamente del arnés de pruebas para detectar regresiones.
    for _ in range(10000):
        if not sim.paso():
            return sim
    pytest.fail('El ejemplo no terminó dentro del presupuesto de esta prueba.')


@pytest.mark.parametrize('entrada', ['', 'A', 'ACGT', 'AAAA', 'GATTACA', 'TTCCGGAA'])
def test_complemento(entrada):
    sim = ejecutar('complemento_adn.yaml', entrada)
    assert ''.join(sim.resultado()) == entrada.translate(str.maketrans('ACGT', 'TGCA'))
    assert sim.pasos == 2 * len(entrada)
    assert sim.cabezal == len(entrada)


@pytest.mark.parametrize('n', range(6))
def test_duplicacion_exhaustiva(n):
    for simbolos in product('abc', repeat=n):
        palabra = ''.join(simbolos)
        sim = ejecutar('duplicacion_ternaria.yaml', palabra)
        assert ''.join(sim.resultado()) == palabra + '#' + palabra
        assert sim.cabezal == -1
        assert sim.pasos == 3 * n * n + 10 * n + 4


BASE = '''mt:
  estados: [q, p]
  alfabeto: [a, B]
  estado_inicial: q
  transiciones:
    - q a R p
'''


@pytest.mark.parametrize('texto', [
    '', 'mt: []', BASE.replace('q a R p', 'q a R z'),
    BASE.replace('q a R p', 'q c R p'),
    BASE.replace('q a R p', 'q a Z p'),
    BASE.replace('estado_inicial: q', 'estado_inicial: z'),
    BASE.replace('[q, p]', '[q, q]'),
    BASE.replace('[a, B]', '[a]'),
    BASE.replace('q a R p', 'q a R'),
    BASE.replace('q a R p', 'q a R p\n    - q a L p'),
    BASE.replace('  estado_inicial: q', '  estado_inicial: q\n  estado_inicial: p'),
    BASE + '  typo: x\n',
    BASE.replace('estados: [q, p]', 'estados: [&x [*x]]'),
    'mt: !!python/object/apply:os.system [echo no]',
])
def test_rechaza_especificaciones_invalidas(texto):
    with pytest.raises(ErrorEspecificacion):
        leer_yaml(texto)


def test_escritura_no_mueve_y_borra():
    mt = leer_yaml(BASE.replace('q a R p', 'q a B p'))
    sim = Simulacion(mt, 'a')
    assert sim.paso()
    assert sim.cabezal == 0
    assert sim.resultado() == []
    assert sim.cinta == {}
    assert not sim.paso()


def test_izquierda_cancelacion_y_cinta_no_acotada():
    sim = Simulacion(cargar_maquina(RAIZ / 'ejemplos/bucle_cancelable.yaml'), '')
    for _ in range(15001):
        assert sim.paso()
    assert sim.cabezal == -15001
    assert not sim.detenida
    sim.cancelar()
    assert not sim.paso()
    assert sim.resumen()['cancelada']
    assert not sim.resumen()['detenida']


def test_derecha_no_acotada():
    mt = leer_yaml((RAIZ / 'ejemplos/bucle_cancelable.yaml').read_text(encoding='utf-8').replace('q B L q', 'q B R q'))
    sim = Simulacion(mt, '')
    for _ in range(15001):
        assert sim.paso()
    assert sim.cabezal == 15001


def test_simbolos_reservados_multicaracter_y_espacio():
    mt = leer_yaml('''mt:
  estados: [q, p, r]
  alfabeto: [R, L, ' ', hola, '0', B]
  estado_inicial: q
  transiciones:
    - [q, hola, 'W:R', p]
    - [p, R, 'W: ', r]
''')
    sim = Simulacion(mt, ['hola'])
    assert sim.paso() and sim.leer() == 'R' and sim.cabezal == 0
    assert sim.paso() and sim.resultado() == [' ']
    assert sim.detenida


def test_numeros_y_booleanos_yaml_se_conservan_como_simbolos():
    mt = leer_yaml(BASE.replace('[a, B]', '[0, yes, on, B]').replace('q a R p', 'q 0 yes p'))
    sim = Simulacion(mt, '0')
    sim.paso()
    assert sim.resultado() == ['yes']


def test_blancos_interiores_y_di_inicial():
    mt = leer_yaml(BASE.replace('    - q a R p', '    - q a R p'))
    sim = Simulacion(mt, 'BaBaB')
    assert sim.resultado() == ['a', 'B', 'a']
    conf = sim.configuracion()
    assert conf.paso == 0 and conf.izquierda == 0 and len(conf.celdas) == 5


def test_entrada_invalida():
    with pytest.raises(ValueError, match='no declarado'):
        Simulacion(leer_yaml(BASE), 'x')


def test_sin_transiciones_y_datos_inmutables():
    mt = leer_yaml(BASE.replace('transiciones:\n    - q a R p', 'transiciones: []'))
    sim = Simulacion(mt, 'a')
    assert sim.detenida and not sim.paso() and sim.pasos == 0
    with pytest.raises(TypeError):
        mt.transiciones[('q', 'a')] = None


def test_cli_traza_completa(tmp_path):
    ruta = tmp_path / 'traza.jsonl'
    proc = subprocess.run([sys.executable, '-m', 'simulador', 'ejemplos/complemento_adn.yaml', 'ACGT', '--traza', str(ruta)], cwd=RAIZ, capture_output=True, text=True, encoding='utf-8')
    assert proc.returncode == 0, proc.stderr
    filas = [json.loads(x) for x in ruta.read_text(encoding='utf-8').splitlines()]
    assert [x['paso'] for x in filas[:-1]] == list(range(9))
    assert filas[0]['celdas'] == list('ACGT')
    assert filas[-2]['celdas'] == list('TGCAB')
    assert filas[-1]['texto'] == 'TGCA'
    assert filas[-1]['detenida'] and not filas[-1]['cancelada']


def test_cli_error_y_tokens(tmp_path):
    proc = subprocess.run([sys.executable, '-m', 'simulador', 'ejemplos/complemento_adn.yaml', 'Q'], cwd=RAIZ, capture_output=True)
    assert proc.returncode == 2
    proc = subprocess.run([sys.executable, '-m', 'simulador', 'ejemplos/complemento_adn.yaml', '--tokens', '["A","C"]', '--resumen'], cwd=RAIZ, capture_output=True, text=True, encoding='utf-8')
    assert proc.returncode == 0
    assert json.loads(proc.stdout)['texto'] == 'TG'
    ruta = tmp_path / 'unicode.yaml'
    ruta.write_text(BASE.replace('[a, B]', '[🧠, B]').replace('q a R p', 'q 🧠 R p'), encoding='utf-8')
    proc = subprocess.run([sys.executable, '-m', 'simulador', str(ruta), '🧠', '--resumen'], cwd=RAIZ,
                          capture_output=True, env={**os.environ, 'PYTHONIOENCODING': 'cp1252'})
    assert proc.returncode == 0
    assert json.loads(proc.stdout.decode('utf-8'))['texto'] == '🧠'
