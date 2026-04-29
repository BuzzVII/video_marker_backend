"""add project scoped annotations

Revision ID: 0002_add_projects
Revises: 0001_initial
Create Date: 2026-04-28 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "0002_add_projects"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project",
        sa.Column("id", sqlmodel.sql.sqltypes.AutoString(), primary_key=True, nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.add_column(
        "image_set",
        sa.Column("project_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )

    connection = op.get_bind()
    image_sets = connection.execute(sa.text("SELECT id, name, created_at FROM image_set")).fetchall()

    for image_set_id, name, created_at in image_sets:
        project_id = f"project-{image_set_id}"
        connection.execute(
            sa.text(
                """
                INSERT INTO project (id, name, created_at, updated_at)
                VALUES (:id, :name, :created_at, :updated_at)
                """
            ),
            {
                "id": project_id,
                "name": name,
                "created_at": created_at,
                "updated_at": created_at,
            },
        )
        connection.execute(
            sa.text("UPDATE image_set SET project_id = :project_id WHERE id = :image_set_id"),
            {"project_id": project_id, "image_set_id": image_set_id},
        )

    with op.batch_alter_table("image_set") as batch_op:
        batch_op.alter_column("project_id", existing_type=sa.String(), nullable=False)
        batch_op.create_index("ix_image_set_project_id", ["project_id"])
        batch_op.create_foreign_key(
            "fk_image_set_project_id_project",
            "project",
            ["project_id"],
            ["id"],
            ondelete="CASCADE",
        )

    op.create_table(
        "annotation_document_new",
        sa.Column("id", sqlmodel.sql.sqltypes.AutoString(), primary_key=True, nullable=False),
        sa.Column("project_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("data_json", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("project_id"),
    )
    op.create_index("ix_annotation_document_project_id", "annotation_document_new", ["project_id"])

    connection.execute(
        sa.text(
            """
            INSERT INTO annotation_document_new (id, project_id, data_json, updated_at)
            SELECT
                'ann-' || annotation_document.image_set_id,
                image_set.project_id,
                annotation_document.data_json,
                annotation_document.updated_at
            FROM annotation_document
            JOIN image_set ON image_set.id = annotation_document.image_set_id
            """
        )
    )

    op.drop_table("annotation_document")
    op.rename_table("annotation_document_new", "annotation_document")


def downgrade() -> None:
    op.create_table(
        "annotation_document_old",
        sa.Column("image_set_id", sqlmodel.sql.sqltypes.AutoString(), primary_key=True, nullable=False),
        sa.Column("data_json", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["image_set_id"], ["image_set.id"], ondelete="CASCADE"),
    )

    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            INSERT INTO annotation_document_old (image_set_id, data_json, updated_at)
            SELECT image_set.id, annotation_document.data_json, annotation_document.updated_at
            FROM annotation_document
            JOIN image_set ON image_set.project_id = annotation_document.project_id
            """
        )
    )

    op.drop_table("annotation_document")
    op.rename_table("annotation_document_old", "annotation_document")

    with op.batch_alter_table("image_set") as batch_op:
        batch_op.drop_constraint("fk_image_set_project_id_project", type_="foreignkey")
        batch_op.drop_index("ix_image_set_project_id")
        batch_op.drop_column("project_id")

    op.drop_table("project")
