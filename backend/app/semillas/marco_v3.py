"""Semilla del Marco de Viabilidad NEPXA v3.0 (specs/001-validador-viabilidad/marco-nepxa.md).

Crea los roles y la versión 3.0 del marco como versión vigente: 6 dimensiones, 28 criterios con su
rúbrica, pesos iguales y los umbrales por defecto. Es idempotente: si ya existe, no hace nada.
"""

from dataclasses import dataclass, field
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modelos.marco import (
    Criterio,
    Dimension,
    EstadoVersion,
    NivelCriterio,
    TipoCalculo,
    VersionMarco,
)
from app.modelos.usuarios import CodigoRol, Rol

NUMERO_VERSION = "3.0"

NOMBRES_ROLES: dict[CodigoRol, str] = {
    CodigoRol.MIEMBRO: "Miembro",
    CodigoRol.PM: "Product Manager",
    CodigoRol.LIDER_COMERCIAL: "Líder Comercial / Negocio",
    CodigoRol.LIDER_TECNICO: "Líder Técnico / Arquitectura",
    CodigoRol.LIDER_ESTRATEGIA: "Líder de Estrategia / Dirección",
    CodigoRol.COMITE: "Comité de Producto",
    CodigoRol.ADMIN_MARCO: "Administrador del marco",
}


@dataclass(frozen=True)
class DatosCriterio:
    codigo: str
    nombre: str
    definicion: str
    niveles: tuple[str, ...]  # descripción de los niveles 1..5
    calculable: TipoCalculo = TipoCalculo.NO


@dataclass(frozen=True)
class DatosDimension:
    codigo: str
    nombre: str
    proposito: str
    rol_sugerido: CodigoRol
    criterios: tuple[DatosCriterio, ...] = field(default_factory=tuple)


# Recurrencia (COM-04) usa escala 1–3 en la fuente; se normaliza a 1, 3 y 5 (FR-008).
RECURRENCIA = DatosCriterio(
    "COM-04",
    "Recurrencia",
    "Probabilidad de generar una relación comercial de mediano o largo plazo mediante "
    "renovaciones.",
    ("Baja", "Media", "Alta"),
)

DIMENSIONES: tuple[DatosDimension, ...] = (
    DatosDimension(
        "MER",
        "Mercado",
        "Evaluar si existe un problema real, relevante y lo bastante grande para justificar una "
        "solución: dolor real del cliente (no interno), magnitud, frecuencia y urgencia.",
        CodigoRol.LIDER_COMERCIAL,
        (
            DatosCriterio(
                "MER-01",
                "Tamaño del problema",
                "Magnitud del impacto que el problema genera en las organizaciones (costo, riesgo, "
                "tiempo o complejidad).",
                (
                    "Impacto marginal, afecta procesos secundarios",
                    "Impacto limitado en áreas específicas",
                    "Impacto relevante en una función clave",
                    "Impacto significativo en varias áreas",
                    "Impacto crítico en la operación o ingresos",
                ),
            ),
            DatosCriterio(
                "MER-02",
                "Frecuencia",
                "Qué tan seguido ocurre el problema en la operación de los clientes "
                "(ej.: reclamos diarios).",
                ("Esporádica", "Ocasional", "Regular", "Frecuente", "Constante (core del negocio)"),
            ),
            DatosCriterio(
                "MER-03",
                "Urgencia",
                "Prioridad del problema para el cliente en continuidad operativa, cumplimiento o "
                "impacto económico.",
                (
                    "Nice to have",
                    "Baja prioridad",
                    "Prioridad media",
                    "Alta prioridad",
                    "Crítico (bloquea operación / genera pérdidas)",
                ),
            ),
            DatosCriterio(
                "MER-04",
                "Disposición a pagar",
                "Grado en que los clientes están dispuestos a invertir para resolver el problema.",
                (
                    "No hay presupuesto",
                    "Interés bajo / exploratorio",
                    "Interés real pero no priorizado",
                    "Presupuesto identificado",
                    "Ya pagan por resolverlo",
                ),
            ),
            DatosCriterio(
                "MER-05",
                "Evidencia de la demanda",
                "Evidencia objetiva de una necesidad real y actual del mercado, más allá de "
                "opiniones o hipótesis.",
                (
                    "Suposición interna",
                    "Opiniones sin validar",
                    "Conversaciones con clientes",
                    "Oportunidades comerciales reales",
                    "Demanda activa / ventas en curso",
                ),
            ),
        ),
    ),
    DatosDimension(
        "COM",
        "Comercial",
        "Evaluar si el producto se puede vender, monetizar y escalar de forma sostenible: si los "
        "prospectos pagarían, si el precio y el margen son atractivos, con qué modelo y si es "
        "repetible o un proyecto único.",
        CodigoRol.LIDER_COMERCIAL,
        (
            DatosCriterio(
                "COM-01",
                "Modelo de ingresos",
                "Nivel de definición y viabilidad del esquema de ingresos (SaaS, licencias, "
                "servicios).",
                (
                    "No definido",
                    "Hipótesis débil",
                    "Parcial (servicios principalmente)",
                    "Mixto (servicios + SaaS)",
                    "Claro y escalable (SaaS dominante)",
                ),
            ),
            DatosCriterio(
                "COM-02",
                "Ticket potencial",
                "Valor económico promedio que se puede generar por cliente.",
                ("Bajo", "Bajo–medio", "Medio", "Alto", "Muy alto (estratégico)"),
            ),
            DatosCriterio(
                "COM-03",
                "Escalabilidad",
                "Capacidad de crecer en ingresos sin aumentar proporcionalmente los costos "
                "operativos.",
                (
                    "100 % servicios",
                    "Alta dependencia de servicios",
                    "Mixto",
                    "Escalable con soporte limitado",
                    "Altamente escalable (SaaS puro)",
                ),
            ),
            RECURRENCIA,
            DatosCriterio(
                "COM-05",
                "Facilidad de venta",
                "Complejidad para explicar, posicionar y cerrar la venta del producto.",
                (
                    "Difícil de explicar",
                    "Complejo / requiere evangelización",
                    "Venta consultiva estándar",
                    "Problema claro y entendible",
                    "Dolor evidente / compra natural",
                ),
            ),
            DatosCriterio(
                "COM-06",
                "Venta integrada",
                "Capacidad de formar parte de soluciones más amplias del portafolio NEPXA (si se "
                "vende solo o en conjunto; si potencia otras soluciones).",
                (
                    "Totalmente aislado",
                    "Integración débil",
                    "Integrable",
                    "Parte de soluciones",
                    "Núcleo de ofertas integradas",
                ),
            ),
        ),
    ),
    DatosDimension(
        "FIN",
        "Financiera y de Inversión",
        "Evaluar la viabilidad económica de la iniciativa: inversión requerida, tiempo de "
        "recuperación, rentabilidad esperada y riesgo financiero.",
        CodigoRol.PM,
        (
            DatosCriterio(
                "FIN-01",
                "Inversión MVP",
                "Esfuerzo económico requerido para construir una versión funcional del producto "
                "(personas, licencias, infraestructura).",
                ("Muy alta", "Alta", "Media", "Baja", "Muy baja"),
            ),
            DatosCriterio(
                "FIN-02",
                "Tiempo de recuperación",
                "Tiempo estimado para recuperar la inversión inicial.",
                ("> 36 meses", "24–36 meses", "12–24 meses", "6–12 meses", "< 6 meses"),
                TipoCalculo.RECUPERACION,
            ),
            DatosCriterio(
                "FIN-03",
                "Potencial de ROI",
                "Relación entre utilidad esperada e inversión. "
                "ROI (%) = (Ingresos esperados − Inversión) / Inversión × 100.",
                ("< 25 %", "25–50 %", "50–75 %", "75–100 %", "> 100 %"),
                TipoCalculo.ROI,
            ),
            DatosCriterio(
                "FIN-04",
                "Riesgo financiero",
                "Nivel de incertidumbre sobre ingresos, adopción y costos.",
                ("Muy alto", "Alto", "Medio", "Bajo", "Muy bajo"),
            ),
        ),
    ),
    DatosDimension(
        "TEC",
        "Técnica",
        "Determinar si NEPXA puede construir, integrar y operar el producto de forma eficiente y "
        "escalable: complejidad real, encaje con la arquitectura, dependencias externas y "
        "capacidad del equipo.",
        CodigoRol.LIDER_TECNICO,
        (
            DatosCriterio(
                "TEC-01",
                "Complejidad técnica",
                "Dificultad para diseñar, desarrollar e implementar la solución (algoritmos, "
                "integraciones, arquitectura, incertidumbre técnica).",
                ("Muy alta / incierta", "Alta", "Media", "Baja", "Muy baja / trivial"),
            ),
            DatosCriterio(
                "TEC-02",
                "Alineación con arquitectura",
                "Grado en que la solución es compatible con la arquitectura actual de NEPXA.",
                (
                    "No encaja",
                    "Requiere cambios grandes",
                    "Ajustes moderados",
                    "Encaja bien",
                    "Encaje natural",
                ),
            ),
            DatosCriterio(
                "TEC-03",
                "Capacidad del equipo",
                "Preparación del equipo interno para desarrollar y mantener la solución (necesidad "
                "de contratación o capacitación).",
                ("No disponible", "Muy limitada", "Parcial", "Suficiente", "Totalmente cubierta"),
            ),
            DatosCriterio(
                "TEC-04",
                "Dependencias",
                "Dependencia de terceros (proveedores, APIs, infraestructura externa) para que la "
                "solución funcione; control sobre la solución.",
                (
                    "Críticas y externas",
                    "Altas",
                    "Moderadas",
                    "Bajas",
                    "Mínimas / control total",
                ),
            ),
            DatosCriterio(
                "TEC-05",
                "Tiempo de desarrollo",
                "Tiempo estimado para construir una versión funcional (MVP) del producto "
                "(time to market).",
                ("> 12 meses", "9–12 meses", "4–9 meses", "2–4 meses", "< 2 meses"),
            ),
        ),
    ),
    DatosDimension(
        "CMP",
        "Competencia",
        "Identificar y calificar la ventaja real que tiene o tendrá NEPXA para competir en el "
        "mercado.",
        CodigoRol.PM,
        (
            DatosCriterio(
                "CMP-01",
                "Diferenciación",
                "Nivel en que la solución ofrece algo único frente a alternativas existentes.",
                ("Commodity", "Baja", "Moderada", "Clara", "Única / fuerte"),
            ),
            DatosCriterio(
                "CMP-02",
                "Competencia",
                "Cantidad y fuerza de competidores que ofrecen soluciones similares.",
                ("Muy alta", "Alta", "Media", "Baja", "Muy baja"),
            ),
            DatosCriterio(
                "CMP-03",
                "Barreras de entrada",
                "Dificultad para que otros competidores desarrollen o copien una solución similar.",
                ("Nulas", "Bajas", "Moderadas", "Altas", "Muy altas"),
            ),
            DatosCriterio(
                "CMP-04",
                "Posicionamiento",
                "Claridad y fuerza con la que la solución puede ser entendida y diferenciada en el "
                "mercado (facilidad de explicar el mensaje comercial).",
                (
                    "Confuso",
                    "Difícil de explicar",
                    "Entendible",
                    "Claro",
                    "Muy claro y diferenciador",
                ),
            ),
        ),
    ),
    DatosDimension(
        "ECO",
        "Ecosistema",
        "Identificar si el producto fortalece o debilita el ecosistema integrado de NEPXA: "
        "integración con Nexopus, sinergia con otras soluciones, reutilización de capacidades y "
        "potencial de cross-selling.",
        CodigoRol.LIDER_ESTRATEGIA,
        (
            DatosCriterio(
                "ECO-01",
                "Integración",
                "Nivel de conexión funcional y técnica con la plataforma central (Nexopus).",
                ("Independiente", "Baja", "Integrable", "Integrado", "Nativo"),
            ),
            DatosCriterio(
                "ECO-02",
                "Sinergia",
                "Capacidad de la solución de complementar y potenciar otros productos del "
                "portafolio.",
                ("Aislado", "Baja", "Media", "Alta", "Muy alta"),
            ),
            DatosCriterio(
                "ECO-03",
                "Reutilización",
                "Grado en que se aprovechan componentes, desarrollos o funcionalidades existentes.",
                ("Todo nuevo", "Baja", "Media", "Alta", "Muy alta"),
            ),
            DatosCriterio(
                "ECO-04",
                "Cross-selling",
                "Capacidad de la solución para generar ventas adicionales dentro del mismo "
                "cliente.",
                ("No genera", "Bajo", "Medio", "Alto", "Muy alto"),
            ),
        ),
    ),
)


def pesos_iguales(cantidad: int) -> list[Decimal]:
    """Pesos con 8 decimales que suman exactamente 1; la última dimensión absorbe el residuo."""
    base = (Decimal(1) / cantidad).quantize(Decimal("0.00000001"))
    return [base] * (cantidad - 1) + [Decimal(1) - base * (cantidad - 1)]


def _niveles(datos: DatosCriterio) -> list[NivelCriterio]:
    if datos is RECURRENCIA:
        return [
            NivelCriterio(nivel=n, descripcion=d)
            for n, d in zip((1, 3, 5), datos.niveles, strict=True)
        ]
    return [NivelCriterio(nivel=n, descripcion=d) for n, d in enumerate(datos.niveles, start=1)]


def construir_marco_v3() -> VersionMarco:
    version = VersionMarco(
        numero=NUMERO_VERSION,
        estado=EstadoVersion.VIGENTE,
        notas_cambio="Versión inicial cargada desde el Marco de Viabilidad NEPXA v3.0.",
    )
    for orden_d, (datos_d, peso) in enumerate(
        zip(DIMENSIONES, pesos_iguales(len(DIMENSIONES)), strict=True), start=1
    ):
        dimension = Dimension(
            codigo=datos_d.codigo,
            nombre=datos_d.nombre,
            proposito=datos_d.proposito,
            peso=peso,
            rol_sugerido=datos_d.rol_sugerido,
            orden=orden_d,
        )
        for orden_c, datos_c in enumerate(datos_d.criterios, start=1):
            dimension.criterios.append(
                Criterio(
                    codigo=datos_c.codigo,
                    nombre=datos_c.nombre,
                    definicion=datos_c.definicion,
                    escala_original=3 if datos_c is RECURRENCIA else 5,
                    calculable=datos_c.calculable,
                    orden=orden_c,
                    niveles=_niveles(datos_c),
                )
            )
        version.dimensiones.append(dimension)
    return version


async def sembrar_datos_base(sesion: AsyncSession) -> None:
    """Crea los roles y el marco v3.0 si no existen. No confirma la transacción."""
    existentes = set((await sesion.execute(select(Rol.codigo))).scalars())
    for codigo, nombre in NOMBRES_ROLES.items():
        if codigo not in existentes:
            sesion.add(Rol(codigo=codigo, nombre=nombre))

    hay_marco = await sesion.scalar(
        select(VersionMarco.id).where(VersionMarco.numero == NUMERO_VERSION)
    )
    if hay_marco is None:
        sesion.add(construir_marco_v3())
    await sesion.flush()
