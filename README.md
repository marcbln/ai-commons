![Minimalist AI Logo](ai-commons-logo.png)
# ai-commons

Shared Python library for interacting with Large Language Models (LLMs). Provides a common interface for different providers and handles configuration like model aliases and API keys.


## Testing

To run the tests for the `ai-commons` library, follow these steps:

1.  **Install `uv`** (if not already installed):
    ```bash
    curl -sSL https://uv.rs/install.sh | sh
    ```
    *(Note: Ensure `uv` is in your PATH after installation)*

2.  **Navigate to the project root**:
    ```bash
    cd /path/to/ai-commons 
    ``` 
    *(Replace `/path/to/ai-commons` with the actual path to the project directory)*

3.  **Install dependencies** (including development dependencies):
    ```bash
    uv pip install -r requirements.txt
    ```

4.  **Run tests** using pytest (managed by `uv`):
    ```bash
    uv run pytest tests/
## Installation as a Dependency

To use this library as a dependency in your Python project:

### Using uv (Recommended)

1. Add the dependency to your `pyproject.toml`:
   ```toml
   ai-commons = { path = "/path/to/ai-commons" }
   ```

2. Install the dependency:
   ```bash
   uv install
   ```

### Using pip

1. Clone the repository:
   ```bash
   git clone https://github.com/marcbln/ai-commons.git
   ```

2. Add the dependency to your `requirements.txt`:
   ```text
   -e ./ai-commons
   ```

3. Install the dependency:
   ```bash
   pip install -r requirements.txt
   ```

Note: If this is a private repository, you'll need to authenticate with GitHub. For uv, this can be done via a GitHub Personal Access Token. For pip, you may need to use `--extra-index-url` with your GitHub token.
## Installation as a Dependency

To use this library as a dependency in your Python project:

### Using uv (Recommended)

1. Add the dependency to your `pyproject.toml`:
   ```toml
   ai-commons = { git = "https://github.com/marcbln/ai-commons.git", rev = "main" }
   ```

2. Install the dependency:
   ```bash
   uv install
   ```

### Using pip

1. Clone the repository:
   ```bash
   git clone https://github.com/marcbln/ai-commons.git
   ```

2. Add the dependency to your `requirements.txt`:
   ```text
   -e ./ai-commons
   ```

3. Install the dependency:
   ```bash
   pip install -r requirements.txt
   ```

Note: If this is a private repository, you'll need to authenticate with GitHub. For uv, this can be done via a GitHub Personal Access Token. For pip, you may need to use `--extra-index-url` with your GitHub token.
