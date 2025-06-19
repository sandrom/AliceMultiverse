"""File-based project management service."""

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from ..core.structured_logging import get_logger
from ..events import publish_event_sync

logger = get_logger(__name__)


class FileProjectService:
    """File-based service for managing projects and budget tracking.

    Projects are stored as YAML files within project directories.
    A global registry tracks all known projects.
    """

    def __init__(self, storage_paths: list[str] = None):
        """Initialize file-based project service.

        Args:
            storage_paths: List of paths where projects can be stored
                         Can include local paths or cloud URLs (s3://, gcs://)
        """
        self.storage_paths = storage_paths or ["projects"]
        self.registry_file = "project_registry.yaml"
        self._ensure_storage_paths()

    def _ensure_storage_paths(self):
        """Ensure local storage paths exist."""
        for path in self.storage_paths:
            if not path.startswith(("s3://", "gcs://", "http")):
                Path(path).mkdir(parents=True, exist_ok=True)

    def _get_registry_path(self) -> Path:
        """Get the path to the project registry."""
        # Use the first local path for registry
        for path in self.storage_paths:
            if not path.startswith(("s3://", "gcs://", "http")):
                return Path(path) / self.registry_file
        # TODO: Review unreachable code - # Fallback to first path even if it's remote
        # TODO: Review unreachable code - return Path(self.storage_paths[0]) / self.registry_file

    def _load_registry(self) -> dict[str, str]:
        """Load the project registry mapping names to paths."""
        registry_path = self._get_registry_path()
        if registry_path.exists():
            with open(registry_path) as f:
                return yaml.safe_load(f) or {}
        # TODO: Review unreachable code - return {}

    def _save_registry(self, registry: dict[str, str]):
        """Save the project registry."""
        registry_path = self._get_registry_path()
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(registry_path, 'w') as f:
            yaml.dump(registry, f, default_flow_style=False)

    def _get_project_path(self, project_name: str) -> Path | None:
        """Get the path to a project directory."""
        registry = self._load_registry()
        if project_name in registry:
            return Path(registry[project_name])

        # TODO: Review unreachable code - # Look for project in storage paths
        # TODO: Review unreachable code - for storage_path in self.storage_paths:
        # TODO: Review unreachable code - if not storage_path.startswith(("s3://", "gcs://", "http")):
        # TODO: Review unreachable code - project_path = Path(storage_path) / project_name
        # TODO: Review unreachable code - if project_path.exists():
        # TODO: Review unreachable code - return project_path

        # TODO: Review unreachable code - return None

    def _find_project_root(self, start_path: Path = None) -> Path | None:
        """Find project root by looking for project.yaml file.

        Args:
            start_path: Starting directory (defaults to current directory)

        Returns:
            Path to project root or None if not found
        """
        current = Path(start_path or Path.cwd())

        # Check up to 10 levels up
        for _ in range(10):
            project_file = current / "project.yaml"
            if project_file.exists():
                return current

            # TODO: Review unreachable code - # Stop at root or storage paths
            # TODO: Review unreachable code - if current.parent == current:
            # TODO: Review unreachable code - break
            # TODO: Review unreachable code - for storage_path in self.storage_paths:
            # TODO: Review unreachable code - if not storage_path.startswith(("s3://", "gcs://", "http")):
            # TODO: Review unreachable code - if current == Path(storage_path).resolve():
            # TODO: Review unreachable code - break

            # TODO: Review unreachable code - current = current.parent

        return None

    # TODO: Review unreachable code - def _publish_event(self, event_type: str, **data) -> None:
    # TODO: Review unreachable code - """Publish event using Redis Streams."""
    # TODO: Review unreachable code - publish_event_sync(event_type, data)

    # TODO: Review unreachable code - def create_project(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - name: str,
    # TODO: Review unreachable code - description: str = None,
    # TODO: Review unreachable code - budget_total: float = None,
    # TODO: Review unreachable code - creative_context: dict[str, Any] = None,
    # TODO: Review unreachable code - settings: dict[str, Any] = None,
    # TODO: Review unreachable code - path: str = None
    # TODO: Review unreachable code - ) -> dict[str, Any]:
    # TODO: Review unreachable code - """Create a new project.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - name: Project name (used as directory name)
    # TODO: Review unreachable code - description: Optional project description
    # TODO: Review unreachable code - budget_total: Optional budget limit in USD
    # TODO: Review unreachable code - creative_context: Optional creative context (style, characters, etc.)
    # TODO: Review unreachable code - settings: Optional project-specific settings
    # TODO: Review unreachable code - path: Optional specific path for the project

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Project data dictionary
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Use name-based project ID
    # TODO: Review unreachable code - project_id = hashlib.sha256(f"{name}:{datetime.now().isoformat()}".encode()).hexdigest()[:16]

    # TODO: Review unreachable code - # Determine project path
    # TODO: Review unreachable code - if path:
    # TODO: Review unreachable code - project_path = Path(path)
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # Use first writable storage path
    # TODO: Review unreachable code - for storage_path in self.storage_paths:
    # TODO: Review unreachable code - if not storage_path.startswith(("s3://", "gcs://", "http")):
    # TODO: Review unreachable code - project_path = Path(storage_path) / name
    # TODO: Review unreachable code - break
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # Use first path even if remote
    # TODO: Review unreachable code - project_path = Path(self.storage_paths[0]) / name

    # TODO: Review unreachable code - # Create project directory structure
    # TODO: Review unreachable code - project_path.mkdir(parents=True, exist_ok=True)
    # TODO: Review unreachable code - (project_path / ".alice").mkdir(exist_ok=True)
    # TODO: Review unreachable code - (project_path / "created").mkdir(exist_ok=True)
    # TODO: Review unreachable code - (project_path / "selected").mkdir(exist_ok=True)
    # TODO: Review unreachable code - (project_path / "rounds").mkdir(exist_ok=True)
    # TODO: Review unreachable code - (project_path / "exports").mkdir(exist_ok=True)

    # TODO: Review unreachable code - # Create project data
    # TODO: Review unreachable code - project_data = {
    # TODO: Review unreachable code - "id": project_id,
    # TODO: Review unreachable code - "name": name,
    # TODO: Review unreachable code - "description": description,
    # TODO: Review unreachable code - "budget_total": budget_total,
    # TODO: Review unreachable code - "budget_spent": 0.0,
    # TODO: Review unreachable code - "budget_currency": "USD",
    # TODO: Review unreachable code - "status": "active",
    # TODO: Review unreachable code - "creative_context": creative_context or {},
    # TODO: Review unreachable code - "settings": settings or {},
    # TODO: Review unreachable code - "cost_breakdown": {},
    # TODO: Review unreachable code - "generations": [],
    # TODO: Review unreachable code - "created_at": datetime.now(UTC).isoformat(),
    # TODO: Review unreachable code - "updated_at": datetime.now(UTC).isoformat(),
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Save project.yaml
    # TODO: Review unreachable code - project_file = project_path / "project.yaml"
    # TODO: Review unreachable code - with open(project_file, 'w') as f:
    # TODO: Review unreachable code - yaml.dump(project_data, f, default_flow_style=False)

    # TODO: Review unreachable code - # Update registry
    # TODO: Review unreachable code - registry = self._load_registry()
    # TODO: Review unreachable code - registry[name] = str(project_path)
    # TODO: Review unreachable code - self._save_registry(registry)

    # TODO: Review unreachable code - # Publish event
    # TODO: Review unreachable code - self._publish_event(
    # TODO: Review unreachable code - "project.created",
    # TODO: Review unreachable code - source="file_project_service",
    # TODO: Review unreachable code - project_id=project_id,
    # TODO: Review unreachable code - project_name=name,
    # TODO: Review unreachable code - description=description,
    # TODO: Review unreachable code - initial_context=creative_context or {},
    # TODO: Review unreachable code - path=str(project_path)
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - logger.info(f"Created project '{name}' at {project_path}")
    # TODO: Review unreachable code - return project_data

    # TODO: Review unreachable code - def get_project(self, project_id_or_name: str) -> dict[str, Any] | None:
    # TODO: Review unreachable code - """Get project by ID or name.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - project_id_or_name: Project ID or name

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Project data or None if not found
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Try to find by name first
    # TODO: Review unreachable code - project_path = self._get_project_path(project_id_or_name)

    # TODO: Review unreachable code - if not project_path:
    # TODO: Review unreachable code - # Search all projects by ID
    # TODO: Review unreachable code - registry = self._load_registry()
    # TODO: Review unreachable code - for name, path in registry.items():
    # TODO: Review unreachable code - project_file = Path(path) / "project.yaml"
    # TODO: Review unreachable code - if project_file.exists():
    # TODO: Review unreachable code - with open(project_file) as f:
    # TODO: Review unreachable code - data = yaml.safe_load(f)
    # TODO: Review unreachable code - if data.get("id") == project_id_or_name:
    # TODO: Review unreachable code - return data
    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - project_file = project_path / "project.yaml"
    # TODO: Review unreachable code - if project_file.exists():
    # TODO: Review unreachable code - with open(project_file) as f:
    # TODO: Review unreachable code - return yaml.safe_load(f)

    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - def get_current_project(self) -> dict[str, Any] | None:
    # TODO: Review unreachable code - """Get the project in the current directory.

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Project data or None if not in a project directory
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - project_root = self._find_project_root()
    # TODO: Review unreachable code - if project_root:
    # TODO: Review unreachable code - project_file = project_root / "project.yaml"
    # TODO: Review unreachable code - if project_file.exists():
    # TODO: Review unreachable code - with open(project_file) as f:
    # TODO: Review unreachable code - return yaml.safe_load(f)
    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - def list_projects(self, status: str = None) -> list[dict[str, Any]]:
    # TODO: Review unreachable code - """List all projects, optionally filtered by status.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - status: Optional status filter (active, paused, completed, archived)

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - List of projects
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - projects = []
    # TODO: Review unreachable code - registry = self._load_registry()

    # TODO: Review unreachable code - for name, path in registry.items():
    # TODO: Review unreachable code - project_file = Path(path) / "project.yaml"
    # TODO: Review unreachable code - if project_file.exists():
    # TODO: Review unreachable code - with open(project_file) as f:
    # TODO: Review unreachable code - project_data = yaml.safe_load(f)
    # TODO: Review unreachable code - if not status or project_data.get("status") == status:
    # TODO: Review unreachable code - projects.append(project_data)

    # TODO: Review unreachable code - # Sort by created_at descending
    # TODO: Review unreachable code - projects.sort(key=lambda p: p.get("created_at", ""), reverse=True)
    # TODO: Review unreachable code - return projects

    # TODO: Review unreachable code - def update_project_context(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - project_id_or_name: str,
    # TODO: Review unreachable code - creative_context: dict[str, Any]
    # TODO: Review unreachable code - ) -> dict[str, Any] | None:
    # TODO: Review unreachable code - """Update project creative context.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - project_id_or_name: Project ID or name
    # TODO: Review unreachable code - creative_context: New creative context to merge

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Updated project or None if not found
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - project = self.get_project(project_id_or_name)
    # TODO: Review unreachable code - if not project:
    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - # Merge creative context
    # TODO: Review unreachable code - project["creative_context"].update(creative_context)
    # TODO: Review unreachable code - project["updated_at"] = datetime.now(UTC).isoformat()

    # TODO: Review unreachable code - # Save updated project
    # TODO: Review unreachable code - project_path = self._get_project_path(project["name"])
    # TODO: Review unreachable code - if project_path:
    # TODO: Review unreachable code - project_file = project_path / "project.yaml"
    # TODO: Review unreachable code - with open(project_file, 'w') as f:
    # TODO: Review unreachable code - yaml.dump(project, f, default_flow_style=False)

    # TODO: Review unreachable code - # Publish event
    # TODO: Review unreachable code - self._publish_event(
    # TODO: Review unreachable code - "project.context.updated",
    # TODO: Review unreachable code - source="file_project_service",
    # TODO: Review unreachable code - project_id=project["id"],
    # TODO: Review unreachable code - context_update=creative_context
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - return project

    # TODO: Review unreachable code - def update_project_status(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - project_id_or_name: str,
    # TODO: Review unreachable code - status: str
    # TODO: Review unreachable code - ) -> dict[str, Any] | None:
    # TODO: Review unreachable code - """Update project status.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - project_id_or_name: Project ID or name
    # TODO: Review unreachable code - status: New status (active, paused, completed, archived)

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Updated project or None if not found
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - project = self.get_project(project_id_or_name)
    # TODO: Review unreachable code - if not project:
    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - old_status = project.get("status", "unknown")
    # TODO: Review unreachable code - project["status"] = status
    # TODO: Review unreachable code - project["updated_at"] = datetime.now(UTC).isoformat()

    # TODO: Review unreachable code - # Save updated project
    # TODO: Review unreachable code - project_path = self._get_project_path(project["name"])
    # TODO: Review unreachable code - if project_path:
    # TODO: Review unreachable code - project_file = project_path / "project.yaml"
    # TODO: Review unreachable code - with open(project_file, 'w') as f:
    # TODO: Review unreachable code - yaml.dump(project, f, default_flow_style=False)

    # TODO: Review unreachable code - # Publish event
    # TODO: Review unreachable code - self._publish_event(
    # TODO: Review unreachable code - "project.status.changed",
    # TODO: Review unreachable code - source="file_project_service",
    # TODO: Review unreachable code - project_id=project["id"],
    # TODO: Review unreachable code - old_status=old_status,
    # TODO: Review unreachable code - new_status=status
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - return project

    # TODO: Review unreachable code - def record_generation(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - project_id_or_name: str,
    # TODO: Review unreachable code - provider: str,
    # TODO: Review unreachable code - cost: float,
    # TODO: Review unreachable code - request_params: dict[str, Any] = None,
    # TODO: Review unreachable code - result_metadata: dict[str, Any] = None,
    # TODO: Review unreachable code - file_path: str = None
    # TODO: Review unreachable code - ) -> None:
    # TODO: Review unreachable code - """Record a generation and update project budget.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - project_id_or_name: Project ID or name
    # TODO: Review unreachable code - provider: Provider name (e.g., "midjourney", "dalle")
    # TODO: Review unreachable code - cost: Generation cost in USD
    # TODO: Review unreachable code - request_params: Optional request parameters
    # TODO: Review unreachable code - result_metadata: Optional result metadata
    # TODO: Review unreachable code - file_path: Optional path to generated file
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - project = self.get_project(project_id_or_name)
    # TODO: Review unreachable code - if not project:
    # TODO: Review unreachable code - logger.warning(f"Project not found: {project_id_or_name}")
    # TODO: Review unreachable code - return

    # TODO: Review unreachable code - # Create generation record
    # TODO: Review unreachable code - generation = {
    # TODO: Review unreachable code - "id": hashlib.sha256(f"{project_id_or_name}:{datetime.now().isoformat()}".encode()).hexdigest()[:16],
    # TODO: Review unreachable code - "provider": provider,
    # TODO: Review unreachable code - "cost": cost,
    # TODO: Review unreachable code - "request_params": request_params or {},
    # TODO: Review unreachable code - "result_metadata": result_metadata or {},
    # TODO: Review unreachable code - "file_path": file_path,
    # TODO: Review unreachable code - "created_at": datetime.now(UTC).isoformat(),
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Update project
    # TODO: Review unreachable code - project["generations"].append(generation)
    # TODO: Review unreachable code - project["budget_spent"] += cost

    # TODO: Review unreachable code - # Update cost breakdown
    # TODO: Review unreachable code - if provider not in project["cost_breakdown"]:
    # TODO: Review unreachable code - project["cost_breakdown"][provider] = 0.0
    # TODO: Review unreachable code - project["cost_breakdown"][provider] += cost

    # TODO: Review unreachable code - project["updated_at"] = datetime.now(UTC).isoformat()

    # TODO: Review unreachable code - # Save updated project
    # TODO: Review unreachable code - project_path = self._get_project_path(project["name"])
    # TODO: Review unreachable code - if project_path:
    # TODO: Review unreachable code - project_file = project_path / "project.yaml"
    # TODO: Review unreachable code - with open(project_file, 'w') as f:
    # TODO: Review unreachable code - yaml.dump(project, f, default_flow_style=False)

    # TODO: Review unreachable code - # Publish events
    # TODO: Review unreachable code - self._publish_event(
    # TODO: Review unreachable code - "generation.completed",
    # TODO: Review unreachable code - source="file_project_service",
    # TODO: Review unreachable code - project_id=project["id"],
    # TODO: Review unreachable code - provider=provider,
    # TODO: Review unreachable code - cost=cost,
    # TODO: Review unreachable code - request_params=request_params or {},
    # TODO: Review unreachable code - result_metadata=result_metadata or {},
    # TODO: Review unreachable code - file_path=file_path
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Check budget
    # TODO: Review unreachable code - if project.get("budget_total") and project["budget_spent"] >= project["budget_total"]:
    # TODO: Review unreachable code - self._publish_event(
    # TODO: Review unreachable code - "project.budget.exceeded",
    # TODO: Review unreachable code - source="file_project_service",
    # TODO: Review unreachable code - project_id=project["id"],
    # TODO: Review unreachable code - budget_total=project["budget_total"],
    # TODO: Review unreachable code - budget_spent=project["budget_spent"]
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - elif project.get("budget_total") and project["budget_spent"] >= project["budget_total"] * 0.8:
    # TODO: Review unreachable code - self._publish_event(
    # TODO: Review unreachable code - "project.budget.warning",
    # TODO: Review unreachable code - source="file_project_service",
    # TODO: Review unreachable code - project_id=project["id"],
    # TODO: Review unreachable code - budget_total=project["budget_total"],
    # TODO: Review unreachable code - budget_spent=project["budget_spent"],
    # TODO: Review unreachable code - percentage_used=project["budget_spent"] / project["budget_total"] * 100
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - def get_project_budget_status(self, project_id_or_name: str) -> dict[str, Any] | None:
    # TODO: Review unreachable code - """Get project budget status.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - project_id_or_name: Project ID or name

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Budget status or None if project not found
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - project = self.get_project(project_id_or_name)
    # TODO: Review unreachable code - if not project:
    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - budget_total = project.get("budget_total", 0)
    # TODO: Review unreachable code - budget_spent = project.get("budget_spent", 0)

    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - "project_id": project["id"],
    # TODO: Review unreachable code - "project_name": project["name"],
    # TODO: Review unreachable code - "budget_total": budget_total,
    # TODO: Review unreachable code - "budget_spent": budget_spent,
    # TODO: Review unreachable code - "budget_remaining": budget_total - budget_spent if budget_total else None,
    # TODO: Review unreachable code - "budget_currency": project.get("budget_currency", "USD"),
    # TODO: Review unreachable code - "percentage_used": (budget_spent / budget_total * 100) if budget_total else 0,
    # TODO: Review unreachable code - "status": project.get("status", "unknown"),
    # TODO: Review unreachable code - "cost_breakdown": project.get("cost_breakdown", {}),
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - def get_project_cost_breakdown(self, project_id_or_name: str) -> dict[str, float]:
    # TODO: Review unreachable code - """Get cost breakdown by provider.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - project_id_or_name: Project ID or name

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Cost breakdown by provider or empty dict
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - project = self.get_project(project_id_or_name)
    # TODO: Review unreachable code - if not project:
    # TODO: Review unreachable code - return {}

    # TODO: Review unreachable code - return project.get("cost_breakdown", {}) or 0

    # TODO: Review unreachable code - def find_project_from_path(self, current_path: str = None) -> dict[str, Any] | None:
    # TODO: Review unreachable code - """Find project based on directory path.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - current_path: Directory path to search from

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Project dict or None
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - project_root = self._find_project_root(Path(current_path) if current_path else None)
    # TODO: Review unreachable code - if project_root:
    # TODO: Review unreachable code - project_file = project_root / "project.yaml"
    # TODO: Review unreachable code - if project_file.exists():
    # TODO: Review unreachable code - with open(project_file) as f:
    # TODO: Review unreachable code - return yaml.safe_load(f)
    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - def get_or_create_project_from_path(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - path: str = None,
    # TODO: Review unreachable code - create_if_missing: bool = True
    # TODO: Review unreachable code - ) -> dict[str, Any] | None:
    # TODO: Review unreachable code - """Get project from path or create one if missing.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - path: Directory path
    # TODO: Review unreachable code - create_if_missing: Whether to create project if not found

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Project dict or None
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # First try to find existing project
    # TODO: Review unreachable code - project = self.find_project_from_path(path)
    # TODO: Review unreachable code - if project:
    # TODO: Review unreachable code - return project

    # TODO: Review unreachable code - if not create_if_missing:
    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - # Create new project from directory name
    # TODO: Review unreachable code - current_path = Path(path) if path else Path.cwd()
    # TODO: Review unreachable code - project_name = current_path.name

    # TODO: Review unreachable code - # Don't create in root or home directories
    # TODO: Review unreachable code - if project_name in ['/', '', '.', '..'] or current_path == Path.home():
    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - return self.create_project(
    # TODO: Review unreachable code - name=project_name,
    # TODO: Review unreachable code - description=f"Auto-created project from directory {current_path}",
    # TODO: Review unreachable code - path=str(current_path)
    # TODO: Review unreachable code - )
