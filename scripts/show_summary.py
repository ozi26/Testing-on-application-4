#!/usr/bin/env python3
# =============================================================================
# SHOW SUMMARY
# Reads analyzer_result.json and prints a human-readable summary.
# Called by the Jenkins pipeline after the analyzer runs.
# =============================================================================

import json
import sys
from pathlib import Path


def main():
    # Default result file — override with argv[1] if provided
    result_file = Path(sys.argv[1] if len(sys.argv) > 1 else "analyzer_result.json")

    if not result_file.exists():
        print(f"ERROR: {result_file} not found.")
        sys.exit(1)

    with open(result_file, "r", encoding="utf-8") as f:
        result = json.load(f)

    print("=" * 60)
    print("ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Has affected tests : {result.get('has_affected_tests', False)}")
    print(f"Test count         : {result.get('test_count', 0)}")

    summary = result.get("summary", {})
    if summary:
        print()
        print(f"Changed files      : {len(summary.get('changed_files', []))}")
        print(f"Source files       : {len(summary.get('source_files', []))}")
        print(f"Config files       : {len(summary.get('config_files', []))}")
        print(f"Total tests        : {summary.get('total_tests_analyzed', 0)}")

    affected = result.get("affected_tests", [])
    print()
    print(f"Affected tests ({len(affected)}):")
    for test in affected:
        print(f"  - {test}")
    print("=" * 60)


if __name__ == "__main__":
    main()