"""DuckDB schema and operations for prompt management."""

import duckdb
from pathlib import Path
from typing import List, Optional
import json
from datetime import datetime

from .models import Prompt, PromptUsage, PromptSearchCriteria


class PromptDatabase:
    """DuckDB-based storage for prompts."""
    
    def __init__(self, db_path: Optional[Path] = None):
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
    
    def get_prompt(self, prompt_id: str) -> Optional[Prompt]:
        """Get a prompt by ID."""
        with duckdb.connect(str(self.db_path)) as conn:
            result = conn.execute(
                "SELECT * FROM prompts WHERE id = ?", [prompt_id]
            ).fetchone()
            
            if result:
                return self._row_to_prompt(result)
            return None
    
    def search_prompts(self, criteria: PromptSearchCriteria) -> List[Prompt]:
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
    
    def add_usage(self, usage: PromptUsage) -> None:
        """Add a usage record."""
        with duckdb.connect(str(self.db_path)) as conn:
            conn.execute("""
                INSERT INTO prompt_usage VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                usage.id,
                usage.prompt_id,
                usage.provider.value,
                usage.timestamp,
                usage.success,
                usage.output_path,
                usage.cost,
                usage.duration_seconds,
                usage.notes,
                json.dumps(usage.parameters),
                json.dumps(usage.metadata)
            ])
            
            # Update prompt stats
            if usage.success:
                conn.execute("""
                    UPDATE prompts 
                    SET use_count = use_count + 1, 
                        success_count = success_count + 1,
                        updated_at = ?
                    WHERE id = ?
                """, [datetime.now(), usage.prompt_id])
            else:
                conn.execute("""
                    UPDATE prompts 
                    SET use_count = use_count + 1,
                        updated_at = ?
                    WHERE id = ?
                """, [datetime.now(), usage.prompt_id])
    
    def get_usage_history(self, prompt_id: str, limit: int = 100) -> List[PromptUsage]:
        """Get usage history for a prompt."""
        with duckdb.connect(str(self.db_path)) as conn:
            results = conn.execute("""
                SELECT * FROM prompt_usage 
                WHERE prompt_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, [prompt_id, limit]).fetchall()
            
            return [self._row_to_usage(row) for row in results]
    
    def _row_to_prompt(self, row) -> Prompt:
        """Convert database row to Prompt object."""
        from .models import PromptCategory, ProviderType
        
        return Prompt(
            id=row[0],
            text=row[1],
            category=PromptCategory(row[2]),
            providers=[ProviderType(p) for p in json.loads(row[3])],
            tags=json.loads(row[4]) if row[4] else [],
            project=row[5],
            style=row[6],
            effectiveness_rating=row[7],
            use_count=row[8],
            success_count=row[9],
            created_at=row[10],
            updated_at=row[11],
            description=row[12],
            notes=row[13],
            context=json.loads(row[14]) if row[14] else {},
            parent_id=row[15],
            related_ids=json.loads(row[16]) if row[16] else [],
            keywords=json.loads(row[17]) if row[17] else []
        )
    
    def _row_to_usage(self, row) -> PromptUsage:
        """Convert database row to PromptUsage object."""
        from .models import ProviderType
        
        return PromptUsage(
            id=row[0],
            prompt_id=row[1],
            provider=ProviderType(row[2]),
            timestamp=row[3],
            success=row[4],
            output_path=row[5],
            cost=row[6],
            duration_seconds=row[7],
            notes=row[8],
            parameters=json.loads(row[9]) if row[9] else {},
            metadata=json.loads(row[10]) if row[10] else {}
        )