"""T011 – Semilla del Marco NEPXA v3.0 (marco-nepxa.md, FR-005, FR-008, FR-012)."""

from collections import Counter

from app.modelos.usuarios import CodigoRol
from app.semillas.marco_v3 import sembrar_datos_base
from tests.integration.conftest import CrearUsuario


async def _marco(usuario_con_sesion: CrearUsuario) -> dict:
    c = await usuario_con_sesion(CodigoRol.MIEMBRO)
    respuesta = await c.get("/api/v1/marco/vigente")
    assert respuesta.status_code == 200
    return respuesta.json()


async def test_marco_vigente_tiene_6_dimensiones_y_28_criterios(
    usuario_con_sesion: CrearUsuario,
) -> None:
    marco = await _marco(usuario_con_sesion)

    assert marco["numero"] == "3.0"
    assert marco["estado"] == "VIGENTE"
    assert [d["codigo"] for d in marco["dimensiones"]] == ["MER", "COM", "FIN", "TEC", "CMP", "ECO"]
    conteo = Counter({d["codigo"]: len(d["criterios"]) for d in marco["dimensiones"]})
    assert conteo == {"MER": 5, "COM": 6, "FIN": 4, "TEC": 5, "CMP": 4, "ECO": 4}
    assert sum(conteo.values()) == 28


async def test_pesos_iguales_que_suman_uno(usuario_con_sesion: CrearUsuario) -> None:
    marco = await _marco(usuario_con_sesion)

    pesos = [float(d["peso"]) for d in marco["dimensiones"]]
    assert abs(sum(pesos) - 1.0) < 1e-9
    assert max(pesos) - min(pesos) <= 0.0001


async def test_umbrales_por_defecto(usuario_con_sesion: CrearUsuario) -> None:
    u = (await _marco(usuario_con_sesion))["umbrales"]

    assert u == {
        "critico": 2.0,
        "validar": 2.5,
        "debil": 3.0,
        "score_go": 4.0,
        "score_iterar": 3.0,
        "score_validar": 2.0,
        "divergencia": 2,
    }


async def test_cada_criterio_tiene_rubrica_completa(usuario_con_sesion: CrearUsuario) -> None:
    marco = await _marco(usuario_con_sesion)

    for dimension in marco["dimensiones"]:
        for criterio in dimension["criterios"]:
            niveles = [n["nivel"] for n in criterio["niveles"]]
            esperado = [1, 3, 5] if criterio["codigo"] == "COM-04" else [1, 2, 3, 4, 5]
            assert niveles == esperado, criterio["codigo"]
            assert all(n["descripcion"] for n in criterio["niveles"])
            assert criterio["nombre"] and criterio["definicion"]


async def test_recurrencia_normalizada_y_criterios_calculables(
    usuario_con_sesion: CrearUsuario,
) -> None:
    marco = await _marco(usuario_con_sesion)
    criterios = {c["codigo"]: c for d in marco["dimensiones"] for c in d["criterios"]}

    recurrencia = criterios["COM-04"]
    assert recurrencia["escala_original"] == 3
    assert [n["descripcion"] for n in recurrencia["niveles"]] == ["Baja", "Media", "Alta"]
    assert criterios["FIN-03"]["calculable"] == "ROI"
    assert criterios["FIN-02"]["calculable"] == "RECUPERACION"
    assert sum(1 for c in criterios.values() if c["calculable"] != "NO") == 2


async def test_roles_sugeridos_por_dimension(usuario_con_sesion: CrearUsuario) -> None:
    marco = await _marco(usuario_con_sesion)

    sugeridos = {d["codigo"]: d["rol_sugerido"] for d in marco["dimensiones"]}
    assert sugeridos == {
        "MER": "LIDER_COMERCIAL",
        "COM": "LIDER_COMERCIAL",
        "FIN": "PM",
        "TEC": "LIDER_TECNICO",
        "CMP": "PM",
        "ECO": "LIDER_ESTRATEGIA",
    }


async def test_la_semilla_es_idempotente(sesion, usuario_con_sesion: CrearUsuario) -> None:
    await sembrar_datos_base(sesion)
    await sembrar_datos_base(sesion)
    await sesion.commit()

    marco = await _marco(usuario_con_sesion)
    assert sum(len(d["criterios"]) for d in marco["dimensiones"]) == 28
