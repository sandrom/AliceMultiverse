#!/usr/bin/env python3
"""Start the asset processor service with proper imports."""

import sys
import os
from pathlib import Path

# Get the project root
project_root = Path(__file__).parent.parent.parent

# Add packages to path
sys.path.insert(0, str(project_root / "packages" / "alice-events"))
sys.path.insert(0, str(project_root / "packages" / "alice-models"))
sys.path.insert(0, str(project_root / "packages" / "alice-config"))
sys.path.insert(0, str(project_root / "packages" / "alice-utils"))

# Add service src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Now we can import
from asset_processor.main import app
import uvicorn

if __name__ == "__main__":
    print("Starting Asset Processor Service...")
    print(f"Project root: {project_root}")
    
    # Get config
    try:
        from alice_config import get_config
        config = get_config()
        port = config.get("services.asset_processor.port", 8001)
    except:
        port = 8001
    
    print(f"Starting on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)