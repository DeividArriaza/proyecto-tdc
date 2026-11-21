"""Interfaz de terminal. Sin argumentos se abre la aplicación de escritorio."""

import argparse
from contextlib import ExitStack
import json
from pathlib import Path
import sys
from .modelo import cargar_maquina, ErrorEspecificacion
from .motor import Simulacion, escribir_di, escribir_resumen


def main(argv=None):
    # También conserva alfabetos Unicode al redirigir la salida en Windows.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description='Simulador de máquinas de Turing de una cinta')
    parser.add_argument('maquina', nargs='?', help='Archivo YAML; sin archivo abre la interfaz gráfica')
    parser.add_argument('entrada', nargs='?', default='', help='Entrada como cadena; por defecto vacía')
    parser.add_argument('--tokens', help='Entrada como lista JSON; permite símbolos de varios caracteres')
    parser.add_argument('--traza', type=Path, help='Guardar todas las DI y el resultado como JSONL UTF-8')
    parser.add_argument('--resumen', action='store_true', help='Mostrar solo el resultado; omite DI en pantalla')
    args = parser.parse_args(argv)
    if args.maquina is None:
        from .interfaz import iniciar
        iniciar()
        return 0
    try:
        entrada = json.loads(args.tokens) if args.tokens is not None else args.entrada
        if args.tokens is not None and not isinstance(entrada, list):
            raise ValueError('--tokens debe ser una lista JSON de símbolos.')
        sim = Simulacion(cargar_maquina(args.maquina), entrada)
        with ExitStack() as stack:
            archivo = stack.enter_context(args.traza.open('w', encoding='utf-8')) if args.traza else None

            def registrar():
                if archivo:
                    escribir_di(archivo, sim)
                if not args.resumen:
                    print(sim.configuracion().texto())

            registrar()
            try:
                while sim.paso():
                    registrar()
            except KeyboardInterrupt:
                sim.cancelar()
            if archivo:
                escribir_resumen(archivo, sim)
            print(json.dumps(sim.resumen(), ensure_ascii=False))
            return 130 if sim.cancelada else 0
    except (ErrorEspecificacion, ValueError, OSError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
