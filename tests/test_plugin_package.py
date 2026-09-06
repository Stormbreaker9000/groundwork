"""The directory boundary is the plugin manifest, so the boundary gets a test.

Installing a Claude Code plugin copies the whole tree under the marketplace
entry's ``source``, minus ``.git``. No ``files``, ``exclude`` or ``ignore``
field exists in any ``plugin.json`` — there is no way to ship a subset of a
directory. So what ships is decided entirely by where the files sit, and
nothing but this test notices when something wanders in.

STO-257 moved the runtime under ``plugin/`` for that reason: before it, every
install carried 2.1M of ``docs/``, 1.1M of Nextra source and 888K of pytest
fixtures, against 532K of actual runtime.
"""
import json
import os
import re
import shutil
import subprocess
import sys

REPO_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
)
PLUGIN_DIR = os.path.join(REPO_ROOT, "plugin")

# Everything a plugin install is allowed to contain, at the top level.
RUNTIME_TOPLEVEL = {
    ".claude-plugin",
    "CLAUDE.md",
    "LICENSE",
    "agents",
    "commands",
    "hooks",
    "lib",
    "skills",
}

# Path segments that must never appear anywhere under plugin/.
NEVER_SHIP = ("/docs/", "/site/", "/assets/", "/tests/", "/fixtures/")


def _shipped_paths():
    """Every tracked path under ``plugin/``, exactly as an install would copy it.

    Reads ``git ls-files`` rather than walking the filesystem: an install
    copies the tree minus ``.git``, and untracked scratch files in a working
    directory are not what ships. Raises rather than returning an empty list —
    an empty result would make every assertion below vacuously true.
    """
    result = subprocess.run(
        ["git", "ls-files", "plugin"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    paths = result.stdout.splitlines()
    if not paths:
        raise AssertionError(
            "git ls-files plugin returned nothing — is plugin/ tracked?"
        )
    return paths


def test_marketplace_source_points_at_the_plugin_directory():
    # The one line that makes the whole arrangement real. If this reverts to
    # "./" the tree below is still tidy and every user still downloads 4.7M.
    path = os.path.join(REPO_ROOT, ".claude-plugin", "marketplace.json")
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    assert [entry["source"] for entry in data["plugins"]] == ["./plugin"]


def test_plugin_ships_only_runtime_directories():
    tops = {path.split("/")[1] for path in _shipped_paths()}
    assert tops == RUNTIME_TOPLEVEL


def test_no_documentation_site_or_fixtures_ship():
    offenders = [
        path
        for path in _shipped_paths()
        if any(segment in path for segment in NEVER_SHIP)
    ]
    assert offenders == []


def test_an_installed_copy_runs_its_own_validator(tmp_path):
    # The check that would have caught the broken path at any point in the
    # last four months. Copy the plugin somewhere else, stand in a directory
    # that is NOT a groundwork checkout, and run the validator by absolute
    # path — which is the only shape available to an installed plugin.
    install = tmp_path / "install"
    shutil.copytree(PLUGIN_DIR, install)

    project = tmp_path / "project"
    (project / ".sdlc").mkdir(parents=True)
    shutil.copytree(
        os.path.join(REPO_ROOT, "tests", "requirements", "fixtures", "valid"),
        project / ".sdlc" / "requirements",
    )

    script = install / "skills" / "requirements" / "scripts" / "validate_requirements.py"
    result = subprocess.run(
        [sys.executable, str(script), ".sdlc/requirements"],
        cwd=project,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_an_installed_copy_runs_the_sibling_skills_validator_too(tmp_path):
    # The design skill reaches across to its sibling rather than owning a copy:
    # `<design-skill>/../requirements/scripts/validate_requirements.py`. Nothing
    # else exercises that ".." hop from a copied install, so it could silently
    # stop resolving (a rename, a moved script) without any test noticing.
    install = tmp_path / "install"
    shutil.copytree(PLUGIN_DIR, install)

    project = tmp_path / "project"
    (project / ".sdlc").mkdir(parents=True)
    shutil.copytree(
        os.path.join(REPO_ROOT, "tests", "requirements", "fixtures", "valid"),
        project / ".sdlc" / "requirements",
    )

    script = (
        install / "skills" / "design" / ".."
        / "requirements" / "scripts" / "validate_requirements.py"
    )
    assert script.resolve().is_file()

    result = subprocess.run(
        [sys.executable, str(script), ".sdlc/requirements"],
        cwd=project,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_no_shipped_file_invokes_a_repo_relative_script_path():
    # A bare `python3 skills/...` resolves only when the working directory is
    # a groundwork checkout. For an installed plugin the working directory is
    # the user's own project, so the command fails with No such file. The
    # fix is the skill base directory the harness injects; this guards it.
    #
    # Matched against the path form rather than requiring a "python3 " prefix
    # on the same line: two real references wrap the invocation across a
    # line break (python3 ends one line, skills/... begins the next), and one
    # is a bare mention of the script path with no python3 at all. All three
    # are just as broken from an installed plugin as the literal form.
    offender_pattern = re.compile(r"skills/(requirements|design)/scripts/[a-z_0-9]+\.py")
    offenders = []
    for path in _shipped_paths():
        if not path.endswith(".md"):
            continue
        with open(os.path.join(REPO_ROOT, path), "r", encoding="utf-8") as handle:
            text = handle.read()
        for match in offender_pattern.finditer(text):
            offenders.append(f"{path}: {match.group(0)}")
    assert offenders == []
