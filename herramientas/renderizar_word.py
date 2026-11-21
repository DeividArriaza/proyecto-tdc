"""Conversión nativa en Windows cuando el renderer de LibreOffice no está disponible.

Usa una instancia independiente e invisible de Word, actualiza los campos y
exporta el mismo documento a PDF. Después genera PNG para la revisión visual.
"""
from pathlib import Path
import sys
import win32com.client
import pymupdf

RAIZ = Path(__file__).resolve().parents[1]


def main():
    docx = RAIZ / 'output/Informe_Proyecto_3.docx'
    pdf = RAIZ / 'output/Informe_Proyecto_3.pdf'
    qa = RAIZ / 'output/qa'
    qa.mkdir(exist_ok=True)
    app = win32com.client.DispatchEx('Word.Application')
    app.Visible = False
    app.DisplayAlerts = 0
    documento = None
    try:
        documento = app.Documents.Open(str(docx), ReadOnly=False, AddToRecentFiles=False)
        documento.Fields.Update()
        for toc in documento.TablesOfContents:
            toc.Update()
        documento.Repaginate()
        for toc in documento.TablesOfContents:
            toc.UpdatePageNumbers()
        documento.Save()
        documento.ExportAsFixedFormat(str(pdf), 17)
    finally:
        if documento is not None:
            documento.Close(False)
        app.Quit()
    d = pymupdf.open(pdf)
    for i, pagina in enumerate(d, 1):
        pagina.get_pixmap(matrix=pymupdf.Matrix(1.4, 1.4)).save(qa / f'pagina_{i:02}.png')
    print(f'{len(d)} páginas renderizadas: {pdf}')


if __name__ == '__main__':
    main()
