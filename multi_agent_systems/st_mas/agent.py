"""
FOMC Topic Analysis Agents.

Supports both predefined topics and dynamic user-defined topics at runtime.
"""
from google.adk.agents import ParallelAgent, LlmAgent

from .agent_helper_functions import (
    create_all_predefined_agents,
)

# Default: Create predefined agents
predefined_agents = create_all_predefined_agents()


# Default pipeline with predefined topics
st_mas = ParallelAgent(
    name="st_mas",
    sub_agents=predefined_agents,
    description="Executes parallel analysis of FOMC topics across multiple economic areas.",
)
