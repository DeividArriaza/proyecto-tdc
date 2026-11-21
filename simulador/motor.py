"""Motor sin dependencia de la interfaz ni del registro de trazas."""

from dataclasses import dataclass
import json
from .modelo import Maquina


@dataclass(frozen=True)
class Configuracion:
    paso: int
    estado: str
    cabezal: int
    izquierda: int
    celdas: tuple[str, ...]

    def registro(self):
        return {'paso': self.paso, 'estado': self.estado, 'cabezal': self.cabezal,
                'izquierda': self.izquierda, 'celdas': list(self.celdas)}

    def texto(self):
        partes = [f'[{s}]' if self.izquierda + i == self.cabezal else s
                  for i, s in enumerate(self.celdas)]
        return f'DI {self.paso} | {self.estado} | h={self.cabezal} | i={self.izquierda} | ' + ' '.join(partes)


class Simulacion:
    def __init__(self, maquina: Maquina, entrada: str | list[str]):
        self.maquina = maquina
        if not isinstance(entrada, (str, list)):
            raise ValueError('La entrada debe ser texto o una lista de símbolos.')
        simbolos = list(entrada)
        for simbolo in simbolos:
            if not isinstance(simbolo, str) or simbolo not in maquina.alfabeto:
                raise ValueError(f'Símbolo de entrada no declarado: {simbolo!r}.')
        self.cinta = {i: s for i, s in enumerate(simbolos) if s != maquina.blanco}
        self.estado = maquina.estado_inicial
        self.cabezal = 0
        self.pasos = 0
        self.izquierda = 0
        self.derecha = max(0, len(simbolos) - 1)
        self.cancelada = False

    def leer(self, posicion: int | None = None):
        return self.cinta.get(self.cabezal if posicion is None else posicion, self.maquina.blanco)

    @property
    def detenida(self):
        return (self.estado, self.leer()) not in self.maquina.transiciones

    def cancelar(self):
        self.cancelada = True

    def paso(self) -> bool:
        if self.cancelada:
            return False
        regla = self.maquina.transiciones.get((self.estado, self.leer()))
        if regla is None:
            return False
        accion, destino = regla
        if accion.tipo == 'L':
            self.cabezal -= 1
        elif accion.tipo == 'R':
            self.cabezal += 1
        elif accion.simbolo == self.maquina.blanco:
            self.cinta.pop(self.cabezal, None)
        else:
            self.cinta[self.cabezal] = accion.simbolo
        self.estado = destino
        self.pasos += 1
        self.izquierda = min(self.izquierda, self.cabezal)
        self.derecha = max(self.derecha, self.cabezal)
        return True

    def configuracion(self):
        return Configuracion(self.pasos, self.estado, self.cabezal, self.izquierda,
                             tuple(self.leer(i) for i in range(self.izquierda, self.derecha + 1)))

    def resultado(self):
        """Contenido entre los extremos no blancos; conserva blancos interiores."""
        if not self.cinta:
            return []
        return [self.leer(i) for i in range(min(self.cinta), max(self.cinta) + 1)]

    def resumen(self):
        simbolos = self.resultado()
        return {'tipo': 'resultado', 'estado': self.estado, 'pasos': self.pasos,
                'cabezal': self.cabezal, 'cancelada': self.cancelada,
                'detenida': self.detenida, 'simbolos': simbolos, 'texto': ''.join(simbolos)}


def escribir_di(archivo, simulacion):
    archivo.write(json.dumps({'tipo': 'di', **simulacion.configuracion().registro()}, ensure_ascii=False) + '\n')


def escribir_resumen(archivo, simulacion):
    archivo.write(json.dumps(simulacion.resumen(), ensure_ascii=False) + '\n')
