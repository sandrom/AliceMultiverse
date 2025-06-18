"""Tests for workflow system."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from alicemultiverse.providers.types import GenerationResult
from alicemultiverse.workflows import (
    WorkflowContext,
    WorkflowExecutor,
    WorkflowStatus,
    WorkflowStep,
    WorkflowTemplate,
    get_workflow,
    list_workflows,
)
from alicemultiverse.workflows.base import StepStatus
from alicemultiverse.workflows.templates.image_enhancement import ImageEnhancementWorkflow


class SimpleTestWorkflow(WorkflowTemplate):
    """Simple workflow for testing."""

    def define_steps(self, context: WorkflowContext):
        return [
            WorkflowStep(
                name="step1",
                provider="leonardo",
                operation="generate",
                parameters={"width": 512, "height": 512}
            ),
            WorkflowStep(
                name="step2",
                provider="magnific",
                operation="upscale",
                parameters={"scale": 2},
                condition="previous.success"
            ),
        ]


class TestWorkflowContext:
    """Test WorkflowContext functionality."""

    def test_context_initialization(self):
        """Test context initialization."""
        context = WorkflowContext(
            initial_prompt="Test prompt",
            initial_params={"param1": "value1"}
        )

        assert context.initial_prompt == "Test prompt"
        assert context.initial_params["param1"] == "value1"
        assert context.total_cost == 0.0
        assert len(context.steps) == 0
        assert len(context.results) == 0

    def test_get_previous_result(self):
        """Test getting previous results."""
        context = WorkflowContext(initial_prompt="Test")

        # No results yet
        assert context.get_previous_result() is None

        # Add a result
        result1 = GenerationResult(success=True, file_path=Path("test1.png"))
        context.results["step1"] = result1

        assert context.get_previous_result() == result1
        assert context.get_previous_result("step1") == result1

        # Add another result
        result2 = GenerationResult(success=True, file_path=Path("test2.png"))
        context.results["step2"] = result2

        # Should get the last one
        assert context.get_previous_result() == result2

    def test_file_management(self):
        """Test file path management."""
        context = WorkflowContext(initial_prompt="Test")

        # Set and get files
        path1 = Path("output1.png")
        context.set_file("output1", path1)
        assert context.get_file("output1") == path1

        # Add temp file
        temp_path = Path("temp.png")
        context.add_temp_file(temp_path)
        assert temp_path in context.temp_files

    def test_condition_evaluation(self):
        """Test condition evaluation."""
        context = WorkflowContext(initial_prompt="Test")

        # No condition
        assert context.evaluate_condition("") is True
        assert context.evaluate_condition(None) is True

        # Previous success - no previous result
        assert context.evaluate_condition("previous.success") is False

        # Add successful result
        context.results["step1"] = GenerationResult(success=True)
        assert context.evaluate_condition("previous.success") is True

        # Specific step success
        step = WorkflowStep(name="step1", provider="test", status=StepStatus.COMPLETED)
        context.steps["step1"] = step
        assert context.evaluate_condition("step1.success") is True
        assert context.evaluate_condition("step2.success") is False

        # Cost conditions
        context.total_cost = 5.0
        assert context.evaluate_condition("cost < 10") is True
        assert context.evaluate_condition("cost > 2") is True
        assert context.evaluate_condition("cost < 2") is False


class TestWorkflowStep:
    """Test WorkflowStep functionality."""

    def test_step_initialization(self):
        """Test step initialization."""
        step = WorkflowStep(
            name="test_step",
            provider="leonardo",
            operation="generate",
            parameters={"model": "phoenix"},
            cost_limit=0.10
        )

        assert step.name == "test_step"
        assert step.provider == "leonardo"
        assert step.operation == "generate"
        assert step.parameters["model"] == "phoenix"
        assert step.cost_limit == 0.10
        assert step.status == StepStatus.PENDING
        assert step.retry_count == 3
        assert step.timeout == 300.0


class TestWorkflowTemplate:
    """Test WorkflowTemplate functionality."""

    def test_template_basics(self):
        """Test basic template functionality."""
        workflow = SimpleTestWorkflow()

        assert workflow.name == "SimpleTestWorkflow"
        assert workflow.get_description() == "Simple workflow for testing."

        # Get required providers
        providers = workflow.get_required_providers()
        assert "leonardo" in providers
        assert "magnific" in providers

    def test_validation(self):
        """Test workflow validation."""
        workflow = SimpleTestWorkflow()
        context = WorkflowContext(initial_prompt="Test")

        errors = workflow.validate(context)
        assert len(errors) == 0

        # Test with no prompt
        context_no_prompt = WorkflowContext(initial_prompt="")
        errors = workflow.validate(context_no_prompt)
        assert len(errors) == 1
        assert "prompt is required" in errors[0]

    def test_cost_estimation(self):
        """Test cost estimation."""
        workflow = SimpleTestWorkflow()
        context = WorkflowContext(initial_prompt="Test")

        cost = workflow.estimate_cost(context)
        assert cost > 0
        assert cost < 1.0  # Reasonable estimate

    def test_cleanup(self):
        """Test cleanup functionality."""
        workflow = SimpleTestWorkflow()
        context = WorkflowContext(initial_prompt="Test")

        # Create a fake temp file
        temp_file = Path("/tmp/test_workflow_temp.png")
        temp_file.write_text("test")
        context.add_temp_file(temp_file)

        # Cleanup should remove it
        workflow.cleanup(context)
        assert not temp_file.exists()


class TestWorkflowExecutor:
    """Test WorkflowExecutor functionality."""

    @pytest.fixture
    def executor(self):
        """Create executor instance."""
        return WorkflowExecutor()

    @pytest.fixture
    def mock_provider(self):
        """Create mock provider."""
        provider = AsyncMock()
        provider.name = "test_provider"
        provider.estimate_cost = MagicMock(return_value=0.05)
        provider.generate = AsyncMock(
            return_value=GenerationResult(
                success=True,
                file_path=Path("output.png"),
                cost=0.05,
                generation_time=5.0
            )
        )
        return provider

    @pytest.mark.asyncio
    async def test_execute_simple_workflow(self, executor, mock_provider):
        """Test executing a simple workflow."""
        with patch("alicemultiverse.workflows.executor.get_provider_async", return_value=mock_provider):
            workflow = SimpleTestWorkflow()

            result = await executor.execute(
                workflow=workflow,
                initial_prompt="Test prompt",
                parameters={"width": 512}
            )

            assert result.workflow_name == "SimpleTestWorkflow"
            assert result.status == WorkflowStatus.COMPLETED
            assert result.completed_steps == 2
            assert result.total_steps == 2
            assert result.total_cost > 0
            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_with_failed_step(self, executor):
        """Test workflow with a failed step."""
        # Mock provider that fails
        mock_provider = AsyncMock()
        mock_provider.name = "test_provider"
        mock_provider.estimate_cost = MagicMock(return_value=0.05)
        mock_provider.generate = AsyncMock(
            return_value=GenerationResult(
                success=False,
                error="Test error"
            )
        )

        with patch("alicemultiverse.workflows.executor.get_provider_async", return_value=mock_provider):
            workflow = SimpleTestWorkflow()

            result = await executor.execute(
                workflow=workflow,
                initial_prompt="Test prompt"
            )

            assert result.status == WorkflowStatus.FAILED
            assert result.completed_steps == 0
            assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_execute_with_condition(self, executor, mock_provider):
        """Test workflow with conditional steps."""
        # First step succeeds
        mock_provider.generate = AsyncMock(
            side_effect=[
                GenerationResult(success=True, file_path=Path("step1.png"), cost=0.05),
                GenerationResult(success=True, file_path=Path("step2.png"), cost=0.10),
            ]
        )

        with patch("alicemultiverse.workflows.executor.get_provider_async", return_value=mock_provider):
            workflow = SimpleTestWorkflow()

            result = await executor.execute(
                workflow=workflow,
                initial_prompt="Test prompt"
            )

            assert result.completed_steps == 2
            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_dry_run(self, executor, mock_provider):
        """Test dry run execution."""
        with patch("alicemultiverse.workflows.executor.get_provider_async", return_value=mock_provider):
            workflow = SimpleTestWorkflow()

            result = await executor.execute(
                workflow=workflow,
                initial_prompt="Test prompt",
                dry_run=True
            )

            assert result.status == WorkflowStatus.COMPLETED
            assert result.completed_steps == 0  # No actual execution
            assert result.total_cost > 0  # Cost estimated
            assert "Dry run" in result.errors[0]

    @pytest.mark.asyncio
    async def test_execute_with_budget_limit(self, executor):
        """Test workflow with budget limit."""
        # Mock expensive provider
        mock_provider = AsyncMock()
        mock_provider.name = "test_provider"
        mock_provider.estimate_cost = MagicMock(return_value=0.50)
        mock_provider.generate = AsyncMock(
            return_value=GenerationResult(
                success=True,
                file_path=Path("output.png"),
                cost=0.50
            )
        )

        with patch("alicemultiverse.workflows.executor.get_provider_async", return_value=mock_provider):
            workflow = SimpleTestWorkflow()

            result = await executor.execute(
                workflow=workflow,
                initial_prompt="Test prompt",
                budget_limit=0.30  # Less than first step cost
            )

            # Should stop after budget exceeded
            assert result.completed_steps < result.total_steps
            assert "Budget limit" in " ".join(result.errors)


class TestWorkflowRegistry:
    """Test workflow registry functionality."""

    def test_get_workflow(self):
        """Test getting workflows from registry."""
        # Should have built-in workflows
        # Workflow API changed - needs update
        assert workflow is not None
        assert isinstance(workflow, ImageEnhancementWorkflow)

        # Test alias
        # Workflow API changed - needs update
        assert workflow is not None
        assert isinstance(workflow, ImageEnhancementWorkflow)

        # Non-existent workflow
        # Workflow API changed - needs update
        assert workflow is None

    def test_list_workflows(self):
        """Test listing workflows."""
        workflows = []  # API changed

        assert len(workflows) > 0
        assert "image_enhancement" in workflows
        assert "video_production" in workflows
        assert "style_transfer" in workflows


class TestImageEnhancementWorkflow:
    """Test the image enhancement workflow template."""

    def test_define_steps_basic(self):
        """Test basic step definition."""
        workflow = ImageEnhancementWorkflow()
        context = WorkflowContext(
            initial_prompt="Beautiful landscape",
            initial_params={}
        )

        steps = workflow.define_steps(context)

        # Should have at least initial generation, upscale, and final output
        assert len(steps) >= 3
        assert steps[0].name == "initial_generation"
        assert steps[1].name == "upscale"
        assert steps[-1].name == "final_output"

    def test_define_steps_with_variations(self):
        """Test step definition with variations."""
        workflow = ImageEnhancementWorkflow()
        context = WorkflowContext(
            initial_prompt="Beautiful landscape",
            initial_params={
                "generate_variations": True,
                "variation_count": 3
            }
        )

        steps = workflow.define_steps(context)

        # Should have variations
        variation_steps = [s for s in steps if s.name.startswith("variation_")]
        assert len(variation_steps) == 3

    def test_cost_estimation(self):
        """Test workflow cost estimation."""
        workflow = ImageEnhancementWorkflow()
        context = WorkflowContext(
            initial_prompt="Test",
            initial_params={
                "initial_provider": "leonardo",
                "upscale_provider": "magnific",
                "generate_variations": True,
                "variation_count": 2
            }
        )

        cost = workflow.estimate_cost(context)

        # Should include initial + upscale + variations
        assert cost > 0.10  # At least initial + upscale
        assert cost < 0.50  # Reasonable upper bound
