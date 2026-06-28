#!/bin/sh
# Run the security findings tests
SCRIPT_DIR="/Users/jonathannecea/Repos/klusai/Jonathan Necea/labs/claude-agent-labs/ex1_agent_sdk"
cd "$SCRIPT_DIR"

# Try pytest first, fall back to python -m unittest
if python3 -m pytest test_security_findings.py -v 2>/dev/null; then
    exit 0
fi

python3 test_security_findings.py
