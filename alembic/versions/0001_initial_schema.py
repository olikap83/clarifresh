"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-19
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "competitors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("platform", sa.String(20), nullable=False),
        sa.Column("handle", sa.String(255), nullable=False),
        sa.Column("account_id", sa.String(255), nullable=True),
        sa.Column("hashtags", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("platform", "handle", name="uq_competitors_platform_handle"),
    )
    op.create_index("ix_competitors_platform_active", "competitors", ["platform", "is_active"])

    op.create_table(
        "social_posts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("competitor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform", sa.String(20), nullable=False),
        sa.Column("platform_post_id", sa.String(255), nullable=False),
        sa.Column("post_type", sa.String(20), nullable=False),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("hashtags", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("thumbnail_url", sa.Text(), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("summary_generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("platform", "platform_post_id", name="uq_social_posts_platform_post_id"),
    )
    op.create_index("ix_social_posts_competitor_posted", "social_posts", ["competitor_id", sa.text("posted_at DESC")])
    op.create_index("ix_social_posts_ingested_at", "social_posts", ["ingested_at"])

    op.create_table(
        "comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("social_post_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("social_posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform_comment_id", sa.String(255), nullable=False),
        sa.Column("author_handle", sa.String(255), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("likes_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("social_post_id", "platform_comment_id", name="uq_comments_post_comment"),
    )
    op.create_index("ix_comments_social_post_id", "comments", ["social_post_id"])

    op.create_table(
        "post_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("social_post_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("social_posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("snapshot_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("views_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("likes_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("comments_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("shares_count", sa.BigInteger(), nullable=True),
        sa.Column("saves_count", sa.BigInteger(), nullable=True),
        sa.Column("engagement_rate", sa.Numeric(8, 4), nullable=True),
        sa.Column("rank_score", sa.Numeric(12, 4), nullable=True),
    )
    op.create_index("ix_post_metrics_post_snapshot", "post_metrics", ["social_post_id", sa.text("snapshot_at DESC")])

    op.create_table(
        "sentiment_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("social_post_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("social_posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("overall_sentiment", sa.String(20), nullable=False),
        sa.Column("positive_score", sa.Numeric(5, 4), nullable=False),
        sa.Column("negative_score", sa.Numeric(5, 4), nullable=False),
        sa.Column("neutral_score", sa.Numeric(5, 4), nullable=False),
        sa.Column("comment_count_analyzed", sa.Integer(), nullable=False),
        sa.Column("key_themes", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("sentiment_summary", sa.Text(), nullable=True),
        sa.Column("raw_claude_response", postgresql.JSONB(), nullable=True),
        sa.Column("model_used", sa.String(100), nullable=False, server_default="claude-sonnet-4-6"),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
    )
    op.create_index("ix_sentiment_results_post_analyzed", "sentiment_results", ["social_post_id", sa.text("analyzed_at DESC")])

    op.create_table(
        "insights",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("platform", sa.String(20), nullable=True),
        sa.Column("competitor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("competitors.id", ondelete="SET NULL"), nullable=True),
        sa.Column("insight_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("top_post_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column("flop_post_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column("recommendations", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("model_used", sa.String(100), nullable=False, server_default="claude-sonnet-4-6"),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
    )
    op.create_index("ix_insights_period_competitor", "insights", ["period_start", "competitor_id"])

    op.create_table(
        "ingestion_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("trigger_type", sa.String(20), nullable=False),
        sa.Column("triggered_by", sa.String(255), nullable=True),
        sa.Column("platform", sa.String(20), nullable=True),
        sa.Column("competitor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("competitors.id", ondelete="SET NULL"), nullable=True),
        sa.Column("apify_run_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("posts_ingested", sa.Integer(), nullable=True),
        sa.Column("comments_ingested", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ingestion_jobs_status_started", "ingestion_jobs", ["status", sa.text("started_at DESC")])


def downgrade() -> None:
    op.drop_table("ingestion_jobs")
    op.drop_table("insights")
    op.drop_table("sentiment_results")
    op.drop_table("post_metrics")
    op.drop_table("comments")
    op.drop_table("social_posts")
    op.drop_table("competitors")
