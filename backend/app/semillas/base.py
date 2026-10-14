"""Carga los datos base (roles y Marco NEPXA v3.0). Uso: python -m app.semillas.base"""

import asyncio

from app.db import fabrica_sesiones
from app.semillas.marco_v3 import sembrar_datos_base


async def principal() -> None:
    async with fabrica_sesiones()() as sesion:
        await sembrar_datos_base(sesion)
        await sesion.commit()
    print("Datos base listos: roles y Marco NEPXA v3.0.")


if __name__ == "__main__":
    asyncio.run(principal())
