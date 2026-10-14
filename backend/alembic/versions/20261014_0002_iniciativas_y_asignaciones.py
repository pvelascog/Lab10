"""Iniciativas y asignación de evaluadores por dimensión (Fase 3, HU1)

Revisión: 0002
Anterior: 0001
Fecha: 2026-10-14 15:07:42.442380
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "iniciativa",
        sa.Column("numero", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("codigo", sa.String(length=20), nullable=False),
        sa.Column("nombre", sa.String(length=200), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column(
            "origen",
            sa.Enum(
                "CLIENTES",
                "EQUIPO_INTERNO",
                "MERCADO",
                "SOCIOS",
                "TENDENCIAS",
                "PORTAFOLIO",
                "INNOVACION_INTERNA",
                name="origen_iniciativa",
                native_enum=False,
                length=30,
            ),
            nullable=False,
        ),
        sa.Column(
            "estado",
            sa.Enum(
                "IDENTIFICADA",
                "ESTRUCTURADA",
                "EN_EVALUACION",
                "CONSOLIDADA",
                "EN_COMITE",
                "DECIDIDA",
                "EN_SEGUIMIENTO",
                "ARCHIVADA",
                name="estado_iniciativa",
                native_enum=False,
                length=30,
            ),
            nullable=False,
        ),
        sa.Column("autor_id", sa.Uuid(), nullable=False),
        sa.Column("pm_id", sa.Uuid(), nullable=True),
        sa.Column("problema", sa.Text(), nullable=True),
        sa.Column("solucion_objetivo", sa.Text(), nullable=True),
        sa.Column("segmento", sa.Text(), nullable=True),
        sa.Column("propuesta_valor", sa.Text(), nullable=True),
        sa.Column("supuestos_clave", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("datos_disponibles", sa.Text(), nullable=True),
        sa.Column("inversion_estimada", sa.Numeric(precision=16, scale=2), nullable=True),
        sa.Column("ingresos_esperados", sa.Numeric(precision=16, scale=2), nullable=True),
        sa.Column("flujo_mensual_neto", sa.Numeric(precision=16, scale=2), nullable=True),
        sa.Column("posible_duplicado_de_id", sa.Uuid(), nullable=True),
        sa.Column("similitud_duplicado", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "actualizado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["autor_id"], ["usuario.id"], name=op.f("fk_iniciativa_autor_id_usuario")
        ),
        sa.ForeignKeyConstraint(
            ["pm_id"], ["usuario.id"], name=op.f("fk_iniciativa_pm_id_usuario")
        ),
        sa.ForeignKeyConstraint(
            ["posible_duplicado_de_id"],
            ["iniciativa.id"],
            name=op.f("fk_iniciativa_posible_duplicado_de_id_iniciativa"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_iniciativa")),
        sa.UniqueConstraint("codigo", name=op.f("uq_iniciativa_codigo")),
        sa.UniqueConstraint("numero", name=op.f("uq_iniciativa_numero")),
    )
    op.create_index(op.f("ix_iniciativa_autor_id"), "iniciativa", ["autor_id"], unique=False)
    op.create_index(op.f("ix_iniciativa_estado"), "iniciativa", ["estado"], unique=False)
    op.create_index(op.f("ix_iniciativa_pm_id"), "iniciativa", ["pm_id"], unique=False)
    op.create_table(
        "asignacion_evaluador",
        sa.Column("iniciativa_id", sa.Uuid(), nullable=False),
        sa.Column("dimension_codigo", sa.String(length=3), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column(
            "origen",
            sa.Enum("MANUAL", "SUGERIDA", name="origen_asignacion", native_enum=False, length=20),
            nullable=False,
        ),
        sa.Column("razon_sugerencia", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "actualizado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["iniciativa_id"],
            ["iniciativa.id"],
            name=op.f("fk_asignacion_evaluador_iniciativa_id_iniciativa"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"], ["usuario.id"], name=op.f("fk_asignacion_evaluador_usuario_id_usuario")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_asignacion_evaluador")),
        sa.UniqueConstraint(
            "iniciativa_id",
            "dimension_codigo",
            "usuario_id",
            name=op.f("uq_asignacion_evaluador_iniciativa_id"),
        ),
    )
    op.create_index(
        op.f("ix_asignacion_evaluador_usuario_id"),
        "asignacion_evaluador",
        ["usuario_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_asignacion_evaluador_usuario_id"), table_name="asignacion_evaluador")
    op.drop_table("asignacion_evaluador")
    op.drop_index(op.f("ix_iniciativa_pm_id"), table_name="iniciativa")
    op.drop_index(op.f("ix_iniciativa_estado"), table_name="iniciativa")
    op.drop_index(op.f("ix_iniciativa_autor_id"), table_name="iniciativa")
    op.drop_table("iniciativa")
