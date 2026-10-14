"""Resultado consolidado y resumen ejecutivo (Fase 6, HU4)

Revisión: 0004
Anterior: 0003
Fecha: 2026-10-14 16:56:55.570095
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "resultado_consolidado",
        sa.Column("evaluacion_id", sa.Uuid(), nullable=False),
        sa.Column("score_total", sa.Float(), nullable=False),
        sa.Column("puntajes_dimension", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("puntajes_criterio", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "resultado",
            sa.Enum(
                "GO", "ITERAR", "VALIDAR", "NO_GO", name="resultado", native_enum=False, length=10
            ),
            nullable=False,
        ),
        sa.Column("regla", sa.String(length=3), nullable=False),
        sa.Column("regla_aplicada", sa.Text(), nullable=False),
        sa.Column(
            "dimensiones_implicadas", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("fortalezas", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("debilidades", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("riesgos", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("supuestos_criticos", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("borrador_ia", sa.Boolean(), nullable=False),
        sa.Column("consolidado_por_id", sa.Uuid(), nullable=True),
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
            ["consolidado_por_id"],
            ["usuario.id"],
            name=op.f("fk_resultado_consolidado_consolidado_por_id_usuario"),
        ),
        sa.ForeignKeyConstraint(
            ["evaluacion_id"],
            ["evaluacion.id"],
            name=op.f("fk_resultado_consolidado_evaluacion_id_evaluacion"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_resultado_consolidado")),
        sa.UniqueConstraint("evaluacion_id", name=op.f("uq_resultado_consolidado_evaluacion_id")),
    )
    op.create_index(
        op.f("ix_resultado_consolidado_resultado"),
        "resultado_consolidado",
        ["resultado"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_resultado_consolidado_resultado"), table_name="resultado_consolidado")
    op.drop_table("resultado_consolidado")
