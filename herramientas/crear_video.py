"""Produce MP4 con voz española, subtítulos y capturas de la aplicación real."""
import asyncio
from pathlib import Path
import json
import re
import subprocess
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps
import edge_tts
import imageio_ffmpeg

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from herramientas.figuras import font
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
VIDEO = RAIZ / 'video'
TMP = RAIZ / 'tmp/video'
FIG = RAIZ / 'output/figuras'


def ajuste(draw, texto, fuente, ancho):
    lineas = []
    linea = ''
    for palabra in texto.split():
        nueva = (linea + ' ' + palabra).strip()
        if draw.textlength(nueva, font=fuente) > ancho and linea:
            lineas.append(linea)
            linea = palabra
        else:
            linea = nueva
    if linea:
        lineas.append(linea)
    return lineas


def texto_figura(nombre, titulo, lineas, mono=False):
    im = Image.new('RGB', (1180, 820), '#f8fafc')
    d = ImageDraw.Draw(im)
    d.text((45, 45), titulo, font=font(38, True), fill='#17324d')
    fuente = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 25) if mono else font(29)
    y = 130
    for linea in lineas:
        d.text((45, y), linea, font=fuente, fill='#17324d')
        y += 42 if mono else 65
    im.save(FIG / nombre)


def preparar_figuras():
    texto_figura('yaml_video.png', 'Una definición YAML', [
        'mt:', '  estados: [q0, qm]', '  alfabeto: [A, C, G, T, B]', '  blanco: B', '  estado_inicial: q0',
        '  transiciones:', '    - q0 A T qm', '    - qm T R q0', '', 'Escritura y movimiento son pasos distintos.',
        'W:R escribe el símbolo R sin moverse.'
    ], True)
    motor = (RAIZ / 'simulador/motor.py').read_text(encoding='utf-8').splitlines()
    comienzo = next(i for i, l in enumerate(motor) if 'def paso(self)' in l)
    lineas = [linea[4:] for linea in motor[comienzo:comienzo+12]]
    texto_figura('codigo_video.png', 'simulador/motor.py', lineas, True)
    texto_figura('pruebas_video.png', 'Evidencia de verificación', [
        '38 passed · evidencia/pruebas.xml', '364 palabras ternarias comprobadas', '15001 pasos hacia cada sentido',
        'Entrada vacía y símbolos compuestos', 'Reglas y especificaciones inválidas', 'DI completas y resultado final',
        'py -m pytest -q', 'py herramientas/medir.py'
    ])


async def voz(indice, escena, semaforo):
    archivo = TMP / f'voz_{indice:02}.mp3'
    marcas = TMP / f'marcas_{indice:02}.json'
    if archivo.exists() and marcas.exists():
        return
    async with semaforo:
        eventos = []
        comunicacion = edge_tts.Communicate(escena['narracion'], 'es-GT-AndresNeural', rate='+4%', boundary='SentenceBoundary')
        with archivo.open('wb') as f:
            async for evento in comunicacion.stream():
                if evento['type'] == 'audio':
                    f.write(evento['data'])
                elif evento['type'] == 'SentenceBoundary':
                    eventos.append({'inicio': evento['offset']/10000000, 'duracion': evento['duration']/10000000, 'texto': evento['text']})
        marcas.write_text(json.dumps(eventos, ensure_ascii=False), encoding='utf-8')
        print(f'Voz {indice+1} generada', flush=True)


def duracion(path):
    p = subprocess.run([FFMPEG, '-i', str(path)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    m = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', p.stderr)
    if not m:
        raise RuntimeError(p.stderr[-1000:])
    return int(m[1])*3600 + int(m[2])*60 + float(m[3])


def reloj(segundos):
    milis = round(segundos * 1000)
    return f'{milis//3600000:02}:{milis//60000%60:02}:{milis//1000%60:02},{milis%1000:03}'


def cuadro(escena, indice, captura, subtitulo):
    im = Image.new('RGB', (1920, 1080), '#0e1e30')
    d = ImageDraw.Draw(im)
    d.text((45, 30), escena['titulo'], font=font(43, True), fill='white')
    d.text((1760, 42), f'{indice+1:02} / 10', font=font(24), fill='#a7bbc9')
    with Image.open(RAIZ / captura) as fuente:
        frame = ImageOps.contain(fuente.convert('RGB'), (1215, 846), Image.Resampling.LANCZOS)
        im.paste(frame, (40 + (1215-frame.width)//2, 120 + (846-frame.height)//2))
    x = 1310
    y = 155
    for punto in escena['puntos']:
        for linea in ajuste(d, punto, font(29, True), 540):
            d.text((x, y), linea, font=font(29, True), fill='#dce8ef')
            y += 43
        y += 42
    d.text((1310, 835), 'CC2019 · Proyecto 3', font=font(24), fill='#5cbcc1')
    d.text((1310, 880), 'Capturas de ejecución real', font=font(21), fill='#9ab1c3')
    d.text((1310, 920), 'Narración sintética en español', font=font(21), fill='#9ab1c3')
    d.rectangle((0, 985, 1920, 1080), fill='#07111e')
    lineas = ajuste(d, subtitulo, font(25), 1810)
    if len(lineas) > 2:
        raise RuntimeError('Subtítulo demasiado largo; divida los segmentos.')
    y = 998 if len(lineas) == 2 else 1016
    for linea in lineas:
        ancho = d.textlength(linea, font=font(25))
        d.text(((1920-ancho)/2, y), linea, font=font(25), fill='white')
        y += 34
    return im


def main():
    VIDEO.mkdir(exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    preparar_figuras()
    escenas = json.loads((VIDEO / 'escenas.json').read_text(encoding='utf-8'))

    async def voces():
        semaforo = asyncio.Semaphore(3)
        await asyncio.gather(*(voz(i, e, semaforo) for i, e in enumerate(escenas)))

    asyncio.run(voces())
    offset = 0.0
    subtitulos = []
    detalles = []
    for indice, escena in enumerate(escenas):
        audio = TMP / f'voz_{indice:02}.mp3'
        segundos = duracion(audio) + 0.6
        eventos = json.loads((TMP / f'marcas_{indice:02}.json').read_text(encoding='utf-8'))
        # Se subdividen oraciones largas y se conservan sus marcas de inicio.
        segmentos = []
        for e in eventos:
            palabras = e['texto'].split()
            grupos = [palabras[j:j+19] for j in range(0, len(palabras), 19)]
            antes = 0
            for g in grupos:
                inicio = e['inicio'] + e['duracion'] * antes / max(1, len(palabras))
                fin = e['inicio'] + e['duracion'] * (antes+len(g)) / max(1, len(palabras))
                segmentos.append({'inicio': inicio, 'fin': fin, 'texto': ' '.join(g)})
                antes += len(g)
        if not segmentos:
            raise RuntimeError(f'No se recibieron marcas de voz para la escena {indice}.')
        for s in segmentos:
            subtitulos.append((offset+s['inicio'], offset+s['fin'], s['texto']))
        capturas = escena['imagenes']
        # Las imágenes cambian a intervalos regulares; se mantiene el resultado al final.
        cambios = sorted({0.0, segundos, *(s['inicio'] for s in segmentos), *(s['fin'] for s in segmentos),
                          *(j*segundos/len(capturas) for j in range(1, len(capturas)))})
        lista = TMP / f'lista_{indice:02}.txt'
        contenido = []
        ultima = None
        for j, (inicio, fin) in enumerate(zip(cambios, cambios[1:])):
            if fin-inicio < 0.001:
                continue
            k = min(len(capturas)-1, int((inicio+0.001)/segundos*len(capturas)))
            texto = next((s['texto'] for s in segmentos if s['inicio']-0.001 <= inicio < s['fin']-0.001), '')
            png = TMP / f'cuadro_{indice:02}_{j:03}.png'
            cuadro(escena, indice, capturas[k], texto).save(png)
            contenido.extend(["file '" + png.as_posix() + "'", f'duration {fin-inicio:.6f}'])
            ultima = png
        contenido.append("file '" + ultima.as_posix() + "'")
        lista.write_text('\n'.join(contenido)+'\n', encoding='utf-8')
        salida = TMP / f'escena_{indice:02}.mp4'
        subprocess.run([FFMPEG, '-y', '-hide_banner', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', str(lista),
                        '-i', str(audio), '-vf', 'fps=24', '-af', 'apad', '-t', f'{segundos:.6f}',
                        '-c:v', 'libx264', '-preset', 'fast', '-crf', '21', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '128k', '-ar', '48000', '-ac', '2', str(salida)], check=True)
        detalles.append({'capitulo': indice+1, 'titulo': escena['titulo'], 'inicio': offset, 'duracion': segundos})
        offset += segundos
        print(f'Escena {indice+1} codificada; acumulado {offset:.1f} s', flush=True)
    if offset > 420:
        raise RuntimeError(f'El video excede siete minutos: {offset:.1f} s.')
    concat = TMP / 'escenas.txt'
    concat.write_text('\n'.join("file '"+(TMP/f'escena_{i:02}.mp4').as_posix()+"'" for i in range(len(escenas)))+'\n', encoding='utf-8')
    salida = VIDEO / 'presentacion.mp4'
    subprocess.run([FFMPEG, '-y', '-hide_banner', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', str(concat),
                    '-c', 'copy', '-movflags', '+faststart', '-metadata', 'title=Proyecto 3 Simulador de maquinas de Turing',
                    '-metadata', 'comment=Narracion sintetica; capturas de la aplicacion real', str(salida)], check=True)
    srt = '\n\n'.join(f'{i+1}\n{reloj(a)} --> {reloj(b)}\n{t}' for i, (a,b,t) in enumerate(subtitulos))+'\n'
    (VIDEO / 'subtitulos.srt').write_text(srt, encoding='utf-8')
    (VIDEO / 'narracion.txt').write_text('\n\n'.join(e['titulo']+'\n'+e['narracion'] for e in escenas)+'\n', encoding='utf-8')
    (VIDEO / 'capitulos.json').write_text(json.dumps(detalles, ensure_ascii=False, indent=2), encoding='utf-8')
    descripcion = 'Proyecto 3 de Teoría de la Computación CC2019, UVG.\n\nRepositorio: https://github.com/DeividArriaza/proyecto-tdc\n\n'
    descripcion += '\n'.join(f'{int(e["inicio"])//60:02}:{int(e["inicio"])%60:02} {e["titulo"]}' for e in detalles)
    descripcion += '\n\nDemostración con capturas de la aplicación real y narración sintética.\n'
    (VIDEO / 'descripcion_youtube.txt').write_text(descripcion, encoding='utf-8')
    print(f'Video terminado: {salida} | {duracion(salida):.2f} s | {salida.stat().st_size/1000000:.1f} MB')


if __name__ == '__main__':
    main()
