"""Pytest configuration: make the validator module importable.

The tests live outside the plugin (STO-257) so their fixtures stop shipping to
every user, so the scripts directory is no longer an ancestor of this file and
has to be named. ``validate_design`` itself adds ``plugin/lib/`` to the path
when imported, so the shared core still resolves.
"""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "plugin", "skills", "design", "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)
