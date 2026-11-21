"""Interfaz Tkinter con ejecución cooperativa y traza completa en disco."""

from collections import deque
import json
from pathlib import Path
import shutil
import tempfile
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from .modelo import cargar_maquina, ErrorEspecificacion
from .motor import Simulacion, escribir_di, escribir_resumen

RAIZ = Path(__file__).resolve().parent.parent
AZUL = '#17324d'
VERDE = '#087f8c'
FONDO = '#edf2f6'


class Aplicacion:
    def __init__(self, root):
        self.root = root
        root.title('Proyecto 3 | Simulador de máquinas de Turing')
        root.geometry('1180x820')
        root.minsize(950, 690)
        root.configure(bg=FONDO)
        self.maquina = self.sim = self.archivo = self.ruta_traza = None
        self.ejecutando = False
        self.tarea = None
        self.finalizado = False
        self.lineas = deque(maxlen=200)
        self.ruta = tk.StringVar()
        self.entrada = tk.StringVar(value='ACGT')
        self.tokens = tk.BooleanVar(value=False)
        self.lento = tk.BooleanVar(value=True)
        self.estado = tk.StringVar(value='Carga una máquina YAML para comenzar.')
        self.resultado = tk.StringVar(value='Resultado al detenerse: pendiente')
        self.info = tk.StringVar(value='Una cinta • Un cabezal • Índices positivos y negativos')
        self._construir()
        root.protocol('WM_DELETE_WINDOW', self.cerrar)

    def _construir(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', font=('Segoe UI', 10), padding=7)
        style.configure('Accent.TButton', background=VERDE, foreground='white')
        style.configure('TCheckbutton', background=FONDO, font=('Segoe UI', 10))
        banner = tk.Frame(self.root, bg=AZUL, padx=24, pady=17)
        banner.pack(fill='x')
        tk.Label(banner, text='MÁQUINAS DE TURING', font=('Segoe UI', 23, 'bold'), fg='white', bg=AZUL).pack(anchor='w')
        tk.Label(banner, text='Teoría de la Computación · Proyecto 3 · UVG', font=('Segoe UI', 11), fg='#cfdae5', bg=AZUL).pack(anchor='w')
        main = tk.Frame(self.root, bg=FONDO, padx=22, pady=14)
        main.pack(fill='both', expand=True)
        row = tk.Frame(main, bg=FONDO)
        row.pack(fill='x')
        ttk.Entry(row, textvariable=self.ruta).pack(side='left', fill='x', expand=True)
        ttk.Button(row, text='Abrir YAML', command=self.abrir).pack(side='left', padx=(8, 0))
        ttk.Button(row, text='Cargar ruta', command=self.cargar).pack(side='left', padx=(8, 0))
        examples = tk.Frame(main, bg=FONDO)
        examples.pack(fill='x', pady=8)
        for texto, archivo, entrada in [('Ejemplo 1 · ADN', 'complemento_adn.yaml', 'ACGT'),
                                         ('Ejemplo 2 · Duplicación', 'duplicacion_ternaria.yaml', 'abc')]:
            ttk.Button(examples, text=texto, command=lambda a=archivo, e=entrada: self.ejemplo(a, e)).pack(side='left', padx=(0, 8))
        tk.Label(main, textvariable=self.info, bg=FONDO, fg=AZUL, font=('Segoe UI', 10), anchor='w').pack(fill='x', pady=(0, 8))
        inputrow = tk.Frame(main, bg=FONDO)
        inputrow.pack(fill='x')
        tk.Label(inputrow, text='Entrada', bg=FONDO, font=('Segoe UI', 11, 'bold')).pack(side='left', padx=(0, 10))
        self.entry = ttk.Entry(inputrow, textvariable=self.entrada, font=('Consolas', 12))
        self.entry.pack(side='left', fill='x', expand=True)
        ttk.Checkbutton(inputrow, text='Lista JSON de símbolos', variable=self.tokens).pack(side='left', padx=10)
        controls = tk.Frame(main, bg=FONDO)
        controls.pack(fill='x', pady=12)
        for texto, command, style in [('Preparar / reiniciar', self.preparar, 'TButton'),
                                      ('Un paso', self.paso, 'TButton'),
                                      ('Ejecutar', self.ejecutar, 'Accent.TButton'),
                                      ('Pausar', self.pausar, 'TButton'),
                                      ('Cancelar', self.cancelar, 'TButton'),
                                      ('Exportar traza', self.exportar, 'TButton')]:
            ttk.Button(controls, text=texto, command=command, style=style).pack(side='left', padx=(0, 7))
        ttk.Checkbutton(main, text='Animación lenta (desmarcar para ejecución rápida)', variable=self.lento).pack(anchor='w')
        self.canvas = tk.Canvas(main, bg='white', height=115, highlightthickness=0)
        self.canvas.pack(fill='x', pady=(10, 8))
        self.canvas.bind('<Configure>', lambda e: self.dibujar())
        tk.Label(main, textvariable=self.estado, bg=FONDO, fg=AZUL, font=('Segoe UI', 12, 'bold'), anchor='w').pack(fill='x')
        tk.Label(main, textvariable=self.resultado, bg=FONDO, fg=VERDE, font=('Segoe UI', 11), anchor='w', wraplength=1080).pack(fill='x', pady=(6, 8))
        tk.Label(main, text='Descripciones instantáneas · últimas 200 · la traza completa se conserva en disco', bg=FONDO, fg=AZUL, font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        traceframe = tk.Frame(main)
        traceframe.pack(fill='both', expand=True, pady=(5, 0))
        self.texto = tk.Text(traceframe, height=8, wrap='none', font=('Consolas', 10), bg='#102235', fg='#e6edf3', insertbackground='white')
        sy = ttk.Scrollbar(traceframe, orient='vertical', command=self.texto.yview)
        sx = ttk.Scrollbar(traceframe, orient='horizontal', command=self.texto.xview)
        self.texto.configure(yscrollcommand=sy.set, xscrollcommand=sx.set, state='disabled')
        sy.pack(side='right', fill='y')
        sx.pack(side='bottom', fill='x')
        self.texto.pack(fill='both', expand=True)

    def abrir(self):
        ruta = filedialog.askopenfilename(initialdir=RAIZ / 'ejemplos', filetypes=[('Máquinas YAML', '*.yaml *.yml'), ('Todos los archivos', '*.*')])
        if ruta:
            self.ruta.set(ruta)
            self.cargar()

    def cargar(self):
        try:
            maquina = cargar_maquina(self.ruta.get())
        except ErrorEspecificacion as exc:
            messagebox.showerror('Especificación inválida', str(exc))
            return False
        self.pausar()
        self._cerrar_registro()
        self.maquina = maquina
        self.sim = None
        self.finalizado = False
        self.ruta_traza = None
        self.lineas.clear()
        self.info.set(f'{maquina.nombre} | {len(maquina.estados)} estados | {len(maquina.transiciones)} reglas | blanco: {maquina.blanco!r}')
        self.estado.set('Máquina validada. Ingresa la entrada y pulsa Preparar o Ejecutar.')
        self.resultado.set('Resultado al detenerse: pendiente')
        self.actualizar()
        return True

    def ejemplo(self, archivo, entrada):
        self.ruta.set(str(RAIZ / 'ejemplos' / archivo))
        self.entrada.set(entrada)
        self.tokens.set(False)
        self.cargar()

    def preparar(self):
        if self.maquina is None:
            if not self.cargar():
                return False
        self.pausar()
        try:
            entrada = json.loads(self.entrada.get()) if self.tokens.get() else self.entrada.get()
            if self.tokens.get() and not isinstance(entrada, list):
                raise ValueError('El modo JSON requiere una lista de símbolos.')
            nueva = Simulacion(self.maquina, entrada)
            registro = tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.jsonl', prefix='turing_', delete=False)
        except (ValueError, OSError) as exc:
            messagebox.showerror('Entrada inválida', str(exc))
            return False
        self._cerrar_registro()
        self.sim = nueva
        self.archivo = registro
        self.ruta_traza = Path(registro.name)
        self.finalizado = False
        self.lineas.clear()
        self.resultado.set('Resultado al detenerse: pendiente')
        self.registrar()
        self._comprobar_final()
        self.actualizar()
        return True

    def registrar(self):
        conf = self.sim.configuracion()
        self.archivo.write(json.dumps({'tipo': 'di', **conf.registro()}, ensure_ascii=False) + '\n')
        # Solo la vista es una ventana; el JSONL conserva cada configuración completa.
        visible = conf.texto()
        self.lineas.append(visible[:1200] + (' … [DI completa en JSONL]' if len(visible) > 1200 else ''))

    def _comprobar_final(self):
        if self.sim and (self.sim.detenida or self.sim.cancelada):
            self.ejecutando = False
            if not self.finalizado:
                escribir_resumen(self.archivo, self.sim)
                self.archivo.flush()
                self.finalizado = True
            prefijo = 'Cancelada; contenido parcial' if self.sim.cancelada else 'Resultado final'
            simbolos = self.sim.resultado()
            self.resultado.set(f'{prefijo}: {json.dumps(simbolos, ensure_ascii=False)}  |  texto: {json.dumps("".join(simbolos), ensure_ascii=False)}')
            return True
        return False

    def paso(self):
        self.pausar()
        if self.sim is None and not self.preparar():
            return
        try:
            if self.sim.paso():
                self.registrar()
            self._comprobar_final()
            self.actualizar()
        except OSError as exc:
            self._error_registro(exc)

    def ejecutar(self):
        if self.sim is None and not self.preparar():
            return
        if self.finalizado or self.ejecutando:
            return
        self.ejecutando = True
        self._programar(0)

    def _programar(self, milisegundos):
        self.tarea = self.root.after(milisegundos, self._lote)

    def _lote(self):
        self.tarea = None
        if not self.ejecutando:
            return
        try:
            hasta = time.perf_counter() + 0.008
            while self.ejecutando:
                if self.sim.paso():
                    self.registrar()
                if self._comprobar_final() or self.lento.get() or time.perf_counter() >= hasta:
                    break
            self.archivo.flush()
            self.actualizar()
            if self.ejecutando:
                self._programar(180 if self.lento.get() else 1)
        except OSError as exc:
            self._error_registro(exc)

    def _error_registro(self, exc):
        self.ejecutando = False
        self.estado.set('Error de almacenamiento. La ejecución está pausada.')
        messagebox.showerror('No se pudo guardar la traza', str(exc))

    def pausar(self):
        self.ejecutando = False
        if self.tarea is not None:
            self.root.after_cancel(self.tarea)
            self.tarea = None

    def cancelar(self):
        self.pausar()
        if self.sim is not None and not self.finalizado:
            self.sim.cancelar()
            self._comprobar_final()
            self.actualizar()

    def exportar(self):
        if not self.ruta_traza:
            messagebox.showinfo('Traza', 'Primero prepara una simulación.')
            return
        destino = filedialog.asksaveasfilename(defaultextension='.jsonl', initialfile='traza.jsonl', filetypes=[('Traza completa JSONL', '*.jsonl')])
        if destino:
            try:
                if self.archivo:
                    self.archivo.flush()
                if Path(destino).resolve() != self.ruta_traza.resolve():
                    shutil.copyfile(self.ruta_traza, destino)
                messagebox.showinfo('Traza exportada', f'Traza hasta el paso actual guardada en:\n{destino}')
            except OSError as exc:
                messagebox.showerror('Error al exportar', str(exc))

    def actualizar(self):
        if self.sim:
            tipo = 'CANCELADA' if self.sim.cancelada else 'DETENIDA' if self.sim.detenida else 'EN EJECUCIÓN' if self.ejecutando else 'PAUSADA'
            self.estado.set(f'{tipo}  |  Paso {self.sim.pasos}  |  Estado {self.sim.estado}  |  Cabezal {self.sim.cabezal}  |  Lee {self.sim.leer()!r}')
        self.texto.configure(state='normal')
        self.texto.delete('1.0', 'end')
        self.texto.insert('end', '\n'.join(self.lineas))
        self.texto.see('end')
        self.texto.configure(state='disabled')
        self.dibujar()

    def dibujar(self):
        self.canvas.delete('all')
        if not self.sim:
            self.canvas.create_text(25, 50, text='La cinta aparecerá aquí al preparar la simulación.', anchor='w', font=('Segoe UI', 12), fill=AZUL)
            return
        width = max(700, self.canvas.winfo_width())
        total = max(7, (width - 30) // 62)
        if total % 2 == 0:
            total -= 1
        mitad = total // 2
        centro = width / 2
        for delta in range(-mitad, mitad + 1):
            posicion = self.sim.cabezal + delta
            x = centro + delta * 62
            selected = delta == 0
            self.canvas.create_rectangle(x - 28, 24, x + 28, 76, fill=VERDE if selected else '#f2f5f8', outline='#c4d0dc')
            simbolo = self.sim.leer(posicion)
            self.canvas.create_text(x, 50, text=simbolo if len(simbolo) <= 5 else simbolo[:4] + '…', font=('Consolas', 17, 'bold'), fill='white' if selected else AZUL)
            self.canvas.create_text(x, 91, text=str(posicion), font=('Segoe UI', 9), fill=AZUL)
        self.canvas.create_text(centro, 12, text='▼ cabezal', fill=VERDE, font=('Segoe UI', 9, 'bold'))

    def _cerrar_registro(self):
        if self.archivo:
            self.archivo.close()
            self.archivo = None

    def cerrar(self):
        self.pausar()
        self._cerrar_registro()
        self.root.destroy()


def iniciar():
    root = tk.Tk()
    Aplicacion(root)
    root.mainloop()
