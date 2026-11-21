"""Figuras originales del informe, generadas desde resultados reales."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import csv

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / 'output' / 'figuras'


def font(n, bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/' + ('arialbd.ttf' if bold else 'arial.ttf'), n)


def diagrama():
    SALIDA.mkdir(parents=True, exist_ok=True)
    im = Image.new('RGB', (1300, 1530), 'white')
    d = ImageDraw.Draw(im)
    color = '#17324d'

    def label(x, y, text, size=24):
        d.multiline_text((x, y), text, anchor='mm', align='center', font=font(size), fill=color, spacing=5)

    def box(y, text, h=75, x=650, w=560):
        d.rectangle((x-w/2, y-h/2, x+w/2, y+h/2), fill='#eef3f7', outline=color, width=3)
        label(x, y, text)

    def decision(y, text):
        d.polygon([(650, y-65), (915, y), (650, y+65), (385, y)], fill='white', outline=color, width=3)
        label(650, y, text, 23)

    def arrow(points, texto=None, at=None):
        d.line(points, fill=color, width=3)
        x, y = points[-1]
        px, py = points[-2]
        if y > py:
            tri = [(x, y), (x-7, y-13), (x+7, y-13)]
        elif y < py:
            tri = [(x, y), (x-7, y+13), (x+7, y+13)]
        elif x > px:
            tri = [(x, y), (x-13, y-7), (x-13, y+7)]
        else:
            tri = [(x, y), (x+13, y-7), (x+13, y+7)]
        d.polygon(tri, fill=color)
        if texto:
            label(*at, texto, 21)

    box(70, 'Inicio')
    arrow([(650, 108), (650, 145)])
    box(185, 'Leer YAML y entrada')
    arrow([(650, 223), (650, 265)])
    decision(330, '¿Especificación y\nentrada válidas?')
    arrow([(385, 330), (155, 330), (155, 435)], 'No', (270, 305))
    box(480, 'Mostrar error\ny finalizar', 90, 155, 280)
    arrow([(650, 395), (650, 440)], 'Sí', (690, 415))
    box(485, 'Inicializar cinta, estado y cabezal\nRegistrar DI 0', 90)
    arrow([(650, 530), (650, 590)])
    decision(655, '¿Cancelación\nsolicitada?')
    arrow([(915, 655), (1110, 655), (1110, 755)], 'Sí', (985, 628))
    box(815, 'Registrar cancelación\ny contenido parcial\nFinalizar', 120, 1110, 340)
    arrow([(650, 720), (650, 785)], 'No', (695, 750))
    decision(850, '¿Existe regla para\n(estado, lectura)?')
    arrow([(385, 850), (160, 850), (160, 980)], 'No', (285, 825))
    box(1045, 'Extraer resultado de\nla configuración final\nRegistrar y finalizar', 130, 160, 300)
    arrow([(650, 915), (650, 980)], 'Sí', (695, 948))
    box(1035, 'Aplicar escritura o movimiento\nActualizar estado y contador', 110)
    arrow([(650, 1090), (650, 1160)])
    box(1210, 'Registrar la nueva DI completa\nActualizar la vista', 100)
    arrow([(650, 1260), (650, 1335), (1290, 1335), (1290, 560), (650, 560), (650, 590)])
    label(650, 1455, 'Sin un máximo de pasos predefinido\nLa ausencia de regla produce la parada normal', 23)
    im.save(SALIDA / 'flujo_simulacion.png')


def tabla_video():
    im = Image.new('RGB', (1180, 820), '#f8fafc')
    d = ImageDraw.Draw(im)
    d.text((45, 45), 'Crecimiento observado', font=font(39, True), fill='#17324d')
    d.text((45, 105), 'Mediciones reales del motor y de la traza', font=font(25), fill='#526479')
    headers = ['n', 'ADN pasos', 'Duplicación pasos']
    xs = [70, 275, 650]
    for x, h in zip(xs, headers):
        d.text((x, 185), h, font=font(29, True), fill='#17324d')
    rows = list(csv.DictReader((RAIZ / 'evidencia/crecimiento.csv').open(encoding='utf-8')))
    for i, n in enumerate([4, 8, 16, 32, 64]):
        y = 260 + i * 68
        a = next(r for r in rows if r['maquina'] == 'complemento_adn' and int(r['n']) == n)
        b = next(r for r in rows if r['maquina'] == 'duplicacion_ternaria' and int(r['n']) == n)
        for x, text in zip(xs, [str(n), a['pasos'], b['pasos']]):
            d.text((x, y), text, font=font(32), fill='#17324d')
    d.text((45, 660), 'Motor: lineal / cuadrático', font=font(30, True), fill='#087f8c')
    d.text((45, 715), 'Con traza completa: cuadrático / cúbico', font=font(29), fill='#17324d')
    im.save(SALIDA / 'crecimiento_video.png')


if __name__ == '__main__':
    diagrama()
    tabla_video()
