"""Empaqueta únicamente archivos versionables; excluye temporales y revisión visual."""
from pathlib import Path
import subprocess
import zipfile

RAIZ = Path(__file__).resolve().parents[1]


def main():
    listado = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=RAIZ)
    rutas = sorted(set(x.decode('utf-8') for x in listado.split(b'\0') if x))
    destino = RAIZ.parent / 'Entrega_Proyecto_3.zip'
    with zipfile.ZipFile(destino, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archivo:
        for ruta in rutas:
            archivo.write(RAIZ / ruta, 'Proyecto_3/' + ruta)
    with zipfile.ZipFile(destino) as archivo:
        assert archivo.testzip() is None
        assert 'Proyecto_3/video/presentacion.mp4' in archivo.namelist()
        assert 'Proyecto_3/output/Informe_Proyecto_3.pdf' in archivo.namelist()
    print(f'{destino} | {len(rutas)} archivos | {destino.stat().st_size/1000000:.1f} MB')


if __name__ == '__main__':
    main()
