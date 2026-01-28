"""
Prompt templates for FOMC topic analysis agents.

Uses a factory pattern for scalable, type-safe prompt generation.
"""

from enum import Enum


class Topic(str, Enum):
    """Predefined FOMC analysis topics."""

    HOUSING = "Real Estate & Housing Market"
    LABOR = "Labor Market & Unemployment"
    INFLATION = "Inflation & Price Stability"
    GDP = "Economic Growth & GDP"
    CONSUMER = "Consumer Spending & Retail"
    INTEREST_RATE = "Interest Rate & Monetary Policy"
    FOREX = "Foreign Exchange & Currency Markets"
    EQUITY = "Equity Markets & Stock Performance"
    BONDS = "Fixed Income & Bond Markets"


def create_analysis_prompt(topic: Topic) -> str:
    """
    Generate a specialized FOMC analysis prompt for a given topic.

    Args:
        topic: The Topic enum value to generate a prompt for.

    Returns:
        A formatted prompt string with {articles_text} placeholder.
    """
    return f"""
Perform a specialized analysis of the provided articles focusing exclusively on: {topic.value} in the context of the FOMC meeting.

A. METRICS ({topic.value}):
Extract every mentioned metric specifically related to {topic.value}.
For each metric:
  1. metric_name: Name of the indicator.
  2. value: Latest specific value (e.g., "4.2%", "150k").
  3. metric_period: The time period this value refers to (e.g., "August 2025", "Q3").
  4. discussion: Explain the significance of this metric. What is being said about it?
  5. sentiment: The sentiment when mentioning this metric.
  6. article_id: The specific Article ID(s) where this is found (e.g., ["0", "3"]).

B. EXPERT ANALYSIS ({topic.value}):
Identify experts providing commentary/analysis on {topic.value} and Fed policy.
For each expert:
  1. expert_name & expert_organization.
  2. expert_opinion: Their forecast/expectation/opinion about the topic.
  3. sentiment: 'positive', 'negative', or 'neutral'.
  4. article_id: The specific Article ID(s).

C. EXECUTIVE SUMMARY:
Write a summary that synthesizes all points to explain {topic.value} in the context of the FOMC decision.

Articles:
{{articles}}
"""
