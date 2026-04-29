"""add reconstruction models and timestamps

Revision ID: 0003_reconstruction_models_and_timestamps
Revises: 0002_add_projects
Create Date: 2026-04-29 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "0003_reconstruction_models_and_timestamps"
down_revision: Union[str, None] = "0002_add_projects"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()

    op.add_column("image_set", sa.Column("updated_at", sa.DateTime(), nullable=True))
    connection.execute(sa.text("UPDATE image_set SET updated_at = created_at"))
    with op.batch_alter_table("image_set") as batch_op:
        batch_op.alter_column("updated_at", existing_type=sa.DateTime(), nullable=False)

    op.add_column("frame", sa.Column("created_at", sa.DateTime(), nullable=True))
    connection.execute(
        sa.text(
            """
            UPDATE frame
            SET created_at = (
                SELECT image_set.created_at
                FROM image_set
                WHERE image_set.id = frame.image_set_id
            )
            """
        )
    )
    with op.batch_alter_table("frame") as batch_op:
        batch_op.alter_column("timestamp_seconds", existing_type=sa.Float(), nullable=True)
        batch_op.alter_column("width", existing_type=sa.Integer(), nullable=True)
        batch_op.alter_column("height", existing_type=sa.Integer(), nullable=True)
        batch_op.alter_column("created_at", existing_type=sa.DateTime(), nullable=False)

    op.add_column("annotation_document", sa.Column("created_at", sa.DateTime(), nullable=True))
    connection.execute(sa.text("UPDATE annotation_document SET created_at = updated_at"))
    with op.batch_alter_table("annotation_document") as batch_op:
        batch_op.alter_column("created_at", existing_type=sa.DateTime(), nullable=False)

    op.create_table(
        "reconstruction_model",
        sa.Column("id", sqlmodel.sql.sqltypes.AutoString(), primary_key=True, nullable=False),
        sa.Column("project_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("data_json", sa.JSON(), nullable=False),
        sa.Column("source", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_reconstruction_model_project_id", "reconstruction_model", ["project_id"])
    op.create_index("ix_reconstruction_model_version", "reconstruction_model", ["version"])


def downgrade() -> None:
    op.drop_index("ix_reconstruction_model_version", table_name="reconstruction_model")
    op.drop_index("ix_reconstruction_model_project_id", table_name="reconstruction_model")
    op.drop_table("reconstruction_model")

    with op.batch_alter_table("annotation_document") as batch_op:
        batch_op.drop_column("created_at")

    with op.batch_alter_table("frame") as batch_op:
        batch_op.alter_column("height", existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column("width", existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column("timestamp_seconds", existing_type=sa.Float(), nullable=False)
        batch_op.drop_column("created_at")

    with op.batch_alter_table("image_set") as batch_op:
        batch_op.drop_column("updated_at")
