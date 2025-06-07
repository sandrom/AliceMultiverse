"""Comprehensive cost tracking and estimation for API calls.

This module provides:
1. Cost estimation before operations
2. Real-time spending tracking
3. Budget alerts and limits
4. Provider cost comparison
5. Historical spending analysis
"""

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

from ..core.structured_logging import get_logger

logger = get_logger(__name__)


class CostCategory(Enum):
    """Categories of costs."""
    
    UNDERSTANDING = "understanding"  # Image analysis
    GENERATION = "generation"       # Image/video generation
    ENHANCEMENT = "enhancement"     # Upscaling, editing
    AUDIO = "audio"                # Sound effects, music
    OTHER = "other"


@dataclass
class ProviderPricing:
    """Pricing information for a provider."""
    
    provider_name: str
    category: CostCategory
    
    # Pricing models
    per_request: Optional[float] = None          # Fixed cost per request
    per_token_input: Optional[float] = None      # Cost per input token
    per_token_output: Optional[float] = None     # Cost per output token
    per_second: Optional[float] = None           # Cost per second (video/audio)
    per_megapixel: Optional[float] = None        # Cost per megapixel (images)
    
    # Additional costs
    setup_fee: float = 0.0
    minimum_charge: float = 0.0
    
    # Free tier
    free_requests_daily: int = 0
    free_requests_monthly: int = 0
    
    # Notes
    notes: str = ""
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class CostEstimate:
    """Estimated cost for an operation."""
    
    operation: str
    provider: str
    category: CostCategory
    
    # Cost breakdown
    min_cost: float
    max_cost: float
    likely_cost: float
    
    # Details
    breakdown: Dict[str, float] = field(default_factory=dict)
    assumptions: List[str] = field(default_factory=list)
    
    # Alternatives
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def formatted_likely(self) -> str:
        """Get formatted likely cost."""
        return f"${self.likely_cost:.4f}"
    
    @property
    def formatted_range(self) -> str:
        """Get formatted cost range."""
        if self.min_cost == self.max_cost:
            return f"${self.min_cost:.4f}"
        return f"${self.min_cost:.4f} - ${self.max_cost:.4f}"


@dataclass
class SpendingRecord:
    """Record of actual spending."""
    
    timestamp: datetime
    provider: str
    category: CostCategory
    operation: str
    cost: float
    
    # Context
    project_id: Optional[str] = None
    asset_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


class CostTracker:
    """Comprehensive cost tracking system."""
    
    # Built-in provider pricing (as of January 2025)
    DEFAULT_PRICING = {
        # Understanding providers
        "anthropic": ProviderPricing(
            provider_name="anthropic",
            category=CostCategory.UNDERSTANDING,
            per_token_input=0.003 / 1000,    # $3 per million tokens
            per_token_output=0.015 / 1000,   # $15 per million tokens
            notes="Claude 3.5 Sonnet pricing"
        ),
        "openai": ProviderPricing(
            provider_name="openai",
            category=CostCategory.UNDERSTANDING,
            per_token_input=0.01 / 1000,     # $10 per million tokens
            per_token_output=0.03 / 1000,    # $30 per million tokens
            notes="GPT-4 Vision pricing"
        ),
        "google": ProviderPricing(
            provider_name="google",
            category=CostCategory.UNDERSTANDING,
            per_token_input=0.00025 / 1000,  # $0.25 per million tokens
            per_token_output=0.0005 / 1000,  # $0.50 per million tokens
            free_requests_daily=50,
            notes="Gemini 1.5 Flash pricing with free tier"
        ),
        "deepseek": ProviderPricing(
            provider_name="deepseek",
            category=CostCategory.UNDERSTANDING,
            per_request=0.0002,              # $0.0002 per request
            notes="DeepSeek Vision fixed pricing"
        ),
        
        # Generation providers
        "midjourney": ProviderPricing(
            provider_name="midjourney",
            category=CostCategory.GENERATION,
            per_request=0.10,                # ~$0.10 per image (based on $30/month for 300 images)
            notes="Estimated from subscription pricing"
        ),
        "dall-e-3": ProviderPricing(
            provider_name="dall-e-3",
            category=CostCategory.GENERATION,
            per_request=0.04,                # $0.04 per image (1024x1024)
            notes="DALL-E 3 standard quality"
        ),
        "dall-e-3-hd": ProviderPricing(
            provider_name="dall-e-3-hd",
            category=CostCategory.GENERATION,
            per_request=0.08,                # $0.08 per image (1024x1024 HD)
            notes="DALL-E 3 HD quality"
        ),
        "stable-diffusion": ProviderPricing(
            provider_name="stable-diffusion",
            category=CostCategory.GENERATION,
            per_request=0.002,               # $0.002 per image
            notes="Stability AI pricing"
        ),
        "flux": ProviderPricing(
            provider_name="flux",
            category=CostCategory.GENERATION,
            per_request=0.003,               # $0.003 per image
            notes="Flux.1 pricing on Replicate"
        ),
        
        # Video generation
        "kling": ProviderPricing(
            provider_name="kling",
            category=CostCategory.GENERATION,
            per_second=0.30,                 # $0.30 per second
            notes="Kling AI video generation"
        ),
        "runway": ProviderPricing(
            provider_name="runway",
            category=CostCategory.GENERATION,
            per_second=0.05,                 # $0.05 per second
            notes="Runway Gen-2 pricing"
        ),
        
        # Enhancement
        "magnific": ProviderPricing(
            provider_name="magnific",
            category=CostCategory.ENHANCEMENT,
            per_request=0.40,                # $0.40 per upscale
            notes="Magnific AI upscaling"
        ),
        "real-esrgan": ProviderPricing(
            provider_name="real-esrgan",
            category=CostCategory.ENHANCEMENT,
            per_megapixel=0.001,             # $0.001 per megapixel
            notes="Real-ESRGAN on Replicate"
        ),
        
        # Audio
        "elevenlabs": ProviderPricing(
            provider_name="elevenlabs",
            category=CostCategory.AUDIO,
            per_request=0.50,                # $0.50 per sound effect
            notes="ElevenLabs sound effects"
        ),
    }
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize cost tracker.
        
        Args:
            data_dir: Directory to store cost data (defaults to ~/.alice/costs/)
        """
        self.data_dir = data_dir or Path.home() / ".alice" / "costs"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load pricing data
        self.pricing: Dict[str, ProviderPricing] = self.DEFAULT_PRICING.copy()
        self._load_custom_pricing()
        
        # Load spending history
        self.spending_records: List[SpendingRecord] = []
        self._load_spending_history()
        
        # Budget tracking
        self.budgets: Dict[str, float] = {}
        self.budget_alerts: Dict[str, float] = {}  # Alert thresholds
        self._load_budgets()
        
        # Free tier tracking
        self.free_tier_usage: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._load_free_tier_usage()
    
    def _load_custom_pricing(self):
        """Load custom pricing overrides."""
        pricing_file = self.data_dir / "custom_pricing.json"
        if pricing_file.exists():
            try:
                with open(pricing_file, 'r') as f:
                    custom_pricing = json.load(f)
                
                for provider, pricing_data in custom_pricing.items():
                    self.pricing[provider] = ProviderPricing(
                        provider_name=provider,
                        **pricing_data
                    )
                
                logger.info(f"Loaded custom pricing for {len(custom_pricing)} providers")
            except Exception as e:
                logger.error(f"Failed to load custom pricing: {e}")
    
    def _load_spending_history(self):
        """Load spending history for current month."""
        current_month = datetime.now().strftime("%Y-%m")
        history_file = self.data_dir / f"spending_{current_month}.jsonl"
        
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            record = SpendingRecord(
                                timestamp=datetime.fromisoformat(data['timestamp']),
                                provider=data['provider'],
                                category=CostCategory(data['category']),
                                operation=data['operation'],
                                cost=data['cost'],
                                project_id=data.get('project_id'),
                                asset_id=data.get('asset_id'),
                                details=data.get('details', {})
                            )
                            self.spending_records.append(record)
                
                logger.info(f"Loaded {len(self.spending_records)} spending records")
            except Exception as e:
                logger.error(f"Failed to load spending history: {e}")
    
    def _load_budgets(self):
        """Load budget configuration."""
        budget_file = self.data_dir / "budgets.json"
        if budget_file.exists():
            try:
                with open(budget_file, 'r') as f:
                    budget_data = json.load(f)
                    self.budgets = budget_data.get('limits', {})
                    self.budget_alerts = budget_data.get('alerts', {})
                
                logger.info(f"Loaded budgets: {self.budgets}")
            except Exception as e:
                logger.error(f"Failed to load budgets: {e}")
    
    def _load_free_tier_usage(self):
        """Load free tier usage tracking."""
        usage_file = self.data_dir / "free_tier_usage.json"
        if usage_file.exists():
            try:
                with open(usage_file, 'r') as f:
                    self.free_tier_usage = json.load(f)
                
                # Clean up old entries
                self._cleanup_free_tier_usage()
            except Exception as e:
                logger.error(f"Failed to load free tier usage: {e}")
    
    def _cleanup_free_tier_usage(self):
        """Remove old free tier usage entries."""
        today = datetime.now().date().isoformat()
        current_month = datetime.now().strftime("%Y-%m")
        
        # Clean daily usage
        if 'daily' in self.free_tier_usage:
            self.free_tier_usage['daily'] = {
                provider: count 
                for provider, count in self.free_tier_usage['daily'].items()
                if provider.endswith(f"_{today}")
            }
        
        # Clean monthly usage  
        if 'monthly' in self.free_tier_usage:
            self.free_tier_usage['monthly'] = {
                provider: count
                for provider, count in self.free_tier_usage['monthly'].items()
                if provider.endswith(f"_{current_month}")
            }
    
    def estimate_cost(
        self,
        provider: str,
        operation: str,
        **kwargs
    ) -> CostEstimate:
        """Estimate cost for an operation.
        
        Args:
            provider: Provider name
            operation: Operation description
            **kwargs: Operation-specific parameters:
                - image_count: Number of images
                - token_count: Estimated tokens
                - duration_seconds: Video/audio duration
                - image_size: (width, height) tuple
                - detailed: Whether detailed analysis is requested
                
        Returns:
            Cost estimate with breakdown and alternatives
        """
        if provider not in self.pricing:
            # Unknown provider - make conservative estimate
            return CostEstimate(
                operation=operation,
                provider=provider,
                category=CostCategory.OTHER,
                min_cost=0.01,
                max_cost=1.00,
                likely_cost=0.10,
                assumptions=["Unknown provider - using conservative estimate"]
            )
        
        pricing = self.pricing[provider]
        
        # Check free tier
        free_remaining = self._get_free_tier_remaining(provider)
        if free_remaining > 0:
            return CostEstimate(
                operation=operation,
                provider=provider,
                category=pricing.category,
                min_cost=0.0,
                max_cost=0.0,
                likely_cost=0.0,
                breakdown={"free_tier": 0.0},
                assumptions=[f"Using free tier ({free_remaining} requests remaining)"]
            )
        
        # Calculate based on pricing model
        if pricing.per_request is not None:
            # Simple per-request pricing
            count = kwargs.get('image_count', 1)
            cost = pricing.per_request * count
            
            estimate = CostEstimate(
                operation=operation,
                provider=provider,
                category=pricing.category,
                min_cost=cost,
                max_cost=cost,
                likely_cost=cost,
                breakdown={"requests": cost}
            )
            
        elif pricing.per_token_input is not None:
            # Token-based pricing (for LLMs)
            # Estimate tokens for image analysis
            if kwargs.get('detailed', False):
                # Detailed analysis uses more tokens
                input_tokens = 1000  # Image encoding
                output_tokens = 500  # Detailed response
            else:
                input_tokens = 1000  # Image encoding
                output_tokens = 200  # Brief response
            
            # Override with provided estimates
            input_tokens = kwargs.get('input_tokens', input_tokens)
            output_tokens = kwargs.get('output_tokens', output_tokens)
            
            input_cost = input_tokens * pricing.per_token_input
            output_cost = output_tokens * pricing.per_token_output
            total_cost = input_cost + output_cost
            
            estimate = CostEstimate(
                operation=operation,
                provider=provider,
                category=pricing.category,
                min_cost=total_cost * 0.8,  # 20% variance
                max_cost=total_cost * 1.2,
                likely_cost=total_cost,
                breakdown={
                    "input_tokens": input_cost,
                    "output_tokens": output_cost
                },
                assumptions=[
                    f"Estimated {input_tokens} input tokens",
                    f"Estimated {output_tokens} output tokens"
                ]
            )
            
        elif pricing.per_second is not None:
            # Duration-based pricing (video/audio)
            duration = kwargs.get('duration_seconds', 5)
            cost = pricing.per_second * duration
            
            estimate = CostEstimate(
                operation=operation,
                provider=provider,
                category=pricing.category,
                min_cost=cost,
                max_cost=cost,
                likely_cost=cost,
                breakdown={"duration": cost},
                assumptions=[f"{duration} seconds of content"]
            )
            
        elif pricing.per_megapixel is not None:
            # Resolution-based pricing
            size = kwargs.get('image_size', (1024, 1024))
            megapixels = (size[0] * size[1]) / 1_000_000
            cost = pricing.per_megapixel * megapixels
            
            estimate = CostEstimate(
                operation=operation,
                provider=provider,
                category=pricing.category,
                min_cost=cost,
                max_cost=cost,
                likely_cost=cost,
                breakdown={"megapixels": cost},
                assumptions=[f"{megapixels:.1f} megapixels"]
            )
            
        else:
            # No pricing model available
            estimate = CostEstimate(
                operation=operation,
                provider=provider,
                category=pricing.category,
                min_cost=0.001,
                max_cost=1.0,
                likely_cost=0.1,
                assumptions=["No pricing model available - using default estimate"]
            )
        
        # Apply minimum charge
        if pricing.minimum_charge > 0:
            if estimate.likely_cost < pricing.minimum_charge:
                estimate.min_cost = pricing.minimum_charge
                estimate.max_cost = max(estimate.max_cost, pricing.minimum_charge)
                estimate.likely_cost = pricing.minimum_charge
                estimate.assumptions.append(f"Minimum charge: ${pricing.minimum_charge:.4f}")
        
        # Add alternatives
        estimate.alternatives = self._find_alternatives(provider, pricing.category, estimate.likely_cost)
        
        return estimate
    
    def _get_free_tier_remaining(self, provider: str) -> int:
        """Get remaining free tier requests for a provider."""
        pricing = self.pricing.get(provider)
        if not pricing:
            return 0
        
        today = datetime.now().date().isoformat()
        current_month = datetime.now().strftime("%Y-%m")
        
        # Check daily limit
        if pricing.free_requests_daily > 0:
            daily_key = f"{provider}_{today}"
            used_today = self.free_tier_usage.get('daily', {}).get(daily_key, 0)
            daily_remaining = pricing.free_requests_daily - used_today
            
            if daily_remaining <= 0:
                return 0
        else:
            daily_remaining = float('inf')
        
        # Check monthly limit  
        if pricing.free_requests_monthly > 0:
            monthly_key = f"{provider}_{current_month}"
            used_monthly = self.free_tier_usage.get('monthly', {}).get(monthly_key, 0)
            monthly_remaining = pricing.free_requests_monthly - used_monthly
            
            if monthly_remaining <= 0:
                return 0
        else:
            monthly_remaining = float('inf')
        
        remaining = min(daily_remaining, monthly_remaining)
        if remaining == float('inf'):
            return 999999  # Large number for unlimited
        return int(remaining)
    
    def _find_alternatives(self, provider: str, category: CostCategory, cost: float) -> List[Dict[str, Any]]:
        """Find alternative providers for an operation."""
        alternatives = []
        
        for alt_provider, alt_pricing in self.pricing.items():
            if alt_provider == provider or alt_pricing.category != category:
                continue
            
            # Estimate cost for alternative
            if alt_pricing.per_request is not None:
                alt_cost = alt_pricing.per_request
            elif alt_pricing.per_token_input is not None:
                # Rough estimate for token-based
                alt_cost = (1000 * alt_pricing.per_token_input + 300 * alt_pricing.per_token_output)
            else:
                continue
            
            # Calculate savings
            savings = cost - alt_cost
            savings_percent = (savings / cost * 100) if cost > 0 else 0
            
            alternatives.append({
                "provider": alt_provider,
                "cost": alt_cost,
                "savings": savings,
                "savings_percent": savings_percent,
                "notes": alt_pricing.notes
            })
        
        # Sort by savings
        alternatives.sort(key=lambda x: x['savings'], reverse=True)
        
        return alternatives[:3]  # Top 3 alternatives
    
    def record_cost(
        self,
        provider: str,
        operation: str,
        cost: float,
        category: Optional[CostCategory] = None,
        project_id: Optional[str] = None,
        asset_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Record actual cost incurred.
        
        Args:
            provider: Provider name
            operation: Operation performed
            cost: Actual cost
            category: Cost category (auto-detected if not provided)
            project_id: Associated project
            asset_id: Associated asset
            details: Additional details
        """
        # Auto-detect category if not provided
        if category is None:
            if provider in self.pricing:
                category = self.pricing[provider].category
            else:
                category = CostCategory.OTHER
        
        # Create spending record
        record = SpendingRecord(
            timestamp=datetime.now(timezone.utc),
            provider=provider,
            category=category,
            operation=operation,
            cost=cost,
            project_id=project_id,
            asset_id=asset_id,
            details=details or {}
        )
        
        self.spending_records.append(record)
        
        # Update free tier usage if applicable
        if cost == 0 and provider in self.pricing:
            self._increment_free_tier_usage(provider)
        
        # Save to disk
        self._save_spending_record(record)
        
        # Check budget alerts
        self._check_budget_alerts()
        
        logger.info(
            f"Recorded cost: ${cost:.4f} for {operation} via {provider}",
            extra={"provider": provider, "cost": cost, "operation": operation}
        )
    
    def _increment_free_tier_usage(self, provider: str):
        """Increment free tier usage counter."""
        today = datetime.now().date().isoformat()
        current_month = datetime.now().strftime("%Y-%m")
        
        # Initialize structure if needed
        if 'daily' not in self.free_tier_usage:
            self.free_tier_usage['daily'] = {}
        if 'monthly' not in self.free_tier_usage:
            self.free_tier_usage['monthly'] = {}
        
        # Increment counters
        daily_key = f"{provider}_{today}"
        monthly_key = f"{provider}_{current_month}"
        
        self.free_tier_usage['daily'][daily_key] = self.free_tier_usage['daily'].get(daily_key, 0) + 1
        self.free_tier_usage['monthly'][monthly_key] = self.free_tier_usage['monthly'].get(monthly_key, 0) + 1
        
        # Save updated usage
        self._save_free_tier_usage()
    
    def _save_spending_record(self, record: SpendingRecord):
        """Save spending record to disk."""
        current_month = datetime.now().strftime("%Y-%m")
        history_file = self.data_dir / f"spending_{current_month}.jsonl"
        
        try:
            with open(history_file, 'a') as f:
                data = {
                    'timestamp': record.timestamp.isoformat(),
                    'provider': record.provider,
                    'category': record.category.value,
                    'operation': record.operation,
                    'cost': record.cost,
                    'project_id': record.project_id,
                    'asset_id': record.asset_id,
                    'details': record.details
                }
                f.write(json.dumps(data) + '\n')
        except Exception as e:
            logger.error(f"Failed to save spending record: {e}")
    
    def _save_free_tier_usage(self):
        """Save free tier usage to disk."""
        usage_file = self.data_dir / "free_tier_usage.json"
        try:
            with open(usage_file, 'w') as f:
                json.dump(self.free_tier_usage, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save free tier usage: {e}")
    
    def _check_budget_alerts(self):
        """Check if any budget alerts should be triggered."""
        if not self.budgets:
            return
        
        # Calculate current spending
        spending = self.get_spending_summary()
        
        for period, limit in self.budgets.items():
            if period not in spending:
                continue
            
            current = spending[period]['total']
            threshold = self.budget_alerts.get(period, 0.8)  # Default 80% alert
            
            if current >= limit * threshold:
                percentage = (current / limit) * 100
                logger.warning(
                    f"Budget alert: {period} spending at {percentage:.1f}% "
                    f"(${current:.2f} of ${limit:.2f})"
                )
    
    def set_budget(self, period: str, limit: float, alert_threshold: float = 0.8):
        """Set a budget limit.
        
        Args:
            period: Budget period ('daily', 'weekly', 'monthly', 'total')
            limit: Budget limit in dollars
            alert_threshold: Alert when spending reaches this fraction (0-1)
        """
        self.budgets[period] = limit
        self.budget_alerts[period] = alert_threshold
        
        # Save budgets
        budget_file = self.data_dir / "budgets.json"
        try:
            with open(budget_file, 'w') as f:
                json.dump({
                    'limits': self.budgets,
                    'alerts': self.budget_alerts
                }, f, indent=2)
            
            logger.info(f"Set {period} budget: ${limit:.2f} (alert at {alert_threshold*100:.0f}%)")
        except Exception as e:
            logger.error(f"Failed to save budgets: {e}")
    
    def get_spending_summary(self, days: int = 30) -> Dict[str, Dict[str, Any]]:
        """Get spending summary for different time periods.
        
        Args:
            days: Number of days to include in analysis
            
        Returns:
            Summary with daily, weekly, monthly, and total spending
        """
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=days)
        
        # Filter recent records
        recent_records = [r for r in self.spending_records if r.timestamp >= cutoff]
        
        # Initialize summaries
        summary = {
            'daily': {'total': 0.0, 'by_provider': defaultdict(float), 'by_category': defaultdict(float)},
            'weekly': {'total': 0.0, 'by_provider': defaultdict(float), 'by_category': defaultdict(float)},
            'monthly': {'total': 0.0, 'by_provider': defaultdict(float), 'by_category': defaultdict(float)},
            'total': {'total': 0.0, 'by_provider': defaultdict(float), 'by_category': defaultdict(float)}
        }
        
        # Time boundaries
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())
        month_start = today_start.replace(day=1)
        
        # Aggregate spending
        for record in recent_records:
            # Always add to total
            summary['total']['total'] += record.cost
            summary['total']['by_provider'][record.provider] += record.cost
            summary['total']['by_category'][record.category.value] += record.cost
            
            # Check time periods
            if record.timestamp >= today_start:
                summary['daily']['total'] += record.cost
                summary['daily']['by_provider'][record.provider] += record.cost
                summary['daily']['by_category'][record.category.value] += record.cost
            
            if record.timestamp >= week_start:
                summary['weekly']['total'] += record.cost
                summary['weekly']['by_provider'][record.provider] += record.cost
                summary['weekly']['by_category'][record.category.value] += record.cost
            
            if record.timestamp >= month_start:
                summary['monthly']['total'] += record.cost
                summary['monthly']['by_provider'][record.provider] += record.cost
                summary['monthly']['by_category'][record.category.value] += record.cost
        
        # Convert defaultdicts to regular dicts
        for period in summary:
            summary[period]['by_provider'] = dict(summary[period]['by_provider'])
            summary[period]['by_category'] = dict(summary[period]['by_category'])
            
            # Add budget info if available
            if period in self.budgets:
                budget = self.budgets[period]
                spent = summary[period]['total']
                summary[period]['budget'] = budget
                summary[period]['remaining'] = max(0, budget - spent)
                summary[period]['utilization'] = (spent / budget * 100) if budget > 0 else 0
        
        return summary
    
    def get_provider_comparison(self, category: Optional[CostCategory] = None) -> List[Dict[str, Any]]:
        """Compare providers by cost and usage.
        
        Args:
            category: Filter by category (all if None)
            
        Returns:
            List of provider comparisons sorted by cost efficiency
        """
        comparisons = []
        
        # Get spending by provider
        spending = self.get_spending_summary()
        provider_spending = spending['total']['by_provider']
        
        for provider_name, pricing in self.pricing.items():
            if category and pricing.category != category:
                continue
            
            # Calculate metrics
            total_spent = provider_spending.get(provider_name, 0)
            request_count = len([r for r in self.spending_records if r.provider == provider_name])
            avg_cost = total_spent / request_count if request_count > 0 else 0
            
            comparison = {
                'provider': provider_name,
                'category': pricing.category.value,
                'total_spent': total_spent,
                'request_count': request_count,
                'average_cost': avg_cost,
                'pricing_model': self._get_pricing_model_description(pricing),
                'free_tier': self._get_free_tier_description(pricing),
                'notes': pricing.notes
            }
            
            # Add cost estimate for standard operation
            if pricing.category == CostCategory.UNDERSTANDING:
                estimate = self.estimate_cost(provider_name, "analyze_image", detailed=False)
                comparison['typical_cost'] = estimate.likely_cost
            elif pricing.category == CostCategory.GENERATION:
                estimate = self.estimate_cost(provider_name, "generate_image")
                comparison['typical_cost'] = estimate.likely_cost
            
            comparisons.append(comparison)
        
        # Sort by total spent (most used first)
        comparisons.sort(key=lambda x: x['total_spent'], reverse=True)
        
        return comparisons
    
    def _get_pricing_model_description(self, pricing: ProviderPricing) -> str:
        """Get human-readable pricing model description."""
        if pricing.per_request is not None:
            return f"${pricing.per_request:.4f} per request"
        elif pricing.per_token_input is not None:
            input_per_million = pricing.per_token_input * 1_000_000
            output_per_million = pricing.per_token_output * 1_000_000
            return f"${input_per_million:.2f}/${output_per_million:.2f} per million tokens (in/out)"
        elif pricing.per_second is not None:
            return f"${pricing.per_second:.2f} per second"
        elif pricing.per_megapixel is not None:
            return f"${pricing.per_megapixel:.4f} per megapixel"
        else:
            return "Custom pricing"
    
    def _get_free_tier_description(self, pricing: ProviderPricing) -> str:
        """Get human-readable free tier description."""
        parts = []
        if pricing.free_requests_daily > 0:
            parts.append(f"{pricing.free_requests_daily}/day")
        if pricing.free_requests_monthly > 0:
            parts.append(f"{pricing.free_requests_monthly}/month")
        
        return " free" if parts else "No free tier"
    
    def estimate_batch_cost(
        self,
        file_count: int,
        providers: List[str],
        operation: str = "analyze_images",
        **kwargs
    ) -> Dict[str, Any]:
        """Estimate cost for processing a batch of files.
        
        Args:
            file_count: Number of files to process
            providers: List of providers to use
            operation: Operation to perform
            **kwargs: Additional parameters for estimation
            
        Returns:
            Batch cost estimate with breakdown
        """
        total_min = 0
        total_max = 0
        total_likely = 0
        breakdown = {}
        
        for provider in providers:
            estimate = self.estimate_cost(provider, operation, image_count=file_count, **kwargs)
            
            total_min += estimate.min_cost
            total_max += estimate.max_cost
            total_likely += estimate.likely_cost
            
            breakdown[provider] = {
                'count': file_count,
                'per_item': estimate.likely_cost / file_count if file_count > 0 else 0,
                'total': estimate.likely_cost,
                'range': estimate.formatted_range
            }
        
        # Check budget
        budget_warnings = []
        if self.budgets:
            for period, limit in self.budgets.items():
                current = self.get_spending_summary()[period]['total']
                if current + total_likely > limit:
                    budget_warnings.append(
                        f"{period.capitalize()} budget would be exceeded "
                        f"(${current + total_likely:.2f} > ${limit:.2f})"
                    )
        
        return {
            'file_count': file_count,
            'providers': providers,
            'total_cost': {
                'min': total_min,
                'max': total_max,
                'likely': total_likely,
                'formatted': f"${total_likely:.2f}"
            },
            'breakdown': breakdown,
            'budget_warnings': budget_warnings,
            'proceed': len(budget_warnings) == 0
        }
    
    def format_cost_report(self) -> str:
        """Generate a formatted cost report."""
        lines = []
        lines.append("=== AliceMultiverse Cost Report ===\n")
        
        # Get spending summary
        summary = self.get_spending_summary()
        
        # Overall spending
        lines.append("📊 Spending Summary:")
        for period in ['daily', 'weekly', 'monthly', 'total']:
            if period in summary:
                data = summary[period]
                line = f"  {period.capitalize()}: ${data['total']:.2f}"
                
                if 'budget' in data:
                    line += f" / ${data['budget']:.2f} ({data['utilization']:.1f}%)"
                
                lines.append(line)
        
        lines.append("")
        
        # Top providers
        lines.append("🏆 Top Providers by Spending:")
        total_by_provider = summary['total']['by_provider']
        top_providers = sorted(total_by_provider.items(), key=lambda x: x[1], reverse=True)[:5]
        
        for provider, amount in top_providers:
            lines.append(f"  {provider}: ${amount:.2f}")
        
        lines.append("")
        
        # Category breakdown
        lines.append("📂 Spending by Category:")
        total_by_category = summary['total']['by_category']
        
        for category, amount in sorted(total_by_category.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {category}: ${amount:.2f}")
        
        lines.append("")
        
        # Budget alerts
        if self.budgets:
            lines.append("⚠️  Budget Status:")
            for period, limit in self.budgets.items():
                if period in summary:
                    summary[period]['total']
                    remaining = summary[period]['remaining']
                    utilization = summary[period]['utilization']
                    
                    if utilization >= 90:
                        emoji = "🔴"
                    elif utilization >= 70:
                        emoji = "🟡"
                    else:
                        emoji = "🟢"
                    
                    lines.append(
                        f"  {emoji} {period.capitalize()}: "
                        f"${remaining:.2f} remaining ({utilization:.1f}% used)"
                    )
        
        lines.append("")
        
        # Recommendations
        lines.append("💡 Cost Optimization Tips:")
        
        # Find most expensive provider
        if top_providers:
            most_expensive = top_providers[0][0]
            alternatives = self._find_alternatives(
                most_expensive,
                self.pricing[most_expensive].category if most_expensive in self.pricing else CostCategory.OTHER,
                1.0
            )
            
            if alternatives:
                alt = alternatives[0]
                lines.append(
                    f"  • Consider {alt['provider']} instead of {most_expensive} "
                    f"(save ~{alt['savings_percent']:.0f}%)"
                )
        
        # Check for providers with free tiers
        free_tier_providers = [
            p for p, pricing in self.pricing.items()
            if pricing.free_requests_daily > 0 or pricing.free_requests_monthly > 0
        ]
        
        if free_tier_providers:
            lines.append(f"  • Use free tiers: {', '.join(free_tier_providers[:3])}")
        
        return '\n'.join(lines)


# Global cost tracker instance
_cost_tracker: Optional[CostTracker] = None


def get_cost_tracker() -> CostTracker:
    """Get global cost tracker instance."""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker


def estimate_cost(provider: str, operation: str, **kwargs) -> CostEstimate:
    """Convenience function to estimate cost."""
    return get_cost_tracker().estimate_cost(provider, operation, **kwargs)


def record_cost(provider: str, operation: str, cost: float, **kwargs):
    """Convenience function to record cost."""
    get_cost_tracker().record_cost(provider, operation, cost, **kwargs)