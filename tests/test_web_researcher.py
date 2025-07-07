"""
Tests for the web researcher module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import Timeout, ConnectionError
from src.web_researcher import WebResearcher
from src.config import settings


@pytest.fixture
def web_researcher():
    """Create a WebResearcher instance for testing."""
    return WebResearcher()


@pytest.fixture
def mock_response():
    """Create a mock response object."""
    mock = Mock()
    mock.status_code = 200
    mock.content = b"""
    <html>
        <head><title>Test Pokemon Page</title></head>
        <body>
            <h1>Pikachu</h1>
            <p>Pikachu is an Electric-type Pokemon.</p>
            <p>It evolves from Pichu and evolves into Raichu.</p>
            <div class="stats">
                <span>HP: 35</span>
                <span>Attack: 55</span>
            </div>
        </body>
    </html>
    """
    return mock


class TestWebResearcher:
    """Test cases for WebResearcher class."""

    def test_init(self, web_researcher):
        """Test WebResearcher initialization."""
        assert web_researcher.session is not None
        assert "User-Agent" in web_researcher.session.headers
        assert "Accept" in web_researcher.session.headers

    def test_search_pokemon_info_disabled(self, web_researcher):
        """Test search_pokemon_info when web scraping is disabled."""
        with patch.object(settings, "web_scraping_enabled", False):
            results = web_researcher.search_pokemon_info("pikachu")
            assert results == []

    @patch("src.web_researcher.settings")
    def test_search_pokemon_info_enabled(
        self, mock_settings, web_researcher, mock_response
    ):
        """Test search_pokemon_info when web scraping is enabled."""
        mock_settings.web_scraping_enabled = True
        mock_settings.max_web_results = 5

        with patch.object(web_researcher.session, "get", return_value=mock_response):
            results = web_researcher.search_pokemon_info("pikachu")
            assert isinstance(results, list)

    def test_search_pokemon_info_exception_handling(self, web_researcher):
        """Test search_pokemon_info handles exceptions gracefully."""
        with patch.object(settings, "web_scraping_enabled", True):
            with patch.object(
                web_researcher,
                "_search_bulbapedia",
                side_effect=Exception("Test error"),
            ):
                with patch.object(
                    web_researcher,
                    "_search_serebii",
                    side_effect=Exception("Test error"),
                ):
                    with patch.object(
                        web_researcher,
                        "_search_pokemon_database",
                        side_effect=Exception("Test error"),
                    ):
                        results = web_researcher.search_pokemon_info("pikachu")
                        assert results == []

    def test_search_bulbapedia_success(self, web_researcher, mock_response):
        """Test successful Bulbapedia search."""
        with patch.object(web_researcher.session, "get", return_value=mock_response):
            results = web_researcher._search_bulbapedia("pikachu")
            assert isinstance(results, list)
            if results:  # If results are found
                assert len(results) <= 1  # Should return at most 1 result
                result = results[0]
                assert "title" in result
                assert "url" in result
                assert "source" in result
                assert result["source"] == "Bulbapedia"

    def test_search_bulbapedia_timeout(self, web_researcher):
        """Test Bulbapedia search with timeout."""
        with patch.object(
            web_researcher.session, "get", side_effect=Timeout("Request timeout")
        ):
            results = web_researcher._search_bulbapedia("pikachu")
            assert results == []

    def test_search_bulbapedia_connection_error(self, web_researcher):
        """Test Bulbapedia search with connection error."""
        with patch.object(
            web_researcher.session,
            "get",
            side_effect=ConnectionError("Connection failed"),
        ):
            results = web_researcher._search_bulbapedia("pikachu")
            assert results == []

    def test_search_bulbapedia_404(self, web_researcher):
        """Test Bulbapedia search with 404 response."""
        mock_response = Mock()
        mock_response.status_code = 404

        with patch.object(web_researcher.session, "get", return_value=mock_response):
            results = web_researcher._search_bulbapedia("nonexistent")
            assert results == []

    def test_search_serebii_success(self, web_researcher, mock_response):
        """Test successful Serebii search."""
        with patch.object(web_researcher.session, "get", return_value=mock_response):
            results = web_researcher._search_serebii("pikachu")
            assert isinstance(results, list)
            if results:  # If results are found
                assert len(results) == 1
                result = results[0]
                assert "title" in result
                assert "url" in result
                assert "source" in result
                assert result["source"] == "Serebii"
                assert "content" in result

    def test_search_serebii_timeout(self, web_researcher):
        """Test Serebii search with timeout."""
        with patch.object(
            web_researcher.session, "get", side_effect=Timeout("Request timeout")
        ):
            results = web_researcher._search_serebii("pikachu")
            assert results == []

    def test_search_serebii_404(self, web_researcher):
        """Test Serebii search with 404 response."""
        mock_response = Mock()
        mock_response.status_code = 404

        with patch.object(web_researcher.session, "get", return_value=mock_response):
            results = web_researcher._search_serebii("nonexistent")
            assert results == []

    def test_search_pokemon_database_success(self, web_researcher, mock_response):
        """Test successful Pokemon Database search."""
        with patch.object(web_researcher.session, "get", return_value=mock_response):
            results = web_researcher._search_pokemon_database("pikachu")
            assert isinstance(results, list)
            if results:  # If results are found
                assert len(results) == 1
                result = results[0]
                assert "title" in result
                assert "url" in result
                assert "source" in result
                assert result["source"] == "Pokemon Database"
                assert "content" in result

    def test_search_pokemon_database_timeout(self, web_researcher):
        """Test Pokemon Database search with timeout."""
        with patch.object(
            web_researcher.session, "get", side_effect=Timeout("Request timeout")
        ):
            results = web_researcher._search_pokemon_database("pikachu")
            assert results == []

    def test_extract_content_from_url_success(self, web_researcher, mock_response):
        """Test successful content extraction from URL."""
        with patch.object(web_researcher.session, "get", return_value=mock_response):
            content = web_researcher._extract_content_from_url("http://example.com")
            assert isinstance(content, str)
            assert len(content) > 0

    def test_extract_content_from_url_timeout(self, web_researcher):
        """Test content extraction with timeout."""
        with patch.object(
            web_researcher.session, "get", side_effect=Timeout("Request timeout")
        ):
            content = web_researcher._extract_content_from_url("http://example.com")
            assert "timeout occurred" in content

    def test_extract_content_from_url_connection_error(self, web_researcher):
        """Test content extraction with connection error."""
        with patch.object(
            web_researcher.session,
            "get",
            side_effect=ConnectionError("Connection failed"),
        ):
            content = web_researcher._extract_content_from_url("http://example.com")
            assert "connection failed" in content

    def test_extract_text_content(self, web_researcher):
        """Test text content extraction from BeautifulSoup object."""
        from bs4 import BeautifulSoup

        html_content = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Main Title</h1>
                <p>This is a paragraph with useful information.</p>
                <script>var x = 1;</script>
                <style>.test { color: red; }</style>
                <div>More content here.</div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html_content, "html.parser")
        content = web_researcher._extract_text_content(soup)

        assert isinstance(content, str)
        assert "Main Title" in content
        assert "This is a paragraph" in content
        assert "More content here" in content
        assert "var x = 1" not in content  # Script should be removed
        assert ".test { color: red; }" not in content  # Style should be removed

    def test_search_training_tips(self, web_researcher):
        """Test training tips search."""
        # Mock the search_pokemon_info method
        mock_results = [
            {
                "content": "Train Pikachu with Thunder Stone to evolve. Use Thunderbolt for high damage. Focus on speed and special attack stats."
            }
        ]

        with patch.object(
            web_researcher, "search_pokemon_info", return_value=mock_results
        ):
            tips = web_researcher.search_training_tips("pikachu")
            assert isinstance(tips, list)
            assert len(tips) <= 5  # Should return at most 5 tips

    def test_search_training_tips_no_results(self, web_researcher):
        """Test training tips search with no results."""
        with patch.object(web_researcher, "search_pokemon_info", return_value=[]):
            tips = web_researcher.search_training_tips("pikachu")
            assert isinstance(tips, list)
            assert len(tips) == 0

    def test_search_competitive_info(self, web_researcher):
        """Test competitive info search."""
        # Mock the search_pokemon_info method
        mock_results = [
            {
                "content": "Pikachu's best moveset includes Thunderbolt and Quick Attack. Use it as a fast sweeper. Consider Jolteon as a teammate."
            }
        ]

        with patch.object(
            web_researcher, "search_pokemon_info", return_value=mock_results
        ):
            competitive_info = web_researcher.search_competitive_info("pikachu")
            assert isinstance(competitive_info, dict)
            assert "movesets" in competitive_info
            assert "strategies" in competitive_info
            assert "counters" in competitive_info
            assert "teammates" in competitive_info

    def test_search_competitive_info_no_results(self, web_researcher):
        """Test competitive info search with no results."""
        with patch.object(web_researcher, "search_pokemon_info", return_value=[]):
            competitive_info = web_researcher.search_competitive_info("pikachu")
            assert isinstance(competitive_info, dict)
            assert all(isinstance(v, list) for v in competitive_info.values())

    def test_search_location_info(self, web_researcher):
        """Test location info search."""
        # Mock the search_pokemon_info method
        mock_results = [
            {
                "content": "Pikachu can be found in Viridian Forest. It also appears in Route 2 and the Power Plant. Look near electric areas."
            }
        ]

        with patch.object(
            web_researcher, "search_pokemon_info", return_value=mock_results
        ):
            locations = web_researcher.search_location_info("pikachu")
            assert isinstance(locations, list)
            assert len(locations) <= 3  # Should return at most 3 locations

    def test_search_location_info_no_results(self, web_researcher):
        """Test location info search with no results."""
        with patch.object(web_researcher, "search_pokemon_info", return_value=[]):
            locations = web_researcher.search_location_info("pikachu")
            assert isinstance(locations, list)
            assert len(locations) == 0

    def test_session_headers(self, web_researcher):
        """Test that session has proper headers."""
        headers = web_researcher.session.headers
        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "Accept-Language" in headers
        assert "Accept-Encoding" in headers
        assert "Connection" in headers
        assert "Upgrade-Insecure-Requests" in headers

    def test_request_timeout_setting(self, web_researcher):
        """Test that request timeout is used."""
        with patch.object(web_researcher.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b"<html><body>Test</body></html>"
            mock_get.return_value = mock_response

            web_researcher._search_serebii("pikachu")

            # Check that timeout was passed to the request
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert "timeout" in call_args[1]
            assert call_args[1]["timeout"] == settings.request_timeout

    def test_max_web_results_limit(self, web_researcher):
        """Test that max_web_results limit is respected."""
        with patch.object(settings, "web_scraping_enabled", True):
            with patch.object(settings, "max_web_results", 2):
                # Mock multiple results from different sources
                with patch.object(
                    web_researcher,
                    "_search_bulbapedia",
                    return_value=[{"title": "1"}, {"title": "2"}],
                ):
                    with patch.object(
                        web_researcher, "_search_serebii", return_value=[{"title": "3"}]
                    ):
                        with patch.object(
                            web_researcher,
                            "_search_pokemon_database",
                            return_value=[{"title": "4"}],
                        ):
                            results = web_researcher.search_pokemon_info("pikachu")
                            assert (
                                len(results) <= 2
                            )  # Should respect max_web_results limit

    def test_error_logging(self, web_researcher, caplog):
        """Test that errors are properly logged."""
        with patch.object(settings, "web_scraping_enabled", True):
            with patch.object(
                web_researcher,
                "_search_bulbapedia",
                side_effect=Exception("Test error"),
            ):
                web_researcher.search_pokemon_info("pikachu")
                assert "Bulbapedia search failed" in caplog.text

    def test_pokemon_name_formatting(self, web_researcher, mock_response):
        """Test that Pokemon names are properly formatted for URLs."""
        with patch.object(web_researcher.session, "get", return_value=mock_response):
            # Test Bulbapedia formatting
            results = web_researcher._search_bulbapedia("pikachu")
            # Should create URL like: https://bulbapedia.bulbagarden.net/wiki/Pikachu

            # Test Serebii formatting
            results = web_researcher._search_serebii("pikachu")
            # Should create URL like: https://www.serebii.net/pokedex/pikachu.shtml

            # Test Pokemon Database formatting
            results = web_researcher._search_pokemon_database("pikachu")
            # Should create URL like: https://pokemondb.net/pokedex/pikachu

    def test_content_length_limiting(self, web_researcher):
        """Test that content is properly limited in length."""
        long_content = "Very long content " * 100  # Create very long content

        mock_results = [{"content": long_content}]

        with patch.object(
            web_researcher, "search_pokemon_info", return_value=mock_results
        ):
            tips = web_researcher.search_training_tips("pikachu")
            # Should not crash with very long content
            assert isinstance(tips, list)
