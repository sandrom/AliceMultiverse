#!/bin/bash
# Wrapper script for alice CLI to set PYTHONPATH
export PYTHONPATH="/Users/sandro/Documents/AI/AliceMultiverse:$PYTHONPATH"
exec /Users/sandro/Documents/AI/AliceMultiverse/.venv/bin/alice "$@"