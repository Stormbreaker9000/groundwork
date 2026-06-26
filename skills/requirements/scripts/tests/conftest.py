"""Pytest configuration: make the validator module importable.

The validator lives one directory up (skills/requirements/scripts/). Add that
directory to sys.path so `import validate_requirements` works regardless of the
directory pytest is invoked from.
"""
import os
import sys

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)
