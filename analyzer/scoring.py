# =============================================================================
# SCORING MODULE
# This module contains functions for calculating how relevant a test is
# to a set of changes. It uses lexical matching - comparing words in
# changed files with words in test files.
# =============================================================================

from analyzer.file_utils import extract_words, read_text_file

def calculate_score(changed_terms, test_file_path, idf_lookup=None):
    """
    Calculate a TF-IDF-weighted relevance score between changed terms
    and a test file.

    This function computes how relevant a test file is to a set of changed
    source/config terms. It uses inverse document frequency (IDF) weights
    when provided, which down-weights terms that appear in many files
    (generic keywords) and up-weights terms that appear in few files
    (distinctive domain terms).

    Args:
        changed_terms: A set of lowercase words extracted from the changed files
        test_file_path: Path to the test file to score
        idf_lookup: Optional dict mapping each term to its IDF weight.
                    If provided, scoring uses weighted sums.
                    If None, scoring falls back to simple ratio.

    Returns:
        A float between 0.0 and 1.0 representing the relevance score.
        Higher scores mean the test is more likely to be affected.

    Examples:
        changed = {"streaming", "playback", "manifest", "media"}
        score = calculate_score(changed, "tests/test_streaming.py", idf_lookup)
        # Returns a high score if the test file contains those terms
    """
    # Import here to avoid a circular import with analyzer.file_utils
    from analyzer.file_utils import extract_words, read_text_file

    # -------------------------------------------------------------------------
    # 1. Read and tokenize the test file
    # -------------------------------------------------------------------------
    test_content = read_text_file(test_file_path)

    # If the test file can't be read, it can't be affected
    if not test_content:
        return 0.0

    test_terms = extract_words(test_content)

    # If the test file has no extractable terms, skip it
    if not test_terms:
        return 0.0

    # -------------------------------------------------------------------------
    # 2. Find common terms between the changed set and the test file
    # -------------------------------------------------------------------------
    common_terms = changed_terms.intersection(test_terms)

    # No overlap at all → zero relevance
    if not common_terms:
        return 0.0

    # -------------------------------------------------------------------------
    # 3. If no IDF table is provided, fall back to simple ratio
    #    This is less accurate but always works.
    # -------------------------------------------------------------------------
    if not idf_lookup:
        # Simple ratio: what fraction of changed terms appear in the test?
        return len(common_terms) / len(changed_terms)

    # -------------------------------------------------------------------------
    # 4. IDF-weighted scoring (the preferred path)
    #    Numerator: sum of IDF weights for terms present in BOTH sets
    #    Denominator: sum of IDF weights for ALL changed terms
    # -------------------------------------------------------------------------
    weighted_common = 0.0
    for term in common_terms:
        # Default weight of 1.0 if term is somehow missing from the lookup
        weighted_common += idf_lookup.get(term, 1.0)

    weighted_changed = 0.0
    for term in changed_terms:
        weighted_changed += idf_lookup.get(term, 1.0)

    # Guard against division by zero (only possible if the IDF table is empty)
    if weighted_changed == 0:
        return 0.0

    # -------------------------------------------------------------------------
    # 5. Return the normalized weighted score (0.0 to 1.0)
    # -------------------------------------------------------------------------
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

def calculate_corpus_idf(file_paths):
    """
    Compute IDF (Inverse Document Frequency) weights for every term
    appearing in a corpus of files.

    IDF formula: log(N / (1 + df))
    Where:
        N  = total number of files in the corpus
        df = number of files containing the term

    Terms appearing in almost every file get weight near 0.
    Terms appearing in only a few files get high weight.

    Args:
        file_paths: List of file paths (source + config + test combined)

    Returns:
        Dict mapping term -> IDF weight (float >= 0).
    """
    import math
    from analyzer.file_utils import extract_words, read_text_file

    # Build document frequency table
    doc_freq = {}
    N = 0

    for path in file_paths:
        content = read_text_file(path)
        if not content:
            continue
        N += 1
        terms = extract_words(content)
        for term in terms:
            doc_freq[term] = doc_freq.get(term, 0) + 1

    if N == 0:
        return {}

    # Compute IDF for each term
    idf = {}
    for term, df in doc_freq.items():
        # Add 1 to smooth out the log for rare terms
        idf[term] = math.log(N / (1 + df)) if N > 1 else 1.0

    return idf