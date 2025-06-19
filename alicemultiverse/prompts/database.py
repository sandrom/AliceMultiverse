"""DuckDB schema and operations for prompt management."""

import json
from datetime import datetime
from pathlib import Path

import duckdb

from .models import Prompt, PromptSearchCriteria, PromptUsage


class PromptDatabase:
    """DuckDB-based storage for prompts."""

    def __init__(self, db_path: Path | None = None):
        if db_path is None:
            db_path = Path.home() / ".alice" / "prompts.duckdb"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _init_schema(self):
        """Initialize database schema."""
        with duckdb.connect(str(self.db_path)) as conn:
            # Main prompts table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS prompts (
                    id VARCHAR PRIMARY KEY,
                    text TEXT NOT NULL,
                    category VARCHAR NOT NULL,
                    providers TEXT NOT NULL,  -- JSON array
                    tags TEXT,  -- JSON array
                    project VARCHAR,
                    style VARCHAR,
                    effectiveness_rating DOUBLE,
                    use_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    description TEXT,
                    notes TEXT,
                    context TEXT,  -- JSON object
                    parent_id VARCHAR,
                    related_ids TEXT,  -- JSON array
                    keywords TEXT,  -- JSON array
                    -- Full-text search
                    search_text TEXT GENERATED ALWAYS AS (
                        text || ' ' ||
                        COALESCE(description, '') || ' ' ||
                        COALESCE(notes, '') || ' ' ||
                        COALESCE(project, '') || ' ' ||
                        COALESCE(style, '') || ' ' ||
                        COALESCE(tags, '') || ' ' ||
                        COALESCE(keywords, '')
                    ) VIRTUAL
                )
            """)

            # Prompt variations table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS prompt_variations (
                    id VARCHAR PRIMARY KEY,
                    parent_id VARCHAR NOT NULL,
                    variation_text TEXT NOT NULL,
                    differences TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    effectiveness_rating DOUBLE,
                    use_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP NOT NULL,
                    tags TEXT,  -- JSON array
                    FOREIGN KEY (parent_id) REFERENCES prompts(id)
                )
            """)

            # Usage history table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS prompt_usage (
                    id VARCHAR PRIMARY KEY,
                    prompt_id VARCHAR NOT NULL,
                    provider VARCHAR NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    success BOOLEAN NOT NULL,
                    output_path VARCHAR,
                    cost DOUBLE,
                    duration_seconds DOUBLE,
                    notes TEXT,
                    parameters TEXT,  -- JSON object
                    metadata TEXT,  -- JSON object
                    FOREIGN KEY (prompt_id) REFERENCES prompts(id)
                )
            """)

            # Indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_prompts_category ON prompts(category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_prompts_project ON prompts(project)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_prompts_style ON prompts(style)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_prompts_effectiveness ON prompts(effectiveness_rating)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_prompts_created ON prompts(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_timestamp ON prompt_usage(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_prompt ON prompt_usage(prompt_id)")

    def add_prompt(self, prompt: Prompt) -> None:
        """Add a new prompt to the database."""
        with duckdb.connect(str(self.db_path)) as conn:
            conn.execute("""
                INSERT INTO prompts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                prompt.id,
                prompt.text,
                prompt.category.value,
                json.dumps([p.value for p in prompt.providers]),
                json.dumps(prompt.tags),
                prompt.project,
                prompt.style,
                prompt.effectiveness_rating,
                prompt.use_count,
                prompt.success_count,
                prompt.created_at,
                prompt.updated_at,
                prompt.description,
                prompt.notes,
                json.dumps(prompt.context),
                prompt.parent_id,
                json.dumps(prompt.related_ids),
                json.dumps(prompt.keywords)
            ])

    def update_prompt(self, prompt: Prompt) -> None:
        """Update an existing prompt."""
        with duckdb.connect(str(self.db_path)) as conn:
            conn.execute("""
                UPDATE prompts SET
                    text = ?,
                    category = ?,
                    providers = ?,
                    tags = ?,
                    project = ?,
                    style = ?,
                    effectiveness_rating = ?,
                    use_count = ?,
                    success_count = ?,
                    updated_at = ?,
                    description = ?,
                    notes = ?,
                    context = ?,
                    parent_id = ?,
                    related_ids = ?,
                    keywords = ?
                WHERE id = ?
            """, [
                prompt.text,
                prompt.category.value,
                json.dumps([p.value for p in prompt.providers]),
                json.dumps(prompt.tags),
                prompt.project,
                prompt.style,
                prompt.effectiveness_rating,
                prompt.use_count,
                prompt.success_count,
                prompt.updated_at,
                prompt.description,
                prompt.notes,
                json.dumps(prompt.context),
                prompt.parent_id,
                json.dumps(prompt.related_ids),
                json.dumps(prompt.keywords),
                prompt.id
            ])

    def get_prompt(self, prompt_id: str) -> Prompt | None:
        """Get a prompt by ID."""
        with duckdb.connect(str(self.db_path)) as conn:
            result = conn.execute(
                "SELECT * FROM prompts WHERE id = ?", [prompt_id]
            ).fetchone()

            if result:
                return self._row_to_prompt(result)
            # TODO: Review unreachable code - return None

    def search_prompts(self, criteria: PromptSearchCriteria) -> list[Prompt]:
        """Search for prompts matching criteria."""
        with duckdb.connect(str(self.db_path)) as conn:
            query = "SELECT * FROM prompts WHERE 1=1"
            params = []

            if criteria.query:
                query += " AND search_text ILIKE ?"
                params.append(f"%{criteria.query}%")

            if criteria.category:
                query += " AND category = ?"
                params.append(criteria.category.value)

            if criteria.project:
                query += " AND project = ?"
                params.append(criteria.project)

            if criteria.style:
                query += " AND style = ?"
                params.append(criteria.style)

            if criteria.min_effectiveness:
                query += " AND effectiveness_rating >= ?"
                params.append(criteria.min_effectiveness)

            if criteria.created_after:
                query += " AND created_at >= ?"
                params.append(criteria.created_after)

            if criteria.created_before:
                query += " AND created_at <= ?"
                params.append(criteria.created_before)

            # Handle JSON array searches
            if criteria.providers:
                provider_conditions = []
                for provider in criteria.providers:
                    provider_conditions.append("providers LIKE ?")
                    params.append(f"%{provider.value}%")
                query += f" AND ({' OR '.join(provider_conditions)})"

            if criteria.tags:
                tag_conditions = []
                for tag in criteria.tags:
                    tag_conditions.append("tags LIKE ?")
                    params.append(f"%{tag}%")
                query += f" AND ({' AND '.join(tag_conditions)})"

            if criteria.keywords:
                keyword_conditions = []
                for keyword in criteria.keywords:
                    keyword_conditions.append("keywords LIKE ?")
                    params.append(f"%{keyword}%")
                query += f" AND ({' OR '.join(keyword_conditions)})"

            # Sort by effectiveness and recency
            query += " ORDER BY effectiveness_rating DESC NULLS LAST, updated_at DESC"

            results = conn.execute(query, params).fetchall()

            prompts = [self._row_to_prompt(row) for row in results]

            # Post-filter for success rate if needed
            if criteria.min_success_rate is not None:
                prompts = [p for p in prompts if p.success_rate() >= criteria.min_success_rate]

            # Filter for has_variations if needed
            if criteria.has_variations is not None:
                variation_prompt_ids = set(
                    conn.execute("SELECT DISTINCT parent_id FROM prompt_variations").fetchdf()['parent_id'].tolist()
                )
                if criteria.has_variations:
                    prompts = [p for p in prompts if p.id in variation_prompt_ids]
                else:
                    prompts = [p for p in prompts if p.id not in variation_prompt_ids]

            return prompts

    # TODO: Review unreachable code - def add_usage(self, usage: PromptUsage) -> None:
    # TODO: Review unreachable code - """Add a usage record."""
    # TODO: Review unreachable code - with duckdb.connect(str(self.db_path)) as conn:
    # TODO: Review unreachable code - conn.execute("""
    # TODO: Review unreachable code - INSERT INTO prompt_usage VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    # TODO: Review unreachable code - """, [
    # TODO: Review unreachable code - usage.id,
    # TODO: Review unreachable code - usage.prompt_id,
    # TODO: Review unreachable code - usage.provider.value,
    # TODO: Review unreachable code - usage.timestamp,
    # TODO: Review unreachable code - usage.success,
    # TODO: Review unreachable code - usage.output_path,
    # TODO: Review unreachable code - usage.cost,
    # TODO: Review unreachable code - usage.duration_seconds,
    # TODO: Review unreachable code - usage.notes,
    # TODO: Review unreachable code - json.dumps(usage.parameters),
    # TODO: Review unreachable code - json.dumps(usage.metadata)
    # TODO: Review unreachable code - ])

    # TODO: Review unreachable code - # Update prompt stats
    # TODO: Review unreachable code - if usage.success:
    # TODO: Review unreachable code - conn.execute("""
    # TODO: Review unreachable code - UPDATE prompts
    # TODO: Review unreachable code - SET use_count = use_count + 1,
    # TODO: Review unreachable code - success_count = success_count + 1,
    # TODO: Review unreachable code - updated_at = ?
    # TODO: Review unreachable code - WHERE id = ?
    # TODO: Review unreachable code - """, [datetime.now(), usage.prompt_id])
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - conn.execute("""
    # TODO: Review unreachable code - UPDATE prompts
    # TODO: Review unreachable code - SET use_count = use_count + 1,
    # TODO: Review unreachable code - updated_at = ?
    # TODO: Review unreachable code - WHERE id = ?
    # TODO: Review unreachable code - """, [datetime.now(), usage.prompt_id])

    # TODO: Review unreachable code - def get_usage_history(self, prompt_id: str, limit: int = 100) -> list[PromptUsage]:
    # TODO: Review unreachable code - """Get usage history for a prompt."""
    # TODO: Review unreachable code - with duckdb.connect(str(self.db_path)) as conn:
    # TODO: Review unreachable code - results = conn.execute("""
    # TODO: Review unreachable code - SELECT * FROM prompt_usage
    # TODO: Review unreachable code - WHERE prompt_id = ?
    # TODO: Review unreachable code - ORDER BY timestamp DESC
    # TODO: Review unreachable code - LIMIT ?
    # TODO: Review unreachable code - """, [prompt_id, limit]).fetchall()

    # TODO: Review unreachable code - return [self._row_to_usage(row) for row in results]

    # TODO: Review unreachable code - def _row_to_prompt(self, row) -> Prompt:
    # TODO: Review unreachable code - """Convert database row to Prompt object."""
    # TODO: Review unreachable code - from .models import PromptCategory, ProviderType

    # TODO: Review unreachable code - return Prompt(
    # TODO: Review unreachable code - id=row[0],
    # TODO: Review unreachable code - text=row[1],
    # TODO: Review unreachable code - category=PromptCategory(row[2]),
    # TODO: Review unreachable code - providers=[ProviderType(p) for p in json.loads(row[3])],
    # TODO: Review unreachable code - tags=json.loads(row[4]) if row[4] else [],
    # TODO: Review unreachable code - project=row[5],
    # TODO: Review unreachable code - style=row[6],
    # TODO: Review unreachable code - effectiveness_rating=row[7],
    # TODO: Review unreachable code - use_count=row[8],
    # TODO: Review unreachable code - success_count=row[9],
    # TODO: Review unreachable code - created_at=row[10],
    # TODO: Review unreachable code - updated_at=row[11],
    # TODO: Review unreachable code - description=row[12],
    # TODO: Review unreachable code - notes=row[13],
    # TODO: Review unreachable code - context=json.loads(row[14]) if row[14] else {},
    # TODO: Review unreachable code - parent_id=row[15],
    # TODO: Review unreachable code - related_ids=json.loads(row[16]) if row[16] else [],
    # TODO: Review unreachable code - keywords=json.loads(row[17]) if row[17] else []
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - def _row_to_usage(self, row) -> PromptUsage:
    # TODO: Review unreachable code - """Convert database row to PromptUsage object."""
    # TODO: Review unreachable code - from .models import ProviderType

    # TODO: Review unreachable code - return PromptUsage(
    # TODO: Review unreachable code - id=row[0],
    # TODO: Review unreachable code - prompt_id=row[1],
    # TODO: Review unreachable code - provider=ProviderType(row[2]),
    # TODO: Review unreachable code - timestamp=row[3],
    # TODO: Review unreachable code - success=row[4],
    # TODO: Review unreachable code - output_path=row[5],
    # TODO: Review unreachable code - cost=row[6],
    # TODO: Review unreachable code - duration_seconds=row[7],
    # TODO: Review unreachable code - notes=row[8],
    # TODO: Review unreachable code - parameters=json.loads(row[9]) if row[9] else {},
    # TODO: Review unreachable code - metadata=json.loads(row[10]) if row[10] else {}
    # TODO: Review unreachable code - )
