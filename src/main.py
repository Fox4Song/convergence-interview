"""
Main entry point for the Pokedex Agent.
"""

import asyncio
import typer
from typing import Optional
import logging
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
import sys

from .llm_agent import LLMAgent
from .visualiser import ResearchVisualiser
from .config import settings

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

app = typer.Typer()
console = Console()


def check_api_key():
    """Check if OpenAI API key is configured."""
    if not settings.openai_api_key:
        console.print("[red]❌ Error: OpenAI API key not found![/red]")
        console.print("\n[yellow]Please set your OpenAI API key:[/yellow]")
        sys.exit(1)


@app.command()
def research(
    query: str = typer.Argument(..., help="Your Pokemon research question"),
    compare: bool = typer.Option(
        False, "--compare", "-c", help="Compare with ChatGPT response"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
):
    """Conduct deep research on a Pokemon query."""
    check_api_key()

    console.print(
        Panel.fit(
            "[bold blue]🔍 Pokedex Research Agent[/bold blue]\n"
            "Conducting deep research for Pokemon questions...",
            border_style="blue",
        )
    )

    asyncio.run(_conduct_research(query, compare, verbose))


@app.command()
def interactive():
    """Start interactive mode for multiple queries."""
    check_api_key()

    console.print(
        Panel.fit(
            "[bold green]🎮 Interactive Pokedex Mode[/bold green]\n"
            "Ask multiple questions and explore Pokemon data!",
            border_style="green",
        )
    )

    while True:
        try:
            query = Prompt.ask(
                "\n[bold cyan]What would you like to know about Pokemon?[/bold cyan]"
            )

            if query.lower() in ["quit", "exit", "q"]:
                console.print("[yellow]Goodbye![/yellow]")
                break

            if query.strip():
                console.print(f"\n[bold]Researching:[/bold] {query}")
                asyncio.run(_conduct_research(query, compare=False, verbose=False))

        except KeyboardInterrupt:
            console.print("\n[yellow]Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


@app.command()
def demo():
    """Run demo queries to showcase the agent's capabilities."""
    check_api_key()

    demo_queries = [
        "Build a team of all bug type Pokemon.",
        "What is an easy Pokemon to train in Pokemon Red?",
        "I have a team of 5 Pikachus. What Pokemon should I add next to my party?",
        "I want to find a unique Pokemon that lives by the sea.",
    ]

    console.print(
        Panel.fit(
            "[bold magenta]🎯 Pokedex Agent Demo[/bold magenta]\n"
            "Running through example queries to showcase capabilities...",
            border_style="magenta",
        )
    )

    for i, query in enumerate(demo_queries, 1):
        console.print(f"\n[bold]Demo {i}/4:[/bold] {query}")
        console.print("-" * 60)

        try:
            asyncio.run(_conduct_research(query, compare=True, verbose=False))
        except Exception as e:
            console.print(f"[red]Error in demo {i}: {e}[/red]")

        if i < len(demo_queries):
            console.print("\n[dim]Press Enter to continue to next demo...[/dim]")
            input()


async def _conduct_research(query: str, compare: bool = False, verbose: bool = False):
    """Conduct research and display results."""
    visualiser = ResearchVisualiser()

    try:
        # Initialise agent
        agent = LLMAgent()

        # Display progress
        visualiser.display_progress("Initialising research agent...")

        # Conduct research
        visualiser.display_progress(
            "Conducting research...", "Gathering data from multiple sources"
        )
        report = await agent.conduct_research(query)

        # Display results
        visualiser.display_research_report(report)

        # Compare with ChatGPT if requested
        if compare:
            visualiser.display_progress(
                "Generating comparison...", "Comparing with ChatGPT response"
            )
            chatgpt_response = await _get_chatgpt_response(query)
            visualiser.display_comparison(report, chatgpt_response)

        # Show detailed findings if verbose
        if verbose:
            _display_verbose_findings(report)

    except Exception as e:
        logger.error(f"Error during research: {e}")
        visualiser.display_error(f"Research failed: {e}")


async def _get_chatgpt_response(query: str) -> str:
    """Get a ChatGPT response for comparison."""
    try:
        import openai

        client = openai.OpenAI(api_key=settings.openai_api_key)

        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful Pokemon expert. Provide a concise but informative answer.",
                },
                {"role": "user", "content": query},
            ],
            max_tokens=500,
            temperature=0.7,
        )

        content = response.choices[0].message.content
        return content if content else "No response generated"

    except Exception as e:
        logger.error(f"Error getting ChatGPT response: {e}")
        return f"Error getting ChatGPT response: {e}"


def _display_verbose_findings(report):
    """Display detailed findings in verbose mode."""
    console.print("\n[bold green]📊 Detailed Findings (Verbose Mode)[/bold green]")

    for key, value in report.detailed_findings.items():
        if key.startswith("pokemon_"):
            pokemon_name = key.replace("pokemon_", "")
            console.print(f"\n[bold]🐾 {pokemon_name.title()}:[/bold]")
            console.print(f"  Types: {', '.join(value.get('types', []))}")
            console.print(f"  Stats: {value.get('stats', {})}")
            if value.get("description"):
                console.print(f"  Description: {value['description'][:200]}...")

        elif key == "analysis":
            console.print(f"\n[bold]🧠 Analysis:[/bold]")
            for finding in value.get("key_findings", []):
                console.print(f"  • {finding}")


@app.callback()
def main():
    """
    🎮 Pokedex Research Agent

    A sophisticated agent that conducts deep research for Pokemon questions.
    Uses multiple data sources including PokeAPI and web research to provide
    comprehensive, well-sourced answers.
    """
    pass


if __name__ == "__main__":
    app()
