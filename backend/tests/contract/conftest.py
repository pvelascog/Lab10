# Las pruebas de contrato usan la misma base de datos y fixtures que las de integración.
from tests.integration.conftest import (  # noqa: F401
    cliente,
    datos_limpios,
    esquema,
    sesion,
    usuario_con_sesion,
)
