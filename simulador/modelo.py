"""Lectura YAML y validación completa antes de ejecutar una máquina."""

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping
import yaml


class ErrorEspecificacion(ValueError):
    """La especificación no define una máquina determinista válida."""


class _Cargador(yaml.BaseLoader):
    """Conserva escalares como texto: 0, yes y on también pueden ser símbolos."""


def _mapa_sin_duplicados(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        if not isinstance(key, str):
            raise ErrorEspecificacion('Las claves YAML deben ser cadenas.')
        if key in result:
            raise ErrorEspecificacion(f'Clave YAML repetida: {key!r}.')
        result[key] = loader.construct_object(value_node, deep=True)
    return result


_Cargador.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapa_sin_duplicados)


@dataclass(frozen=True)
class Accion:
    tipo: str  # L, R o W; W no mueve el cabezal
    simbolo: str | None = None


@dataclass(frozen=True)
class Maquina:
    nombre: str
    estados: frozenset[str]
    alfabeto: frozenset[str]
    estado_inicial: str
    blanco: str
    transiciones: Mapping[tuple[str, str], tuple[Accion, str]]


def _conjunto(valor, campo):
    if not isinstance(valor, list) or not valor:
        raise ErrorEspecificacion(f'{campo} debe ser una lista no vacía.')
    if any(not isinstance(x, str) or not x for x in valor):
        raise ErrorEspecificacion(f'Cada elemento de {campo} debe ser texto no vacío.')
    if len(set(valor)) != len(valor):
        raise ErrorEspecificacion(f'{campo} contiene elementos repetidos.')
    return frozenset(valor)


def leer_yaml(texto: str) -> Maquina:
    try:
        raiz = yaml.load(texto, Loader=_Cargador)
    except yaml.YAMLError as exc:
        raise ErrorEspecificacion(f'YAML inválido: {exc}') from exc
    if not isinstance(raiz, dict) or set(raiz) != {'mt'}:
        raise ErrorEspecificacion('El documento debe contener únicamente la clave mt.')
    spec = raiz['mt']
    if not isinstance(spec, dict):
        raise ErrorEspecificacion('mt debe ser un mapa YAML.')
    requeridos = {'estados', 'alfabeto', 'estado_inicial', 'transiciones'}
    opcionales = {'nombre', 'descripcion', 'blanco'}
    faltan = requeridos - set(spec)
    extras = set(spec) - requeridos - opcionales
    if faltan:
        raise ErrorEspecificacion(f'Faltan campos: {", ".join(sorted(faltan))}.')
    if extras:
        raise ErrorEspecificacion(f'Campos desconocidos: {", ".join(sorted(extras))}.')
    estados = _conjunto(spec['estados'], 'estados')
    alfabeto = _conjunto(spec['alfabeto'], 'alfabeto')
    inicio = spec['estado_inicial']
    blanco = spec.get('blanco', 'B')
    nombre = spec.get('nombre', 'Máquina sin nombre')
    if not isinstance(nombre, str) or not nombre:
        raise ErrorEspecificacion('nombre debe ser texto no vacío.')
    if 'descripcion' in spec and not isinstance(spec['descripcion'], str):
        raise ErrorEspecificacion('descripcion debe ser texto.')
    if not isinstance(inicio, str) or inicio not in estados:
        raise ErrorEspecificacion('estado_inicial no pertenece a estados.')
    if not isinstance(blanco, str) or blanco not in alfabeto:
        raise ErrorEspecificacion('El símbolo blanco debe pertenecer al alfabeto (por defecto B).')
    filas = spec['transiciones']
    if not isinstance(filas, list):
        raise ErrorEspecificacion('transiciones debe ser una lista; use [] para una máquina sin reglas.')
    tabla = {}
    for numero, fila in enumerate(filas, 1):
        campos = fila.split() if isinstance(fila, str) else fila
        if not isinstance(campos, list) or len(campos) != 4 or any(not isinstance(x, str) for x in campos):
            raise ErrorEspecificacion(f'Transición {numero}: se requieren cuatro elementos de texto.')
        origen, lectura, operacion, destino = campos
        if origen not in estados or destino not in estados:
            raise ErrorEspecificacion(f'Transición {numero}: estado no declarado.')
        if lectura not in alfabeto:
            raise ErrorEspecificacion(f'Transición {numero}: símbolo de lectura no declarado: {lectura!r}.')
        if operacion in ('L', 'R'):
            accion = Accion(operacion)
        else:
            escritura = operacion[2:] if operacion.startswith('W:') else operacion
            if escritura not in alfabeto:
                raise ErrorEspecificacion(f'Transición {numero}: escritura no declarada: {escritura!r}.')
            accion = Accion('W', escritura)
        clave = (origen, lectura)
        if clave in tabla:
            raise ErrorEspecificacion(f'Transición {numero}: regla repetida para {clave!r}; la máquina debe ser determinista.')
        tabla[clave] = (accion, destino)
    return Maquina(nombre, estados, alfabeto, inicio, blanco, MappingProxyType(tabla))


def cargar_maquina(ruta: str | Path) -> Maquina:
    try:
        return leer_yaml(Path(ruta).read_text(encoding='utf-8-sig'))
    except (OSError, UnicodeError) as exc:
        raise ErrorEspecificacion(f'No se pudo leer el archivo YAML: {exc}') from exc
