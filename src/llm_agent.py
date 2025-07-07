"""
LLM Agent for orchestrating Pokemon research.
"""

import openai
import json
import logging
from typing import List, Dict, Optional, Any
from .config import settings
from .models import (
    ResearchContext,
    ResearchStep,
    ResearchStepType,
    ResearchReport,
    PokemonData,
)
from .pokeapi_client import PokeAPIClient
from .web_researcher import WebResearcher

logger = logging.getLogger(__name__)


class LLMAgent:
    """Main LLM agent for conducting Pokemon research."""

    def __init__(self):
        openai.api_key = settings.openai_api_key
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.pokeapi_client = PokeAPIClient()
        self.web_researcher = WebResearcher()

    async def conduct_research(self, query: str) -> ResearchReport:
        """Conduct comprehensive research on a Pokemon query."""
        context = ResearchContext(original_query=query)

        # Step 1: Clarify goals
        await self._clarify_goals(context)

        # Step 2: Conduct research
        await self._conduct_research_steps(context)

        # Step 3: Analyse findings
        await self._analyse_findings(context)

        # Step 4: Generate report
        return await self._generate_report(context)

    async def _clarify_goals(self, context: ResearchContext):
        """Clarify research goals with the user."""
        system_prompt = """You are a Pokemon research assistant. When given a user query, you must:

        1. Think step by step about what they're really asking.
        2. Identify exactly which Pokemon or types need investigation.
        3. Note any special constraints (game version, difficulty, environment, etc.).
        4. Decide the main focus areas for research.

        OUTPUT REQUIREMENTS:
        • **Strictly** return **only** a JSON object—no prose, no bullet lists, no commentary.
        • The JSON must match this exact schema:

        {
            "goals": [string, …],
            "pokemon_to_research": [string, …],
            "research_focus": string,
            "constraints": [string, …]
        }

        Example:
        {
            "goals": ["identify high-speed bug-types", "recommend a balanced bug-type team"],
            "pokemon_to_research": ["scizor", "heracross"],
            "research_focus": "focus on bug Pokémon with strong attack and speed stats",
            "constraints": ["Generation: IV", "Battle format: single"]
        }"""

        try:
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context.original_query},
                ],
                max_tokens=500,
                temperature=0.3,
            )

            content = response.choices[0].message.content
            if content is None:
                raise RuntimeError("LLM returned no clarification goal content")
            clarification_data = json.loads(content.strip())
            context.clarified_goals = clarification_data.get("goals", [])
            context.collected_data["pokemon_to_research"] = clarification_data.get(
                "pokemon_to_research", []
            )
            context.collected_data["research_focus"] = clarification_data.get(
                "research_focus", ""
            )
            context.collected_data["constraints"] = clarification_data.get(
                "constraints", []
            )

            step = ResearchStep(
                step_type=ResearchStepType.CLARIFICATION,
                description="Clarified research goals and identified key areas to investigate",
                output_data=clarification_data,
            )
            context.research_steps.append(step)

        except Exception as e:
            logger.error(f"Error in goal clarification: {e}")
            step = ResearchStep(
                step_type=ResearchStepType.CLARIFICATION,
                description="Failed to clarify goals",
                success=False,
                error_message=str(e),
            )
            context.research_steps.append(step)

    async def _conduct_research_steps(self, context: ResearchContext):
        """Conduct the main research steps."""
        pokemon_list = context.collected_data.get("pokemon_to_research", [])

        for pokemon_name in pokemon_list:
            # Research from PokeAPI
            await self._research_pokemon_api(pokemon_name, context)

            # Research from web sources
            await self._research_pokemon_web(pokemon_name, context)

        # Research based on query type
        # TODO: In the future, add more research modes based on LLM response
        if (
            "team" in context.original_query.lower()
            or "party" in context.original_query.lower()
        ):
            await self._research_team_composition(context)
        elif (
            "train" in context.original_query.lower()
            or "easy" in context.original_query.lower()
            or "evolution" in context.original_query.lower()
        ):
            await self._research_training_info(context)
        elif (
            "unique" in context.original_query.lower()
            or "sea" in context.original_query.lower()
        ):
            await self._research_unique_pokemon(context)

    async def _research_pokemon_api(self, pokemon_name: str, context: ResearchContext):
        """Research Pokemon using PokeAPI."""
        try:
            async with self.pokeapi_client as client:
                pokemon_data = await client.get_pokemon_by_name(pokemon_name)
                if pokemon_data:
                    # Get additional information
                    description = await client.get_pokemon_description(pokemon_name)
                    evolution_chain = await client.get_evolution_chain(pokemon_name)

                    if description:
                        pokemon_data.description = description
                    if evolution_chain:
                        pokemon_data.evolution_chain = evolution_chain

                    context.collected_data[f"pokemon_{pokemon_name}"] = (
                        pokemon_data.model_dump()
                    )

                    step = ResearchStep(
                        step_type=ResearchStepType.POKEAPI_QUERY,
                        description=f"Retrieved comprehensive data for {pokemon_name} from PokeAPI",
                        output_data={"pokemon_data": pokemon_data.model_dump()},
                        sources=[f"https://pokeapi.co/api/v2/pokemon/{pokemon_name}"],
                    )
                    context.research_steps.append(step)

        except Exception as e:
            logger.error(f"Error researching {pokemon_name} via API: {e}")
            step = ResearchStep(
                step_type=ResearchStepType.POKEAPI_QUERY,
                description=f"Failed to retrieve data for {pokemon_name}",
                success=False,
                error_message=str(e),
            )
            context.research_steps.append(step)

    async def _research_pokemon_web(self, pokemon_name: str, context: ResearchContext):
        """Research Pokemon using web sources."""
        try:
            web_results = self.web_researcher.search_pokemon_info(pokemon_name)
            training_tips = self.web_researcher.search_training_tips(pokemon_name)
            competitive_info = self.web_researcher.search_competitive_info(pokemon_name)
            location_info = self.web_researcher.search_location_info(pokemon_name)

            web_data = {
                "web_results": web_results,
                "training_tips": training_tips,
                "competitive_info": competitive_info,
                "location_info": location_info,
            }

            context.collected_data[f"web_data_{pokemon_name}"] = web_data

            step = ResearchStep(
                step_type=ResearchStepType.WEB_SEARCH,
                description=f"Gathered additional information about {pokemon_name} from web sources",
                output_data=web_data,
                sources=[result["url"] for result in web_results],
            )
            context.research_steps.append(step)

        except Exception as e:
            logger.error(f"Error researching {pokemon_name} via web: {e}")
            step = ResearchStep(
                step_type=ResearchStepType.WEB_SEARCH,
                description=f"Failed to gather web data for {pokemon_name}",
                success=False,
                error_message=str(e),
            )
            context.research_steps.append(step)

    async def _research_team_composition(self, context: ResearchContext):
        """Research team composition strategies."""
        try:
            # Get all Pokemon types for team building
            async with self.pokeapi_client as client:
                all_types = await client.get_all_types()

            team_research = {
                "available_types": all_types,
                "type_advantages": self._get_type_advantages(),
                "team_strategies": self._get_team_strategies(),
            }

            context.collected_data["team_research"] = team_research

            step = ResearchStep(
                step_type=ResearchStepType.ANALYSIS,
                description="Researched team composition strategies and type advantages",
                output_data=team_research,
            )
            context.research_steps.append(step)

        except Exception as e:
            logger.error(f"Error researching team composition: {e}")

    async def _research_training_info(self, context: ResearchContext):
        """Research training and evolution information."""
        try:
            # Focus on easy-to-train Pokemon
            async with self.pokeapi_client as client:
                # Get some common early-game Pokemon
                early_pokemon = [
                    "pikachu",
                    "charmander",
                    "bulbasaur",
                    "squirtle",
                    "pidgey",
                    "rattata",
                ]
                training_data = {}

                for pokemon_name in early_pokemon:
                    pokemon_data = await client.get_pokemon_by_name(pokemon_name)
                    if pokemon_data:
                        training_data[pokemon_name] = {
                            "base_exp": pokemon_data.base_experience,
                            "evolution_chain": await client.get_evolution_chain(
                                pokemon_name
                            ),
                            "stats": pokemon_data.stats,
                        }

            context.collected_data["training_research"] = training_data

            step = ResearchStep(
                step_type=ResearchStepType.ANALYSIS,
                description="Researched training information for early-game Pokemon",
                output_data=training_data,
            )
            context.research_steps.append(step)

        except Exception as e:
            logger.error(f"Error researching training info: {e}")

    async def _research_unique_pokemon(self, context: ResearchContext):
        """Research unique or special Pokemon."""
        try:
            # Search for unique Pokemon based on criteria
            unique_criteria = [
                "legendary",
                "mythical",
                "regional",
                "fossil",
                "water",
                "ocean",
            ]
            unique_pokemon = {}

            async with self.pokeapi_client as client:
                for criteria in unique_criteria:
                    if criteria in context.original_query.lower():
                        # Search for Pokemon matching criteria
                        search_results = await client.search_pokemon(criteria)
                        unique_pokemon[criteria] = [
                            p.model_dump() for p in search_results[:10]
                        ]

            context.collected_data["unique_pokemon"] = unique_pokemon

            step = ResearchStep(
                step_type=ResearchStepType.ANALYSIS,
                description="Researched unique Pokemon matching the query criteria",
                output_data=unique_pokemon,
            )
            context.research_steps.append(step)

        except Exception as e:
            logger.error(f"Error researching unique Pokemon: {e}")

    async def _analyse_findings(self, context: ResearchContext):
        """Analyse all collected findings."""
        system_prompt = """You are a Pokémon research analyst. Given raw query context and collected data, you must:

        1. Think step by step about what the data shows.
        2. Identify the **key findings**—the most salient patterns or numbers.
        3. Derive **actionable recommendations** based on the user's goals.
        4. Note any **important considerations** or caveats.
        5. List the **limitations** of this research.
        6. Assign a **confidence_score** (0.0-1.0) to your analysis.

        OUTPUT REQUIREMENTS:
        • **Return strictly** a single JSON object.  
        • **No** prose, bullet lists, or commentary outside the JSON.  
        • JSON must match this exact schema:

        {
            "key_findings": [string, …],   
            "recommendations": [string, …],
            "considerations": [string, …],
            "limitations": [string, …],
            "confidence_score": number         // between 0.0 and 1.0
        }

        Example:
        {
            "key_findings": ["Pikachu has the highest base_experience"],
            "recommendations": ["Add Jolteon for electric coverage"],
            "considerations": ["Data only from Generation III"],
            "limitations": ["No location info for Ultra Beasts"],
            "confidence_score": 0.85
        }"""

        user_prompt = f"""USER QUERY:
        {context.original_query}

        RESEARCH GOALS:
        {'; '.join(context.clarified_goals)}

        COLLECTED DATA:
        ```json
        {json.dumps(context.collected_data, indent=2)}
        ```"""

        try:
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=1000,
                temperature=0.3,
            )

            content = response.choices[0].message.content
            if content is None:
                raise RuntimeError("LLM returned no analysis content")
            analysis_data = json.loads(content.strip())
            context.collected_data["analysis"] = analysis_data

            step = ResearchStep(
                step_type=ResearchStepType.ANALYSIS,
                description="Analysed all research findings and generated insights",
                output_data=analysis_data,
            )
            context.research_steps.append(step)

        except Exception as e:
            logger.error(f"Error in analysis: {e}")

    async def _generate_report(self, context: ResearchContext) -> ResearchReport:
        """Generate the final research report."""
        system_prompt = """You are a professional Pokemon research report writer. Generate comprehensive, well-structured research reports based on collected data and analysis.

        Your reports should be:
        - Informative and detailed
        - Well-structured with clear sections
        - Helpful and actionable for the user
        - Professional in tone and presentation"""

        user_prompt = f"""Generate a comprehensive research report based on the following data:

        Query: {context.original_query}
        Analysis: {json.dumps(context.collected_data.get("analysis", {}), indent=2)}
        Research Steps: {len(context.research_steps)} steps completed

        Create a detailed report with:
        1. Executive summary
        2. Detailed findings
        3. Specific recommendations
        4. Sources used

        Make it informative, well-structured, and helpful for the user."""

        try:
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=settings.max_tokens_per_response,
                temperature=0.4,
            )

            report_content = response.choices[0].message.content
            if report_content is None:
                raise RuntimeError("LLM returned no report content")
            report_content = report_content.strip()

            # Extract sources from research steps
            all_sources = []
            for step in context.research_steps:
                all_sources.extend(step.sources)
            all_sources = list(set(all_sources))  # Remove duplicates

            analysis_data = context.collected_data.get("analysis", {})

            return ResearchReport(
                query=context.original_query,
                executive_summary=(
                    report_content[:500] + "..."
                    if len(report_content) > 500
                    else report_content
                ),
                detailed_findings=context.collected_data,
                recommendations=analysis_data.get("recommendations", []),
                sources=all_sources,
                research_steps=context.research_steps,
                confidence_score=analysis_data.get("confidence_score", 0.7),
                limitations=analysis_data.get("limitations", []),
            )

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return ResearchReport(
                query=context.original_query,
                executive_summary="Error generating report",
                detailed_findings=context.collected_data,
                recommendations=[],
                sources=[],
                research_steps=context.research_steps,
                confidence_score=0.0,
                limitations=["Failed to generate complete report"],
            )

    def _get_type_advantages(self) -> Dict[str, List[str]]:
        """Get type advantages for team building."""
        return {
            "fire": ["grass", "ice", "bug", "steel"],
            "water": ["fire", "ground", "rock"],
            "grass": ["water", "ground", "rock"],
            "electric": ["water", "flying"],
            "ice": ["grass", "ground", "flying", "dragon"],
            "fighting": ["normal", "ice", "rock", "steel", "dark"],
            "poison": ["grass", "fairy"],
            "ground": ["fire", "electric", "poison", "rock", "steel"],
            "flying": ["grass", "fighting", "bug"],
            "psychic": ["fighting", "poison"],
            "bug": ["grass", "psychic", "dark"],
            "rock": ["fire", "ice", "flying", "bug"],
            "ghost": ["psychic", "ghost"],
            "dragon": ["dragon"],
            "dark": ["psychic", "ghost"],
            "steel": ["ice", "rock", "fairy"],
            "fairy": ["fighting", "dragon", "dark"],
        }

    def _get_team_strategies(self) -> List[str]:
        """Get common team building strategies."""
        return [
            "Balanced team with different types",
            "Weather-based team (rain, sun, sand, hail)",
            "Trick room team for slower Pokemon",
            "Hyper offense with fast sweepers",
            "Stall team with defensive Pokemon",
            "Volt-turn team with momentum moves",
        ]
