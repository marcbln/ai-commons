![Minimalist AI Logo](ai-commons-logo.png)
# ai-commons

Shared Python library for interacting with Large Language Models (LLMs). Provides a common interface for different providers and handles configuration like model aliases and API keys.

## Features (Planned/Included)

*   Unified `LLMClient` for various LLM providers (e.g., OpenAI, OpenRouter, Gemini).
*   Configuration management for API keys, model aliases, and other settings (`ConfigManager`).
*   Helper utilities for common AI-related tasks.

## Development & Testing

To set up the development environment and run tests for the `ai-commons` library:

1.  **Install `uv`** (if not already installed):
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Source your shell profile or open a new terminal to make uv available
    # e.g., source ~/.bashrc, source ~/.zshrc, etc.
    ```

2.  **Clone the repository**:
    ```bash
    git clone https://github.com/marcbln/ai-commons.git
    cd ai-commons
    ```

3.  **Create and activate a virtual environment** (optional but recommended):
    ```bash
    uv venv .venv
    source .venv/bin/activate  # On Linux/macOS
    # .venv\Scripts\activate   # On Windows
    ```

4.  **Install dependencies** (including development dependencies specified in `pyproject.toml`):
    ```bash
    uv pip install -e ".[dev]"
    ```
    *Note: `-e` installs the project in editable mode. `.[dev]` installs the optional "dev" dependencies.*

5.  **Run tests** using pytest (managed by `uv`):
    ```bash
    uv run pytest
    ```
    *(This assumes your tests are in a `tests/` directory or discoverable by pytest from the root. Your `pyproject.toml` also specifies `pythonpath = "src"` for pytest, which is good.)*

## Installation & Usage as a Dependency

You can use `ai-commons` in your own Python projects managed with `uv`.

### 1. Adding to a `uv`-managed Project

If you have an existing Python project managed with `uv` (i.e., it has a `pyproject.toml`), follow these steps:

1.  **Navigate to your project's root directory.**

2.  **Add `ai-commons` as a Git dependency:**
    You can do this in two ways:

    **Option A: Using `uv add` (Recommended)**
    This command will automatically update your `pyproject.toml`:
    ```bash
    uv add ai-commons --git https://github.com/marcbln/ai-commons.git --rev main
    ```
    *   Replace `main` with a specific tag (e.g., `v0.1.0`) or commit SHA for a more stable dependency.

    **Option B: Manually editing `pyproject.toml`**
    Open your project's `pyproject.toml` file and add `ai-commons` to your `[project.dependencies]` list:
    ```toml
    [project]
    name = "my-awesome-project"
    version = "0.1.0"
    dependencies = [
        # ... other dependencies ...
        "ai-commons@git+https://github.com/marcbln/ai-commons.git@main",
    ]
    # ... rest of your pyproject.toml ...
    ```
    *   Again, you can replace `@main` with `@<tag_name>` or `@<commit_sha>`.
    *   Alternatively, using the TOML table format (often preferred for clarity with Git dependencies):
        ```toml
        [project]
        name = "my-awesome-project"
        version = "0.1.0"
        dependencies = [
            # ... other dependencies ...
        ]

        [project.dependencies]
        # ... other dependencies ...
        ai-commons = { git = "https://github.com/marcbln/ai-commons.git", rev = "main" }
        ```
        (Note: If you have existing dependencies directly in the `[project].dependencies` array, you might need to adjust. `uv add` handles this best).

3.  **Install/Update dependencies:**
    After modifying `pyproject.toml` (either with `uv add` or manually), sync your environment:
    ```bash
    uv pip sync
    ```
    Or, if you are installing for the first time or want to ensure all dependencies are met:
    ```bash
    uv pip install -e .  # If it's the project you are currently developing
    # or simply `uv install` if you don't need editable mode for the main project
    ```

4.  **Use `ai-commons` in your code:**
    ```python
    from ai_commons.config import ConfigManager
    from ai_commons.llm import LLMClient

    # Initialize configuration (ai-commons will look for .env, config files, or env vars)
    config_manager = ConfigManager()
    api_key = config_manager.get_api_key("openrouter") # Or your preferred provider
    model_name = config_manager.get_model_alias("default_chat")

    if not api_key:
        print("API key not found. Please set it via environment variables or ai-commons config.")
        exit()

    client = LLMClient(provider="openrouter", api_key=api_key) # Or client = LLMClient(config=config_manager)

    try:
        prompt = "Explain the concept of a Large Language Model in one sentence."
        response = client.generate_text(prompt=prompt, model=model_name)
        print(f"LLM Response: {response}")
    except Exception as e:
        print(f"An error occurred: {e}")
    ```

### 2. Using in a `uv` Single File App (SFA)

`uv` allows you to run Python scripts with their dependencies defined directly in the file. This is great for small utilities or scripts.

1.  **Create your Python script** (e.g., `my_ai_script.py`):
    At the top of your script, define `ai-commons` as a dependency:

    ```python
    # /// script
    # requires-python = ">=3.9"
    # dependencies = [
    #   "ai-commons@git+https://github.com/marcbln/ai-commons.git@main",
    #   # Add any other dependencies your script needs, e.g., "python-dotenv"
    #   "python-dotenv"
    # ]
    # ///

    import os
    from dotenv import load_dotenv
    from ai_commons.config import ConfigManager
    from ai_commons.llm import LLMClient

    # Load environment variables from a .env file (optional, for API keys)
    load_dotenv()

    def run_llm_task():
        # ai-commons' ConfigManager will also try to load .env or use existing env vars
        config = ConfigManager()
        api_key = config.get_api_key("openrouter") # Provider name defined in your ai-commons config
        model_alias = config.get_model_alias("default_chat") # Alias defined in your ai-commons config

        if not api_key:
            print("Error: OpenRouter API key not found.")
            print("Please ensure OPENROUTER_API_KEY is set in your environment or .env file,")
            print("or configure it via ai_commons configuration methods.")
            return

        # You might pass the whole config object, or specific parts like api_key
        # depending on how LLMClient is designed in ai-commons
        llm_client = LLMClient(provider="openrouter", api_key=api_key)
        # Or potentially: llm_client = LLMClient(config=config)

        try:
            user_prompt = "What is the capital of France?"
            print(f"Sending prompt: '{user_prompt}' using model '{model_alias}'...")
            response = llm_client.generate_text(prompt=user_prompt, model=model_alias)
            print(f"LLM says: {response}")
        except Exception as e:
            print(f"An error occurred: {e}")

    if __name__ == "__main__":
        # Example: Create a dummy .env file for the SFA if it doesn't exist
        # In a real scenario, the user would manage their .env or environment variables
        if not os.path.exists(".env"):
            with open(".env", "w") as f:
                f.write("# OPENROUTER_API_KEY=your_actual_openrouter_api_key_here\n")
                f.write("# ANTHROPIC_API_KEY=your_actual_anthropic_api_key_here\n")
            print("Created a dummy .env file. Please edit it with your actual API keys.")

        # Create a dummy ai-commons.yaml if not present for the SFA example
        # to showcase model aliasing.
        if not os.path.exists("ai-commons.yaml"):
            with open("ai-commons.yaml", "w") as f:
                f.write(
                    "default_provider: openrouter\n"
                    "api_keys:\n"
                    "  # Keys can be here or in .env (recommended)\n"
                    "providers:\n"
                    "  openrouter:\n"
                    "    # api_key: sk-or-...\n"
                    "    models:\n"
                    "      default_chat: openai/gpt-3.5-turbo\n"
                    "      default_instruct: google/gemini-flash-1.5\n"
                )
            print("Created a dummy ai-commons.yaml. Configure as needed.")

        run_llm_task()

    ```
    *   **Important:** Replace `@main` with a specific tag or commit SHA for stability in production scripts.
    *   The `ai-commons` library itself should handle how it discovers API keys (e.g., from environment variables like `OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY`, or from its own configuration file `ai-commons.yaml`). The SFA example shows loading a `.env` file as one common pattern, but `ai-commons`'s `ConfigManager` should be the primary way it gets this info.

2.  **Run the script using `uv`:**
    ```bash
    uv run my_ai_script.py
    ```
    `uv` will automatically detect the `/// script` block, resolve and install `ai-commons` (and any other specified dependencies) into a temporary environment, and then execute your script.

    **Note on API Keys for SFAs:**
    For SFAs that require API keys (like `ai-commons` does), ensure the necessary environment variables are set in the shell where you run `uv run ...`, or that your SFA (or `ai-commons` itself) loads them from a known location (e.g., a `.env` file or a global config file). The example above includes `python-dotenv` and creates dummy config files to illustrate.

## Configuration

`ai-commons` typically manages its configuration (API keys, model aliases) through:
1.  Environment Variables (e.g., `OPENROUTER_API_KEY`).
2.  A `ai-commons.yaml` (or similar) configuration file in the project root or user's home directory.
3.  A `.env` file.

Refer to the `ai_commons.config.ConfigManager` class for specific details on how configuration is loaded.

---

Remember to adapt the example code snippets (especially the SFA example and API key handling) to match the exact public API and configuration mechanisms of your `ai-commons` library as it evolves.