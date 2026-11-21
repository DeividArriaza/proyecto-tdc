"""Pruebas del ciclo de eventos; se omiten cuando no existe servidor gráfico."""
import json
import tkinter as tk
import time
import pytest

from simulador.interfaz import Aplicacion


@pytest.fixture(scope='module')
def app():
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f'No hay un servidor gráfico disponible: {exc}')
    root.withdraw()
    a = Aplicacion(root)
    yield a
    a.cerrar()


def test_ejecucion_continua_y_traza(app):
    app.ejemplo('duplicacion_ternaria.yaml', 'abc')
    assert app.preparar()
    app.lento.set(False)
    app.ejecutar()
    limite = time.monotonic() + 5
    while not app.finalizado and time.monotonic() < limite:
        app.root.update()
    assert app.finalizado
    assert app.sim.pasos == 61
    assert ''.join(app.sim.resultado()) == 'abc#abc'
    filas = [json.loads(x) for x in app.ruta_traza.read_text(encoding='utf-8').splitlines()]
    assert [x['paso'] for x in filas[:-1]] == list(range(62))
    assert filas[-1]['detenida'] and not filas[-1]['cancelada']


def test_pausar_reanudar_y_cancelar(app):
    app.ejemplo('bucle_cancelable.yaml', '')
    assert app.preparar()
    app.ejecutar()
    tarea = app.tarea
    app.pausar()
    assert app.tarea is None and not app.ejecutando
    assert tarea not in app.root.tk.call('after', 'info')
    app.root.update()
    assert app.sim.pasos == 0
    app.ejecutar()
    app.root.update()
    assert app.sim.pasos >= 1
    app.cancelar()
    pasos = app.sim.pasos
    app.root.update()
    assert app.sim.pasos == pasos and app.sim.cancelada
    assert not app.sim.detenida and app.finalizado
    assert app.tarea is None
