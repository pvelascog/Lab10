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
