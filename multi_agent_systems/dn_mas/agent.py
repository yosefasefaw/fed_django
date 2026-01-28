from google.adk.agents import SequentialAgent
from google.adk.agents import LlmAgent
import os
from .instructions import *
from .schemas import *


GEMINI_MODEL = "gemini-3-flash-preview"

information_extraction_agent = LlmAgent(
    name="information_extraction_agent",
    model=GEMINI_MODEL,
    instruction=information_extraction_instruction,
    description="Extracts information from the article.",
    output_key="extracted_information"
)

information_summarizer_agent = LlmAgent(
    name="information_summarizer_agent",
    model=GEMINI_MODEL,
    instruction=information_summarizer_instruction,
    description="Write a summary based on the information extracted.",
    output_key="summary",
)

information_citation_agent = LlmAgent(
    name="information_citation_agent",
    model=GEMINI_MODEL,
    instruction=information_citation_instruction,
    description="Add citations to the summary.",
    output_key="summary_with_citations",
    output_schema=SummaryWithCitations,
)

summarizer_agent = SequentialAgent(
    name="summarization_pipeline",
    sub_agents=[information_extraction_agent, information_summarizer_agent, information_citation_agent],
    description="Executes a sequence of information extraction, summarization, and citation.",
)

# For ADK tools compatibility, the root agent must be named `root_agent`
dn_mas = summarizer_agent