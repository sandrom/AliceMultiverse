"""Workflow executor for running multi-step AI workflows."""

import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from alicemultiverse.events import publish_event
from alicemultiverse.events.workflow_events import (
    WorkflowCompletedEvent,
    WorkflowFailedEvent,
    WorkflowStartedEvent,
    WorkflowStepCompletedEvent,
    WorkflowStepStartedEvent,
)
# Provider functionality not yet implemented
# from alicemultiverse.providers.registry import get_provider_async
from alicemultiverse.providers.provider_types import GenerationRequest, GenerationType

from .base import (
    StepStatus,
    WorkflowContext,
    WorkflowResult,
    WorkflowStatus,
    WorkflowStep,
    WorkflowTemplate,
)

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """Executes workflow templates with state management and error handling."""

    def __init__(self):
        """Initialize workflow executor."""
        self._running_workflows: dict[str, WorkflowContext] = {}

    async def execute(
        self,
        workflow: WorkflowTemplate,
        initial_prompt: str,
        parameters: dict[str, Any] | None = None,
        budget_limit: float | None = None,
        dry_run: bool = False
    ) -> WorkflowResult:
        """Execute a workflow template.
        
        Args:
            workflow: Workflow template to execute
            initial_prompt: Initial prompt for the workflow
            parameters: Additional parameters
            budget_limit: Maximum budget for the workflow
            dry_run: If True, only estimate costs without executing
            
        Returns:
            Workflow execution result
        """
        # Create context
        context = WorkflowContext(
            initial_prompt=initial_prompt,
            initial_params=parameters or {},
            start_time=datetime.now()
        )

        # Validate workflow
        errors = workflow.validate(context)
        if errors:
            return WorkflowResult(
                workflow_name=workflow.name,
                status=WorkflowStatus.FAILED,
                context=context,
                total_cost=0.0,
                execution_time=0.0,
                completed_steps=0,
                total_steps=0,
                errors=errors
            )

        # Get steps
        steps = workflow.define_steps(context)
        total_steps = len(steps)

        # Store workflow
        workflow_id = f"{workflow.name}_{int(time.time())}"
        self._running_workflows[workflow_id] = context

        # Publish start event
        await self._publish_workflow_started(workflow.name, workflow_id, total_steps)

        # Execute workflow
        try:
            if dry_run:
                # Just estimate costs
                total_cost = await self._estimate_workflow_cost(steps, context)
                return WorkflowResult(
                    workflow_name=workflow.name,
                    status=WorkflowStatus.COMPLETED,
                    context=context,
                    total_cost=total_cost,
                    execution_time=0.0,
                    completed_steps=0,
                    total_steps=total_steps,
                    errors=["Dry run - no actual execution"]
                )

            # Execute steps
            completed_steps = 0
            errors = []

            for i, step in enumerate(steps):
                logger.info(f"Executing step {i+1}/{total_steps}: {step.name}")

                # Check condition
                if step.condition and not context.evaluate_condition(step.condition):
                    logger.info(f"Skipping step {step.name} - condition not met: {step.condition}")
                    step.status = StepStatus.SKIPPED
                    continue

                # Check budget
                if budget_limit and context.total_cost >= budget_limit:
                    error = f"Budget limit ${budget_limit:.2f} exceeded at step {step.name}"
                    logger.warning(error)
                    errors.append(error)
                    break

                # Execute step
                try:
                    await self._execute_step(step, context, workflow_id)
                    completed_steps += 1

                    # Check step cost limit
                    if step.cost_limit and step.cost > step.cost_limit:
                        logger.warning(
                            f"Step {step.name} cost ${step.cost:.3f} "
                            f"exceeded limit ${step.cost_limit:.3f}"
                        )

                except Exception as e:
                    error = f"Step {step.name} failed: {e!s}"
                    logger.error(error, exc_info=True)
                    errors.append(error)
                    step.status = StepStatus.FAILED
                    step.error = str(e)

                    # Determine if we should continue
                    if i < total_steps - 1:  # Not the last step
                        logger.info("Continuing workflow despite step failure")
                    else:
                        break

            # Determine final status
            if completed_steps == total_steps:
                status = WorkflowStatus.COMPLETED
            elif completed_steps > 0:
                status = WorkflowStatus.COMPLETED  # Partial success
            else:
                status = WorkflowStatus.FAILED

            # Get final outputs
            final_outputs = self._get_final_outputs(context)

            # Calculate execution time
            context.end_time = datetime.now()
            execution_time = (context.end_time - context.start_time).total_seconds()

            # Create result
            result = WorkflowResult(
                workflow_name=workflow.name,
                status=status,
                context=context,
                total_cost=context.total_cost,
                execution_time=execution_time,
                completed_steps=completed_steps,
                total_steps=total_steps,
                final_outputs=final_outputs,
                errors=errors
            )

            # Publish completion event
            await self._publish_workflow_completed(workflow.name, workflow_id, result)

            return result

        except Exception as e:
            logger.error(f"Workflow {workflow.name} failed: {e}", exc_info=True)

            # Publish failure event
            await self._publish_workflow_failed(workflow.name, workflow_id, str(e))

            return WorkflowResult(
                workflow_name=workflow.name,
                status=WorkflowStatus.FAILED,
                context=context,
                total_cost=context.total_cost,
                execution_time=time.time() - context.start_time.timestamp(),
                completed_steps=0,
                total_steps=total_steps,
                errors=[str(e)]
            )
        finally:
            # Cleanup
            workflow.cleanup(context)
            self._running_workflows.pop(workflow_id, None)

    async def _execute_step(
        self,
        step: WorkflowStep,
        context: WorkflowContext,
        workflow_id: str
    ):
        """Execute a single workflow step.
        
        Args:
            step: Step to execute
            context: Workflow context
            workflow_id: Workflow identifier
        """
        step.start_time = datetime.now()
        step.status = StepStatus.RUNNING
        context.steps[step.name] = step

        # Publish step started event
        await self._publish_step_started(workflow_id, step.name)

        try:
            # Provider functionality not yet implemented
            logger.warning(f"Step {step.name} cannot execute - provider functionality not implemented")
            
            # Mark step as failed
            step.status = StepStatus.FAILED
            step.error = "Provider functionality not yet implemented"
            
            # Create minimal result for compatibility
            class MinimalResult:
                success = False
                error = "Provider functionality not yet implemented"
                cost = 0.0
                file_path = None
            
            result = MinimalResult()
            step.result = result
            context.results[step.name] = result

            # Publish step completed event
            await self._publish_step_completed(workflow_id, step.name, result)

        finally:
            step.end_time = datetime.now()

    def _build_request(
        self,
        step: WorkflowStep,
        context: WorkflowContext
    ) -> GenerationRequest:
        """Build generation request for a step.
        
        Args:
            step: Workflow step
            context: Workflow context
            
        Returns:
            Generation request
        """
        # Start with step parameters
        params = step.parameters.copy()

        # Add context parameters
        params.update(context.initial_params)

        # Handle input from previous step
        if "input_from" in params:
            input_step = params.pop("input_from")
            prev_result = context.get_previous_result(input_step)
            if prev_result and prev_result.file_path:
                params["input_image"] = str(prev_result.file_path)

        # Use prompt from context or parameters
        prompt = params.pop("prompt", context.initial_prompt)

        # Determine generation type
        if step.operation == "upscale":
            generation_type = GenerationType.IMAGE
        elif step.operation == "generate_video":
            generation_type = GenerationType.VIDEO
        elif step.operation == "generate_audio":
            generation_type = GenerationType.AUDIO
        else:
            generation_type = GenerationType.IMAGE

        # Extract standard parameters
        model = params.pop("model", None)
        output_format = params.pop("output_format", None)

        return GenerationRequest(
            prompt=prompt,
            generation_type=generation_type,
            model=model,
            output_format=output_format,
            parameters=params
        )

    def _is_final_step(self, step: WorkflowStep, context: WorkflowContext) -> bool:
        """Check if this is a final output step."""
        # Simple heuristic - could be made configurable
        return "final" in step.name.lower() or "output" in step.name.lower()

    def _get_final_outputs(self, context: WorkflowContext) -> list[Path]:
        """Get final output files from workflow."""
        outputs = []

        # Get outputs from steps marked as final
        for step_name, step in context.steps.items():
            if step.result and step.result.file_path and self._is_final_step(step, context):
                outputs.append(step.result.file_path)

        # If no explicit final steps, use last successful step
        if not outputs:
            for step_name in reversed(list(context.steps.keys())):
                step = context.steps[step_name]
                if step.result and step.result.file_path:
                    outputs.append(step.result.file_path)
                    break

        return outputs

    async def _estimate_workflow_cost(
        self,
        steps: list[WorkflowStep],
        context: WorkflowContext
    ) -> float:
        """Estimate total workflow cost.
        
        Args:
            steps: Workflow steps
            context: Workflow context
            
        Returns:
            Estimated total cost
        """
        total = 0.0

        for step in steps:
            # Skip conditional steps for estimation
            if step.condition:
                continue

            try:
                # Provider functionality not yet implemented
                logger.warning(f"Cannot estimate cost for step {step.name} - provider not implemented")
                # Use a default estimate
                total += 0.05
            except Exception as e:
                logger.warning(f"Could not estimate cost for step {step.name}: {e}")
                # Use a default estimate
                total += 0.05

        return total

    # Event publishing methods

    async def _publish_workflow_started(
        self,
        workflow_name: str,
        workflow_id: str,
        total_steps: int
    ):
        """Publish workflow started event."""
        event = WorkflowStartedEvent(
            workflow_name=workflow_name,
            workflow_id=workflow_id,
            total_steps=total_steps
        )
        await publish_event(event)

    async def _publish_workflow_completed(
        self,
        workflow_name: str,
        workflow_id: str,
        result: WorkflowResult
    ):
        """Publish workflow completed event."""
        event = WorkflowCompletedEvent(
            workflow_name=workflow_name,
            workflow_id=workflow_id,
            total_cost=result.total_cost,
            execution_time=result.execution_time,
            completed_steps=result.completed_steps,
            total_steps=result.total_steps
        )
        await publish_event(event)

    async def _publish_workflow_failed(
        self,
        workflow_name: str,
        workflow_id: str,
        error: str
    ):
        """Publish workflow failed event."""
        event = WorkflowFailedEvent(
            workflow_name=workflow_name,
            workflow_id=workflow_id,
            error=error
        )
        await publish_event(event)

    async def _publish_step_started(self, workflow_id: str, step_name: str):
        """Publish step started event."""
        event = WorkflowStepStartedEvent(
            workflow_id=workflow_id,
            step_name=step_name
        )
        await publish_event(event)

    async def _publish_step_completed(
        self,
        workflow_id: str,
        step_name: str,
        result: Any
    ):
        """Publish step completed event."""
        event = WorkflowStepCompletedEvent(
            workflow_id=workflow_id,
            step_name=step_name,
            success=result.success if hasattr(result, "success") else True,
            cost=result.cost if hasattr(result, "cost") else 0.0
        )
        await publish_event(event)
