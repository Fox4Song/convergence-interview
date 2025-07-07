"""
Data models for the Pokedex Agent.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ResearchStepType(str, Enum):
    """Types of research steps."""

    CLARIFICATION = "clarification"
    POKEAPI_QUERY = "pokeapi_query"
    WEB_SEARCH = "web_search"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"


class ResearchStep(BaseModel):
    """A single step in the research process."""

    step_type: ResearchStepType
    description: str
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    sources: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    success: bool = True
    error_message: Optional[str] = None


class PokemonData(BaseModel):
    """Pokemon data structure."""

    id: int
    name: str
    types: List[str]
    height: float
    weight: float
    base_experience: int
    abilities: List[str]
    stats: Dict[str, int]
    moves: List[str]
    sprites: Dict[str, str]
    description: Optional[str] = None
    evolution_chain: Optional[List[str]] = None
    location_areas: Optional[List[str]] = None


class ResearchContext(BaseModel):
    """Context for the research process."""

    original_query: str
    clarified_goals: List[str] = Field(default_factory=list)
    research_steps: List[ResearchStep] = Field(default_factory=list)
    collected_data: Dict[str, Any] = Field(default_factory=dict)
    current_focus: Optional[str] = None
    user_feedback: Optional[str] = None


class ResearchReport(BaseModel):
    """Final research report."""

    query: str
    executive_summary: str
    detailed_findings: Dict[str, Any]
    recommendations: List[str]
    sources: List[str]
    research_steps: List[ResearchStep]
    generated_at: datetime = Field(default_factory=datetime.now)
    confidence_score: float = Field(ge=0.0, le=1.0)
    limitations: List[str] = Field(default_factory=list)


class TeamRecommendation(BaseModel):
    """Pokemon team recommendation."""

    team_name: str
    pokemon: List[PokemonData]
    strategy: str
    strengths: List[str]
    weaknesses: List[str]
    synergy_notes: str
    training_tips: List[str]


class ComparisonResult(BaseModel):
    """Result of comparing our agent vs ChatGPT."""

    our_agent_response: ResearchReport
    chatgpt_response: str
    comparison_analysis: str
    advantages_our_agent: List[str]
    advantages_chatgpt: List[str]
    overall_assessment: str
