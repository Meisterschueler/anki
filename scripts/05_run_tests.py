"""
05_run_tests.py — Run the test suite (pipeline step 5).

Executes all pytest tests in the tests/ directory.
Exit code is forwarded so CI pipelines can detect failures.

Usage:
    python scripts/05_run_tests.py          # run all tests
    python scripts/05_run_tests.py -k dim   # only dimension tests
"""

import sys
from pathlib import Path

# Ensure project root is on the path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest

if __name__ == "__main__":
    # Forward any extra CLI args (e.g. -k, -x, --tb=short)
    exit_code = pytest.main(["-v", str(PROJECT_ROOT / "tests")] + sys.argv[1:])
    sys.exit(exit_code)
