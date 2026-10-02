# =============================================================================
# FILE UTILITIES MODULE
# This module contains helper functions for reading files and extracting
# words from text. These functions are used by both the code parser and
# the configuration parser.
# =============================================================================

from ast import pattern
import re                           # 're' is Python's regular expression library
from pathlib import Path
from pathlib import Path               # 'Path' helps us work with file paths easily


def read_text_file(file_path):
    """
    Read a text file and return its contents as a string.
    
    Args:
        file_path: The path to the file we want to read (can be string or Path)
    
    Returns:
        A string containing the entire file contents.
        If the file cannot be read, returns an empty string.
    
    Example:
        content = read_text_file("config.yaml")
        # content now contains the text inside config.yaml
    """
    try:
        # Path(file_path) converts the input to a Path object
        # .read_text() reads the file and returns its contents as a string
        # encoding="utf-8" ensures we can read special characters
        return Path(file_path).read_text(encoding="utf-8")
    except (FileNotFoundError, PermissionError, UnicodeDecodeError):
        # If the file doesn't exist, we don't have permission, or it's not
        # readable as text, we return an empty string instead of crashing
        return ""


# -----------------------------------------------------------------------------
# STOP WORDS
# Common programming keywords that appear in every language and thus
# create noise in lexical matching. Filtering these out dramatically
# improves test selection precision.
# -----------------------------------------------------------------------------
# Universal programming stop-words — shared across ALL languages.
# Terms here are weighted ZERO in scoring because they appear in
# virtually every file regardless of domain.

STOP_WORDS = {

    # ---- Language keywords (universal) ----
    "if", "else", "elif", "for", "while", "do", "switch", "case",
    "break", "continue", "return", "yield", "try", "catch",
    "except", "finally", "throw", "throws", "raise", "class",
    "interface", "struct", "enum", "public", "private", "protected",
    "static", "final", "const", "let", "var", "function", "func",
    "def", "method", "new", "this", "self", "super", "extends",
    "implements", "import", "from", "require", "export", "module",
    "package", "namespace", "using", "include", "async", "await",
    "promise", "callback", "resolve", "reject", "lambda", "global",
    "nonlocal", "pass", "assert", "with", "as", "go", "defer",
    "chan", "select", "context", "fmt", "task", "get", "set",
    "init", "main",

    # ---- Type names ----
    "int", "integer", "float", "double", "string", "str", "bool",
    "boolean", "char", "byte", "long", "short", "unsigned", "signed",
    "void", "null", "nil", "none", "true", "false", "undefined",
    "nan", "inf", "any", "object", "var", "variable",

    # ---- Common variable names ----
    "err", "error", "errors", "msg", "message", "value", "val",
    "result", "res", "req", "request", "response", "data", "item",
    "items", "obj", "array", "list", "dict", "map", "set", "key",
    "name", "type", "kind", "id", "index", "count", "length",
    "size", "args", "kwargs", "params", "options", "config",
    "settings", "setting", "input", "output", "source", "target",
    "dest", "base", "root", "file", "path", "url", "uri", "http",
    "https", "host", "port", "user", "users", "admin", "session",
    "token", "auth", "login", "create", "read", "update", "delete",
    "list", "find", "search", "add", "remove", "push", "pop",
    "save", "load", "fetch", "send", "sent",

    # ---- Common English words (from comments/strings) ----
    "the", "a", "an", "and", "or", "not", "is", "are", "was",
    "were", "this", "that", "these", "those", "with", "without",
    "for", "of", "to", "in", "on", "at", "by", "as", "if", "then",
    "when", "where", "will", "should", "would", "could", "have",
    "has", "had", "all", "any", "some", "each", "every", "only",
    "also", "just", "can", "cannot", "but", "or", "so", "than",
    "too", "very", "much", "many", "more", "less", "most", "least",
    "which", "who", "what", "how", "why", "where", "when", "while",
    "here", "there", "now", "then", "still", "already", "yet",
    "always", "never", "often", "sometimes", "usually", "once",
    "twice", "again", "back", "forward", "up", "down", "over",
    "under", "above", "below", "before", "after", "during", "between",
    "into", "out", "off", "on", "through", "around", "about",
    "against", "along", "across", "behind", "beside", "beyond",

    # ---- Common verb forms ----
    "is", "are", "was", "were", "be", "been", "being", "have",
    "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "can", "could", "may", "might", "must", "ought",
    "need", "dare", "used", "get", "got", "getting", "make",
    "made", "making", "take", "took", "taken", "taking", "come",
    "came", "coming", "see", "saw", "seen", "seeing", "know",
    "knew", "known", "knowing", "think", "thought", "thinking",
    "want", "wanted", "wanting", "use", "used", "using", "find",
    "found", "finding", "give", "gave", "given", "giving",
    "tell", "told", "telling", "work", "worked", "working",
    "call", "called", "calling", "try", "tried", "trying",
    "ask", "asked", "asking", "feel", "felt", "feeling",
    "seem", "seemed", "seeming", "leave", "left", "leaving",
    "look", "looked", "looking", "show", "showed", "showing",

    # ---- API / HTTP vocabulary (shared across all languages) ----
    "route", "router", "endpoint", "api", "rest", "graphql",
    "json", "jsonify", "parse", "stringify", "serialize",
    "deserialize", "body", "header", "headers", "param", "params",
    "query", "payload", "status", "code", "statuscode", "content",
    "mime", "cookie", "middleware", "handler", "controller",
    "service", "client", "server", "app", "express", "flask",
    "fastapi", "django", "spring", "httpstatus", "responseentity",
    "requestentity", "catalog", "streaming", "auth", "notification",
    "recommendation", "subscription", "history", "watchlist",

    # ---- Test framework keywords ----
    "describe", "test", "tests", "it", "expect", "assert", "should",
    "before", "after", "beforeeach", "aftereach", "jest", "mocha",
    "jasmine", "pytest", "unittest", "setup", "teardown", "fixture",
    "mock", "stub", "spy", "patch", "monkeypatch", "unit",
    "integration", "spec", "specs", "check", "verify", "validate",
    "success", "failure", "pass", "fail", "given", "when", "then",
    "arrange", "act", "assert",

    # ---- Common file/config vocabulary ----
    "config", "configuration", "settings", "option", "options",
    "default", "enabled", "disabled", "timeout", "retry", "attempts",
    "protocol", "scheme", "version", "env", "environment", "dev",
    "prod", "staging", "database", "db", "cache", "redis", "queue",
    "topic", "channel", "log", "logger", "logging", "level",
    "debug", "info", "warn", "error", "max", "min", "limit",
    "threshold", "size", "count", "interval", "unknown", "standard",
    "net", "support", "declare", "define", "overridden", "preference",
}


def extract_words(text):
    """Extract meaningful words, excluding stop-words."""
    import re
    pattern = r"[A-Za-z_][A-Za-z0-9_]*"
    words = re.findall(pattern, text)

    result = set()
    for word in words:
        wl = word.lower()
        if wl in STOP_WORDS:
            continue
        if len(wl) <= 2:
            continue
        if wl.isdigit():
            continue
        result.add(wl)

    return result

def get_file_extension(file_path):
    """
    Get the file extension from a file path.
    
    Args:
        file_path: The path to the file (can be string or Path)
    
    Returns:
        The file extension without the dot, in lowercase.
        Returns an empty string if there's no extension.
    
    Example:
        ext = get_file_extension("config.yaml")
        # ext is now "yaml"
    """
    # Path(file_path).suffix returns the extension including the dot
    # Example: ".yaml" or ".py"
    # We remove the dot with [1:] and convert to lowercase
    return Path(file_path).suffix.lower().lstrip(".")


def is_config_file(file_path):
    """
    Check if a file is a configuration file, using language-agnostic
    heuristics based on name patterns and extensions.
    """
    from analyzer.config import (
        CONFIG_EXTENSIONS,
        CONFIG_NAME_MARKERS,
        CONFIG_FILE_NAMES,
        SOURCE_EXTENSIONS,
    )

    path = Path(file_path)
    filename = path.name.lower()
    extension = path.suffix.lower().lstrip(".")

    # ---- Rule 0: File is inside a "config" or "settings" directory ----
    # This catches: rideshareservices/config/driver_config.py
    #               src/config/database.py
    #               app/settings/base.py
    for part in path.parts[:-1]:       # exclude the filename itself
        part_lower = part.lower()
        if part_lower in ("config", "configs", "conf", "settings",
                          "configuration", "env", "environments"):
            return True

    # ---- Rule 1: Exact filename match ----
    if filename in CONFIG_FILE_NAMES:
        return True

    # ---- Rule 2: Name contains a config marker ----
    for marker in CONFIG_NAME_MARKERS:
        if marker in filename:
            return True

    # ---- Rule 3: Extension is a known config extension ----
    if extension in CONFIG_EXTENSIONS and extension not in SOURCE_EXTENSIONS:
        return True

    # ---- Rule 4: Filename starts with config/settings ----
    if filename.startswith(("config", "settings", "conf.")):
        return True

    return False


def is_source_file(file_path):
    """
    Check if a file is a source code file based on its extension.
    
    Args:
        file_path: The path to the file
    
    Returns:
        True if the file has a source code extension, False otherwise.
    
    Example:
        is_source_file("order_service.py")  # Returns True
        is_source_file("config.yaml")       # Returns False
    """
    # Import the SOURCE_EXTENSIONS set from our config module
    from analyzer.config import SOURCE_EXTENSIONS
    
    # Get the file extension and check if it's in our set of source extensions
    return get_file_extension(file_path) in SOURCE_EXTENSIONS


def is_test_file(file_path):
    """
    Check if a file is a test file based on language-agnostic name patterns.
    
    Works for:
      - test_order.py, order_test.py         (Python)
      - OrderTest.java, OrderTests.java      (Java)
      - order.test.js, order.spec.js         (JavaScript)
      - order_test.go                        (Go)
      - order_spec.rb                        (Ruby)
      - OrderTests.cs                        (.NET)
      - order.spec.ts                        (TypeScript)
    
    Args:
        file_path: Path to the file
    
    Returns:
        True if the file appears to be a test file.
    """
    from analyzer.config import TEST_FILE_PATTERNS, SOURCE_EXTENSIONS
    
    path = Path(file_path)
    filename = path.name.lower()
    extension = path.suffix.lower().lstrip(".")
    
    # Only files with source-code extensions can be tests
    if extension not in SOURCE_EXTENSIONS:
        return False
    
    # Check for any test pattern in the filename
    return any(pattern in filename for pattern in TEST_FILE_PATTERNS)