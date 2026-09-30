# =============================================================================
# CONFIGURATION MODULE
# Language-agnostic detection of source files, config files, and test files.
# No per-project modifications needed.
# =============================================================================

# -----------------------------------------------------------------------------
# UNIVERSAL CONFIG FILE EXTENSIONS
# These extensions are used for configuration in virtually every language.
# If an extension could be BOTH config and source (like .js or .json),
# it must be disambiguated by filename pattern (see CONFIG_NAME_MARKERS below).
# -----------------------------------------------------------------------------
CONFIG_EXTENSIONS = {
    # Structured data formats (universally used for config)
    "yaml", "yml", "toml", "ini", "cfg", "conf",
    "properties", "env", "hcl", "tf", "tfvars",
    
    # JavaScript config extensions
    # NOTE: .json and .js are ambiguous — handled by name markers, not extension.
    
    # Other common config formats
    "dockerfile",       # Dockerfile
    "xml",              # XML configs (Java, .NET, Maven, etc.)
}

# -----------------------------------------------------------------------------
# CONFIG NAME MARKERS (case-insensitive)
# If a filename contains any of these substrings, it's treated as a config file
# REGARDLESS of its extension. This handles:
#   - order.config.js         (JavaScript)
#   - server.config.ts        (TypeScript)
#   - app.config.json         (.NET)
#   - settings.config.py      (Python)
#   - payment.conf            (generic)
#   - app.settings            (.NET)
#   - web.config              (.NET)
#   - app.config              (.NET / Python)
#   - .env.local              (Node.js)
#   - application.properties  (Spring)
#   - application.yml         (Spring)
# -----------------------------------------------------------------------------
CONFIG_NAME_MARKERS = (
    ".config.",         # order.config.js, app.config.ts, foo.config.json
    "config.",          # config.json, config.yaml (at start of name)
    ".conf.",           # app.conf.js
    ".settings",        # app.settings
    ".env",             # .env, .env.local, .env.production
    "-config.",         # my-config.json
    "_config.",         # my_config.yaml
)

# Filenames that are ALWAYS configuration, no matter where they live
CONFIG_FILE_NAMES = {
    # Universal
    "dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "jenkinsfile", "makefile", "vagrantfile",
    
    # JavaScript ecosystem
    "package.json", "tsconfig.json", "jsconfig.json",
    "jest.config.js", "jest.config.ts", "vitest.config.js",
    "babel.config.js", "webpack.config.js", "vite.config.js",
    "rollup.config.js", "eslint.config.js", "prettier.config.js",
    ".eslintrc", ".eslintrc.json", ".eslintrc.js",
    ".prettierrc", ".prettierrc.json", ".prettierrc.js",
    ".babelrc", ".browserslistrc",
    
    # Python ecosystem
    "setup.py", "setup.cfg", "pyproject.toml", "tox.ini",
    "requirements.txt", "requirements-dev.txt", "pipfile",
    "poetry.lock", "alembic.ini",
    "pytest.ini", ".pylintrc", ".flake8",
    
    # Java / JVM ecosystem
    "pom.xml", "build.gradle", "build.gradle.kts",
    "settings.gradle", "gradle.properties",
    "application.properties", "application.yml", "application.yaml",
    "logback.xml", "log4j2.xml",
    
    # .NET ecosystem
    "web.config", "app.config", "appsettings.json",
    "appsettings.development.json", "appsettings.production.json",
    "nuget.config", "global.json",
    
    # Go ecosystem
    "go.mod", "go.sum",
    
    # Rust ecosystem
    "cargo.toml", "cargo.lock",
    
    # Ruby ecosystem
    "gemfile", "gemfile.lock", "rakefile",
    
    # PHP ecosystem
    "composer.json", "composer.lock", ".htaccess",
    
    # Kubernetes / infrastructure
    "chart.yaml", "values.yaml", ".gitlab-ci.yml",
    ".github", ".gitignore", ".dockerignore",
    
    # Generic
    ".editorconfig", ".gitattributes",
}

# -----------------------------------------------------------------------------
# SOURCE CODE EXTENSIONS
# Extensions that are SOURCE CODE. If a filename also matches a CONFIG name
# marker, the config marker wins (e.g., order.config.js is config, but
# order_service.js is source).
# -----------------------------------------------------------------------------
SOURCE_EXTENSIONS = {
    # Python
    "py", "pyx", "pxd", "pyi",
    # JavaScript / TypeScript
    "js", "jsx", "mjs", "cjs", "ts", "tsx",
    # Java / JVM
    "java", "kt", "kts", "scala", "groovy",
    # C family
    "c", "h", "cpp", "cc", "cxx", "hpp", "hh", "hxx",
    "cs", "fs", "vb",
    # Go
    "go",
    # Rust
    "rs",
    # Ruby
    "rb", "erb",
    # PHP
    "php", "phtml",
    # Swift / Objective-C
    "swift", "m", "mm",
    # Shell
    "sh", "bash", "zsh", "fish", "ps1",
    # Web
    "html", "htm", "css", "scss", "sass", "less", "vue", "svelte",
    # Data / query languages
    "sql", "graphql", "gql",
    # Functional
    "ex", "exs", "erl", "hrl", "hs", "lhs", "ml", "mli", "clj", "cljs",
    # Other
    "dart", "lua", "pl", "pm", "r", "jl", "nim", "zig", "v",
}

# -----------------------------------------------------------------------------
# TEST NAME MARKERS (case-insensitive)
# If a filename contains one of these patterns, it's treated as a test file.
# Works across any language.
# -----------------------------------------------------------------------------
TEST_FILE_PATTERNS = (
    # Python
    "test_", "_test", "_tests",
    # Java / JVM
    "test", "tests", "itest", "ittest", "integrationtest",
    # JavaScript / TypeScript
    ".test.", ".spec.", "_test.", "_spec.",
    # Go
    "_test",           # foo_test.go
    # Ruby
    "_spec", "spec_",
    # .NET
    ".tests.", "tests.", "test.",
    # PHP
    "testcase", "test.php",
    # Generic
    "spec",
)