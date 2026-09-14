"""Initial prediction schema."""

import sqlalchemy as sa
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "model_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("experiment_id", sa.String(100), nullable=False),
        sa.Column("model_version", sa.String(150), nullable=False, unique=True),
        sa.Column("architecture", sa.String(100), nullable=False),
        sa.Column("backend", sa.String(30), nullable=False),
        sa.Column("artifact_sha256", sa.String(64), nullable=False),
        sa.Column("runtime", sa.String(100), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_model_versions_experiment_id", "model_versions", ["experiment_id"])
    op.create_table(
        "prediction_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("correlation_id", sa.String(36), nullable=False),
        sa.Column("model_version_id", sa.Integer(), sa.ForeignKey("model_versions.id"), nullable=False),
        sa.Column("backend", sa.String(30), nullable=False),
        sa.Column("image_width", sa.Integer(), nullable=False),
        sa.Column("image_height", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(50), nullable=False),
        sa.Column("storage_uri", sa.String(500)),
        sa.Column("latency_ms", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_prediction_requests_created_at", "prediction_requests", ["created_at"])
    op.create_table(
        "detections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "prediction_id",
            sa.String(36),
            sa.ForeignKey("prediction_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("class_id", sa.Integer(), nullable=False),
        sa.Column("class_name", sa.String(100), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("x1", sa.Float(), nullable=False),
        sa.Column("y1", sa.Float(), nullable=False),
        sa.Column("x2", sa.Float(), nullable=False),
        sa.Column("y2", sa.Float(), nullable=False),
    )
    op.create_index("ix_detections_prediction_id", "detections", ["prediction_id"])


def downgrade():
    op.drop_table("detections")
    op.drop_table("prediction_requests")
    op.drop_table("model_versions")
