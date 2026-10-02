# =============================================================================
# RUN ANALYZER — Test Impact Analyzer for Microservices
# =============================================================================
# Main entry point for the analyzer. Detects changes in source code and
# configuration files, selects the minimal subset of tests that must run,
# and outputs analyzer_result.json for the Jenkins pipeline.
#
# Universal — works on any project in any language without modification.
# =============================================================================

import sys
import re
import json
import math
import subprocess
import argparse
from pathlib import Path

# -----------------------------------------------------------------------------
# Make the project root importable
# -----------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# -----------------------------------------------------------------------------
# Analyzer module imports (all at module level, column 0)
# -----------------------------------------------------------------------------
from analyzer.git_changes import get_changed_files, categorize_changed_files
from analyzer.code_parser import extract_code_terms
from analyzer.config_parser import parse_config_file
from analyzer.scoring import (
    calculate_score,
    compute_service_relevance,
    calculate_corpus_idf,
)
from analyzer.file_utils import (
    get_file_extension,
    is_test_file,
    extract_words,
)
from analyzer.config import SOURCE_EXTENSIONS


# =============================================================================
# MODULE-LEVEL HELPERS
# =============================================================================
# All functions below must be at column 0 (no indentation). Do NOT nest
# them inside other functions — that breaks imports and scope resolution.
# =============================================================================


def extract_service_name(file_path):
    """
    Extract the service name from a file path.

    Priority order:
      1. Parent directory named "<service>-service" or "<service>_service"
      2. Filename stem with common suffixes stripped
      3. Parent directory name
      4. Filename stem as last resort

    Universal — works for monorepos and flat repos alike.

    Examples:
        media_streaming_services/auth-service/src/app.py           -> "auth"
        media_streaming_services/notification-service/Service.cs   -> "notification"
        rideshare_services/config/driver_config.py                 -> "driver"
        rideshare_services/driver_service.py                       -> "driver"
        tests/test_driver_service.py                               -> "driver"
        ecommerce_services/config/cart.config.js                   -> "cart"
        src/paymentservice/index.js                                -> "paymentservice"
    """
    path = Path(file_path)

    # ---- Priority 1: parent dir named "<service>-service" or "<service>_service" ----
    for part in reversed(path.parts[:-1]):
        part_lower = part.lower()
        for suffix in ("-service", "_service"):
            if part_lower.endswith(suffix):
                return part_lower[: -len(suffix)]

    # ---- Priority 2: filename stem with suffixes stripped ----
    name = path.stem.lower()

    # Strip leading test/spec prefixes
    for prefix in ("test_", "spec_", "tests_", "itest_", "it_"):
        if name.startswith(prefix):
            name = name[len(prefix):]
            break

    # Strip known trailing suffixes (longest first)
    SUFFIXES = [
        "_service_test", "_service_tests", "_service_spec",
        ".service.test", ".service.spec", ".service",
        "_service", "service",
        "_config", ".config", "-config",
        "_settings", ".settings",
        "_test", ".test", "_tests", ".tests",
        "_spec", ".spec",
        "_server", ".server",
        "_client", ".client",
        "_handler", ".handler",
        "_controller", ".controller",
        "_repository", ".repository",
        "_dao", ".dao",
        "_model", ".model",
        "_view", ".view",
    ]
    for suffix in sorted(SUFFIXES, key=len, reverse=True):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break

    name = name.strip("._-")

    # ---- Priority 3: if name is empty or generic, use parent dir ----
    GENERIC_NAMES = {
        "app", "main", "index", "server", "service", "handler",
        "controller", "model", "view", "__init__",
    }
    if not name or name in GENERIC_NAMES:
        for part in reversed(path.parts[:-1]):
            part_lower = part.lower()
            if part_lower in ("src", "test", "tests", "lib", "app",
                              "main", "java", "python", "js"):
                continue
            for suffix in ("-service", "_service", "-api", "_api"):
                if part_lower.endswith(suffix):
                    return part_lower[: -len(suffix)]
            return part_lower
        return name or path.stem.lower()

    return name


def extract_services_from_config(config_file):
    """
    Extract service names from a config file's CONTENTS.

    Looks for `metadata.name` fields and env hostnames in YAML files
    (Kubernetes manifests). Returns an empty set for other formats.
    """
    try:
        import yaml
    except ImportError:
        return set()

    services = set()
    suffix = Path(config_file).suffix.lower()

    if suffix not in (".yaml", ".yml"):
        return services

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            documents = list(yaml.safe_load_all(f))
    except Exception:
        return services

    for doc in documents:
        if not isinstance(doc, dict):
            continue

        metadata = doc.get("metadata", {})
        if isinstance(metadata, dict):
            name = metadata.get("name")
            if isinstance(name, str) and name:
                services.add(name)

        spec = doc.get("spec", {})
        if isinstance(spec, dict):
            template = spec.get("template", {})
            if isinstance(template, dict):
                spec2 = template.get("spec", {})
                if isinstance(spec2, dict):
                    containers = spec2.get("containers", []) or []
                    for container in containers:
                        if not isinstance(container, dict):
                            continue
                        env_list = container.get("env", []) or []
                        for env_var in env_list:
                            if not isinstance(env_var, dict):
                                continue
                            value = env_var.get("value")
                            if not isinstance(value, str):
                                continue
                            match = re.match(
                                r"^([a-z][a-z0-9\-]*service)(:\d+)?$", value
                            )
                            if match:
                                services.add(match.group(1))

    return services

def find_test_files(test_dir):
    """
    Find all test files in a directory, across any programming language.
    Recursively walks the entire tree so tests at any depth are found.
    """
    test_path = Path(test_dir)
    if not test_path.exists():
        return []

    test_files = []
    SKIP_DIRS = {
        "node_modules", "venv", ".git", "__pycache__",
        "dist", "build", "coverage", ".pytest_cache",
        "target", "bin", "obj", "images", ".idea", ".vscode",
    }

    for file_path in test_path.rglob("*"):
        if not file_path.is_file():
            continue
        if any(p in file_path.parts for p in SKIP_DIRS):
            continue

        # Only source-code files can be tests
        ext = get_file_extension(file_path)
        if ext not in SOURCE_EXTENSIONS:
            continue

        # Language-agnostic test detector
        if is_test_file(str(file_path)):
            test_files.append(str(file_path))

    return test_files


# =============================================================================
# MAIN ANALYSIS PIPELINE
# =============================================================================


def analyze_changes(repo_path=".", commit_range="HEAD~1..HEAD", test_dir="tests"):
    """
    Analyze changes and select affected tests.

    Args:
        repo_path: Path to the Git repository being analyzed
        commit_range: Git range (e.g., "HEAD~1..HEAD")
        test_dir: Directory containing test files

    Returns:
        Dict with keys: changed_files, source_files, config_files,
        code_terms, config_terms, all_terms, test_files, ranked_tests.
        Returns {"error": "..."} on failure.
    """
    print("=" * 60)
    print("TEST IMPACT ANALYZER")
    print("=" * 60)

    # -------------------------------------------------------------------------
    # Step 1: Get changed files from Git
    # -------------------------------------------------------------------------
    print("\n[Step 1] Getting changed files from Git...")
    changed_files = get_changed_files(repo_path, commit_range)

    if not changed_files:
        print("No changed files found. Nothing to analyze.")
        return {"error": "No changes found"}

    print(f"Found {len(changed_files)} changed file(s):")
    for f in changed_files:
        print(f"  - {f}")

    # -------------------------------------------------------------------------
    # Step 2: Categorize into source and config files
    # -------------------------------------------------------------------------
    print("\n[Step 2] Categorizing changed files...")
    source_files, config_files = categorize_changed_files(changed_files)

    print(f"Source code files ({len(source_files)}):")
    for f in source_files:
        print(f"  - {f}")

    print(f"Configuration files ({len(config_files)}):")
    for f in config_files:
        print(f"  - {f}")

    # -------------------------------------------------------------------------
    # Step 3: Extract terms from changed files
    # -------------------------------------------------------------------------
    print("\n[Step 3] Extracting terms from changed files...")

    code_terms = extract_code_terms(source_files)
    print(f"Extracted {len(code_terms)} terms from source code files")

    config_terms = set()
    for config_file in config_files:
        try:
            parsed = parse_config_file(config_file)
            for key in parsed.keys():
                config_terms.update(extract_words(str(key)))
        except Exception as e:
            print(f"  [WARN] Could not parse {config_file}: {e}")

    print(f"Extracted {len(config_terms)} terms from configuration files")

    all_terms = code_terms | config_terms
    print(f"Total unique terms: {len(all_terms)}")

    # -------------------------------------------------------------------------
    # Step 4: Find all test files
    # -------------------------------------------------------------------------
    print("\n[Step 4] Finding test files...")
    test_files = find_test_files(test_dir)

    if not test_files:
        print(f"No test files found in: {test_dir}")
        return {"error": "No test files found"}

    print(f"Found {len(test_files)} test file(s):")
    for f in test_files:
        print(f"  - {f}")

    # -------------------------------------------------------------------------
    # Step 4.5a: Extract affected service names
    # -------------------------------------------------------------------------
    affected_services = set()

    # --- From source code file paths ---
    for f in source_files:
        service = extract_service_name(f)
        if service:
            affected_services.add(service)

    # --- From config file paths (THIS WAS MISSING) ---
    # Extracts the service name directly from the filename.
    # Example: config/history.properties -> "history"
    #          config/streaming.config.js -> "streaming"
    for f in config_files:
        service = extract_service_name(f)
        if service:
            affected_services.add(service)

    # --- From config file contents via git diff (supplementary) ---
    # For Kubernetes manifests and other YAML configs where the service
    # name lives inside the file rather than in the filename.
    for f in config_files:
        git_path = f.replace("\\", "/")

        try:
            diff_output = subprocess.run(
                ["git", "diff", commit_range, "--", git_path],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            ).stdout
        except subprocess.CalledProcessError:
            diff_output = ""

        if diff_output:
            changed_lines = []
            for line in diff_output.splitlines():
                if line.startswith(("---", "+++", "@@")):
                    continue
                if line.startswith(("+", "-")):
                    changed_lines.append(line[1:])

            for line in changed_lines:
                for match in re.finditer(
                    r'(?:name|app|value):\s*["\']?'
                    r'([a-z][a-z0-9\-]*(?:service|cart|frontend[a-z\-]*))',
                    line,
                ):
                    affected_services.add(match.group(1))
        else:
            file_services = extract_services_from_config(f)
            affected_services.update(file_services)

    # --- Final fallback: use changed file paths if nothing was found ---
    if not affected_services:
        for f in source_files + config_files:
            service = extract_service_name(f)
            if service:
                affected_services.add(service)

    print(f"Affected services: {sorted(affected_services)}")

    # -------------------------------------------------------------------------
    # Step 4.5b: Compute service-relevance scores
    # -------------------------------------------------------------------------
    service_relevance = {
        test_file: compute_service_relevance(test_file, affected_services)
        for test_file in test_files
    }
    print(f"Service-relevance scores computed for {len(service_relevance)} test(s)")

    # -------------------------------------------------------------------------
    # Step 4.25: Compute IDF weights over the FULL project corpus
    # -------------------------------------------------------------------------
    print("\n[Step 4.25] Computing IDF weights across corpus...")

    corpus_files = []
    target_root = Path(repo_path)
    SKIP_DIRS = {
        "node_modules", "venv", ".git", "__pycache__",
        "dist", "build", "coverage", ".pytest_cache",
        "target", "bin", "obj", "images", ".idea", ".vscode",
    }

    if target_root.exists():
        for f in target_root.rglob("*"):
            if not f.is_file():
                continue
            if any(part in SKIP_DIRS for part in f.parts):
                continue
            ext = get_file_extension(f)
            if ext in SOURCE_EXTENSIONS:
                corpus_files.append(str(f))

    # Include test files in the corpus as well
    for tf in test_files:
        if tf not in corpus_files:
            corpus_files.append(tf)

    idf_lookup = calculate_corpus_idf(corpus_files)
    print(f"Computed IDF for {len(idf_lookup)} terms across "
          f"{len(corpus_files)} files")

    if idf_lookup:
        top_terms = sorted(idf_lookup.items(), key=lambda x: x[1], reverse=True)[:10]
        print("Most distinctive terms (highest IDF):")
        for term, weight in top_terms:
            print(f"  {weight:.2f}  {term}")

        bottom_terms = sorted(idf_lookup.items(), key=lambda x: x[1])[:10]
        print("Most common terms (lowest IDF):")
        for term, weight in bottom_terms:
            print(f"  {weight:.2f}  {term}")

    # -------------------------------------------------------------------------
    # Step 5: Rank tests by combined score
    # -------------------------------------------------------------------------
    print("\n[Step 5] Ranking tests by relevance...")

    WEIGHT_LEXICAL = 0.3
    WEIGHT_SERVICE = 0.7
    THRESHOLD = 0.55

    scored_tests = []
    for test_file in test_files:
        lexical_score = calculate_score(all_terms, test_file, idf_lookup)
        service_score = service_relevance.get(test_file, 0.0)
        final_score = (WEIGHT_LEXICAL * lexical_score) + (WEIGHT_SERVICE * service_score)
        if final_score > 0:
            scored_tests.append((test_file, final_score))

    scored_tests.sort(key=lambda x: x[1], reverse=True)
    ranked_tests = [(t, s) for t, s in scored_tests if s >= THRESHOLD]

    print(f"Ranked tests ({len(ranked_tests)} above threshold {THRESHOLD}):")
    for test_file, score in ranked_tests:
        print(f"  {score:.3f}  {test_file}")

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)

    return {
        "changed_files": changed_files,
        "source_files": source_files,
        "config_files": config_files,
        "code_terms": code_terms,
        "config_terms": config_terms,
        "all_terms": all_terms,
        "test_files": test_files,
        "ranked_tests": ranked_tests,
    }


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    """Main entry point — parses CLI args, runs analysis, writes JSON."""
    parser = argparse.ArgumentParser(
        description="Test Impact Analyzer — select affected tests based on changes"
    )
    parser.add_argument("--repo", default=".", help="Path to the Git repository")
    parser.add_argument("--range", default="HEAD~1..HEAD", help="Git commit range")
    parser.add_argument("--tests", default="tests", help="Directory containing test files")

    args = parser.parse_args()

    results = analyze_changes(
        repo_path=args.repo,
        commit_range=args.range,
        test_dir=args.tests,
    )

    # -------------------------------------------------------------------------
    # Jenkins integration: write analyzer_result.json
    # -------------------------------------------------------------------------
    if "error" not in results:
        output_path = Path("analyzer_result.json")

        jenkins_output = {
            "affected_tests": [test for test, score in results["ranked_tests"]],
            "has_affected_tests": len(results["ranked_tests"]) > 0,
            "test_count": len(results["ranked_tests"]),
            "summary": {
                "changed_files": results["changed_files"],
                "source_files": results["source_files"],
                "config_files": results["config_files"],
                "total_tests_analyzed": len(results["test_files"]),
                "affected_tests_count": len(results["ranked_tests"]),
            },
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(jenkins_output, f, indent=2, ensure_ascii=False)

        print(f"\n[Jenkins] Result written to: {output_path}")
        print(f"[Jenkins] Affected tests: {jenkins_output['test_count']}")

    sys.exit(0 if "error" not in results else 1)


if __name__ == "__main__":
    main()