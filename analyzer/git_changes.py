# =============================================================================
# GIT CHANGES MODULE
# This module contains functions for interacting with Git repositories.
# It uses Git commands to find out which files have changed in a commit
# or pull request.
# =============================================================================

import subprocess               # For running Git commands as subprocesses
from pathlib import Path        # For working with file paths
from analyzer.file_utils import is_config_file, is_source_file


def get_changed_files(repo_path=".", commit_range="HEAD~1..HEAD"):
    """
    Get a list of files that changed in a Git commit range.

    Automatically excludes generated/analyzer artifacts so they don't
    pollute the analysis (analyzer_result.json, test_dependencies.json,
    coverage reports, etc.).
    """
    # Generated artifacts to ignore
    IGNORED_FILES = {
        "analyzer_result.json",
        "test_dependencies.json",
        ".coverage",
        "coverage.xml",
        "pytest.xml",
    }
    IGNORED_SUFFIXES = (".pyc", ".pyo", ".class", ".log", ".tmp")

    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMR", commit_range],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )

        changed_files = []
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            # Skip generated/analyzer artifacts
            filename = line.split("/")[-1]
            if filename in IGNORED_FILES:
                continue
            if any(line.endswith(s) for s in IGNORED_SUFFIXES):
                continue
            # Skip files inside venv/, node_modules/, __pycache__/, .pytest_cache/
            if any(part in line.split("/") for part in
                   ("venv", "node_modules", "__pycache__",
                    ".pytest_cache", ".git", "dist", "build", "coverage")):
                continue

            changed_files.append(line)

        return changed_files

    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e}")
        return []
    except FileNotFoundError:
        print("Error: Git is not installed")
        return []

def categorize_changed_files(changed_files):
    """
    Separate changed files into source code and configuration files.
    
    IMPORTANT: Config detection takes priority. If a file matches a
    config pattern (e.g., payment.config.js or settings.py), it goes
    into config_files even if its extension is also a source extension.
    
    This handles ambiguous files correctly:
      - payment.config.js     → config (NOT source)
      - order_service.js      → source
      - config.py             → config
      - utils.py              → source
    """
    from analyzer.file_utils import is_config_file, is_source_file
    
    source_files = []
    config_files = []
    
    for file_path in changed_files:
        # ---- Config takes priority ----
        if is_config_file(file_path):
            config_files.append(file_path)
        # ---- Otherwise, check if it's source ----
        elif is_source_file(file_path):
            source_files.append(file_path)
        # ---- Files that are neither (README.md, LICENSE) are ignored ----
    
    return source_files, config_files