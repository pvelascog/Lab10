"""Esquema inicial: usuarios, roles, marco versionado y auditoría (Fase 2)

Revisión: 0001
Anterior:
Fecha: 2026-10-14 14:49:32.568133
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Similitud de texto para detectar iniciativas duplicadas (research.md D2).
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.create_table(
        "rol",
        sa.Column(
            "codigo",
            sa.Enum(
                "MIEMBRO",
                "PM",
                "LIDER_COMERCIAL",
                "LIDER_TECNICO",
                "LIDER_ESTRATEGIA",
                "COMITE",
                "ADMIN_MARCO",
                name="codigo_rol",
                native_enum=False,
                length=30,
            ),
            nullable=False,
        ),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rol")),
        sa.UniqueConstraint("codigo", name=op.f("uq_rol_codigo")),
    )
    op.create_table(
        "usuario",
        sa.Column("nombre", sa.String(length=200), nullable=False),
        sa.Column("correo", sa.String(length=320), nullable=False),
        sa.Column("hash_contrasena", sa.String(length=255), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("intentos_fallidos", sa.Integer(), nullable=False),
        sa.Column("bloqueado_hasta", sa.DateTime(timezone=True), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_usuario")),
        sa.UniqueConstraint("correo", name=op.f("uq_usuario_correo")),
    )
    op.create_table(
        "auditoria",
        sa.Column("usuario_id", sa.Uuid(), nullable=True),
        sa.Column("accion", sa.String(length=50), nullable=False),
        sa.Column("entidad", sa.String(length=50), nullable=False),
        sa.Column("entidad_id", sa.String(length=64), nullable=True),
        sa.Column("antes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("despues", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "fecha", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuario.id"],
            name=op.f("fk_auditoria_usuario_id_usuario"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auditoria")),
    )
    op.create_index(op.f("ix_auditoria_accion"), "auditoria", ["accion"], unique=False)
    op.create_index(op.f("ix_auditoria_usuario_id"), "auditoria", ["usuario_id"], unique=False)
    op.create_table(
        "usuario_rol",
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("rol_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["rol_id"], ["rol.id"], name=op.f("fk_usuario_rol_rol_id_rol"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuario.id"],
            name=op.f("fk_usuario_rol_usuario_id_usuario"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("usuario_id", "rol_id", name=op.f("pk_usuario_rol")),
    )
    op.create_table(
        "version_marco",
        sa.Column("numero", sa.String(length=20), nullable=False),
        sa.Column(
            "estado",
            sa.Enum(
                "BORRADOR",
                "VIGENTE",
                "RETIRADA",
                name="estado_version",
                native_enum=False,
                length=20,
            ),
            nullable=False,
        ),
        sa.Column("umbral_critico", sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column("umbral_validar", sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column("umbral_debil", sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column("umbral_score_go", sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column("umbral_score_iterar", sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column("umbral_score_validar", sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column("umbral_divergencia", sa.Integer(), nullable=False),
        sa.Column("creada_por_id", sa.Uuid(), nullable=True),
        sa.Column("notas_cambio", sa.Text(), nullable=True),
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
            ["creada_por_id"],
            ["usuario.id"],
            name=op.f("fk_version_marco_creada_por_id_usuario"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_version_marco")),
        sa.UniqueConstraint("numero", name=op.f("uq_version_marco_numero")),
    )
    op.create_index(
        "uq_version_marco_vigente",
        "version_marco",
        ["estado"],
        unique=True,
        postgresql_where="estado = 'VIGENTE'",
    )
    op.create_table(
        "dimension",
        sa.Column("version_marco_id", sa.Uuid(), nullable=False),
        sa.Column("codigo", sa.String(length=3), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("proposito", sa.Text(), nullable=False),
        sa.Column("peso", sa.Numeric(precision=9, scale=8), nullable=False),
        sa.Column(
            "rol_sugerido",
            sa.Enum(
                "MIEMBRO",
                "PM",
                "LIDER_COMERCIAL",
                "LIDER_TECNICO",
                "LIDER_ESTRATEGIA",
                "COMITE",
                "ADMIN_MARCO",
                name="codigo_rol",
                native_enum=False,
                length=30,
            ),
            nullable=True,
        ),
        sa.Column("orden", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["version_marco_id"],
            ["version_marco.id"],
            name=op.f("fk_dimension_version_marco_id_version_marco"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dimension")),
        sa.UniqueConstraint(
            "version_marco_id", "codigo", name=op.f("uq_dimension_version_marco_id")
        ),
    )
    op.create_table(
        "criterio",
        sa.Column("dimension_id", sa.Uuid(), nullable=False),
        sa.Column("codigo", sa.String(length=10), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("definicion", sa.Text(), nullable=False),
        sa.Column("escala_original", sa.Integer(), nullable=False),
        sa.Column(
            "calculable",
            sa.Enum("NO", "ROI", "RECUPERACION", name="tipo_calculo", native_enum=False, length=20),
            nullable=False,
        ),
        sa.Column("orden", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["dimension_id"],
            ["dimension.id"],
            name=op.f("fk_criterio_dimension_id_dimension"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_criterio")),
        sa.UniqueConstraint("dimension_id", "codigo", name=op.f("uq_criterio_dimension_id")),
    )
    op.create_table(
        "nivel_criterio",
        sa.Column("criterio_id", sa.Uuid(), nullable=False),
        sa.Column("nivel", sa.Integer(), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.CheckConstraint("nivel BETWEEN 1 AND 5", name=op.f("ck_nivel_criterio_nivel_rango")),
        sa.ForeignKeyConstraint(
            ["criterio_id"],
            ["criterio.id"],
            name=op.f("fk_nivel_criterio_criterio_id_criterio"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_nivel_criterio")),
        sa.UniqueConstraint("criterio_id", "nivel", name=op.f("uq_nivel_criterio_criterio_id")),
    )


def downgrade() -> None:
    op.drop_table("nivel_criterio")
    op.drop_table("criterio")
    op.drop_table("dimension")
    op.drop_index(
        "uq_version_marco_vigente",
        table_name="version_marco",
        postgresql_where="estado = 'VIGENTE'",
    )
    op.drop_table("version_marco")
    op.drop_table("usuario_rol")
    op.drop_index(op.f("ix_auditoria_usuario_id"), table_name="auditoria")
    op.drop_index(op.f("ix_auditoria_accion"), table_name="auditoria")
    op.drop_table("auditoria")
    op.drop_table("usuario")
    op.drop_table("rol")
