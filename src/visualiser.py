"""
Visualisation module for displaying research results.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.layout import Layout
from rich.text import Text
from rich.syntax import Syntax
from rich.tree import Tree
from typing import List, Dict, Any
import json
from .models import ResearchReport, ResearchStep, PokemonData

console = Console()


class ResearchVisualiser:
    """Visualises research results and process."""

    def __init__(self):
        self.console = console

    def display_research_report(self, report: ResearchReport):
        """Display the complete research report."""
        self.console.print("\n" + "=" * 80)
        self.console.print("[bold blue]🔍 POKeDEX RESEARCH REPORT[/bold blue]")
        self.console.print("=" * 80)

        # Executive Summary
        self._display_executive_summary(report)

        # Research Process
        self._display_research_process(report.research_steps)

        # Recommendations
        self._display_recommendations(report.recommendations)

        # Sources
        self._display_sources(report.sources)

        # Confidence and Limitations
        self._display_confidence_limitations(report)

    def _display_executive_summary(self, report: ResearchReport):
        """Display the executive summary."""
        panel = Panel(
            f"[bold]Query:[/bold] {report.query}\n\n"
            f"[bold]Executive Summary:[/bold]\n{report.executive_summary}",
            title="📋 Executive Summary",
            border_style="blue",
        )
        self.console.print(panel)
        self.console.print()

    def _display_research_process(self, steps: List[ResearchStep]):
        """Display the research process steps."""
        self.console.print("[bold green]🔬 Research Process[/bold green]")

        tree = Tree("📚 Research Steps")

        for i, step in enumerate(steps, 1):
            step_icon = "✅" if step.success else "❌"
            step_node = tree.add(
                f"{step_icon} Step {i}: {step.step_type.value.title()}"
            )
            step_node.add(f"📝 {step.description}")

            if step.sources:
                sources_node = step_node.add("🔗 Sources:")
                for source in step.sources:
                    sources_node.add(f"  • {source}")

            if step.error_message:
                step_node.add(f"⚠️  Error: {step.error_message}")

        self.console.print(tree)
        self.console.print()

    def _display_recommendations(self, recommendations: List[str]):
        """Display recommendations."""
        if recommendations:
            panel = Panel(
                "\n".join([f"• {rec}" for rec in recommendations]),
                title="💡 Recommendations",
                border_style="green",
            )
            self.console.print(panel)
            self.console.print()

    def _display_sources(self, sources: List[str]):
        """Display sources used."""
        if sources:
            panel = Panel(
                "\n".join([f"• {source}" for source in sources]),
                title="📚 Sources",
                border_style="blue",
            )
            self.console.print(panel)
            self.console.print()

    def _display_confidence_limitations(self, report: ResearchReport):
        """Display confidence score and limitations."""
        confidence_color = (
            "green"
            if report.confidence_score > 0.7
            else "yellow" if report.confidence_score > 0.4 else "red"
        )

        panel = Panel(
            f"[bold]Confidence Score:[/bold] [{confidence_color}]{report.confidence_score:.2f}[/{confidence_color}]\n\n"
            f"[bold]Limitations:[/bold]\n"
            + "\n".join([f"• {limitation}" for limitation in report.limitations]),
            title="📈 Confidence & Limitations",
            border_style="cyan",
        )
        self.console.print(panel)
        self.console.print()

    def display_comparison(self, our_report: ResearchReport, chatgpt_response: str):
        """Display comparison between our agent and ChatGPT."""
        self.console.print("\n" + "=" * 80)
        self.console.print(
            "[bold yellow]🆚 COMPARISON: Our Agent vs ChatGPT[/bold yellow]"
        )
        self.console.print("=" * 80)

        # Our Agent Results
        our_panel = Panel(
            f"[bold]Query:[/bold] {our_report.query}\n\n"
            f"[bold]Our Agent Response:[/bold]\n{our_report.executive_summary[:500]}...",
            title="🤖 Our Pokedex Agent",
            border_style="green",
        )
        self.console.print(our_panel)

        # ChatGPT Response
        chatgpt_panel = Panel(
            f"[bold]ChatGPT Response:[/bold]\n{chatgpt_response[:500]}...",
            title="💬 ChatGPT",
            border_style="blue",
        )
        self.console.print(chatgpt_panel)

        # Comparison Analysis
        comparison_panel = Panel(
            "[bold green]Our Agent Advantages:[/bold green]\n"
            "• Comprehensive research from multiple sources\n"
            "• Detailed Pokemon data from PokeAPI\n"
            "• Web research for additional context\n"
            "• Structured analysis and recommendations\n"
            "• Transparent research process\n\n"
            "[bold blue]ChatGPT Advantages:[/bold blue]\n"
            "• Faster response time\n"
            "• General knowledge about Pokemon\n"
            "• Conversational tone\n\n"
            "[bold yellow]Overall Assessment:[/bold yellow]\n"
            "Our agent provides more thorough, research-backed responses with "
            "detailed data and transparent methodology, while ChatGPT offers "
            "quicker but less comprehensive answers.",
            title="📊 Comparison Analysis",
            border_style="yellow",
        )
        self.console.print(comparison_panel)

    def display_progress(self, step: str, description: str = ""):
        """Display progress during research."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task(f"[cyan]{step}", total=None)
            progress.update(task, description=description)

    def display_error(self, error: str):
        """Display error messages."""
        panel = Panel(f"❌ {error}", title="Error", border_style="red")
        self.console.print(panel)
