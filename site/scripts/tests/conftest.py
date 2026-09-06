"""Pytest configuration: make the exporter module importable.

The exporter lives one directory up (site/scripts/). Add that directory to
sys.path so `import export_reference` works regardless of the directory
pytest is invoked from. Mirrors the two conftests under tests/.
"""
import os
import sys

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)
