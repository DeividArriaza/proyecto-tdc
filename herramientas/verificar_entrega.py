"""Revisa artefactos, decodifica el video completo y registra hashes de entrega."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile
import imageio_ffmpeg
import pymupdf

RAIZ = Path(__file__).resolve().parents[1]


def main():
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    video = RAIZ / 'video/presentacion.mp4'
    metadatos = subprocess.run([ff, '-hide_banner', '-i', str(video)], capture_output=True, text=True, encoding='utf-8', errors='replace').stderr
    dur = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', metadatos)
    segundos = int(dur[1])*3600 + int(dur[2])*60 + float(dur[3])
    assert segundos <= 420
    assert '1920x1080' in metadatos and 'h264' in metadatos and 'aac' in metadatos
    subprocess.run([ff, '-hide_banner', '-loglevel', 'error', '-i', str(video), '-f', 'null', '-'], check=True)
    audio = subprocess.run([ff, '-hide_banner', '-i', str(video), '-vn', '-af', 'volumedetect', '-f', 'null', '-'], capture_output=True, text=True, encoding='utf-8', errors='replace')
    media = re.search(r'mean_volume: ([-\d.]+) dB', audio.stderr)
    assert media and -60 < float(media[1]) < 0
    pdf = pymupdf.open(RAIZ / 'output/Informe_Proyecto_3.pdf')
    assert len(pdf) == 16
    assert '38 casos de prueba' in ''.join(p.get_text() for p in pdf)
    assert all(p.get_text().strip() for p in pdf)
    with zipfile.ZipFile(RAIZ / 'output/Informe_Proyecto_3.docx') as z:
        assert z.testzip() is None
    suites = ET.parse(RAIZ / 'evidencia/pruebas.xml').getroot()
    tests = sum(int(s.get('tests', 0)) for s in suites.iter('testsuite'))
    failures = sum(int(s.get('failures', 0)) + int(s.get('errors', 0)) + int(s.get('skipped', 0)) for s in suites.iter('testsuite'))
    assert tests == 38 and failures == 0
    trazas = {}
    for nombre, pasos, resultado in [('adn_ACGT.jsonl', 8, 'TGCA'), ('duplicacion_abc.jsonl', 61, 'abc#abc')]:
        filas = [json.loads(x) for x in (RAIZ / 'evidencia' / nombre).read_text(encoding='utf-8').splitlines()]
        assert [r['paso'] for r in filas[:-1]] == list(range(pasos+1))
        assert filas[-1]['texto'] == resultado and filas[-1]['detenida']
        trazas[nombre] = {'descripciones': pasos+1, 'pasos': pasos, 'resultado': resultado}
    finales = ['output/Informe_Proyecto_3.docx', 'output/Informe_Proyecto_3.pdf', 'video/presentacion.mp4', 'video/subtitulos.srt']
    manifiesto = {
        'pruebas_locales': {'total': tests, 'fallos': 0, 'omitidas': 0},
        'informe_paginas': len(pdf),
        'video': {'duracion_segundos': segundos, 'resolucion': '1920x1080', 'video': 'H.264', 'audio': 'AAC', 'volumen_medio_db': float(media[1]), 'decodificacion_completa': 'correcta', 'narracion': 'sintética es-GT-AndresNeural'},
        'trazas': trazas,
        'archivos': {f: {'bytes': (RAIZ / f).stat().st_size, 'sha256': hashlib.sha256((RAIZ / f).read_bytes()).hexdigest()} for f in finales},
        'pendientes_externos': ['disponibilidad y registro de ejemplos', 'participación real de integrantes en video', 'publicación no listada de YouTube y enlace', 'registro del grupo en Canvas'],
    }
    (RAIZ / 'evidencia/validacion_final.json').write_text(json.dumps(manifiesto, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(manifiesto, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
