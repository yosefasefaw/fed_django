"""
FOMC Topic Analysis Agents - Helper Functions.

Factory functions for creating topic-specific analysis agents.
"""
from google.adk.agents import LlmAgent

from .instructions import create_analysis_prompt, Topic
from .schemas import TopicSummaryAndAnalysisLLM


GEMINI_MODEL = "gemini-3-flash-preview"


def create_topic_agent(topic: Topic) -> LlmAgent:
    """
    Factory function to create a topic-specific analysis agent.
    
    Args:
        topic: The Topic enum value for this agent.
        
    Returns:
        A configured LlmAgent for the specified topic with structured output.
    """
    return LlmAgent(
        name=f"{topic.name.lower()}_analysis_agent",
        model=GEMINI_MODEL,
        instruction=create_analysis_prompt(topic),
        description=f"Analyze {topic.value} content from FOMC related articles",
        output_key=f"{topic.name.lower()}_analysis",
        output_schema=TopicSummaryAndAnalysisLLM,
    )


def create_all_predefined_agents() -> list[LlmAgent]:
    """Create agents for all predefined topics in the Topic enum."""
    return [create_topic_agent(topic) for topic in Topic]

# we need to be able to change the TOPIC list dynamically according to the user's choice
