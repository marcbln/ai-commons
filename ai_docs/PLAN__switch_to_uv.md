# Plan: Switch ai-commons from Poetry to uv/hatchling

**Goal:** Migrate the project's dependency management and build system from Poetry to `uv` and `hatchling`.

**Reason:** User request to align with other projects and potentially leverage `uv`'s performance benefits.

**Steps:**

1.  **Modify `pyproject.toml`:**
    *   Replace the `[build-system]` section to use `hatchling`:
        ```toml
        [build-system]
        requires = ["hatchling"]
        build-backend = "hatchling.build"
        ```
    *   Remove the `[tool.setuptools.package-data]` section (if present after potential previous modifications, though the target state doesn't have it).
    *   Ensure the `[project]` and `[project.optional-dependencies]` sections remain standard and compatible.
    *   Keep `[tool.pytest.ini_options]` as is.
    *   **Target `pyproject.toml`:**
        ```toml
        [build-system]
        requires = ["hatchling"]
        build-backend = "hatchling.build"

        [project]
        name = "ai-commons"
        version = "0.1.0"
        description = "Shared LLM interaction library"
        authors = [{name="Your Name", email="your@email.com"}]
        license = {text = "MIT"}
        dependencies = [
            "openai>=1.0.0",
            "requests>=2.31.0",
            "PyYAML>=6.0.1",
            "typing-extensions",
        ]
        requires-python = "^3.9"

        [project.optional-dependencies]
        dev = [
            "pytest",
            "pytest-cov",
            "pytest-mock",
        ]

        [tool.pytest.ini_options]
        pythonpath = "src"
        ```

2.  **Remove `poetry.lock`:** Delete the existing `poetry.lock` file as it's specific to Poetry and will be replaced by `uv`'s mechanisms (e.g., `uv pip freeze > requirements.txt` or `uv lock`).

3.  **Update Environment/Workflow:**
    *   Install dependencies using `uv` (e.g., `uv pip install -r requirements.txt` or `uv sync` if using `uv lock`).
    *   Update any relevant documentation (like `README.md`) or CI/CD scripts to use `uv` commands instead of `poetry`.

**Implementation:** Requires switching to a mode with file writing and deletion capabilities (e.g., `code` mode).