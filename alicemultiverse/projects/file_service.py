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
        # Fallback to first path even if it's remote
        return Path(self.storage_paths[0]) / self.registry_file

    def _load_registry(self) -> dict[str, str]:
        """Load the project registry mapping names to paths."""
        registry_path = self._get_registry_path()
        if registry_path.exists():
            with open(registry_path) as f:
                return yaml.safe_load(f) or {}
        return {}

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

        # Look for project in storage paths
        for storage_path in self.storage_paths:
            if not storage_path.startswith(("s3://", "gcs://", "http")):
                project_path = Path(storage_path) / project_name
                if project_path.exists():
                    return project_path

        return None

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

            # Stop at root or storage paths
            if current.parent == current:
                break
            for storage_path in self.storage_paths:
                if not storage_path.startswith(("s3://", "gcs://", "http")):
                    if current == Path(storage_path).resolve():
                        break

            current = current.parent

        return None

    def _publish_event(self, event_type: str, **data) -> None:
        """Publish event using Redis Streams."""
        publish_event_sync(event_type, data)

    def create_project(
        self,
        name: str,
        description: str = None,
        budget_total: float = None,
        creative_context: dict[str, Any] = None,
        settings: dict[str, Any] = None,
        path: str = None
    ) -> dict[str, Any]:
        """Create a new project.

        Args:
            name: Project name (used as directory name)
            description: Optional project description
            budget_total: Optional budget limit in USD
            creative_context: Optional creative context (style, characters, etc.)
            settings: Optional project-specific settings
            path: Optional specific path for the project

        Returns:
            Project data dictionary
        """
        # Use name-based project ID
        project_id = hashlib.sha256(f"{name}:{datetime.now().isoformat()}".encode()).hexdigest()[:16]

        # Determine project path
        if path:
            project_path = Path(path)
        else:
            # Use first writable storage path
            for storage_path in self.storage_paths:
                if not storage_path.startswith(("s3://", "gcs://", "http")):
                    project_path = Path(storage_path) / name
                    break
            else:
                # Use first path even if remote
                project_path = Path(self.storage_paths[0]) / name

        # Create project directory structure
        project_path.mkdir(parents=True, exist_ok=True)
        (project_path / ".alice").mkdir(exist_ok=True)
        (project_path / "created").mkdir(exist_ok=True)
        (project_path / "selected").mkdir(exist_ok=True)
        (project_path / "rounds").mkdir(exist_ok=True)
        (project_path / "exports").mkdir(exist_ok=True)

        # Create project data
        project_data = {
            "id": project_id,
            "name": name,
            "description": description,
            "budget_total": budget_total,
            "budget_spent": 0.0,
            "budget_currency": "USD",
            "status": "active",
            "creative_context": creative_context or {},
            "settings": settings or {},
            "cost_breakdown": {},
            "generations": [],
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
        }

        # Save project.yaml
        project_file = project_path / "project.yaml"
        with open(project_file, 'w') as f:
            yaml.dump(project_data, f, default_flow_style=False)

        # Update registry
        registry = self._load_registry()
        registry[name] = str(project_path)
        self._save_registry(registry)

        # Publish event
        self._publish_event(
            "project.created",
            source="file_project_service",
            project_id=project_id,
            project_name=name,
            description=description,
            initial_context=creative_context or {},
            path=str(project_path)
        )

        logger.info(f"Created project '{name}' at {project_path}")
        return project_data

    def get_project(self, project_id_or_name: str) -> dict[str, Any] | None:
        """Get project by ID or name.

        Args:
            project_id_or_name: Project ID or name

        Returns:
            Project data or None if not found
        """
        # Try to find by name first
        project_path = self._get_project_path(project_id_or_name)

        if not project_path:
            # Search all projects by ID
            registry = self._load_registry()
            for name, path in registry.items():
                project_file = Path(path) / "project.yaml"
                if project_file.exists():
                    with open(project_file) as f:
                        data = yaml.safe_load(f)
                        if data.get("id") == project_id_or_name:
                            return data
            return None

        project_file = project_path / "project.yaml"
        if project_file.exists():
            with open(project_file) as f:
                return yaml.safe_load(f)

        return None

    def get_current_project(self) -> dict[str, Any] | None:
        """Get the project in the current directory.

        Returns:
            Project data or None if not in a project directory
        """
        project_root = self._find_project_root()
        if project_root:
            project_file = project_root / "project.yaml"
            if project_file.exists():
                with open(project_file) as f:
                    return yaml.safe_load(f)
        return None

    def list_projects(self, status: str = None) -> list[dict[str, Any]]:
        """List all projects, optionally filtered by status.

        Args:
            status: Optional status filter (active, paused, completed, archived)

        Returns:
            List of projects
        """
        projects = []
        registry = self._load_registry()

        for name, path in registry.items():
            project_file = Path(path) / "project.yaml"
            if project_file.exists():
                with open(project_file) as f:
                    project_data = yaml.safe_load(f)
                    if not status or project_data.get("status") == status:
                        projects.append(project_data)

        # Sort by created_at descending
        projects.sort(key=lambda p: p.get("created_at", ""), reverse=True)
        return projects

    def update_project_context(
        self,
        project_id_or_name: str,
        creative_context: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Update project creative context.

        Args:
            project_id_or_name: Project ID or name
            creative_context: New creative context to merge

        Returns:
            Updated project or None if not found
        """
        project = self.get_project(project_id_or_name)
        if not project:
            return None

        # Merge creative context
        project["creative_context"].update(creative_context)
        project["updated_at"] = datetime.now(UTC).isoformat()

        # Save updated project
        project_path = self._get_project_path(project["name"])
        if project_path:
            project_file = project_path / "project.yaml"
            with open(project_file, 'w') as f:
                yaml.dump(project, f, default_flow_style=False)

        # Publish event
        self._publish_event(
            "project.context.updated",
            source="file_project_service",
            project_id=project["id"],
            context_update=creative_context
        )

        return project

    def update_project_status(
        self,
        project_id_or_name: str,
        status: str
    ) -> dict[str, Any] | None:
        """Update project status.

        Args:
            project_id_or_name: Project ID or name
            status: New status (active, paused, completed, archived)

        Returns:
            Updated project or None if not found
        """
        project = self.get_project(project_id_or_name)
        if not project:
            return None

        old_status = project.get("status", "unknown")
        project["status"] = status
        project["updated_at"] = datetime.now(UTC).isoformat()

        # Save updated project
        project_path = self._get_project_path(project["name"])
        if project_path:
            project_file = project_path / "project.yaml"
            with open(project_file, 'w') as f:
                yaml.dump(project, f, default_flow_style=False)

        # Publish event
        self._publish_event(
            "project.status.changed",
            source="file_project_service",
            project_id=project["id"],
            old_status=old_status,
            new_status=status
        )

        return project

    def record_generation(
        self,
        project_id_or_name: str,
        provider: str,
        cost: float,
        request_params: dict[str, Any] = None,
        result_metadata: dict[str, Any] = None,
        file_path: str = None
    ) -> None:
        """Record a generation and update project budget.

        Args:
            project_id_or_name: Project ID or name
            provider: Provider name (e.g., "midjourney", "dalle")
            cost: Generation cost in USD
            request_params: Optional request parameters
            result_metadata: Optional result metadata
            file_path: Optional path to generated file
        """
        project = self.get_project(project_id_or_name)
        if not project:
            logger.warning(f"Project not found: {project_id_or_name}")
            return

        # Create generation record
        generation = {
            "id": hashlib.sha256(f"{project_id_or_name}:{datetime.now().isoformat()}".encode()).hexdigest()[:16],
            "provider": provider,
            "cost": cost,
            "request_params": request_params or {},
            "result_metadata": result_metadata or {},
            "file_path": file_path,
            "created_at": datetime.now(UTC).isoformat(),
        }

        # Update project
        project["generations"].append(generation)
        project["budget_spent"] += cost

        # Update cost breakdown
        if provider not in project["cost_breakdown"]:
            project["cost_breakdown"][provider] = 0.0
        project["cost_breakdown"][provider] += cost

        project["updated_at"] = datetime.now(UTC).isoformat()

        # Save updated project
        project_path = self._get_project_path(project["name"])
        if project_path:
            project_file = project_path / "project.yaml"
            with open(project_file, 'w') as f:
                yaml.dump(project, f, default_flow_style=False)

        # Publish events
        self._publish_event(
            "generation.completed",
            source="file_project_service",
            project_id=project["id"],
            provider=provider,
            cost=cost,
            request_params=request_params or {},
            result_metadata=result_metadata or {},
            file_path=file_path
        )

        # Check budget
        if project.get("budget_total") and project["budget_spent"] >= project["budget_total"]:
            self._publish_event(
                "project.budget.exceeded",
                source="file_project_service",
                project_id=project["id"],
                budget_total=project["budget_total"],
                budget_spent=project["budget_spent"]
            )
        elif project.get("budget_total") and project["budget_spent"] >= project["budget_total"] * 0.8:
            self._publish_event(
                "project.budget.warning",
                source="file_project_service",
                project_id=project["id"],
                budget_total=project["budget_total"],
                budget_spent=project["budget_spent"],
                percentage_used=project["budget_spent"] / project["budget_total"] * 100
            )

    def get_project_budget_status(self, project_id_or_name: str) -> dict[str, Any] | None:
        """Get project budget status.

        Args:
            project_id_or_name: Project ID or name

        Returns:
            Budget status or None if project not found
        """
        project = self.get_project(project_id_or_name)
        if not project:
            return None

        budget_total = project.get("budget_total", 0)
        budget_spent = project.get("budget_spent", 0)

        return {
            "project_id": project["id"],
            "project_name": project["name"],
            "budget_total": budget_total,
            "budget_spent": budget_spent,
            "budget_remaining": budget_total - budget_spent if budget_total else None,
            "budget_currency": project.get("budget_currency", "USD"),
            "percentage_used": (budget_spent / budget_total * 100) if budget_total else 0,
            "status": project.get("status", "unknown"),
            "cost_breakdown": project.get("cost_breakdown", {}),
        }

    def get_project_cost_breakdown(self, project_id_or_name: str) -> dict[str, float]:
        """Get cost breakdown by provider.

        Args:
            project_id_or_name: Project ID or name

        Returns:
            Cost breakdown by provider or empty dict
        """
        project = self.get_project(project_id_or_name)
        if not project:
            return {}

        return project.get("cost_breakdown", {})

    def find_project_from_path(self, current_path: str = None) -> dict[str, Any] | None:
        """Find project based on directory path.

        Args:
            current_path: Directory path to search from

        Returns:
            Project dict or None
        """
        project_root = self._find_project_root(Path(current_path) if current_path else None)
        if project_root:
            project_file = project_root / "project.yaml"
            if project_file.exists():
                with open(project_file) as f:
                    return yaml.safe_load(f)
        return None

    def get_or_create_project_from_path(
        self,
        path: str = None,
        create_if_missing: bool = True
    ) -> dict[str, Any] | None:
        """Get project from path or create one if missing.

        Args:
            path: Directory path
            create_if_missing: Whether to create project if not found

        Returns:
            Project dict or None
        """
        # First try to find existing project
        project = self.find_project_from_path(path)
        if project:
            return project

        if not create_if_missing:
            return None

        # Create new project from directory name
        current_path = Path(path) if path else Path.cwd()
        project_name = current_path.name

        # Don't create in root or home directories
        if project_name in ['/', '', '.', '..'] or current_path == Path.home():
            return None

        return self.create_project(
            name=project_name,
            description=f"Auto-created project from directory {current_path}",
            path=str(current_path)
        )
