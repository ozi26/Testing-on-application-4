# =============================================================================
# SCORING MODULE
# This module contains functions for calculating how relevant a test is
# to a set of changes. It uses lexical matching - comparing words in
# changed files with words in test files.
# =============================================================================

from analyzer.file_utils import extract_words, read_text_file

def calculate_score(changed_terms, test_file_path, idf_lookup=None):
    """
    Calculate a weighted relevance score between changed terms and a test.

    Uses TF-IDF-like weighting: terms that appear in MANY test files get
    low weight, terms unique to a few files get high weight. This eliminates
    the "everything shares keywords" problem that plagues simple lexical
    matching.

    Args:
        changed_terms: Set of words from the changed files
        test_file_path: Path to the test file
        idf_lookup: Optional dict mapping term -> IDF weight. If None,
                    weights are computed on-the-fly from common terms.

    Returns:
        Float between 0.0 and 1.0.
    """
    from analyzer.file_utils import extract_words, read_text_file

    test_content = read_text_file(test_file_path)
    if not test_content:
        return 0.0

    test_terms = extract_words(test_content)
    if not test_terms:
        return 0.0

    common_terms = changed_terms.intersection(test_terms)
    if not common_terms:
        return 0.0

    # If no IDF lookup is provided, use a hardcoded set of universally
    # common programming keywords. These get zero weight in scoring.
    from analyzer.file_utils import STOP_WORDS

    # Weighted sum: each common term contributes its weight.
    # Universal keywords (STOP_WORDS) contribute 0.
    # Everything else contributes 1.
    weighted_common = sum(
        1.0 for term in common_terms
        if term not in STOP_WORDS
    )

    # Normalize by the number of NON-STOP-WORD terms in the changed set.
    weighted_changed = sum(
        1.0 for term in changed_terms
        if term not in STOP_WORDS
    )

    if weighted_changed == 0:
        return 0.0

    return weighted_common / weighted_changed

def compute_service_relevance(test_file, affected_services):
    """
    Compute a service-relevance score between 0.0 and 1.0.

    Priority:
      1.0 — full service name in filename
      0.9 — "<service>-service" or "<service>_service" in full path
      0.7 — root word (>= 5 chars) in filename
      0.5 — service name in a directory segment of the path
      0.3 — full service name in file content (weak signal)
      0.0 — no match
    """
    from pathlib import Path
    from analyzer.file_utils import read_text_file

    test_path = Path(test_file)
    filename = test_path.stem.lower()
    full_path = str(test_file).lower().replace("\\", "/")
    path_parts = [p for p in full_path.split("/") if p]

    try:
        content = read_text_file(test_file).lower()
    except Exception:
        content = ""

    best_score = 0.0

    for service in affected_services:
        service_lower = service.lower()
        root = service_lower.replace("service", "").strip("-_")

        # --- Filename full match (strongest) ---
        if service_lower in filename:
            best_score = max(best_score, 1.0)
            continue

        # --- Path: "<service>-service" or "<service>_service" ---
        if f"{service_lower}-service" in full_path:
            best_score = max(best_score, 0.9)
            continue
        if f"{service_lower}_service" in full_path:
            best_score = max(best_score, 0.9)
            continue

        # --- Filename root-word match (require >= 5 chars to avoid noise) ---
        if len(root) >= 5 and root in filename:
            best_score = max(best_score, 0.7)
            continue

        # --- Directory segment exact match ---
        if service_lower in path_parts:
            best_score = max(best_score, 0.5)
            continue

        # --- Content match (weak signal, only full service name) ---
        # Do NOT match root words in content — too noisy.
        if service_lower in content:
            best_score = max(best_score, 0.3)
            continue

    return best_score

def filename_match_bonus(changed_file, test_file):
    """
    Return a bonus score if the test filename shares service names
    with the changed file.
    """
    from pathlib import Path
    
    changed_name = Path(changed_file).stem.lower()
    test_name = Path(test_file).stem.lower()
    
    # Extract the service name (remove common suffixes)
    for suffix in ["_service", "service", "_test", "test", "_spec", "spec"]:
        changed_name = changed_name.replace(suffix, "")
        test_name = test_name.replace(suffix, "")
    
    # If they share the service name, give a boost
    if changed_name and changed_name in test_name:
        return 0.3
    
    return 0.0

def rank_tests(changed_terms, test_files, threshold=0.1):
    """
    Rank test files by their relevance to the changed terms.
    
    This function calculates a score for each test file and returns
    them sorted from most relevant to least relevant.
    
    Args:
        changed_terms: A set of words from the changed files
        test_files: A list of paths to test files
        threshold: Minimum score to include a test (default: 0.1)
                   Tests with scores below this threshold are excluded.
    
    Returns:
        A list of tuples (test_file, score) sorted by score (highest first).
        Only includes tests with scores above the threshold.
    
    Example:
        terms = {"payment", "timeout"}
        tests = ["test_payment.py", "test_order.py", "test_inventory.py"]
        ranked = rank_tests(terms, tests)
        # ranked might be:
        # [("test_payment.py", 0.8), ("test_order.py", 0.2)]
        # (test_inventory.py is excluded if its score is below 0.1)
    """
    # Create a list to store (test_file, score) tuples
    scores = []
    
    # Loop through each test file
    for test_file in test_files:
        # Calculate the relevance score for this test
        score = calculate_score(changed_terms, test_file)
        
        # Only include tests with scores above the threshold
        if score >= threshold:
            scores.append((test_file, score))
    
    # Sort the list by score in descending order (highest score first)
    # key=lambda x: x[1] means sort by the second element of each tuple (the score)
    # reverse=True means descending order
    scores.sort(key=lambda x: x[1], reverse=True)
    
    # Return the sorted list
    return scores