"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-28 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "image_set",
        sa.Column("id", sqlmodel.sql.sqltypes.AutoString(), primary_key=True, nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("source_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("original_video_path", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "frame",
        sa.Column("id", sqlmodel.sql.sqltypes.AutoString(), primary_key=True, nullable=False),
        sa.Column("image_set_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("frame_index", sa.Integer(), nullable=False),
        sa.Column("timestamp_seconds", sa.Float(), nullable=False),
        sa.Column("image_path", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["image_set_id"], ["image_set.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_frame_image_set_id", "frame", ["image_set_id"])
    op.create_index(
        "ix_frame_image_set_id_frame_index",
        "frame",
        ["image_set_id", "frame_index"],
        unique=True,
    )
    op.create_table(
        "annotation_document",
        sa.Column("image_set_id", sqlmodel.sql.sqltypes.AutoString(), primary_key=True, nullable=False),
        sa.Column("data_json", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["image_set_id"], ["image_set.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("annotation_document")
    op.drop_index("ix_frame_image_set_id_frame_index", table_name="frame")
    op.drop_index("ix_frame_image_set_id", table_name="frame")
    op.drop_table("frame")
    op.drop_table("image_set")
