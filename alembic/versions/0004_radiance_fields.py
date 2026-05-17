"""add radiance field jobs and assets

Revision ID: 0004_radiance_fields
Revises: 0003_reconstruction_models_and_timestamps
Create Date: 2026-05-17 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "0004_radiance_fields"
down_revision: Union[str, None] = "0003_reconstruction_models_and_timestamps"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "radiance_field_job",
        sa.Column("id", sqlmodel.sql.sqltypes.AutoString(), primary_key=True, nullable=False),
        sa.Column("project_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("image_set_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("stage", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("progress", sa.Float(), nullable=False),
        sa.Column("error_message", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("work_dir", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("config_json", sa.JSON(), nullable=False),
        sa.Column("result_radiance_field_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["image_set_id"], ["image_set.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_radiance_field_job_project_id", "radiance_field_job", ["project_id"])
    op.create_index("ix_radiance_field_job_image_set_id", "radiance_field_job", ["image_set_id"])
    op.create_index("ix_radiance_field_job_status", "radiance_field_job", ["status"])
    op.create_index(
        "ix_radiance_field_job_result_radiance_field_id",
        "radiance_field_job",
        ["result_radiance_field_id"],
    )

    op.create_table(
        "radiance_field",
        sa.Column("id", sqlmodel.sql.sqltypes.AutoString(), primary_key=True, nullable=False),
        sa.Column("project_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("source_job_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("source_image_set_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("asset_path", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("asset_format", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_job_id"], ["radiance_field_job.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_image_set_id"], ["image_set.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_radiance_field_project_id", "radiance_field", ["project_id"])
    op.create_index("ix_radiance_field_source_job_id", "radiance_field", ["source_job_id"])
    op.create_index("ix_radiance_field_source_image_set_id", "radiance_field", ["source_image_set_id"])
    op.create_index("ix_radiance_field_status", "radiance_field", ["status"])


def downgrade() -> None:
    op.drop_index("ix_radiance_field_status", table_name="radiance_field")
    op.drop_index("ix_radiance_field_source_image_set_id", table_name="radiance_field")
    op.drop_index("ix_radiance_field_source_job_id", table_name="radiance_field")
    op.drop_index("ix_radiance_field_project_id", table_name="radiance_field")
    op.drop_table("radiance_field")

    op.drop_index("ix_radiance_field_job_result_radiance_field_id", table_name="radiance_field_job")
    op.drop_index("ix_radiance_field_job_status", table_name="radiance_field_job")
    op.drop_index("ix_radiance_field_job_image_set_id", table_name="radiance_field_job")
    op.drop_index("ix_radiance_field_job_project_id", table_name="radiance_field_job")
    op.drop_table("radiance_field_job")
