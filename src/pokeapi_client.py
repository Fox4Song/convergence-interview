"""
PokeAPI client for fetching Pokemon data.
"""

import aiohttp
import asyncio
from typing import List, Dict, Optional, Any
import logging
from .config import settings
from .models import PokemonData

logger = logging.getLogger(__name__)


class PokeAPIClient:
    """Client for interacting with the PokeAPI."""

    def __init__(self):
        self.base_url = settings.pokeapi_base_url
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _make_request(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Make a request to the PokeAPI."""
        if not self.session:
            self.session = aiohttp.ClientSession()

        url = f"{self.base_url}/{endpoint}"
        try:
            async with self.session.get(
                url, timeout=settings.request_timeout
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(
                        f"PokeAPI request failed: {response.status} for {url}"
                    )
                    return None
        except Exception as e:
            logger.error(f"Error making PokeAPI request to {url}: {e}")
            return None

    async def get_pokemon_by_name(self, name: str) -> Optional[PokemonData]:
        """Get Pokemon data by name."""
        data = await self._make_request(f"pokemon/{name.lower()}")
        if not data:
            return None

        return PokemonData(
            id=data["id"],
            name=data["name"],
            types=[t["type"]["name"] for t in data["types"]],
            height=data["height"] / 10.0,  # Convert to meters
            weight=data["weight"] / 10.0,  # Convert to kg
            base_experience=data["base_experience"],
            abilities=[a["ability"]["name"] for a in data["abilities"]],
            stats={s["stat"]["name"]: s["base_stat"] for s in data["stats"]},
            moves=[
                m["move"]["name"] for m in data["moves"][:20]
            ],  # Limit to first 20 moves
            sprites={
                "front_default": data["sprites"]["front_default"],
                "back_default": data["sprites"]["back_default"],
                "front_shiny": data["sprites"]["front_shiny"],
                "back_shiny": data["sprites"]["back_shiny"],
            },
        )

    async def get_pokemon_by_id(self, pokemon_id: int) -> Optional[PokemonData]:
        """Get Pokemon data by ID."""
        return await self.get_pokemon_by_name(str(pokemon_id))

    async def get_pokemon_by_type(self, pokemon_type: str) -> List[PokemonData]:
        """Get all Pokemon of a specific type."""
        data = await self._make_request(f"type/{pokemon_type.lower()}")
        if not data:
            return []

        pokemon_list = []
        for pokemon_info in data["pokemon"][:50]:  # Limit to first 50
            pokemon_name = pokemon_info["pokemon"]["name"]
            pokemon_data = await self.get_pokemon_by_name(pokemon_name)
            if pokemon_data:
                pokemon_list.append(pokemon_data)

        return pokemon_list

    async def search_pokemon(self, query: str) -> List[PokemonData]:
        """Search for Pokemon by name (partial match)."""
        # Get all Pokemon first (this is a limitation of the API)
        data = await self._make_request("pokemon?limit=1000")
        if not data:
            return []

        matching_pokemon = []
        query_lower = query.lower()

        for pokemon_info in data["results"]:
            if query_lower in pokemon_info["name"].lower():
                pokemon_data = await self.get_pokemon_by_name(pokemon_info["name"])
                if pokemon_data:
                    matching_pokemon.append(pokemon_data)

        return matching_pokemon

    async def get_evolution_chain(self, pokemon_name: str) -> List[str]:
        """Get evolution chain for a Pokemon."""
        # First get the species data
        species_data = await self._make_request(
            f"pokemon-species/{pokemon_name.lower()}"
        )
        if not species_data or not species_data.get("evolution_chain"):
            return []

        # Extract evolution chain ID
        evolution_chain_url = species_data["evolution_chain"]["url"]
        chain_id = evolution_chain_url.split("/")[-2]

        # Get evolution chain data
        chain_data = await self._make_request(f"evolution-chain/{chain_id}")
        if not chain_data:
            return []

        # Extract evolution chain
        evolutions = []
        chain = chain_data["chain"]

        def extract_evolutions(chain_link):
            evolutions.append(chain_link["species"]["name"])
            for evolution in chain_link.get("evolves_to", []):
                extract_evolutions(evolution)

        extract_evolutions(chain)
        return evolutions

    async def get_pokemon_description(self, pokemon_name: str) -> Optional[str]:
        """Get Pokemon description from species data."""
        species_data = await self._make_request(
            f"pokemon-species/{pokemon_name.lower()}"
        )
        if not species_data or not species_data.get("flavor_text_entries"):
            return None

        # Get English description
        for entry in species_data["flavor_text_entries"]:
            if entry["language"]["name"] == "en":
                return entry["flavor_text"].replace("\n", " ").replace("\f", " ")

        return None

    async def get_all_types(self) -> List[str]:
        """Get all available Pokemon types."""
        data = await self._make_request("type")
        if not data:
            return []

        return [t["name"] for t in data["results"]]

    async def get_generation_info(self, generation: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific generation."""
        return await self._make_request(f"generation/{generation.lower()}")


# Convenience function for synchronous usage
def get_pokemon_sync(name: str) -> Optional[PokemonData]:
    """Synchronous wrapper for getting Pokemon data."""

    async def _get_pokemon():
        async with PokeAPIClient() as client:
            return await client.get_pokemon_by_name(name)

    return asyncio.run(_get_pokemon())
