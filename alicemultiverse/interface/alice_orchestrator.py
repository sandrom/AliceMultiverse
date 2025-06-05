"""Alice Orchestrator - The intelligent orchestration layer for creative chaos.

This is the evolution of AliceInterface, designed to be the sole endpoint
for AI assistants. It understands creative chaos and translates natural
language into technical operations while maintaining context across sessions.
"""

from dataclasses import dataclass, field
from datetime import UTC,  datetime, timedelta
from enum import Enum
from typing import Any

from ..assets.discovery import AssetDiscovery
from ..core.structured_logging import get_logger, trace_operation, CorrelationContext
from ..events import publish_event

logger = get_logger(__name__)


class CreativeIntent(Enum):
    """Types of creative intents Alice can understand."""

    SEARCH = "search"
    CREATE = "create"
    ORGANIZE = "organize"
    REMEMBER = "remember"
    EXPLORE = "explore"
    REFINE = "refine"
    COMBINE = "combine"
    EVOLVE = "evolve"


@dataclass
class CreativeMemory:
    """Represents Alice's memory of creative work."""

    recent_searches: list[str] = field(default_factory=list)
    recent_creations: list[str] = field(default_factory=list)
    active_styles: dict[str, Any] = field(default_factory=dict)
    project_context: dict[str, Any] = field(default_factory=dict)
    creative_patterns: dict[str, int] = field(default_factory=dict)  # Pattern -> frequency
    last_interaction: datetime | None = None


@dataclass
class CreativeResponse:
    """Alice's response to creative requests."""

    success: bool
    message: str
    assets: list[dict[str, Any]] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)
    memory_updated: bool = False
    events_published: list[str] = field(default_factory=list)


class AliceOrchestrator:
    """Alice - The intelligent orchestrator for creative workflows.

    Alice understands:
    - Natural language descriptions of creative intent
    - Temporal references ("that thing from last month")
    - Creative patterns and preferences
    - Context that spans months of work
    - The chaos of creative exploration

    Alice handles:
    - All technical complexity
    - Provider selection and failover
    - Resource optimization
    - Context preservation
    - Event orchestration
    """

    def __init__(self, project_id: str | None = None) -> None:
        """Initialize Alice with optional project context.

        Args:
            project_id: Optional project to load context for
        """
        self.project_id = project_id
        self.memory = CreativeMemory()
        self.session = None
        self._init_session()
        self._load_context()

    def _init_session(self) -> None:
        """Initialize database session."""
        logger.info("Running in file-based mode")
        self.session = None
        self.asset_repo = None
        self.project_repo = None
        self.discovery = AssetDiscovery(search_paths=[])

    def _load_context(self) -> None:
        """Load project context if available."""
        if self.project_id and self.project_repo:
            try:
                project = self.project_repo.get_project(self.project_id)
                if project:
                    self.memory.project_context = project.creative_context or {}
                    self.memory.active_styles = project.style_preferences or {}
                    logger.info(f"Loaded context for project: {project.name}")
            except Exception as e:
                logger.error(f"Failed to load project context: {e}")

    def _update_memory(self, intent: CreativeIntent, data: dict[str, Any]) -> None:
        """Update Alice's memory based on interactions."""
        self.memory.last_interaction = datetime.now(UTC)

        # Track patterns
        pattern_key = f"{intent.value}:{data.get('style', 'default')}"
        self.memory.creative_patterns[pattern_key] = (
            self.memory.creative_patterns.get(pattern_key, 0) + 1
        )

        # Update recent activities
        if intent == CreativeIntent.SEARCH:
            query = data.get("query", "")
            if query and query not in self.memory.recent_searches:
                self.memory.recent_searches.append(query)
                if len(self.memory.recent_searches) > 20:
                    self.memory.recent_searches.pop(0)

        elif intent == CreativeIntent.CREATE:
            creation = data.get("prompt", "")
            if creation:
                self.memory.recent_creations.append(creation)
                if len(self.memory.recent_creations) > 10:
                    self.memory.recent_creations.pop(0)

    def _parse_temporal_reference(self, text: str) -> datetime | None:
        """Parse natural language time references.

        Understands:
        - "yesterday", "last week", "last month"
        - "in January", "in March"
        - "3 days ago", "2 weeks ago"
        - "that cyberpunk thing from October"
        """
        text_lower = text.lower()
        now = datetime.now(UTC)

        # Relative times
        if "yesterday" in text_lower:
            return now - timedelta(days=1)
        elif "today" in text_lower:
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif "last week" in text_lower:
            return now - timedelta(weeks=1)
        elif "last month" in text_lower:
            return now - timedelta(days=30)
        elif "last year" in text_lower:
            return now - timedelta(days=365)

        # "X ago" patterns
        import re

        ago_pattern = r"(\d+)\s+(day|week|month|hour)s?\s+ago"
        match = re.search(ago_pattern, text_lower)
        if match:
            amount = int(match.group(1))
            unit = match.group(2)
            if unit == "day":
                return now - timedelta(days=amount)
            elif unit == "week":
                return now - timedelta(weeks=amount)
            elif unit == "month":
                return now - timedelta(days=amount * 30)
            elif unit == "hour":
                return now - timedelta(hours=amount)

        # Month names
        months = {
            "january": 1,
            "february": 2,
            "march": 3,
            "april": 4,
            "may": 5,
            "june": 6,
            "july": 7,
            "august": 8,
            "september": 9,
            "october": 10,
            "november": 11,
            "december": 12,
        }

        for month_name, month_num in months.items():
            if month_name in text_lower:
                # Assume current year, or last year if month is in future
                year = now.year
                if month_num > now.month:
                    year -= 1
                return datetime(year, month_num, 1)

        return None

    def _extract_creative_elements(self, text: str) -> dict[str, Any]:
        """Extract creative elements from natural language.

        Identifies:
        - Styles: "cyberpunk", "neon", "dreamy"
        - Moods: "dark", "energetic", "calm"
        - Subjects: "character", "landscape", "abstract"
        - Colors: "blue", "vibrant", "monochrome"
        - References: "like the one we did", "similar to"
        """
        elements = {"styles": [], "moods": [], "subjects": [], "colors": [], "references": []}

        text_lower = text.lower()

        # Style keywords
        style_keywords = [
            "cyberpunk",
            "steampunk",
            "fantasy",
            "scifi",
            "realistic",
            "anime",
            "cartoon",
            "abstract",
            "surreal",
            "minimalist",
            "retro",
            "vintage",
            "modern",
            "futuristic",
            "gothic",
        ]
        elements["styles"] = [s for s in style_keywords if s in text_lower]

        # Mood keywords
        mood_keywords = [
            "dark",
            "bright",
            "moody",
            "cheerful",
            "energetic",
            "calm",
            "peaceful",
            "dramatic",
            "mysterious",
            "playful",
            "serious",
            "whimsical",
            "melancholic",
            "uplifting",
        ]
        elements["moods"] = [m for m in mood_keywords if m in text_lower]

        # Color keywords
        color_keywords = [
            "red",
            "blue",
            "green",
            "yellow",
            "purple",
            "orange",
            "pink",
            "black",
            "white",
            "gray",
            "neon",
            "pastel",
            "vibrant",
            "muted",
            "monochrome",
            "colorful",
        ]
        elements["colors"] = [c for c in color_keywords if c in text_lower]

        # Reference patterns
        if any(phrase in text_lower for phrase in ["like the", "similar to", "same as"]):
            elements["references"].append("has_reference")

        return elements

    # === Primary Creative Interface ===

    @trace_operation("understand_request")
    async def understand(self, request: str) -> CreativeResponse:
        """Understand and execute any creative request.

        This is the primary endpoint that interprets natural language
        and orchestrates all necessary operations.

        Args:
            request: Natural language request from AI assistant

        Returns:
            Creative response with results and context
        """
        try:
            # Determine intent
            intent = self._determine_intent(request)

            # Extract temporal and creative elements
            temporal_ref = self._parse_temporal_reference(request)
            creative_elements = self._extract_creative_elements(request)

            # Route to appropriate handler
            if intent == CreativeIntent.SEARCH:
                return await self._handle_search(request, temporal_ref, creative_elements)
            elif intent == CreativeIntent.CREATE:
                return await self._handle_creation(request, creative_elements)
            elif intent == CreativeIntent.ORGANIZE:
                return await self._handle_organization(request)
            elif intent == CreativeIntent.REMEMBER:
                return await self._handle_memory_request(request)
            elif intent == CreativeIntent.EXPLORE:
                return await self._handle_exploration(request, creative_elements)
            else:
                return await self._handle_general_request(request)

        except Exception as e:
            logger.error(f"Failed to understand request: {e}")
            return CreativeResponse(
                success=False,
                message=f"I encountered an error: {e!s}",
                suggestions=["Try rephrasing your request", "Be more specific about what you want"],
            )

    def _determine_intent(self, request: str) -> CreativeIntent:
        """Determine the creative intent from natural language."""
        request_lower = request.lower()

        # Memory patterns - check first for questions about past actions
        memory_keywords = ["remember", "recall", "what did", "what have", "history", "past"]
        # Check for questions about past searches/creations
        if any(keyword in request_lower for keyword in memory_keywords):
            return CreativeIntent.REMEMBER
        # Also check for specific patterns like "what have I searched"
        if ("what" in request_lower and "have" in request_lower and 
            any(word in request_lower for word in ["searched", "created", "made", "looked"])):
            return CreativeIntent.REMEMBER

        # Search patterns
        search_keywords = ["find", "search", "look for", "where is", "show me", "get"]
        if any(keyword in request_lower for keyword in search_keywords):
            return CreativeIntent.SEARCH

        # Creation patterns
        create_keywords = ["create", "generate", "make", "produce", "design"]
        if any(keyword in request_lower for keyword in create_keywords):
            return CreativeIntent.CREATE

        # Organization patterns
        organize_keywords = ["organize", "sort", "arrange", "clean up", "structure"]
        if any(keyword in request_lower for keyword in organize_keywords):
            return CreativeIntent.ORGANIZE

        # Exploration patterns
        explore_keywords = ["explore", "variations", "similar", "related"]
        if any(keyword in request_lower for keyword in explore_keywords):
            return CreativeIntent.EXPLORE

        # Default to search for questions
        if "?" in request_lower:
            return CreativeIntent.SEARCH

        return CreativeIntent.SEARCH  # Default

    @trace_operation("handle_search")
    async def _handle_search(
        self, request: str, temporal_ref: datetime | None, creative_elements: dict[str, Any]
    ) -> CreativeResponse:
        """Handle search requests with natural language understanding."""
        try:
            # Build search parameters
            search_params = {}

            if temporal_ref:
                search_params["created_after"] = temporal_ref

            if creative_elements["styles"]:
                search_params["style_tags"] = creative_elements["styles"]

            if creative_elements["moods"]:
                search_params["mood_tags"] = creative_elements["moods"]

            if creative_elements["colors"]:
                search_params["color_tags"] = creative_elements["colors"]

            # Use semantic search if we have a good description
            if len(request) > 20 and not any(
                k in search_params for k in ["style_tags", "mood_tags"]
            ):
                # Semantic search through description
                results = await self._semantic_search(request)
            else:
                # Structured search
                results = await self._structured_search(search_params)

            # Update memory
            self._update_memory(CreativeIntent.SEARCH, {"query": request})

            # Generate suggestions based on results
            suggestions = self._generate_search_suggestions(results, creative_elements)

            return CreativeResponse(
                success=True,
                message=f"Found {len(results)} assets matching your request",
                assets=results,
                suggestions=suggestions,
                memory_updated=True,
            )

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return CreativeResponse(
                success=False,
                message="I couldn't complete the search",
                suggestions=["Try being more specific", "Use style or mood keywords"],
            )

    @trace_operation("handle_creation")
    async def _handle_creation(
        self, request: str, creative_elements: dict[str, Any]
    ) -> CreativeResponse:
        """Handle content creation requests."""
        try:
            # Extract prompt and parameters
            prompt = self._extract_prompt(request)

            # Apply active styles from memory
            if self.memory.active_styles:
                prompt = self._enhance_prompt_with_style(prompt, self.memory.active_styles)

            # Publish workflow started event
            workflow_id = f"create_{datetime.now(UTC).timestamp()}"
            await publish_event(
                "workflow.started",
                {
                    "workflow_id": workflow_id,
                    "workflow_type": "image_generation",
                    "workflow_name": "AI-requested creation",
                    "initiated_by": "ai_assistant",
                    "input_parameters": {
                        "prompt": prompt,
                        "styles": creative_elements["styles"],
                        "original_request": request,
                    },
                }
            )

            # Update memory
            self._update_memory(
                CreativeIntent.CREATE,
                {
                    "prompt": prompt,
                    "style": (
                        creative_elements["styles"][0] if creative_elements["styles"] else "default"
                    ),
                },
            )

            return CreativeResponse(
                success=True,
                message="Creation workflow initiated",
                context={"workflow_id": workflow_id, "prompt": prompt},
                suggestions=["Check back in a moment for results", "I'll notify you when complete"],
                memory_updated=True,
                events_published=["workflow.started"],
            )

        except Exception as e:
            logger.error(f"Creation failed: {e}")
            return CreativeResponse(
                success=False,
                message="I couldn't start the creation process",
                suggestions=[
                    "Check if the generation service is available",
                    "Try a simpler prompt",
                ],
            )

    async def _handle_memory_request(self, request: str) -> CreativeResponse:
        """Handle requests about past work and context."""
        try:
            request_lower = request.lower()

            # Recent searches
            if "search" in request_lower or "looked for" in request_lower:
                return CreativeResponse(
                    success=True,
                    message="Here are your recent searches",
                    context={"recent_searches": self.memory.recent_searches[-10:]},
                    suggestions=["Would you like to repeat any of these searches?"],
                )

            # Recent creations
            elif "created" in request_lower or "made" in request_lower:
                return CreativeResponse(
                    success=True,
                    message="Here are your recent creations",
                    context={"recent_creations": self.memory.recent_creations[-10:]},
                    suggestions=["Would you like to create variations of any of these?"],
                )

            # Active styles
            elif "style" in request_lower:
                return CreativeResponse(
                    success=True,
                    message="Here are your active style preferences",
                    context={"active_styles": self.memory.active_styles},
                    suggestions=["Would you like to update any of these styles?"],
                )

            # Creative patterns
            else:
                top_patterns = sorted(
                    self.memory.creative_patterns.items(), key=lambda x: x[1], reverse=True
                )[:5]

                return CreativeResponse(
                    success=True,
                    message="Here are your most common creative patterns",
                    context={"patterns": dict(top_patterns)},
                    suggestions=["I can help you explore new variations of these patterns"],
                )

        except Exception as e:
            logger.error(f"Memory request failed: {e}")
            return CreativeResponse(success=False, message="I couldn't access the memory right now")

    @trace_operation("semantic_search")
    async def _semantic_search(self, description: str) -> list[dict[str, Any]]:
        """Perform semantic search based on description."""
        # This would integrate with embedding-based search
        # For now, search by extracting keywords as tags
        if self.asset_repo:
            # Extract potential tags from description
            keywords = [word.lower() for word in description.split() if len(word) > 3]
            assets = self.asset_repo.search(tags=keywords, limit=20, tag_mode="any")
            return [self._asset_to_dict(asset) for asset in assets]
        return []

    @trace_operation("structured_search")
    async def _structured_search(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Perform structured search with specific parameters."""
        if self.asset_repo:
            assets = self.asset_repo.search(**params)
            return [self._asset_to_dict(asset) for asset in assets]
        return []

    def _asset_to_dict(self, asset) -> dict[str, Any]:
        """Convert database asset to dictionary."""
        return {
            "id": asset.content_hash,
            "path": asset.file_path,
            "type": asset.media_type,
            "source": asset.source_type,
            "created": asset.generated_at or asset.first_seen,
            "prompt": asset.generation_params.get("prompt") if asset.generation_params else None,
            "tags": [],  # Would extract from relationships
            "quality": asset.rating,
        }

    def _generate_search_suggestions(
        self, results: list[dict[str, Any]], elements: dict[str, Any]
    ) -> list[str]:
        """Generate helpful suggestions based on search results."""
        suggestions = []

        if not results:
            suggestions.append("Try broadening your search terms")
            suggestions.append("Remove some filters to see more results")
        elif len(results) > 10:
            suggestions.append("Try adding more specific keywords to narrow results")
            if not elements["styles"]:
                suggestions.append("Add a style like 'cyberpunk' or 'fantasy'")

        return suggestions

    def _extract_prompt(self, request: str) -> str:
        """Extract the actual prompt from a creation request."""
        # Remove creation keywords (case insensitive)
        create_words = ["create", "generate", "make", "produce", "design"]
        prompt = request
        for word in create_words:
            # Replace all case variations
            prompt = prompt.replace(word, "")
            prompt = prompt.replace(word.capitalize(), "")
            prompt = prompt.replace(word.upper(), "")
        return prompt.strip()

    def _enhance_prompt_with_style(self, prompt: str, styles: dict[str, Any]) -> str:
        """Enhance prompt with active style preferences."""
        # This would intelligently merge style preferences
        # For now, just append key style elements
        style_additions = []
        for key, value in styles.items():
            if isinstance(value, str):
                style_additions.append(value)

        if style_additions:
            return f"{prompt}, {', '.join(style_additions)}"
        return prompt

    async def _handle_organization(self, request: str) -> CreativeResponse:
        """Handle organization requests."""
        # Trigger organization workflow
        return CreativeResponse(
            success=True,
            message="Organization feature coming soon",
            suggestions=["This will organize your assets intelligently"],
        )

    async def _handle_exploration(
        self, request: str, creative_elements: dict[str, Any]
    ) -> CreativeResponse:
        """Handle exploration and variation requests."""
        # Find similar assets or create variations
        return CreativeResponse(
            success=True,
            message="Exploration feature coming soon",
            suggestions=["This will help you explore creative variations"],
        )

    async def _handle_general_request(self, request: str) -> CreativeResponse:
        """Handle general requests that don't fit other categories."""
        return CreativeResponse(
            success=True,
            message="I understand you want to do something creative",
            suggestions=[
                "Try asking me to 'find' something specific",
                "Or ask me to 'create' something new",
                "I can also 'remember' what we've worked on",
            ],
        )

    # === Context Management ===

    async def save_context(self) -> bool:
        """Save current context to database."""
        if self.project_id and self.project_repo:
            try:
                # Update project context
                await publish_event(
                    "context.updated",
                    {
                        "project_id": self.project_id,
                        "context_type": "creative",
                        "update_type": "modification",
                        "context_key": "memory",
                        "new_value": {
                            "recent_searches": self.memory.recent_searches,
                            "recent_creations": self.memory.recent_creations,
                            "active_styles": self.memory.active_styles,
                            "patterns": self.memory.creative_patterns,
                        },
                    }
                )
                return True
            except Exception as e:
                logger.error(f"Failed to save context: {e}")
        return False

    def __del__(self) -> None:
        """Cleanup on deletion."""
        if self.session:
            self.session.close()
