"""Genera evidencia reproducible del número de pasos y volumen de la traza."""

import csv
import json
from pathlib import Path
import sys

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from simulador import Simulacion, cargar_maquina


def main():
    salida = RAIZ / 'evidencia'
    salida.mkdir(exist_ok=True)
    filas = []
    for nombre, letra in [('complemento_adn', 'A'), ('duplicacion_ternaria', 'a')]:
        mt = cargar_maquina(RAIZ / 'ejemplos' / (nombre + '.yaml'))
        for n in [0, 1, 2, 4, 8, 16, 32, 64]:
            sim = Simulacion(mt, letra * n)
            celdas_di = len(sim.configuracion().celdas)
            while sim.paso():
                celdas_di += sim.derecha - sim.izquierda + 1
            filas.append({'maquina': nombre, 'n': n, 'pasos': sim.pasos,
                          'descripciones': sim.pasos + 1, 'celdas_en_traza': celdas_di,
                          'amplitud_final': sim.derecha - sim.izquierda + 1,
                          'resultado': ''.join(sim.resultado())})
    with (salida / 'crecimiento.csv').open('w', encoding='utf-8', newline='') as f:
        escritor = csv.DictWriter(f, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)
    (salida / 'crecimiento.json').write_text(json.dumps(filas, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(filas, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
