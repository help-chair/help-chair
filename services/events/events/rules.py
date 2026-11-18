"""Motor de reglas de destino de Eventos (ESQUELETO).

Define el vocabulario (evento, destino, decisión) y la firma de ``evaluar``.
La lógica de las 9 reglas se implementa después (TDD): ver ``tests/test_rules.py``.
"""

from dataclasses import dataclass
from enum import StrEnum


class Origen(StrEnum):
    SISTEMA = "sistema"
    USUARIO = "usuario"


class Tipo(StrEnum):
    INFORMATIVO = "informativo"
    ADVERTENCIA = "advertencia"
    EXCEPCION = "excepcion"


class Categoria(StrEnum):
    SEGURIDAD = "seguridad"  # seguridad o credenciales
    SOLICITUD_CATALOGO = "solicitud_catalogo"
    FALLA = "falla"  # falla, degradación o interrupción
    CAMBIO = "cambio"  # requiere modificar configuración o infraestructura


class Destino(StrEnum):
    REGISTRO = "registro"  # regla 1: solo bitácora, cierre automático
    AUTOR_SOLUCION = "autor_solucion"  # regla 2: autor del artículo de la KB
    EVENTOS = "eventos"  # regla 3: registro y vigilancia dentro de Eventos
    ACCESOS = "accesos"  # regla 4
    PETICIONES = "peticiones"  # reglas 5 y 8
    INCIDENCIAS = "incidencias"  # reglas 6 y 9
    PROBLEMAS = "problemas"  # regla 7


@dataclass(frozen=True)
class Evento:
    """Datos mínimos que el motor necesita para decidir."""

    origen: Origen
    tipo: Tipo  # tipo con el que llega el evento (el motor puede reclasificarlo en Decision)
    requiere_accion: bool = False
    categoria: Categoria | None = None
    autor_solucion_kb: str | None = None  # autor del artículo de la KB, si existe
    repeticiones: int = 0  # veces que se repitió el patrón dentro de la ventana de T días
    umbral: int = 3  # N: umbral de recurrencia


@dataclass(frozen=True)
class Decision:
    regla: int  # 1..9
    destino: Destino
    # Clasificación ITIL que la regla ASIGNA al evento (columna "Tipo" de docs/reglas.md).
    # Puede diferir del tipo con el que llegó: p. ej. una advertencia repetida (regla 7)
    # se reclasifica como Excepción.
    tipo: Tipo


def evaluar(evento: Evento) -> Decision:
    """Devuelve la regla aplicada y el destino del evento."""
    raise NotImplementedError("Motor de reglas pendiente de implementar")
