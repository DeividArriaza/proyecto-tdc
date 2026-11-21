"""Captura la aplicación real durante ejecuciones reproducibles de demostración.

Este arnés llama a los mismos métodos de la interfaz que sus botones.
No sustituye el motor ni dibuja una interfaz simulada para el video.
"""
from pathlib import Path
import ctypes
import json
import sys
import time
import subprocess
import tkinter as tk
from PIL import ImageGrab

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from simulador.interfaz import Aplicacion


def main():
    if len(sys.argv) == 1:
        for escena in ['inicio', 'adn', 'dup', 'bucle']:
            subprocess.run([sys.executable, __file__, escena], check=True)
        return
    escena = sys.argv[1]
    if sys.platform == 'win32':
        ctypes.windll.user32.SetProcessDPIAware()
    salida = RAIZ / 'evidencia' / 'capturas'
    salida.mkdir(parents=True, exist_ok=True)
    root = tk.Tk()
    app = Aplicacion(root)
    root.geometry('1180x820+30+30')
    root.attributes('-topmost', True)
    root.update()
    registros = []

    def capturar(nombre):
        grupo = 'adn' if nombre.startswith(('01_', '02_')) else 'dup' if nombre.startswith('03_') else 'bucle' if nombre.startswith('04_') else 'inicio'
        if grupo != escena:
            return
        app.actualizar()
        root.update()
        root.update_idletasks()
        time.sleep(0.08)  # Permite que el compositor pinte el nuevo estado.
        hwnd = ctypes.windll.user32.GetAncestor(root.winfo_id(), 2) if sys.platform == 'win32' else None
        captura = None
        for intento in range(5):
            try:
                if hwnd and intento == 0:
                    captura = ImageGrab.grab(window=hwnd)
                else:
                    root.lift()
                    root.update()
                    time.sleep(0.15)
                    x, y = root.winfo_rootx(), root.winfo_rooty()
                    captura = ImageGrab.grab(bbox=(x, y, x + root.winfo_width(), y + root.winfo_height()))
                if captura.convert('L').getextrema()[1] >= 30:
                    break
                captura.close()
                captura = None
            except OSError:
                time.sleep(0.15)
        if captura is None:
            raise RuntimeError(f'Captura inválida en {nombre}; no se utiliza como evidencia.')
        captura.save(salida / (nombre + '.png'))
        captura.close()
        if app.sim:
            registros.append({'captura': nombre, **app.sim.resumen()})

    capturar('00_inicio')
    app.ejemplo('complemento_adn.yaml', 'ACGT')
    capturar('01_adn_cargado')
    assert app.preparar()
    capturar('02_adn_paso_00')
    for i in range(1, 9):
        app.paso()
        capturar(f'02_adn_paso_{i:02}')
    assert app.sim.pasos == 8 and app.sim.resultado() == list('TGCA')
    app.archivo.flush()
    (RAIZ / 'evidencia' / 'adn_gui.jsonl').write_bytes(app.ruta_traza.read_bytes())
    app.ejemplo('duplicacion_ternaria.yaml', 'abc')
    assert app.preparar()
    capturar('03_dup_paso_00')
    for i in range(1, 62):
        app.paso()
        if i in [2, 5, 8, 11, 17, 25, 37, 49, 61]:
            capturar(f'03_dup_paso_{i:02}')
    assert app.sim.detenida and app.sim.resultado() == list('abc#abc')
    app.archivo.flush()
    (RAIZ / 'evidencia' / 'duplicacion_gui.jsonl').write_bytes(app.ruta_traza.read_bytes())
    app.ejemplo('bucle_cancelable.yaml', '')
    assert app.preparar()
    capturar('04_bucle_00')
    for i in range(1, 17):
        app.paso()
        if i % 2 == 0:
            capturar(f'04_bucle_{i:02}')
    app.cancelar()
    capturar('04_bucle_cancelado')
    assert app.sim.cancelada and not app.sim.detenida
    app.archivo.flush()
    (RAIZ / 'evidencia' / 'cancelacion_gui.jsonl').write_bytes(app.ruta_traza.read_bytes())
    (RAIZ / 'evidencia' / f'capturas_{escena}.json').write_text(json.dumps(registros, ensure_ascii=False, indent=2), encoding='utf-8')
    app.cerrar()
    print(f'{len(registros) + 1} capturas de la aplicación verificadas en {salida}')


if __name__ == '__main__':
    main()
