# MCP Server Refactoring Plan

## Current State Analysis

### File Statistics
- **Total Lines**: 2,930 lines
- **Total MCP Tools**: 46 tools in main file + 4 (image_presentation) + 5 (video_creation) + 7 (prompts) = **62 total tools**
- **Single Monolithic File**: `alicemultiverse/mcp_server.py`

### Current Tool Categories

1. **Core Operations** (9 tools)
   - `search_assets`
   - `organize_media`
   - `tag_assets`
   - `find_similar_assets`
   - `get_asset_info`
   - `assess_quality`
   - `get_organization_stats`
   - `find_duplicates`
   - `update_project_context`

2. **Cost Management** (3 tools)
   - `estimate_cost`
   - `get_spending_report`
   - `set_budget`

3. **Project Management** (3 tools)
   - `create_project`
   - `list_projects`
   - `get_project_context`

4. **Quick Marks/Selections** (3 tools)
   - `quick_mark`
   - `list_quick_marks`
   - `export_quick_marks`

5. **Image Analysis** (5 tools)
   - `analyze_images_optimized`
   - `estimate_analysis_cost`
   - `analyze_with_local`
   - `check_ollama_status`
   - `pull_ollama_model`

6. **Tag Management** (5 tools)
   - `analyze_with_hierarchy`
   - `create_tag_mood_board`
   - `get_tag_insights`
   - `batch_cluster_images`
   - `suggest_tags_for_project`

7. **Style Analysis** (5 tools)
   - `analyze_style_similarity`
   - `find_similar_style`
   - `extract_style_prompts`
   - `build_style_collections`
   - `check_style_compatibility`

8. **Music/Video** (6 tools)
   - `analyze_music`
   - `sync_images_to_music`
   - `suggest_cuts_for_mood`
   - `export_timeline`
   - `create_video_timeline`
   - `generate_veo3_video`

9. **External Modules**
   - **Image Presentation** (4 tools in `image_presentation_mcp.py`)
   - **Video Creation** (5 tools in `video_creation_mcp.py`)
   - **Prompt Management** (7 tools via `PromptMCPTools`)

## Identified Issues

1. **Size**: Nearly 3,000 lines in a single file is difficult to maintain
2. **Mixed Concerns**: Core operations, cost tracking, project management, analysis, etc. all in one file
3. **Code Duplication**: Similar error handling and response formatting patterns repeated
4. **Poor Testability**: Hard to test individual tool groups in isolation
5. **Initialization Clutter**: All services initialized at module level

## Proposed Module Structure

```
alicemultiverse/mcp/
├── __init__.py
├── server.py                 # Main MCP server setup (minimal)
├── base.py                   # Base classes and utilities
├── tools/
│   ├── __init__.py
│   ├── core.py              # Core asset operations (search, organize, tag, etc.)
│   ├── cost.py              # Cost management tools
│   ├── projects.py          # Project management tools
│   ├── selections.py        # Quick marks and selections
│   ├── analysis.py          # Image analysis tools
│   ├── tags.py              # Tag hierarchy and management
│   ├── style.py             # Style analysis and collections
│   ├── music_video.py       # Music analysis and video timeline
│   └── local_models.py      # Ollama and local model tools
└── utils/
    ├── __init__.py
    ├── decorators.py        # Common decorators for tools
    ├── responses.py         # Standardized response formatting
    └── validation.py        # Input validation utilities
```

## Refactoring Steps

### Phase 1: Create Infrastructure (Non-Breaking)

1. **Create new directory structure**
   ```bash
   mkdir -p alicemultiverse/mcp/tools
   mkdir -p alicemultiverse/mcp/utils
   ```

2. **Create base utilities**
   - `base.py`: Base classes for tool groups
   - `utils/responses.py`: Standardized response formatting
   - `utils/decorators.py`: Error handling decorators
   - `utils/validation.py`: Common validation functions

3. **Create tool modules** (initially empty)
   - One module per category listed above

### Phase 2: Extract Tool Groups (Incremental)

1. **Start with smallest groups** (easier to test)
   - Extract cost management tools first (only 3 tools)
   - Test that they work via the new module

2. **Extract by dependency order**
   - Projects (independent)
   - Selections (depends on projects)
   - Core operations (depends on multiple services)

3. **Keep backward compatibility**
   - Import extracted tools back into main `mcp_server.py`
   - Gradually deprecate the monolithic file

### Phase 3: Refactor Common Patterns

1. **Standardize error handling**
   ```python
   @handle_mcp_errors
   async def tool_function(...):
       # Tool implementation
   ```

2. **Standardize response format**
   ```python
   return success_response(message="...", data={...})
   return error_response(error="...", message="...")
   ```

3. **Extract validation**
   ```python
   @validate_params(asset_ids=list, threshold=float)
   async def tool_function(...):
       # Tool implementation
   ```

### Phase 4: Optimize Initialization

1. **Lazy loading of services**
   ```python
   class ToolGroup:
       @property
       def service(self):
           if not self._service:
               self._service = ServiceClass()
           return self._service
   ```

2. **Configuration injection**
   - Pass configuration to tool groups
   - Avoid global imports

### Phase 5: Testing and Documentation

1. **Unit tests per module**
   - Test each tool group independently
   - Mock dependencies

2. **Integration tests**
   - Test full MCP server with all modules

3. **Update documentation**
   - Document new structure
   - Migration guide for developers

## Code Examples

### Example: Extracted Cost Management Module

```python
# alicemultiverse/mcp/tools/cost.py
from typing import Any, Dict
from ..base import ToolGroup
from ..utils.decorators import handle_mcp_errors
from ..utils.responses import success_response, error_response
from ...core.cost_tracker import get_cost_tracker

class CostManagementTools(ToolGroup):
    """Cost tracking and budget management tools."""
    
    def __init__(self, server):
        super().__init__(server)
        self._cost_tracker = None
    
    @property
    def cost_tracker(self):
        if not self._cost_tracker:
            self._cost_tracker = get_cost_tracker()
        return self._cost_tracker
    
    def register(self):
        """Register all cost management tools."""
        self.server.tool()(self.estimate_cost)
        self.server.tool()(self.get_spending_report)
        self.server.tool()(self.set_budget)
    
    @handle_mcp_errors
    async def estimate_cost(
        self,
        operation: str,
        file_count: int = 1,
        providers: list[str] | None = None,
        detailed: bool = False,
    ) -> Dict[str, Any]:
        """Estimate cost for an operation before running it."""
        # Implementation moved from main file
        ...
```

### Example: Base Class

```python
# alicemultiverse/mcp/base.py
from abc import ABC, abstractmethod

class ToolGroup(ABC):
    """Base class for MCP tool groups."""
    
    def __init__(self, server):
        self.server = server
    
    @abstractmethod
    def register(self):
        """Register all tools in this group."""
        pass
```

### Example: Response Utilities

```python
# alicemultiverse/mcp/utils/responses.py
from typing import Any, Dict

def success_response(message: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create standardized success response."""
    response = {
        "success": True,
        "message": message
    }
    if data is not None:
        response["data"] = data
    return response

def error_response(error: str, message: str) -> Dict[str, Any]:
    """Create standardized error response."""
    return {
        "success": False,
        "error": error,
        "message": message
    }
```

### Example: New Server Setup

```python
# alicemultiverse/mcp/server.py
from mcp import Server
from .tools import (
    CoreTools, CostManagementTools, ProjectTools,
    SelectionTools, AnalysisTools, TagTools,
    StyleTools, MusicVideoTools, LocalModelTools
)
from ..interface.image_presentation_mcp import register_image_presentation_tools
from ..interface.video_creation_mcp import register_video_creation_tools
from ..prompts.mcp_tools import PromptMCPTools

def create_server():
    """Create and configure MCP server with all tools."""
    server = Server("alice-multiverse")
    
    # Register tool groups
    tool_groups = [
        CoreTools(server),
        CostManagementTools(server),
        ProjectTools(server),
        SelectionTools(server),
        AnalysisTools(server),
        TagTools(server),
        StyleTools(server),
        MusicVideoTools(server),
        LocalModelTools(server),
    ]
    
    for group in tool_groups:
        group.register()
    
    # Register external tool modules
    register_image_presentation_tools(server, image_api)
    register_video_creation_tools(server, search_db)
    
    # Register prompt tools
    prompt_tools = PromptMCPTools()
    prompt_tools.register(server)
    
    return server
```

## Benefits of Refactoring

1. **Maintainability**: Each module is focused on a specific domain
2. **Testability**: Can test tool groups in isolation
3. **Reusability**: Common patterns extracted to utilities
4. **Scalability**: Easy to add new tool groups
5. **Performance**: Lazy loading reduces startup time
6. **Developer Experience**: Easier to find and modify specific tools

## Migration Strategy

1. **Incremental**: Move one tool group at a time
2. **Backward Compatible**: Keep existing imports working
3. **Test Coverage**: Add tests before refactoring
4. **Documentation**: Update as each phase completes
5. **Review**: Get feedback after each phase

## Timeline Estimate

- Phase 1: 2-3 hours (infrastructure setup)
- Phase 2: 4-6 hours (extract tool groups)
- Phase 3: 2-3 hours (refactor patterns)
- Phase 4: 1-2 hours (optimize initialization)
- Phase 5: 3-4 hours (testing and docs)

**Total: 12-18 hours of work**

## Next Steps

1. Review and approve this plan
2. Create the infrastructure (Phase 1)
3. Start with cost management tools as proof of concept
4. Iterate based on learnings