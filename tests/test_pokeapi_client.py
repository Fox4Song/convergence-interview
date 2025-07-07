"""
Tests for the PokeAPI client.
"""

import pytest
from unittest.mock import AsyncMock, patch
from src.pokeapi_client import PokeAPIClient


@pytest.fixture
def mock_pokemon_data():
    """Mock Pokemon data for testing."""
    return {
        "id": 25,
        "name": "pikachu",
        "types": [{"type": {"name": "electric"}}],
        "height": 40,
        "weight": 60,
        "base_experience": 112,
        "abilities": [{"ability": {"name": "static"}}],
        "stats": [
            {"stat": {"name": "hp"}, "base_stat": 35},
            {"stat": {"name": "attack"}, "base_stat": 55},
            {"stat": {"name": "defense"}, "base_stat": 40},
            {"stat": {"name": "special-attack"}, "base_stat": 50},
            {"stat": {"name": "special-defense"}, "base_stat": 50},
            {"stat": {"name": "speed"}, "base_stat": 90},
        ],
        "moves": [{"move": {"name": "thunder-shock"}}],
        "sprites": {
            "front_default": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png",
            "back_default": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/25.png",
            "front_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/25.png",
            "back_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/shiny/25.png",
        },
    }


@pytest.mark.asyncio
async def test_get_pokemon_by_name_success(mock_pokemon_data):
    """Test successful Pokemon retrieval by name."""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_pokemon_data)
        mock_get.return_value.__aenter__.return_value = mock_response

        async with PokeAPIClient() as client:
            pokemon = await client.get_pokemon_by_name("pikachu")

        assert pokemon is not None
        assert pokemon.name == "pikachu"
        assert pokemon.types == ["electric"]
        assert pokemon.height == 4.0  # Converted from decimeters
        assert pokemon.weight == 6.0  # Converted from hectograms
        assert pokemon.base_experience == 112
        assert pokemon.abilities == ["static"]
        assert pokemon.stats["hp"] == 35
        assert pokemon.stats["speed"] == 90


@pytest.mark.asyncio
async def test_get_pokemon_by_name_not_found():
    """Test Pokemon retrieval when not found."""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_get.return_value.__aenter__.return_value = mock_response

        async with PokeAPIClient() as client:
            pokemon = await client.get_pokemon_by_name("nonexistent")

        assert pokemon is None


@pytest.mark.asyncio
async def test_get_pokemon_by_type():
    """Test getting Pokemon by type."""
    mock_type_data = {
        "pokemon": [{"pokemon": {"name": "pikachu"}}, {"pokemon": {"name": "raichu"}}]
    }

    with patch("aiohttp.ClientSession.get") as mock_get:
        # Mock type endpoint response
        mock_type_response = AsyncMock()
        mock_type_response.status = 200
        mock_type_response.json = AsyncMock(return_value=mock_type_data)

        # Mock individual Pokemon responses
        mock_pokemon_response = AsyncMock()
        mock_pokemon_response.status = 200
        mock_pokemon_response.json = AsyncMock(
            return_value={
                "name": "pikachu",
                "id": 25,
                "types": [{"type": {"name": "electric"}}],
                "height": 40,
                "weight": 60,
                "base_experience": 112,
                "abilities": [{"ability": {"name": "static"}}],
                "stats": [
                    {"stat": {"name": "hp"}, "base_stat": 35},
                    {"stat": {"name": "attack"}, "base_stat": 55},
                ],
                "moves": [{"move": {"name": "thunder-shock"}}],
                "sprites": {
                    "front_default": "https://example.com/front.png",
                    "back_default": "https://example.com/back.png",
                    "front_shiny": "https://example.com/front-shiny.png",
                    "back_shiny": "https://example.com/back-shiny.png",
                },
            }
        )

        mock_get.return_value.__aenter__.side_effect = [
            mock_type_response,
            mock_pokemon_response,
        ]

        async with PokeAPIClient() as client:
            pokemon_list = await client.get_pokemon_by_type("electric")

        assert len(pokemon_list) > 0


@pytest.mark.asyncio
async def test_get_all_types():
    """Test getting all available types."""
    mock_types_data = {
        "results": [
            {"name": "normal"},
            {"name": "fire"},
            {"name": "water"},
            {"name": "electric"},
        ]
    }

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_types_data)
        mock_get.return_value.__aenter__.return_value = mock_response

        async with PokeAPIClient() as client:
            types = await client.get_all_types()

        assert "normal" in types
        assert "fire" in types
        assert "water" in types
        assert "electric" in types


@pytest.mark.asyncio
async def test_get_pokemon_description():
    """Test getting Pokemon description."""
    mock_species_data = {
        "flavor_text_entries": [
            {
                "language": {"name": "en"},
                "flavor_text": "When several of these POKeMON gather, their electricity can cause lightning storms.",
            }
        ]
    }

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_species_data)
        mock_get.return_value.__aenter__.return_value = mock_response

        async with PokeAPIClient() as client:
            description = await client.get_pokemon_description("pikachu")

        assert description is not None
        assert "electricity" in description.lower()


@pytest.mark.asyncio
async def test_get_evolution_chain():
    """Test getting evolution chain."""
    mock_species_data = {
        "evolution_chain": {"url": "https://pokeapi.co/api/v2/evolution-chain/10/"}
    }

    mock_chain_data = {
        "chain": {
            "species": {"name": "pichu"},
            "evolves_to": [
                {
                    "species": {"name": "pikachu"},
                    "evolves_to": [{"species": {"name": "raichu"}}],
                }
            ],
        }
    }

    with patch("aiohttp.ClientSession.get") as mock_get:
        # Mock species endpoint response
        mock_species_response = AsyncMock()
        mock_species_response.status = 200
        mock_species_response.json = AsyncMock(return_value=mock_species_data)

        # Mock evolution chain endpoint response
        mock_chain_response = AsyncMock()
        mock_chain_response.status = 200
        mock_chain_response.json = AsyncMock(return_value=mock_chain_data)

        mock_get.return_value.__aenter__.side_effect = [
            mock_species_response,
            mock_chain_response,
        ]

        async with PokeAPIClient() as client:
            evolution_chain = await client.get_evolution_chain("pikachu")

        assert "pichu" in evolution_chain
        assert "pikachu" in evolution_chain
        assert "raichu" in evolution_chain


def test_get_pokemon_sync():
    """Test synchronous wrapper function."""
    with patch("src.pokeapi_client.asyncio.run") as mock_run:
        mock_run.return_value = None
        # Import the function directly since it's not a method of the class
        from src.pokeapi_client import get_pokemon_sync

        result = get_pokemon_sync("pikachu")
        mock_run.assert_called_once()
