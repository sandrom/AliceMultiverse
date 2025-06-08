"""Style recommendation engine for personalized suggestions."""

import random
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set

from .style_memory import StyleMemory, StylePreference, PreferenceType
from .learning_engine import StyleLearningEngine, LearningInsight
from ..core.structured_logging import get_logger

logger = get_logger(__name__)


@dataclass
class StyleRecommendation:
    """A style recommendation."""
    recommendation_id: str
    recommendation_type: str  # preset, variation, exploration, trending
    
    # Recommendation content
    title: str
    description: str
    preferences: Dict[PreferenceType, Any]  # Recommended preferences
    
    # Scoring
    relevance_score: float  # How relevant to user's style
    novelty_score: float   # How different from recent choices
    confidence: float      # Overall confidence
    
    # Reasoning
    reasoning: List[str] = field(default_factory=list)
    based_on: List[str] = field(default_factory=list)  # Preference IDs
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    preview_url: Optional[str] = None


@dataclass
class RecommendationSet:
    """A set of related recommendations."""
    set_id: str
    theme: str
    description: str
    
    recommendations: List[StyleRecommendation] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    # Context
    context: Dict[str, Any] = field(default_factory=dict)
    target_project: Optional[str] = None


class StyleRecommendationEngine:
    """Generates personalized style recommendations."""
    
    def __init__(
        self,
        style_memory: StyleMemory,
        learning_engine: Optional[StyleLearningEngine] = None
    ):
        """Initialize recommendation engine.
        
        Args:
            style_memory: StyleMemory instance
            learning_engine: Optional learning engine
        """
        self.style_memory = style_memory
        self.learning_engine = learning_engine
        
        # Recommendation parameters
        self.exploration_rate = 0.2  # 20% exploration vs exploitation
        self.min_confidence = 0.6
        self.max_recommendations = 10
        
    def get_recommendations(
        self,
        context: Optional[Dict[str, Any]] = None,
        recommendation_types: Optional[List[str]] = None,
        limit: int = 5
    ) -> List[StyleRecommendation]:
        """Get personalized style recommendations.
        
        Args:
            context: Current context
            recommendation_types: Types to include
            limit: Maximum recommendations
            
        Returns:
            List of recommendations
        """
        context = context or {}
        types = recommendation_types or ["preset", "variation", "exploration"]
        
        recommendations = []
        
        # Get recommendations by type
        if "preset" in types:
            recommendations.extend(self._generate_preset_recommendations(context))
        
        if "variation" in types:
            recommendations.extend(self._generate_variation_recommendations(context))
        
        if "exploration" in types:
            recommendations.extend(self._generate_exploration_recommendations(context))
        
        if "trending" in types:
            recommendations.extend(self._generate_trending_recommendations(context))
        
        # Score and sort
        for rec in recommendations:
            rec.confidence = self._calculate_confidence(rec, context)
        
        recommendations.sort(key=lambda r: r.confidence, reverse=True)
        
        return recommendations[:limit]
    
    def get_recommendation_sets(
        self,
        theme: Optional[str] = None,
        project: Optional[str] = None
    ) -> List[RecommendationSet]:
        """Get themed recommendation sets.
        
        Args:
            theme: Optional theme filter
            project: Optional project context
            
        Returns:
            List of recommendation sets
        """
        sets = []
        
        # Generate themed sets
        if not theme or theme == "daily":
            sets.append(self._generate_daily_set(project))
        
        if not theme or theme == "style_fusion":
            sets.append(self._generate_style_fusion_set(project))
        
        if not theme or theme == "mood_based":
            sets.append(self._generate_mood_based_set(project))
        
        if not theme or theme == "project_specific" and project:
            sets.append(self._generate_project_set(project))
        
        return [s for s in sets if s and s.recommendations]
    
    def get_next_best_action(
        self,
        current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Suggest next best action based on current state.
        
        Args:
            current_state: Current workflow state
            
        Returns:
            Action recommendation
        """
        # Analyze current preferences
        current_prefs = current_state.get("preferences", {})
        
        # Find missing preference types
        missing_types = []
        for pref_type in PreferenceType:
            if pref_type not in current_prefs:
                missing_types.append(pref_type)
        
        if missing_types:
            # Recommend filling in missing preferences
            next_type = missing_types[0]
            predictions = self._predict_preference(next_type, current_state)
            
            return {
                "action": "add_preference",
                "preference_type": next_type.value,
                "suggestions": predictions[:3],
                "reason": f"Complete your style by choosing {next_type.value}"
            }
        
        # Check for improvement opportunities
        if self.learning_engine:
            # Get predictions for better combinations
            current_ids = [
                f"{k.value}:{v}" for k, v in current_prefs.items()
            ]
            
            suggestions = self.learning_engine.suggest_combinations(
                current_ids,
                current_state
            )
            
            if suggestions:
                best = suggestions[0]
                new_prefs = [
                    p for p in best["combination"]
                    if p not in current_ids
                ]
                
                if new_prefs:
                    return {
                        "action": "enhance_combination",
                        "add_preferences": new_prefs,
                        "expected_improvement": best["success_rate"],
                        "reason": best["reason"]
                    }
        
        # Suggest finalization
        return {
            "action": "finalize",
            "reason": "Your style selection is complete",
            "confidence": self._calculate_selection_confidence(current_prefs)
        }
    
    def track_recommendation_feedback(
        self,
        recommendation_id: str,
        accepted: bool,
        quality_score: Optional[float] = None,
        notes: Optional[str] = None
    ):
        """Track feedback on recommendations.
        
        Args:
            recommendation_id: Recommendation that was shown
            accepted: Whether user accepted it
            quality_score: Optional quality rating
            notes: Optional feedback notes
        """
        # In a full implementation, this would update recommendation models
        logger.info(
            f"Recommendation {recommendation_id} feedback: "
            f"accepted={accepted}, quality={quality_score}"
        )
    
    def _generate_preset_recommendations(
        self,
        context: Dict[str, Any]
    ) -> List[StyleRecommendation]:
        """Generate preset style recommendations."""
        recommendations = []
        
        # Get user's top preferences by type
        top_by_type = {}
        for pref_type in PreferenceType:
            top = self.style_memory.profile.get_top_preferences(
                preference_type=pref_type,
                limit=3
            )
            if top:
                top_by_type[pref_type] = top
        
        # Create "Best of" preset
        if len(top_by_type) >= 3:
            best_prefs = {}
            base_ids = []
            
            for pref_type, prefs in top_by_type.items():
                if prefs:
                    best_prefs[pref_type] = prefs[0].value
                    base_ids.append(prefs[0].preference_id)
            
            rec = StyleRecommendation(
                recommendation_id=f"preset_best_{datetime.now().strftime('%Y%m%d')}",
                recommendation_type="preset",
                title="Your Signature Style",
                description="Your most successful preferences combined",
                preferences=best_prefs,
                relevance_score=0.95,
                novelty_score=0.1,
                confidence=0.9,
                reasoning=[
                    "Based on your highest-rated preferences",
                    "Proven successful combination"
                ],
                based_on=base_ids,
                tags=["signature", "proven", "favorite"]
            )
            recommendations.append(rec)
        
        # Create time-based preset
        hour = datetime.now().hour
        time_period = "morning" if hour < 12 else "afternoon" if hour < 18 else "evening"
        
        time_prefs = self._get_time_preferences(hour)
        if time_prefs:
            rec = StyleRecommendation(
                recommendation_id=f"preset_time_{time_period}",
                recommendation_type="preset",
                title=f"Perfect for {time_period.title()}",
                description=f"Styles you prefer during {time_period}",
                preferences=time_prefs,
                relevance_score=0.8,
                novelty_score=0.2,
                confidence=0.75,
                reasoning=[
                    f"Optimized for {time_period} creativity",
                    "Based on your time patterns"
                ],
                tags=[time_period, "time-based"]
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _generate_variation_recommendations(
        self,
        context: Dict[str, Any]
    ) -> List[StyleRecommendation]:
        """Generate variations of successful styles."""
        recommendations = []
        
        # Get recent successful preferences
        recent_success = []
        for pref in self.style_memory.all_preferences.values():
            if (
                pref.preference_score > 0.7 and
                (datetime.now() - pref.last_used).days <= 7
            ):
                recent_success.append(pref)
        
        if not recent_success:
            return recommendations
        
        # Create variations
        for base_pref in recent_success[:3]:
            # Find similar values
            similar = self._find_similar_values(
                base_pref.preference_type,
                base_pref.value
            )
            
            if similar:
                variation_prefs = {
                    base_pref.preference_type: similar[0]
                }
                
                # Add complementary preferences
                complements = self._find_complementary_preferences(
                    base_pref.preference_id
                )
                
                for comp in complements[:2]:
                    if comp.preference_type not in variation_prefs:
                        variation_prefs[comp.preference_type] = comp.value
                
                rec = StyleRecommendation(
                    recommendation_id=f"variation_{base_pref.preference_id}_{datetime.now().timestamp()}",
                    recommendation_type="variation",
                    title=f"Variation on {base_pref.value}",
                    description="A fresh take on your successful style",
                    preferences=variation_prefs,
                    relevance_score=0.7,
                    novelty_score=0.6,
                    confidence=0.7,
                    reasoning=[
                        f"Similar to your successful '{base_pref.value}'",
                        "Adds complementary elements"
                    ],
                    based_on=[base_pref.preference_id],
                    tags=["variation", "fresh", "similar"]
                )
                recommendations.append(rec)
        
        return recommendations
    
    def _generate_exploration_recommendations(
        self,
        context: Dict[str, Any]
    ) -> List[StyleRecommendation]:
        """Generate exploratory recommendations."""
        recommendations = []
        
        # Find underexplored preference types
        usage_by_type = defaultdict(int)
        for pref in self.style_memory.all_preferences.values():
            usage_by_type[pref.preference_type] += pref.usage_count
        
        # Sort by least used
        underexplored = sorted(
            PreferenceType,
            key=lambda pt: usage_by_type.get(pt, 0)
        )[:3]
        
        for pref_type in underexplored:
            # Get trending values for this type
            trending = self._get_trending_values(pref_type)
            
            if trending:
                explore_prefs = {pref_type: trending[0]}
                
                # Add safe complements
                safe_prefs = self.style_memory.profile.get_top_preferences(
                    limit=2,
                    min_confidence=0.8
                )
                
                for safe in safe_prefs:
                    if safe.preference_type not in explore_prefs:
                        explore_prefs[safe.preference_type] = safe.value
                
                rec = StyleRecommendation(
                    recommendation_id=f"explore_{pref_type.value}_{datetime.now().timestamp()}",
                    recommendation_type="exploration",
                    title=f"Explore {pref_type.value.replace('_', ' ').title()}",
                    description="Expand your creative horizons",
                    preferences=explore_prefs,
                    relevance_score=0.5,
                    novelty_score=0.9,
                    confidence=0.6,
                    reasoning=[
                        f"You haven't explored {pref_type.value} much",
                        "Combined with your proven preferences for safety"
                    ],
                    tags=["exploration", "new", "discovery"]
                )
                recommendations.append(rec)
        
        return recommendations
    
    def _generate_trending_recommendations(
        self,
        context: Dict[str, Any]
    ) -> List[StyleRecommendation]:
        """Generate trending style recommendations."""
        recommendations = []
        
        # Analyze recent patterns across all preferences
        recent_date = datetime.now() - timedelta(days=7)
        recent_prefs = defaultdict(int)
        
        for pref in self.style_memory.all_preferences.values():
            if pref.last_used >= recent_date:
                recent_prefs[pref.preference_id] += pref.usage_count
        
        # Find rising trends
        trending = sorted(
            recent_prefs.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        if trending:
            trend_preferences = {}
            base_ids = []
            
            for pref_id, _ in trending[:3]:
                if pref_id in self.style_memory.all_preferences:
                    pref = self.style_memory.all_preferences[pref_id]
                    trend_preferences[pref.preference_type] = pref.value
                    base_ids.append(pref_id)
            
            if len(trend_preferences) >= 2:
                rec = StyleRecommendation(
                    recommendation_id=f"trending_{datetime.now().strftime('%Y%m%d')}",
                    recommendation_type="trending",
                    title="Trending This Week",
                    description="Your most used styles recently",
                    preferences=trend_preferences,
                    relevance_score=0.85,
                    novelty_score=0.3,
                    confidence=0.8,
                    reasoning=[
                        "Based on your recent activity",
                        "Currently popular in your workflow"
                    ],
                    based_on=base_ids,
                    tags=["trending", "recent", "popular"]
                )
                recommendations.append(rec)
        
        return recommendations
    
    def _generate_daily_set(self, project: Optional[str]) -> RecommendationSet:
        """Generate daily recommendation set."""
        recommendations = []
        
        # Get various types
        recommendations.extend(self.get_recommendations(
            {"project": project} if project else {},
            ["preset", "variation"],
            3
        ))
        
        if recommendations:
            return RecommendationSet(
                set_id=f"daily_{datetime.now().strftime('%Y%m%d')}",
                theme="daily",
                description="Today's personalized style recommendations",
                recommendations=recommendations,
                context={"time": "daily", "date": datetime.now().date()},
                target_project=project
            )
        
        return None
    
    def _generate_style_fusion_set(self, project: Optional[str]) -> RecommendationSet:
        """Generate style fusion recommendations."""
        recommendations = []
        
        # Get top preferences from different types
        fusion_base = {}
        for pref_type in [PreferenceType.COLOR_PALETTE, PreferenceType.TECHNIQUE, PreferenceType.MOOD]:
            top = self.style_memory.profile.get_top_preferences(pref_type, 2)
            if len(top) >= 2:
                fusion_base[pref_type] = [top[0], top[1]]
        
        # Create fusion combinations
        if len(fusion_base) >= 2:
            # Mix and match
            for i in range(2):
                fusion_prefs = {}
                base_ids = []
                
                for pref_type, options in fusion_base.items():
                    choice = options[i % len(options)]
                    fusion_prefs[pref_type] = choice.value
                    base_ids.append(choice.preference_id)
                
                rec = StyleRecommendation(
                    recommendation_id=f"fusion_{i}_{datetime.now().timestamp()}",
                    recommendation_type="variation",
                    title=f"Style Fusion {i+1}",
                    description="Unexpected combination of your favorites",
                    preferences=fusion_prefs,
                    relevance_score=0.75,
                    novelty_score=0.7,
                    confidence=0.7,
                    reasoning=["Creative fusion of proven elements"],
                    based_on=base_ids,
                    tags=["fusion", "creative", "experimental"]
                )
                recommendations.append(rec)
        
        if recommendations:
            return RecommendationSet(
                set_id=f"fusion_{datetime.now().strftime('%Y%m%d')}",
                theme="style_fusion",
                description="Creative fusions of your favorite styles",
                recommendations=recommendations,
                target_project=project
            )
        
        return None
    
    def _generate_mood_based_set(self, project: Optional[str]) -> RecommendationSet:
        """Generate mood-based recommendations."""
        recommendations = []
        
        # Define mood profiles
        mood_profiles = {
            "energetic": {
                PreferenceType.COLOR_PALETTE: ["vibrant", "warm", "bright"],
                PreferenceType.PACING: ["fast", "dynamic", "rhythmic"],
                PreferenceType.MOOD: ["energetic", "exciting", "powerful"]
            },
            "calm": {
                PreferenceType.COLOR_PALETTE: ["pastel", "cool", "muted"],
                PreferenceType.PACING: ["slow", "gentle", "flowing"],
                PreferenceType.MOOD: ["serene", "peaceful", "contemplative"]
            },
            "dramatic": {
                PreferenceType.COLOR_PALETTE: ["high contrast", "dark", "bold"],
                PreferenceType.LIGHTING: ["dramatic", "moody", "directional"],
                PreferenceType.MOOD: ["intense", "mysterious", "powerful"]
            }
        }
        
        # Match user preferences to moods
        for mood, profile in mood_profiles.items():
            score = 0
            matched_prefs = {}
            
            for pref_type, values in profile.items():
                # Check if user has preferences matching this mood
                user_prefs = self.style_memory.profile.preferences.get(pref_type, [])
                
                for pref in user_prefs:
                    if any(v in str(pref.value).lower() for v in values):
                        score += pref.preference_score
                        if pref_type not in matched_prefs:
                            matched_prefs[pref_type] = pref.value
            
            if score > 0.5 and len(matched_prefs) >= 2:
                # Fill in missing preferences
                for pref_type, values in profile.items():
                    if pref_type not in matched_prefs:
                        matched_prefs[pref_type] = values[0]
                
                rec = StyleRecommendation(
                    recommendation_id=f"mood_{mood}_{datetime.now().timestamp()}",
                    recommendation_type="preset",
                    title=f"{mood.title()} Mood",
                    description=f"Perfect for creating {mood} content",
                    preferences=matched_prefs,
                    relevance_score=min(1.0, score),
                    novelty_score=0.4,
                    confidence=0.75,
                    reasoning=[f"Matches your {mood} style preferences"],
                    tags=["mood", mood]
                )
                recommendations.append(rec)
        
        if recommendations:
            return RecommendationSet(
                set_id=f"moods_{datetime.now().strftime('%Y%m%d')}",
                theme="mood_based",
                description="Style recommendations by mood",
                recommendations=recommendations,
                target_project=project
            )
        
        return None
    
    def _generate_project_set(self, project: str) -> RecommendationSet:
        """Generate project-specific recommendations."""
        recommendations = []
        
        # Get project style from memory
        project_style = self.style_memory.profile.project_styles.get(project, {})
        
        if project_style:
            # Create recommendation from project style
            rec = StyleRecommendation(
                recommendation_id=f"project_{project}_{datetime.now().timestamp()}",
                recommendation_type="preset",
                title=f"{project} Style",
                description=f"Your established style for {project}",
                preferences=project_style,
                relevance_score=0.95,
                novelty_score=0.1,
                confidence=0.9,
                reasoning=[f"Based on your {project} history"],
                tags=["project", project]
            )
            recommendations.append(rec)
        
        # Add variations
        variations = self._generate_variation_recommendations({"project": project})
        recommendations.extend(variations[:2])
        
        if recommendations:
            return RecommendationSet(
                set_id=f"project_{project}_{datetime.now().strftime('%Y%m%d')}",
                theme="project_specific",
                description=f"Recommendations for {project}",
                recommendations=recommendations,
                target_project=project
            )
        
        return None
    
    def _calculate_confidence(
        self,
        recommendation: StyleRecommendation,
        context: Dict[str, Any]
    ) -> float:
        """Calculate overall confidence for a recommendation."""
        # Base confidence from relevance and success probability
        confidence = recommendation.relevance_score * 0.6
        
        # Adjust for novelty (some exploration is good)
        optimal_novelty = 0.3
        novelty_factor = 1 - abs(recommendation.novelty_score - optimal_novelty)
        confidence += novelty_factor * 0.2
        
        # Boost for context match
        if context.get("project") and recommendation.tags:
            if context["project"] in recommendation.tags:
                confidence += 0.1
        
        # Boost for trending
        if recommendation.recommendation_type == "trending":
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _calculate_selection_confidence(
        self,
        preferences: Dict[PreferenceType, Any]
    ) -> float:
        """Calculate confidence in a preference selection."""
        if not preferences:
            return 0.0
            
        # Check coverage
        coverage = len(preferences) / len(PreferenceType)
        
        # Check individual preference scores
        scores = []
        for pref_type, value in preferences.items():
            pref_id = f"{pref_type.value}:{value}"
            if pref_id in self.style_memory.all_preferences:
                pref = self.style_memory.all_preferences[pref_id]
                scores.append(pref.preference_score)
        
        avg_score = sum(scores) / len(scores) if scores else 0.5
        
        return coverage * 0.4 + avg_score * 0.6
    
    def _predict_preference(
        self,
        preference_type: PreferenceType,
        context: Dict[str, Any]
    ) -> List[Tuple[Any, float]]:
        """Predict likely preference values."""
        if self.learning_engine:
            predictions = self.learning_engine.predict_preferences(
                context,
                [preference_type]
            )
            return predictions.get(preference_type, [])
        
        # Fallback to top preferences
        top = self.style_memory.profile.get_top_preferences(
            preference_type,
            limit=3
        )
        return [(p.value, p.preference_score) for p in top]
    
    def _get_time_preferences(self, hour: int) -> Dict[PreferenceType, Any]:
        """Get preferences for a specific hour."""
        hour_prefs = self.style_memory.profile.time_of_day_preferences.get(hour, [])
        
        if not hour_prefs:
            return {}
            
        # Count most common by type
        type_values = defaultdict(list)
        
        for pref_id in hour_prefs:
            if pref_id in self.style_memory.all_preferences:
                pref = self.style_memory.all_preferences[pref_id]
                type_values[pref.preference_type].append(pref.value)
        
        # Get most common per type
        result = {}
        for pref_type, values in type_values.items():
            if values:
                # Get most common
                value_counts = defaultdict(int)
                for v in values:
                    value_counts[v] += 1
                
                most_common = max(value_counts.items(), key=lambda x: x[1])
                result[pref_type] = most_common[0]
        
        return result
    
    def _find_similar_values(
        self,
        preference_type: PreferenceType,
        value: Any
    ) -> List[Any]:
        """Find similar values for variation."""
        # In a real implementation, this would use embeddings or ontologies
        # For now, return random values of same type
        all_values = set()
        
        for pref in self.style_memory.all_preferences.values():
            if pref.preference_type == preference_type and pref.value != value:
                all_values.add(pref.value)
        
        return list(all_values)[:3]
    
    def _find_complementary_preferences(
        self,
        preference_id: str
    ) -> List[StylePreference]:
        """Find preferences that work well with given one."""
        complementary = []
        
        # Check co-occurrence patterns
        cooccur = self.style_memory.patterns.get("co_occurrence", {}).get(preference_id, {})
        
        for other_id, count in cooccur.most_common(5):
            if other_id in self.style_memory.all_preferences:
                pref = self.style_memory.all_preferences[other_id]
                if pref.preference_score > 0.6:
                    complementary.append(pref)
        
        return complementary
    
    def _get_trending_values(
        self,
        preference_type: PreferenceType
    ) -> List[Any]:
        """Get trending values for a preference type."""
        # Get recent preferences of this type
        recent_date = datetime.now() - timedelta(days=14)
        recent_values = []
        
        for pref in self.style_memory.all_preferences.values():
            if (
                pref.preference_type == preference_type and
                pref.last_used >= recent_date
            ):
                recent_values.extend([pref.value] * pref.usage_count)
        
        if not recent_values:
            return []
            
        # Count occurrences
        value_counts = defaultdict(int)
        for v in recent_values:
            value_counts[v] += 1
        
        # Return top trending
        trending = sorted(value_counts.items(), key=lambda x: x[1], reverse=True)
        return [v[0] for v in trending[:3]]