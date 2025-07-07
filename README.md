# Pokedex Research Agent

A sophisticated AI agent that conducts deep research for Pokemon questions, providing comprehensive, well-sourced answers that go beyond simple ChatGPT responses.

## Features

- **Multi-Source Research**: Combines PokeAPI data with web research from Bulbapedia, Serebii, and Pokemon Database
- **Structured Analysis**: Breaks down research into clear steps with transparent methodology
- **Comprehensive Reports**: Provides detailed findings, recommendations, and confidence scores
- **Interactive CLI**: User-friendly command-line interface with rich visualisations
- **Comparison Mode**: Side-by-side comparison with ChatGPT to demonstrate superiority
- **Demo Mode**: Pre-built examples showcasing the agent's capabilities

## Quick Start

### Prerequisites

- Python 3.9+
- Docker (optional, for containerised development)
- OpenAI API key

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd convergence-interview
   ```

2. **Set up the environment:**
   ```bash
   # Using Docker (recommended)
   make build
   make start
   make deps
   
   # Or using pip directly
   pip install -r requirements.txt
   ```

### Usage

#### Basic Research
```bash
python -m src.main research "Build a team of all bug type Pokemon"
```

#### Interactive Mode
```bash
python -m src.main interactive
```

#### Demo Mode (Showcases all features)
```bash
python -m src.main demo
```

#### Compare with ChatGPT
```bash
python -m src.main research "What is an easy Pokemon to train in Pokemon Ruby?" --compare
```

#### Verbose Output
```bash
python -m src.main research "I want to find a unique Pokemon that lives by the sea" --verbose
```

## Example Queries

The agent can handle various types of Pokemon questions:

- **Team Building**: "Build a team of all bug type Pokemon"
- **Training Advice**: "What is an easy Pokemon to train in Pokemon Ruby?"
- **Discovery**: "I want to find a unique Pokemon that lives by the sea"
- **Strategy**: "What Pokemon should I add next to my party?"
- **Competitive**: "What's the best moveset for Charizard?"
- **Lore**: "Tell me about the legend of Mewtwo"

## Architecture

### Core Components

1. **LLM Agent** (`src/llm_agent.py`)
   - Orchestrates the research process
   - Manages OpenAI API interactions
   - Coordinates data collection and analysis

2. **PokeAPI Client** (`src/pokeapi_client.py`)
   - Fetches comprehensive Pokemon data
   - Handles evolution chains, descriptions, and stats
   - Manages async API requests efficiently

3. **Web Researcher** (`src/web_researcher.py`)
   - Scrapes additional information from Pokemon websites
   - Gathers training tips and competitive strategies
   - Provides location and lore information

4. **Visualiser** (`src/visualiser.py`)
   - Rich terminal-based output
   - Progress indicators and structured reports
   - Comparison visualisations

5. **Data Models** (`src/models.py`)
   - Structured data representation
   - Research context and reporting models
   - Type-safe data handling

### Research Process

1. **Goal Clarification**: Analyses the query to identify research objectives
2. **Data Collection**: Gathers information from PokeAPI and web sources
3. **Analysis**: Processes findings and generates insights
4. **Synthesis**: Creates comprehensive recommendations
5. **Reporting**: Delivers structured, well-sourced results

## Research Methodology

### Data Sources

- **PokeAPI**: Official Pokemon database with stats, types, abilities
- **Bulbapedia**: Comprehensive Pokemon encyclopedia
- **Serebii**: Game-specific information and strategies
- **Pokemon Database**: Detailed Pokemon profiles and data

### Analysis Framework

- **Multi-perspective**: Considers competitive, casual, and lore aspects
- **Evidence-based**: All claims are backed by data sources
- **Transparent**: Research steps are clearly documented
- **Confidence scoring**: Indicates reliability of findings

## Comparison with ChatGPT

Our agent provides several advantages over ChatGPT:

| Feature | Our Agent | ChatGPT |
|---------|-----------|---------|
| **Data Sources** | Multiple APIs + Web scraping | Training data only |
| **Research Process** | Transparent, step-by-step | Black box |
| **Sources** | Cited and verifiable | No citations |
| **Depth** | Comprehensive analysis | Surface-level answers |
| **Accuracy** | Real-time data | May be outdated |
| **Customisation** | Query-specific research | Generic responses |

## Testing

Run the test suite:

```bash
# Using Docker
make tests

# Or directly
pytest tests/
```

## Project Structure

```
convergence-interview/
├── src/                    # Source code
│   ├── __init__.py
│   ├── main.py            # CLI entry point
│   ├── config.py          # Configuration management
│   ├── models.py          # Data models
│   ├── llm_agent.py       # Main research agent
│   ├── pokeapi_client.py  # PokeAPI integration
│   ├── web_researcher.py  # Web scraping
│   └── visualiser.py      # Output formatting
├── tests/                 # Test files
├── requirements/          # Python dependencies
├── Dockerfile             # Docker image configuration
├── docker-compose.dev.yaml # Development Docker Compose
└── Makefile              # Common development commands
```

## Development

### Adding New Features

1. **New Data Sources**: Extend `WebResearcher` class
2. **Analysis Methods**: Add methods to `LLMAgent`
3. **Visualisations**: Enhance `ResearchVisualiser`
4. **Data Models**: Update `models.py`


## Sources

- [PokeAPI](https://pokeapi.co/) for comprehensive Pokemon data
- [Bulbapedia](https://bulbapedia.bulbagarden.net/) for detailed Pokemon information
- [Serebii](https://www.serebii.net/) for game-specific data
- [Pokemon Database](https://pokemondb.net/) for additional resources
