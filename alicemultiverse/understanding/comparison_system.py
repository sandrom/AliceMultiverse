"""
Model Comparison System with Elo Ratings

Simple A/B comparison with optional strength rating for comparing
AI model outputs. Uses Elo rating system to track performance.
"""

import random
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
import duckdb


class ComparisonResult(Enum):
    """Result of a model comparison."""
    A_WINS = "a_wins"
    B_WINS = "b_wins"
    DRAW = "draw"
    SKIPPED = "skipped"


class WinStrength(Enum):
    """How much better the winner was."""
    SLIGHT = 1  # Barely better
    CLEAR = 2   # Clearly better
    MUCH = 3    # Much better


@dataclass
class ModelComparison:
    """A single comparison session."""
    session_id: str
    content_hash: str
    model_a_id: str
    model_b_id: str
    result: Optional[ComparisonResult] = None
    strength: Optional[WinStrength] = None
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class EloRatingSystem:
    """
    Elo rating system for AI models.
    
    Each model starts at 1500 rating.
    K-factor determines how much ratings change per comparison.
    """
    
    def __init__(self, k_factor: int = 32, db_path: str = "alice.db"):
        self.k_factor = k_factor
        self.conn = duckdb.connect(db_path)
        self._init_tables()
    
    def _init_tables(self):
        """Initialize database tables."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS model_ratings (
                provider VARCHAR,
                model_name VARCHAR,
                rating DECIMAL(10,2) DEFAULT 1500.0,
                games_played INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                draws INTEGER DEFAULT 0,
                last_updated TIMESTAMP,
                PRIMARY KEY (provider, model_name)
            );
            
            CREATE TABLE IF NOT EXISTS comparison_history (
                session_id VARCHAR PRIMARY KEY,
                content_hash VARCHAR,
                model_a VARCHAR,  -- provider:model
                model_b VARCHAR,
                result VARCHAR,  -- a_wins, b_wins, draw
                strength INTEGER,  -- 1-3 if winner
                rating_change_a DECIMAL(10,2),
                rating_change_b DECIMAL(10,2),
                completed_at TIMESTAMP
            );
        """)
    
    def get_rating(self, provider: str, model: str) -> float:
        """Get current Elo rating for a model."""
        result = self.conn.execute("""
            SELECT rating FROM model_ratings 
            WHERE provider = ? AND model_name = ?
        """, [provider, model]).fetchone()
        
        return result[0] if result else 1500.0
    
    def update_ratings(
        self, 
        model_a: Tuple[str, str],  # (provider, model)
        model_b: Tuple[str, str],
        result: ComparisonResult,
        strength: WinStrength = WinStrength.SLIGHT,
        session_id: Optional[str] = None
    ):
        """Update Elo ratings based on comparison result."""
        if result == ComparisonResult.SKIPPED:
            return
        
        # Get current ratings
        rating_a = self.get_rating(*model_a)
        rating_b = self.get_rating(*model_b)
        
        # Calculate expected scores
        expected_a = 1 / (1 + 10**((rating_b - rating_a) / 400))
        expected_b = 1 - expected_a
        
        # Determine actual scores based on result and strength
        if result == ComparisonResult.DRAW:
            score_a = score_b = 0.5
        elif result == ComparisonResult.A_WINS:
            # Strength affects how much of a "win" it is
            score_a = 0.5 + (0.5 * strength.value / 3)  # 0.67, 0.83, 1.0
            score_b = 1 - score_a
        else:  # B wins
            score_b = 0.5 + (0.5 * strength.value / 3)
            score_a = 1 - score_b
        
        # Calculate rating changes
        change_a = self.k_factor * (score_a - expected_a)
        change_b = self.k_factor * (score_b - expected_b)
        
        new_rating_a = rating_a + change_a
        new_rating_b = rating_b + change_b
        
        # Update database
        self._update_model_rating(model_a, new_rating_a, result, True)
        self._update_model_rating(model_b, new_rating_b, result, False)
        
        # Record comparison
        if session_id:
            self._record_comparison(
                session_id, model_a, model_b, result, 
                strength, change_a, change_b
            )
    
    def _update_model_rating(
        self, 
        model: Tuple[str, str],
        new_rating: float,
        result: ComparisonResult,
        is_model_a: bool
    ):
        """Update model rating in database."""
        provider, model_name = model
        
        # Determine win/loss/draw
        if result == ComparisonResult.DRAW:
            draw_increment = 1
            win_increment = loss_increment = 0
        elif (result == ComparisonResult.A_WINS and is_model_a) or \
             (result == ComparisonResult.B_WINS and not is_model_a):
            win_increment = 1
            draw_increment = loss_increment = 0
        else:
            loss_increment = 1
            win_increment = draw_increment = 0
        
        self.conn.execute("""
            INSERT INTO model_ratings (provider, model_name, rating, games_played, 
                                     wins, losses, draws, last_updated)
            VALUES (?, ?, ?, 1, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT (provider, model_name) DO UPDATE SET
                rating = ?,
                games_played = games_played + 1,
                wins = wins + ?,
                losses = losses + ?,
                draws = draws + ?,
                last_updated = CURRENT_TIMESTAMP
        """, [
            provider, model_name, new_rating, 
            win_increment, loss_increment, draw_increment,
            new_rating, win_increment, loss_increment, draw_increment
        ])
    
    def get_leaderboard(self, min_games: int = 5) -> List[Dict]:
        """Get model leaderboard sorted by rating."""
        return self.conn.execute("""
            SELECT 
                provider,
                model_name,
                rating,
                games_played,
                wins,
                losses,
                draws,
                ROUND(CAST(wins AS FLOAT) / NULLIF(games_played, 0) * 100, 1) as win_rate
            FROM model_ratings
            WHERE games_played >= ?
            ORDER BY rating DESC
        """, [min_games]).fetchall()
    
    def suggest_matchup(self, available_models: List[Tuple[str, str]]) -> Tuple[str, str]:
        """
        Suggest an interesting matchup.
        
        Strategy:
        - 70% of the time: Match models with similar ratings
        - 20% of the time: Test underdog against champion  
        - 10% of the time: Random pairing
        """
        if len(available_models) < 2:
            raise ValueError("Need at least 2 models for comparison")
        
        # Get ratings for all models
        model_ratings = [
            (model, self.get_rating(*model)) 
            for model in available_models
        ]
        model_ratings.sort(key=lambda x: x[1], reverse=True)
        
        strategy = random.random()
        
        if strategy < 0.7 and len(model_ratings) > 2:
            # Similar ratings - pick two adjacent models
            idx = random.randint(0, len(model_ratings) - 2)
            return model_ratings[idx][0], model_ratings[idx + 1][0]
        
        elif strategy < 0.9 and len(model_ratings) > 3:
            # David vs Goliath
            champion = model_ratings[0][0]
            underdog = random.choice(model_ratings[len(model_ratings)//2:])[0]
            return champion, underdog
        
        else:
            # Random pairing
            return random.sample(available_models, 2)


class ComparisonInterface:
    """Web interface data provider for model comparisons."""
    
    def __init__(self, elo_system: EloRatingSystem):
        self.elo = elo_system
        self.active_sessions = {}
    
    def create_comparison(
        self,
        content_hash: str,
        models: Optional[List[Tuple[str, str]]] = None
    ) -> ModelComparison:
        """Create a new comparison session."""
        if models and len(models) >= 2:
            model_a, model_b = models[:2]
        else:
            # Auto-select models
            available = self._get_available_models()
            model_a, model_b = self.elo.suggest_matchup(available)
        
        session = ModelComparison(
            session_id=str(uuid.uuid4()),
            content_hash=content_hash,
            model_a_id=f"{model_a[0]}:{model_a[1]}",
            model_b_id=f"{model_b[0]}:{model_b[1]}"
        )
        
        self.active_sessions[session.session_id] = session
        return session
    
    def submit_result(
        self,
        session_id: str,
        result: ComparisonResult,
        strength: Optional[WinStrength] = None
    ):
        """Submit comparison result."""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.result = result
        session.strength = strength or WinStrength.SLIGHT
        session.completed_at = datetime.now()
        
        # Update Elo ratings
        model_a = session.model_a_id.split(":")
        model_b = session.model_b_id.split(":")
        
        self.elo.update_ratings(
            model_a, model_b, result, session.strength, session_id
        )
        
        # Clean up
        del self.active_sessions[session_id]
    
    def _get_available_models(self) -> List[Tuple[str, str]]:
        """Get list of available models."""
        # This would connect to actual available providers
        return [
            ("anthropic", "claude-3-5-sonnet"),
            ("openai", "gpt-4o"),
            ("google", "gemini-1.5-flash"),
            ("deepseek", "deepseek-reasoner")
        ]


# Usage example
if __name__ == "__main__":
    # Initialize system
    elo = EloRatingSystem()
    interface = ComparisonInterface(elo)
    
    # Create comparison
    session = interface.create_comparison("sha256:abc123")
    print(f"Compare {session.model_a_id} vs {session.model_b_id}")
    print("Press A/←, B/→, or =/Space")
    
    # Simulate user choosing A as slightly better
    interface.submit_result(
        session.session_id,
        ComparisonResult.A_WINS,
        WinStrength.SLIGHT
    )
    
    # Show leaderboard
    print("\n=== Model Leaderboard ===")
    for row in elo.get_leaderboard(min_games=0):
        provider, model, rating, games, wins, losses, draws, win_rate = row
        print(f"{provider}:{model} - {rating:.0f} ({wins}W-{losses}L-{draws}D)")