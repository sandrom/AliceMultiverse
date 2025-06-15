"""Cost management MCP tools."""

import logging
from datetime import datetime, timedelta
from typing import Any

from mcp import Server

from ...core.cost_tracker import get_cost_tracker
from ..base import (
    ValidationError,
    create_tool_response,
    handle_errors,
    validate_positive_int,
)

logger = logging.getLogger(__name__)


def register_cost_tools(server: Server) -> None:
    """Register all cost management tools with the MCP server.
    
    Args:
        server: MCP server instance
    """

    @server.tool()
    @handle_errors
    async def estimate_cost(
        operation: str,
        provider: str | None = None,
        model: str | None = None,
        count: int = 1,
        parameters: dict[str, Any] | None = None
    ) -> Any:
        """Estimate cost for an operation.
        
        Args:
            operation: Type of operation (analyze, generate, etc.)
            provider: Provider name
            model: Model name
            count: Number of items
            parameters: Additional parameters
            
        Returns:
            Cost estimate
        """
        # Validate inputs
        count = validate_positive_int(count, "count")

        # Get cost tracker
        tracker = get_cost_tracker()

        # Estimate based on operation type
        if operation == "analyze":
            # Image analysis cost
            if not provider:
                # Estimate for cheapest provider
                provider = "anthropic"  # Claude Haiku is typically cheapest
                model = "claude-3-haiku"

            # Base cost per image
            base_costs = {
                "openai": 0.01,
                "anthropic": 0.004,
                "google": 0.002,
                "ollama": 0.0,  # Free local models
            }

            cost_per_item = base_costs.get(provider, 0.01)
            total_cost = cost_per_item * count

        elif operation == "generate":
            # Generation cost
            if not provider:
                provider = "openai"
                model = "dall-e-3"

            # Rough estimates
            if provider == "openai" and model == "dall-e-3":
                cost_per_item = 0.04  # Standard quality
                if parameters and parameters.get("quality") == "hd":
                    cost_per_item = 0.08
            else:
                cost_per_item = 0.02  # Default estimate

            total_cost = cost_per_item * count

        else:
            raise ValidationError(f"Unknown operation: {operation}")

        return create_tool_response(
            success=True,
            data={
                "operation": operation,
                "provider": provider,
                "model": model,
                "count": count,
                "cost_per_item": cost_per_item,
                "total_cost": total_cost,
                "currency": "USD"
            }
        )

    @server.tool()
    @handle_errors
    async def get_spending_report(
        days: int = 7,
        group_by: str = "provider"
    ) -> Any:
        """Get spending report for the specified period.
        
        Args:
            days: Number of days to include
            group_by: How to group costs (provider, model, operation)
            
        Returns:
            Spending report
        """
        # Validate inputs
        days = validate_positive_int(days, "days")
        if group_by not in ["provider", "model", "operation", "date"]:
            raise ValidationError(
                "group_by must be one of: provider, model, operation, date"
            )

        # Get cost tracker
        tracker = get_cost_tracker()

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Get spending data
        total_spent = tracker.get_total_cost(start_date, end_date)
        breakdown = tracker.get_cost_breakdown(
            start_date, end_date, group_by=group_by
        )

        # Get current budget info
        budget_info = tracker.get_budget_status()

        # Format report
        report = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "total_spent": round(total_spent, 2),
            "breakdown": {k: round(v, 2) for k, v in breakdown.items()},
            "budget": {
                "daily_limit": budget_info.get("daily_limit"),
                "monthly_limit": budget_info.get("monthly_limit"),
                "daily_used": round(budget_info.get("daily_used", 0), 2),
                "monthly_used": round(budget_info.get("monthly_used", 0), 2),
            },
            "currency": "USD"
        }

        # Add warnings if approaching limits
        warnings = []
        if budget_info.get("daily_limit"):
            daily_percent = (budget_info["daily_used"] / budget_info["daily_limit"]) * 100
            if daily_percent > 80:
                warnings.append(f"Daily spending at {daily_percent:.0f}% of limit")

        if budget_info.get("monthly_limit"):
            monthly_percent = (budget_info["monthly_used"] / budget_info["monthly_limit"]) * 100
            if monthly_percent > 80:
                warnings.append(f"Monthly spending at {monthly_percent:.0f}% of limit")

        if warnings:
            report["warnings"] = warnings

        return create_tool_response(success=True, data=report)

    @server.tool()
    @handle_errors
    async def set_budget(
        daily_limit: float | None = None,
        monthly_limit: float | None = None
    ) -> Any:
        """Set spending budget limits.
        
        Args:
            daily_limit: Daily spending limit in USD
            monthly_limit: Monthly spending limit in USD
            
        Returns:
            Updated budget configuration
        """
        # Validate inputs
        if daily_limit is not None and daily_limit <= 0:
            raise ValidationError("daily_limit must be positive")
        if monthly_limit is not None and monthly_limit <= 0:
            raise ValidationError("monthly_limit must be positive")

        if daily_limit is None and monthly_limit is None:
            raise ValidationError("At least one limit must be specified")

        # Get cost tracker
        tracker = get_cost_tracker()

        # Update limits
        if daily_limit is not None:
            tracker.set_daily_limit(daily_limit)
        if monthly_limit is not None:
            tracker.set_monthly_limit(monthly_limit)

        # Get updated status
        status = tracker.get_budget_status()

        return create_tool_response(
            success=True,
            data={
                "daily_limit": status.get("daily_limit"),
                "monthly_limit": status.get("monthly_limit"),
                "daily_used": round(status.get("daily_used", 0), 2),
                "monthly_used": round(status.get("monthly_used", 0), 2),
                "currency": "USD"
            },
            message="Budget limits updated successfully"
        )
