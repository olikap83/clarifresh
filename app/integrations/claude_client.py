import json
import logging
from typing import Any

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

SENTIMENT_SYSTEM = """You are a social media sentiment analyst for an ag-tech produce company.
You analyze comments on competitor social media posts to understand audience reception.

Return ONLY a valid JSON object with this exact schema:
{
  "overall_sentiment": "positive" | "negative" | "neutral" | "mixed",
  "positive_score": float (0.0 to 1.0),
  "negative_score": float (0.0 to 1.0),
  "neutral_score": float (0.0 to 1.0),
  "key_themes": [list of 3-5 short theme strings],
  "sentiment_summary": "2-3 sentence prose summary of the comment sentiment"
}

The three scores must sum to 1.0. Do not include any text outside the JSON object."""

SUMMARY_SYSTEM = """You are a content strategy analyst for an ag-tech produce company.
You analyze competitor social media posts to extract strategic insights.

Return ONLY a valid JSON object with this exact schema:
{
  "summary": "2-3 sentence summary covering: what the post communicates, the content strategy evident, and the likely target audience signal"
}

Do not include any text outside the JSON object."""

INSIGHTS_SYSTEM = """You are a senior competitive intelligence analyst for an ag-tech produce company.
You analyze social media performance data to generate actionable weekly insights.

Return ONLY a valid JSON object with this exact schema:
{
  "title": "concise insight report title",
  "body": "3-5 paragraph prose analysis of the week's competitive landscape",
  "recommendations": ["3-5 specific actionable recommendation strings"],
  "top_post_ids": ["list of UUIDs of the top performing posts you reference"],
  "flop_post_ids": ["list of UUIDs of the underperforming posts you reference"]
}

Do not include any text outside the JSON object."""


def _call_claude(system: str, user_content: str, cache_system: bool = True) -> tuple[str, int, int]:
    system_block: Any = [
        {
            "type": "text",
            "text": system,
            **({"cache_control": {"type": "ephemeral"}} if cache_system else {}),
        }
    ]

    response = _client.messages.create(
        model=settings.claude_model,
        max_tokens=1024,
        system=system_block,
        messages=[{"role": "user", "content": user_content}],
    )

    text = response.content[0].text
    prompt_tokens = response.usage.input_tokens
    completion_tokens = response.usage.output_tokens
    return text, prompt_tokens, completion_tokens


def analyze_sentiment(comments: list[str]) -> tuple[dict, int, int]:
    comment_block = "\n".join(f"- {c}" for c in comments[:200])
    user_msg = f"Analyze the sentiment of these {len(comments)} social media comments:\n\n{comment_block}"
    raw, pt, ct = _call_claude(SENTIMENT_SYSTEM, user_msg)
    return json.loads(raw), pt, ct


def generate_summary(platform: str, post_type: str, caption: str, hashtags: list[str]) -> tuple[str, int, int]:
    user_msg = (
        f"Platform: {platform}\n"
        f"Post type: {post_type}\n"
        f"Caption: {caption or '(no caption)'}\n"
        f"Hashtags: {', '.join(hashtags) if hashtags else '(none)'}\n\n"
        "Generate a strategic summary of this post."
    )
    raw, pt, ct = _call_claude(SUMMARY_SYSTEM, user_msg)
    data = json.loads(raw)
    return data["summary"], pt, ct


def generate_insights(posts_data: str) -> tuple[dict, int, int]:
    user_msg = f"Generate a weekly competitive intelligence insight report from this post performance data:\n\n{posts_data}"
    raw, pt, ct = _call_claude(INSIGHTS_SYSTEM, user_msg)
    return json.loads(raw), pt, ct
