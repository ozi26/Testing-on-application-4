#!/usr/bin/env python3
# =============================================================================
# RUN SELECTED TESTS — Multi-language, monorepo-aware
# =============================================================================
# Reads analyzer_result.json and runs only the affected tests.
# Each test is run from the directory of the service it belongs to,
# not from the workspace root.
# =============================================================================

import json
import sys
import subprocess
from pathlib import Path


# -----------------------------------------------------------------------------
# Find the project root for a test file by walking up the directory tree
# until we find a project marker (package.json, pom.xml, .csproj, etc.)
# -----------------------------------------------------------------------------
PROJECT_MARKERS = {
    ".js":  ["package.json"],
    ".ts":  ["package.json", "tsconfig.json"],
    ".py":  ["pyproject.toml", "setup.py", "pytest.ini", "requirements.txt"],
    ".java": ["pom.xml", "build.gradle", "build.gradle.kts"],
    ".cs":  ["*.csproj", "*.sln"],
}


def find_project_root(test_file):
    """
    Walk up from the test file's directory to find the nearest project marker.
    Returns the directory containing the marker, or the test file's dir.
    """
    test_path = Path(test_file).resolve()
    ext = test_path.suffix.lower()
    markers = PROJECT_MARKERS.get(ext, [])
    if not markers:
        return test_path.parent

    current = test_path.parent
    for _ in range(6):  # walk up at most 6 levels
        for marker in markers:
            if "*" in marker:
                if any(current.glob(marker)):
                    return current
            else:
                if (current / marker).exists():
                    return current
        if current.parent == current:
            break
        current = current.parent

    return test_path.parent


# -----------------------------------------------------------------------------
# Test runner dispatch per extension
# -----------------------------------------------------------------------------
def run_js_tests(test_files):
    """Run JavaScript tests grouped by their service directory."""
    exit_code = 0
    groups = {}
    for test_file in test_files:
        root = find_project_root(test_file)
        groups.setdefault(root, []).append(str(Path(test_file).relative_to(root)))

    for root, files in groups.items():
        print(f"\n  Running JS tests in: {root}")
        print(f"    Files: {files}")
        # Jest accepts relative paths from the project root
        cmd = ["npm", "test", "--"] + files
        result = subprocess.run(cmd, cwd=root)
        exit_code = max(exit_code, result.returncode)
    return exit_code


def run_py_tests(test_files):
    """Run Python tests with pytest, grouped by project root."""
    exit_code = 0
    groups = {}
    for test_file in test_files:
        root = find_project_root(test_file)
        groups.setdefault(root, []).append(str(Path(test_file).relative_to(root)))

    for root, files in groups.items():
        print(f"\n  Running Python tests in: {root}")
        print(f"    Files: {files}")
        cmd = [sys.executable, "-m", "pytest"] + files + ["-v"]
        result = subprocess.run(cmd, cwd=root)
        exit_code = max(exit_code, result.returncode)
    return exit_code


def run_cs_tests(test_files):
    """Run C# tests with dotnet test, grouped by project root."""
    exit_code = 0
    groups = {}
    for test_file in test_files:
        root = find_project_root(test_file)
        groups.setdefault(root, []).append(test_file)

    for root, files in groups.items():
        print(f"\n  Running C# tests in: {root}")
        # dotnet test runs the entire project's test suite.
        # We can't select individual .cs files, so we pass the filter
        # for the test project that contains them.
        csproj = list(root.glob("*.csproj"))
        if csproj:
            print(f"    Project: {csproj[0].name}")
            cmd = ["dotnet", "test", str(csproj[0])]
            result = subprocess.run(cmd, cwd=root)
            exit_code = max(exit_code, result.returncode)
        else:
            print(f"    [SKIP] No .csproj found in {root}")
    return exit_code


def run_java_tests(test_files):
    """Run Java tests with maven."""
    exit_code = 0
    groups = {}
    for test_file in test_files:
        root = find_project_root(test_file)
        groups.setdefault(root, []).append(test_file)

    for root, files in groups.items():
        print(f"\n  Running Java tests in: {root}")
        if (root / "pom.xml").exists():
            cmd = ["mvn", "test"]
            result = subprocess.run(cmd, cwd=root)
            exit_code = max(exit_code, result.returncode)
        elif (root / "build.gradle").exists():
            cmd = ["gradle", "test"]
            result = subprocess.run(cmd, cwd=root)
            exit_code = max(exit_code, result.returncode)
        else:
            print(f"    [SKIP] No build file found in {root}")
    return exit_code


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main():
    result_file = Path("analyzer_result.json")
    if not result_file.exists():
        print("ERROR: analyzer_result.json not found!")
        sys.exit(1)

    with open(result_file, "r", encoding="utf-8") as f:
        result = json.load(f)

    if not result.get("has_affected_tests", False):
        print("=" * 60)
        print("NO AFFECTED TESTS — Skipping test execution")
        print("=" * 60)
        sys.exit(0)

    affected_tests = result["affected_tests"]

    # Group by extension
    by_ext = {}
    for test in affected_tests:
        ext = Path(test).suffix.lower()
        by_ext.setdefault(ext, []).append(test)

    print("=" * 60)
    print(f"Running {len(affected_tests)} affected test file(s)")
    print(f"Grouped by extension: {list(by_ext.keys())}")
    print("=" * 60)

    overall_exit = 0

    if ".js" in by_ext or ".ts" in by_ext:
        js_files = by_ext.get(".js", []) + by_ext.get(".ts", [])
        print(f"\n[JS] Running {len(js_files)} JavaScript test file(s)")
        overall_exit = max(overall_exit, run_js_tests(js_files))

    if ".py" in by_ext:
        py_files = by_ext[".py"]
        print(f"\n[PY] Running {len(py_files)} Python test file(s)")
        overall_exit = max(overall_exit, run_py_tests(py_files))

    if ".cs" in by_ext:
        cs_files = by_ext[".cs"]
        print(f"\n[CS] Running {len(cs_files)} C# test file(s)")
        overall_exit = max(overall_exit, run_cs_tests(cs_files))

    if ".java" in by_ext:
        java_files = by_ext[".java"]
        print(f"\n[JAVA] Running {len(java_files)} Java test file(s)")
        overall_exit = max(overall_exit, run_java_tests(java_files))

    print("\n" + "=" * 60)
    if overall_exit == 0:
        print("ALL TESTS PASSED")
    else:
        print(f"SOME TESTS FAILED (exit code {overall_exit})")
    print("=" * 60)

    sys.exit(overall_exit)


if __name__ == "__main__":
    main()