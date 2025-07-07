"""
Web research module for gathering additional Pokemon information.
"""

import requests
from requests.adapters import HTTPAdapter
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Any
import logging
import re
from urllib.parse import urljoin, urlparse
from .config import settings

logger = logging.getLogger(__name__)


class WebResearcher:
    """Web research functionality for gathering Pokemon information."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )
        # Reduce the number of retries and connection pooling
        adapter = HTTPAdapter(pool_connections=1, pool_maxsize=1, max_retries=1)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def search_pokemon_info(self, query: str) -> List[Dict[str, Any]]:
        """Search for Pokemon information on the web."""
        if not settings.web_scraping_enabled:
            # logger.info("Web scraping disabled, returning empty results")
            return []

        results = []

        try:
            # Search on Bulbapedia
            bulbapedia_results = self._search_bulbapedia(query)
            results.extend(bulbapedia_results)
        except Exception as e:
            logger.warning(f"Bulbapedia search failed: {e}")

        try:
            # Search on Serebii
            serebii_results = self._search_serebii(query)
            results.extend(serebii_results)
        except Exception as e:
            logger.warning(f"Serebii search failed: {e}")

        try:
            # Search on Pokemon Database
            pokedb_results = self._search_pokemon_database(query)
            results.extend(pokedb_results)
        except Exception as e:
            logger.warning(f"Pokemon Database search failed: {e}")

        return results[: settings.max_web_results]

    def _search_bulbapedia(self, query: str) -> List[Dict[str, Any]]:
        """Search Bulbapedia for Pokemon information."""
        try:
            # Try direct Pokemon page instead of search
            pokemon_name = query.lower().replace(" ", "_")
            direct_url = (
                f"https://bulbapedia.bulbagarden.net/wiki/{pokemon_name.title()}"
            )

            response = self.session.get(direct_url, timeout=settings.request_timeout)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                content = self._extract_text_content(soup)

                return [
                    {
                        "title": f"{query.title()} - Bulbapedia",
                        "url": direct_url,
                        "source": "Bulbapedia",
                        "content": content[:1000],  # Limit content length
                    }
                ]

            return []

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout searching Bulbapedia for {query}")
            return []
        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection error searching Bulbapedia for {query}")
            return []
        except Exception as e:
            logger.error(f"Error searching Bulbapedia: {e}")
            return []

    def _search_serebii(self, query: str) -> List[Dict[str, Any]]:
        """Search Serebii for Pokemon information."""
        try:
            # Serebii doesn't have a direct search, so we'll try common Pokemon pages
            pokemon_name = query.lower().replace(" ", "")
            serebii_url = f"https://www.serebii.net/pokedex/{pokemon_name}.shtml"

            response = self.session.get(serebii_url, timeout=settings.request_timeout)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                content = self._extract_text_content(soup)

                return [
                    {
                        "title": f"{query.title()} - Serebii",
                        "url": serebii_url,
                        "source": "Serebii",
                        "content": content[:1000],  # Limit content length
                    }
                ]

            return []

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout searching Serebii for {query}")
            return []
        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection error searching Serebii for {query}")
            return []
        except Exception as e:
            logger.error(f"Error searching Serebii: {e}")
            return []

    def _search_pokemon_database(self, query: str) -> List[Dict[str, Any]]:
        """Search Pokemon Database for information."""
        try:
            # Try to find Pokemon on Pokemon Database
            pokemon_name = query.lower().replace(" ", "-")
            pokedb_url = f"https://pokemondb.net/pokedex/{pokemon_name}"

            response = self.session.get(pokedb_url, timeout=settings.request_timeout)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                content = self._extract_text_content(soup)

                return [
                    {
                        "title": f"{query.title()} - Pokemon Database",
                        "url": pokedb_url,
                        "source": "Pokemon Database",
                        "content": content[:1000],  # Limit content length
                    }
                ]

            return []

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout searching Pokemon Database for {query}")
            return []
        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection error searching Pokemon Database for {query}")
            return []
        except Exception as e:
            logger.error(f"Error searching Pokemon Database: {e}")
            return []

    def _extract_content_from_url(self, url: str) -> str:
        """Extract content from a given URL."""
        try:
            response = self.session.get(url, timeout=settings.request_timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            return self._extract_text_content(soup)

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout extracting content from {url}")
            return f"Content from {url} (timeout occurred)"
        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection error extracting content from {url}")
            return f"Content from {url} (connection failed)"
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return ""

    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """Extract meaningful text content from BeautifulSoup object."""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text content
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = " ".join(chunk for chunk in chunks if chunk)

        return text

    def search_training_tips(self, pokemon_name: str) -> List[str]:
        """Search for training tips for a specific Pokemon."""
        query = f"{pokemon_name} training tips pokemon"
        results = self.search_pokemon_info(query)

        tips = []
        for result in results:
            content = result.get("content", "")
            # Extract sentences that might contain training tips
            sentences = re.split(r"[.!?]+", content)
            for sentence in sentences:
                sentence = sentence.strip()
                if any(
                    keyword in sentence.lower()
                    for keyword in [
                        "train",
                        "evolve",
                        "level",
                        "move",
                        "ability",
                        "stats",
                    ]
                ):
                    if len(sentence) > 20 and len(sentence) < 200:
                        tips.append(sentence)

        return tips[:5]  # Return top 5 tips

    def search_competitive_info(self, pokemon_name: str) -> Dict[str, Any]:
        """Search for competitive battling information."""
        query = f"{pokemon_name} competitive pokemon battle"
        results = self.search_pokemon_info(query)

        competitive_info = {
            "movesets": [],
            "strategies": [],
            "counters": [],
            "teammates": [],
        }

        for result in results:
            content = result.get("content", "").lower()

            # Extract moveset information
            if "moveset" in content or "moves" in content:
                sentences = re.split(r"[.!?]+", content)
                for sentence in sentences:
                    if any(
                        move in sentence
                        for move in [
                            "thunderbolt",
                            "flamethrower",
                            "earthquake",
                            "psychic",
                        ]
                    ):
                        competitive_info["movesets"].append(sentence.strip())

            # Extract strategy information
            if "strategy" in content or "tactic" in content:
                sentences = re.split(r"[.!?]+", content)
                for sentence in sentences:
                    if "strategy" in sentence or "tactic" in sentence:
                        competitive_info["strategies"].append(sentence.strip())

        return competitive_info

    def search_location_info(self, pokemon_name: str) -> List[str]:
        """Search for location information about a Pokemon."""
        query = f"{pokemon_name} location catch pokemon"
        results = self.search_pokemon_info(query)

        locations = []
        for result in results:
            content = result.get("content", "")
            # Look for location-related keywords
            location_keywords = [
                "route",
                "cave",
                "forest",
                "mountain",
                "ocean",
                "sea",
                "lake",
                "river",
            ]
            sentences = re.split(r"[.!?]+", content)

            for sentence in sentences:
                sentence = sentence.strip()
                if any(keyword in sentence.lower() for keyword in location_keywords):
                    if len(sentence) > 10 and len(sentence) < 150:
                        locations.append(sentence)

        return locations[:3]  # Return top 3 locations
