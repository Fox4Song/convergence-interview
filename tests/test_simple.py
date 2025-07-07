"""
Simple tests to verify the basic setup works.
"""

import pytest
from src.models import ResearchContext, ResearchStep, ResearchStepType


def test_models_import():
    """Test that models can be imported and created."""
    context = ResearchContext(original_query="test")
    assert context.original_query == "test"
    assert len(context.clarified_goals) == 0


def test_research_step():
    """Test that research steps can be created."""
    step = ResearchStep(
        step_type=ResearchStepType.CLARIFICATION, description="Test step"
    )
    assert step.step_type == ResearchStepType.CLARIFICATION
    assert step.description == "Test step"
    assert step.success is True


def test_config_import():
    """Test that config can be imported."""
    from src.config import settings

    assert hasattr(settings, "openai_api_key")
    assert hasattr(settings, "pokeapi_base_url")


def test_pokeapi_client_import():
    """Test that PokeAPI client can be imported."""
    from src.pokeapi_client import PokeAPIClient

    assert PokeAPIClient is not None


def test_web_researcher_import():
    """Test that web researcher can be imported."""
    from src.web_researcher import WebResearcher

    assert WebResearcher is not None


@pytest.mark.asyncio
async def test_simple_async():
    """Test that async functionality works."""

    async def dummy_async_function():
        return "async works"

    result = await dummy_async_function()
    assert result == "async works"
