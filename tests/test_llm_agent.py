"""
Tests for the LLM agent.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.models import ResearchContext, ResearchReport


@pytest.fixture
def mock_llm_agent():
    """Create a fully mocked LLM agent."""
    with (
        patch("src.llm_agent.openai.OpenAI") as mock_openai,
        patch("src.llm_agent.openai.api_key", "test-key"),
        patch("src.llm_agent.PokeAPIClient") as mock_pokeapi,
        patch("src.llm_agent.WebResearcher") as mock_web_researcher,
    ):

        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Mock PokeAPI client
        mock_poke_client = AsyncMock()
        mock_pokeapi.return_value.__aenter__.return_value = mock_poke_client

        # Mock WebResearcher
        mock_web = MagicMock()
        mock_web_researcher.return_value = mock_web

        # Import and create agent after all mocks are in place
        from src.llm_agent import LLMAgent

        agent = LLMAgent()

        return {
            "agent": agent,
            "mock_openai": mock_openai,
            "mock_client": mock_client,
            "mock_pokeapi": mock_pokeapi,
            "mock_poke_client": mock_poke_client,
            "mock_web_researcher": mock_web_researcher,
            "mock_web": mock_web,
        }


@pytest.mark.asyncio
async def test_conduct_research_basic(mock_llm_agent):
    """Test basic research conduction."""
    agent = mock_llm_agent["agent"]
    mock_client = mock_llm_agent["mock_client"]
    mock_poke_client = mock_llm_agent["mock_poke_client"]
    mock_web = mock_llm_agent["mock_web"]

    # Mock the clarification response
    mock_choice = MagicMock()
    mock_choice.message.content = '{"goals": ["test"], "pokemon_to_research": ["pikachu"], "research_focus": "test", "constraints": []}'
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response

    # Mock the analysis response
    mock_analysis_choice = MagicMock()
    mock_analysis_choice.message.content = '{"key_findings": ["finding1"], "recommendations": ["rec1"], "considerations": ["cons1"], "limitations": ["lim1"], "confidence_score": 0.85}'
    mock_analysis_response = MagicMock()
    mock_analysis_response.choices = [mock_analysis_choice]

    # Mock the report response
    mock_report_choice = MagicMock()
    mock_report_choice.message.content = (
        "This is a comprehensive research report about the query."
    )
    mock_report_response = MagicMock()
    mock_report_response.choices = [mock_report_choice]

    # Set up side effect to return different responses for different calls
    mock_client.chat.completions.create.side_effect = [
        mock_response,  # First call for clarification
        mock_analysis_response,  # Second call for analysis
        mock_report_response,  # Third call for report
    ]

    # Mock PokeAPI responses to return proper data
    mock_pokemon = MagicMock()
    mock_pokemon.model_dump.return_value = {
        "name": "pikachu",
        "types": ["electric"],
        "stats": {"hp": 35, "attack": 55},
    }
    mock_poke_client.get_pokemon_by_name.return_value = mock_pokemon
    mock_poke_client.get_pokemon_description.return_value = "A cute electric mouse"
    mock_poke_client.get_evolution_chain.return_value = ["pichu", "pikachu", "raichu"]

    # Mock web researcher responses
    mock_web.search_pokemon_info.return_value = [
        {
            "title": "Pikachu Info",
            "url": "http://example.com",
            "content": "Pikachu is electric",
        }
    ]
    mock_web.search_training_tips.return_value = ["Train Pikachu with Thunder Stone"]
    mock_web.search_competitive_info.return_value = {"movesets": [], "strategies": []}
    mock_web.search_location_info.return_value = ["Found in Viridian Forest"]

    report = await agent.conduct_research("Test query")

    assert isinstance(report, ResearchReport)
    assert report.query == "Test query"


@pytest.mark.asyncio
async def test_clarify_goals(mock_llm_agent):
    """Test goal clarification process."""
    agent = mock_llm_agent["agent"]
    mock_client = mock_llm_agent["mock_client"]

    mock_choice = MagicMock()
    mock_choice.message.content = '{"goals": ["goal1", "goal2"], "pokemon_to_research": ["pikachu"], "research_focus": "focus", "constraints": ["constraint1"]}'
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response

    context = ResearchContext(original_query="Test query")
    await agent._clarify_goals(context)

    assert len(context.clarified_goals) == 2
    assert context.collected_data["pokemon_to_research"] == ["pikachu"]
    assert context.collected_data["research_focus"] == "focus"
    assert len(context.research_steps) == 1


@pytest.mark.asyncio
async def test_research_pokemon_api(mock_llm_agent):
    """Test Pokemon API research."""
    agent = mock_llm_agent["agent"]
    mock_poke_client = mock_llm_agent["mock_poke_client"]

    # Mock Pokemon data
    mock_pokemon = MagicMock()
    mock_pokemon.model_dump.return_value = {
        "name": "pikachu",
        "types": ["electric"],
        "stats": {"hp": 35, "attack": 55},
    }
    mock_poke_client.get_pokemon_by_name.return_value = mock_pokemon
    mock_poke_client.get_pokemon_description.return_value = "A cute electric mouse"
    mock_poke_client.get_evolution_chain.return_value = ["pichu", "pikachu", "raichu"]

    context = ResearchContext(original_query="Test query")
    await agent._research_pokemon_api("pikachu", context)

    assert "pokemon_pikachu" in context.collected_data
    assert len(context.research_steps) == 1
    assert context.research_steps[0].success is True


@pytest.mark.asyncio
async def test_research_pokemon_web(mock_llm_agent):
    """Test web research for Pokemon."""
    agent = mock_llm_agent["agent"]
    mock_web = mock_llm_agent["mock_web"]

    mock_web.search_pokemon_info.return_value = [
        {
            "title": "Pikachu Info",
            "url": "http://example.com",
            "content": "Pikachu is electric",
        }
    ]
    mock_web.search_training_tips.return_value = ["Train Pikachu with Thunder Stone"]
    mock_web.search_competitive_info.return_value = {"movesets": [], "strategies": []}
    mock_web.search_location_info.return_value = ["Found in Viridian Forest"]

    context = ResearchContext(original_query="Test query")
    await agent._research_pokemon_web("pikachu", context)

    assert "web_data_pikachu" in context.collected_data
    assert len(context.research_steps) == 1
    assert context.research_steps[0].success is True


@pytest.mark.asyncio
async def test_research_team_composition(mock_llm_agent):
    """Test team composition research."""
    agent = mock_llm_agent["agent"]
    mock_poke_client = mock_llm_agent["mock_poke_client"]

    mock_poke_client.get_all_types.return_value = ["fire", "water", "grass", "electric"]

    context = ResearchContext(original_query="Build a team")
    await agent._research_team_composition(context)

    assert "team_research" in context.collected_data
    assert "available_types" in context.collected_data["team_research"]
    assert len(context.research_steps) == 1


@pytest.mark.asyncio
async def test_research_training_info(mock_llm_agent):
    """Test training information research."""
    agent = mock_llm_agent["agent"]
    mock_poke_client = mock_llm_agent["mock_poke_client"]

    # Mock Pokemon data for training research
    mock_pokemon = MagicMock()
    mock_pokemon.base_experience = 112
    mock_pokemon.stats = {"hp": 35, "attack": 55}
    mock_poke_client.get_pokemon_by_name.return_value = mock_pokemon
    mock_poke_client.get_evolution_chain.return_value = ["pichu", "pikachu", "raichu"]

    context = ResearchContext(original_query="Easy to train")
    await agent._research_training_info(context)

    assert "training_research" in context.collected_data
    assert len(context.research_steps) == 1


@pytest.mark.asyncio
async def test_research_unique_pokemon(mock_llm_agent):
    """Test unique Pokemon research."""
    agent = mock_llm_agent["agent"]
    mock_poke_client = mock_llm_agent["mock_poke_client"]

    # Mock search results
    mock_pokemon = MagicMock()
    mock_pokemon.model_dump.return_value = {"name": "lapras", "types": ["water", "ice"]}
    mock_poke_client.search_pokemon.return_value = [mock_pokemon]

    context = ResearchContext(original_query="unique sea pokemon")
    await agent._research_unique_pokemon(context)

    assert "unique_pokemon" in context.collected_data
    assert len(context.research_steps) == 1


@pytest.mark.asyncio
async def test_analyze_findings(mock_llm_agent):
    """Test analysis of research findings."""
    agent = mock_llm_agent["agent"]
    mock_client = mock_llm_agent["mock_client"]

    mock_choice = MagicMock()
    mock_choice.message.content = '{"key_findings": ["finding1"], "recommendations": ["rec1"], "considerations": ["cons1"], "limitations": ["lim1"], "confidence_score": 0.85}'
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response

    context = ResearchContext(original_query="Test query")
    context.collected_data = {"test": "data"}

    await agent._analyse_findings(context)

    assert "analysis" in context.collected_data
    assert len(context.research_steps) == 1


@pytest.mark.asyncio
async def test_generate_report(mock_llm_agent):
    """Test report generation."""
    agent = mock_llm_agent["agent"]
    mock_client = mock_llm_agent["mock_client"]

    mock_choice = MagicMock()
    mock_choice.message.content = (
        "This is a comprehensive research report about the query."
    )
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response

    context = ResearchContext(original_query="Test query")
    context.collected_data = {"analysis": {"confidence_score": 0.8}}

    report = await agent._generate_report(context)

    assert isinstance(report, ResearchReport)
    assert report.query == "Test query"
    assert report.confidence_score == 0.8


def test_get_type_advantages(mock_llm_agent):
    """Test type advantages dictionary."""
    agent = mock_llm_agent["agent"]
    advantages = agent._get_type_advantages()

    assert "fire" in advantages
    assert "water" in advantages
    assert "grass" in advantages
    assert isinstance(advantages["fire"], list)
    assert "grass" in advantages["fire"]  # Fire is super effective against grass


def test_get_team_strategies(mock_llm_agent):
    """Test team strategies list."""
    agent = mock_llm_agent["agent"]
    strategies = agent._get_team_strategies()

    assert isinstance(strategies, list)
    assert len(strategies) > 0
    assert any("balanced" in strategy.lower() for strategy in strategies)
    assert any("weather" in strategy.lower() for strategy in strategies)


@pytest.mark.asyncio
async def test_error_handling(mock_llm_agent):
    """Test error handling in research process."""
    agent = mock_llm_agent["agent"]
    mock_client = mock_llm_agent["mock_client"]
    mock_client.chat.completions.create.side_effect = Exception("API Error")

    context = ResearchContext(original_query="Test query")
    await agent._clarify_goals(context)

    assert len(context.research_steps) == 1
    assert context.research_steps[0].success is False
    error_message = context.research_steps[0].error_message
    assert error_message is not None
    assert "API Error" in error_message
