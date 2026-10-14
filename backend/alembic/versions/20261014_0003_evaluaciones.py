"""Evaluaciones, calificaciones, envíos por dimensión y comentarios (Fase 5, HU3)

Revisión: 0003
Anterior: 0002
Fecha: 2026-10-14 16:27:01.538011
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "evaluacion",
        sa.Column("iniciativa_id", sa.Uuid(), nullable=False),
        sa.Column("version_marco_id", sa.Uuid(), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column(
            "estado",
            sa.Enum(
                "ABIERTA",
                "CONSOLIDADA",
                "DECIDIDA",
                name="estado_evaluacion",
                native_enum=False,
                length=20,
            ),
            nullable=False,
        ),
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
            name=op.f("fk_evaluacion_iniciativa_id_iniciativa"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["version_marco_id"],
            ["version_marco.id"],
            name=op.f("fk_evaluacion_version_marco_id_version_marco"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evaluacion")),
        sa.UniqueConstraint("iniciativa_id", "numero", name=op.f("uq_evaluacion_iniciativa_id")),
    )
    op.create_index(
        op.f("ix_evaluacion_iniciativa_id"), "evaluacion", ["iniciativa_id"], unique=False
    )
    op.create_table(
        "envio_dimension",
        sa.Column("evaluacion_id", sa.Uuid(), nullable=False),
        sa.Column("dimension_codigo", sa.String(length=3), nullable=False),
        sa.Column("evaluador_id", sa.Uuid(), nullable=False),
        sa.Column(
            "enviado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["evaluacion_id"],
            ["evaluacion.id"],
            name=op.f("fk_envio_dimension_evaluacion_id_evaluacion"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["evaluador_id"], ["usuario.id"], name=op.f("fk_envio_dimension_evaluador_id_usuario")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_envio_dimension")),
        sa.UniqueConstraint(
            "evaluacion_id",
            "dimension_codigo",
            "evaluador_id",
            name=op.f("uq_envio_dimension_evaluacion_id"),
        ),
    )
    op.create_table(
        "calificacion",
        sa.Column("evaluacion_id", sa.Uuid(), nullable=False),
        sa.Column("criterio_id", sa.Uuid(), nullable=False),
        sa.Column("evaluador_id", sa.Uuid(), nullable=True),
        sa.Column("nivel", sa.Integer(), nullable=False),
        sa.Column("justificacion", sa.Text(), nullable=False),
        sa.Column("fuente", sa.Text(), nullable=True),
        sa.Column(
            "origen",
            sa.Enum(
                "HUMANA",
                "IA_SUGERIDA",
                "IA_CONFIRMADA",
                "CALCULADA_CONFIRMADA",
                name="origen_calificacion",
                native_enum=False,
                length=30,
            ),
            nullable=False,
        ),
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
        sa.CheckConstraint(
            "length(trim(justificacion)) > 0",
            name=op.f("ck_calificacion_justificacion_obligatoria"),
        ),
        sa.CheckConstraint("nivel BETWEEN 1 AND 5", name=op.f("ck_calificacion_nivel_rango")),
        sa.ForeignKeyConstraint(
            ["criterio_id"], ["criterio.id"], name=op.f("fk_calificacion_criterio_id_criterio")
        ),
        sa.ForeignKeyConstraint(
            ["evaluacion_id"],
            ["evaluacion.id"],
            name=op.f("fk_calificacion_evaluacion_id_evaluacion"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["evaluador_id"], ["usuario.id"], name=op.f("fk_calificacion_evaluador_id_usuario")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_calificacion")),
        sa.UniqueConstraint(
            "evaluacion_id",
            "criterio_id",
            "evaluador_id",
            name=op.f("uq_calificacion_evaluacion_id"),
        ),
    )
    op.create_index(
        op.f("ix_calificacion_evaluacion_id"), "calificacion", ["evaluacion_id"], unique=False
    )
    op.create_table(
        "comentario_divergencia",
        sa.Column("evaluacion_id", sa.Uuid(), nullable=False),
        sa.Column("criterio_id", sa.Uuid(), nullable=False),
        sa.Column("autor_id", sa.Uuid(), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
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
            ["autor_id"], ["usuario.id"], name=op.f("fk_comentario_divergencia_autor_id_usuario")
        ),
        sa.ForeignKeyConstraint(
            ["criterio_id"],
            ["criterio.id"],
            name=op.f("fk_comentario_divergencia_criterio_id_criterio"),
        ),
        sa.ForeignKeyConstraint(
            ["evaluacion_id"],
            ["evaluacion.id"],
            name=op.f("fk_comentario_divergencia_evaluacion_id_evaluacion"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_comentario_divergencia")),
    )


def downgrade() -> None:
    op.drop_table("comentario_divergencia")
    op.drop_index(op.f("ix_calificacion_evaluacion_id"), table_name="calificacion")
    op.drop_table("calificacion")
    op.drop_table("envio_dimension")
    op.drop_index(op.f("ix_evaluacion_iniciativa_id"), table_name="evaluacion")
    op.drop_table("evaluacion")
