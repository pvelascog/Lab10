"""Errores de negocio con el formato de respuesta de contracts/api.md."""


class ErrorAplicacion(Exception):
    def __init__(self, estado: int, detalle: str, campos: dict[str, str] | None = None) -> None:
        super().__init__(detalle)
        self.estado = estado
        self.detalle = detalle
        self.campos = campos


class DatosInvalidos(ErrorAplicacion):
    """400: datos de entrada inválidos, con el mensaje de cada campo."""

    def __init__(self, campos: dict[str, str], detalle: str = "Datos inválidos") -> None:
        super().__init__(400, detalle, campos)


class NoEncontrado(ErrorAplicacion):
    def __init__(self, detalle: str = "Recurso no encontrado") -> None:
        super().__init__(404, detalle)


class SinPermiso(ErrorAplicacion):
    def __init__(self, detalle: str = "No tiene permisos para esta acción") -> None:
        super().__init__(403, detalle)


class Conflicto(ErrorAplicacion):
    """409: la operación no es posible en el estado actual."""

    def __init__(self, detalle: str) -> None:
        super().__init__(409, detalle)


class ReglaIncumplida(ErrorAplicacion):
    """422: falta cumplir una regla de negocio; `campos` indica qué falta."""

    def __init__(self, detalle: str, campos: dict[str, str] | None = None) -> None:
        super().__init__(422, detalle, campos)
