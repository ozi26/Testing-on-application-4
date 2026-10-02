# =============================================================================
# SCORING MODULE
# This module contains functions for calculating how relevant a test is
# to a set of changes. It uses lexical matching - comparing words in
# changed files with words in test files.
# =============================================================================

from analyzer.file_utils import extract_words, read_text_file

def calculate_score(changed_terms, test_file_path, idf_lookup=None):
    """
    Score = fraction of the CHANGED file's distinctive terms that
    appear in the test file.
    
    Uses IDF to define "distinctive": only terms with IDF above a
    threshold count toward the numerator.
    """
    from analyzer.file_utils import extract_words, read_text_file
    
    test_content = read_text_file(test_file_path)
    if not test_content:
        return 0.0
    test_terms = extract_words(test_content)
    if not test_terms:
        return 0.0
    
    # If no IDF provided, use all changed terms
    if not idf_lookup:
        common = changed_terms.intersection(test_terms)
        return len(common) / len(changed_terms) if changed_terms else 0.0
    
    # Filter changed_terms to only distinctive ones (IDF > 1.5)
    DISTINCTIVE_THRESHOLD = 1.5
    distinctive_terms = {
        t for t in changed_terms
        if idf_lookup.get(t, 0.0) > DISTINCTIVE_THRESHOLD
    }
    
    if not distinctive_terms:
        # No distinctive terms — use all
        distinctive_terms = changed_terms
    
    # Numerator: how many of the distinctive terms are in the test?
    matched = distinctive_terms.intersection(test_terms)
    
    # Score = fraction of distinctive terms matched
    return len(matched) / len(distinctive_terms)

def compute_service_relevance(test_file, affected_services):
    """
    Compute a service-relevance score between 0.0 and 1.0.

    Uses WORD BOUNDARIES and PATH SEGMENT EQUALITY, not substring
    matching, to avoid false positives like matching "streaming_service"
    inside the parent folder "media_streaming_services".
    """
    import re
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

        # --- 1. Filename full match (word-boundary aware) ---
        if re.search(rf"(?:^|[_\-.]){re.escape(service_lower)}(?:$|[_\-.])", filename):
            best_score = max(best_score, 1.0)
            continue

        # --- 2. Path SEGMENT match (not substring) ---
        matched_path = False
        for part in path_parts:
            if part in (f"{service_lower}-service", f"{service_lower}_service"):
                best_score = max(best_score, 0.95)
                matched_path = True
                break
            if part == service_lower:
                best_score = max(best_score, 0.9)
                matched_path = True
                break
        if matched_path:
            continue

        # --- 3. Filename root-word match (word boundary, min length 5) ---
        if len(root) >= 5:
            if re.search(rf"(?:^|[_\-.]){re.escape(root)}(?:$|[_\-.])", filename):
                best_score = max(best_score, 0.7)
                continue

        # --- 4. Content match — require an actual reference ---
        # Only match imports, from clauses, or URL paths.
        # Do NOT match casual mentions of the service name.
        if re.search(rf"\bimport\s+{re.escape(service_lower)}\b", content):
            best_score = max(best_score, 0.4)
            continue
        if re.search(rf"\bfrom\s+{re.escape(service_lower)}\b", content):
            best_score = max(best_score, 0.4)
            continue
        if re.search(rf"/{re.escape(service_lower)}(?:-service)?/", content):
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