Okay, here is a detailed plan for creating the new shared LLM library.

**Plan: Create Shared LLM Library (`ai-commons`)**

**1. Goal:**

Create a standalone Python library named `ai-commons` that encapsulates shared functionality for interacting with LLMs, including model alias resolution, provider handling (OpenAI, OpenRouter), API client logic, and configuration management. This library will serve as a common dependency for the `aicoder` and `ai-git` projects, eliminating code duplication and promoting consistency.

**2. Library Name & Purpose:**

*   **Project/Repo Name:** `ai-commons`
*   **Python Package Name:** `ai_commons`
*   **Purpose:** To provide a robust, reusable, and maintainable core for interacting with various LLM APIs, managing configurations like model aliases, and handling common tasks required by AI-powered tools.

**3. Directory Structure:**

```
ai-commons/
├── src/
│   └── ai_commons/
│       ├── __init__.py
│       ├── client.py           # Main LLMClient class
│       ├── config.py           # Configuration constants (base URLs, etc.)
│       ├── exceptions.py       # Custom exception classes
│       ├── providers/          # Provider-specific adapters
│       │   ├── __init__.py
│       │   ├── base.py         # Abstract LLMProvider base class
│       │   ├── openai_provider.py
│       │   └── openrouter_provider.py
│       ├── data/               # Packaged data files
│       │   └── model-aliases.yaml
│       └── utils/              # Optional: Shared utilities (e.g., logging)
│           └── __init__.py
├── tests/                  # Unit tests
│   ├── __init__.py
│   ├── test_client.py
│   ├── test_providers.py
│   └── test_config.py
├── .gitignore
├── LICENSE                 # Choose an appropriate license (e.g., ALL, MIT)
├── pyproject.toml          # Project definition and dependencies
└── README.md               # Library documentation
```

**4. Dependencies (`pyproject.toml`):**

*   **Core:**
    *   `openai>=1.0.0` (Provides the client structure, also used for DeepSeek-like APIs)
    *   `requests>=2.31.0` (For OpenRouter HTTP calls - consider `httpx` if async is needed later)
    *   `PyYAML>=6.0.2` (For loading `model-aliases.yaml`)
    *   `python-dotenv>=1.0.0` (Optional, but helpful for loading env vars during testing/dev)
    *   `rich>=13.0.0` (Optional, for internal logging/output if desired)
*   **Development:**
    *   `pytest`
    *   `pytest-cov`
    *   (Potentially `pytest-mock` if needed for API testing)

**5. Core Components Implementation Details:**

*   **`src/ai_commons/exceptions.py`:**
    *   Define custom exceptions for better error handling:
        *   `LLMClientError(Exception)`: Base exception for the library.
        *   `ConfigurationError(LLMClientError)`: For issues loading/parsing config.
        *   `ModelAliasError(ConfigurationError)`: For unknown aliases.
        *   `APIKeyError(LLMClientError)`: For missing or invalid API keys.
        *   `UnknownProviderError(LLMClientError)`: If model prefix doesn't match known providers.
        *   `APIRequestError(LLMClientError)`: For errors during the actual API call.

*   **`src/ai_commons/config.py`:**
    *   Define constants like `OPENROUTER_API_BASE_URL`, `OPENAI_API_BASE_URL`, `DEEPSEEK_API_BASE_URL` (if supporting directly), default timeouts, etc.

*   **`src/ai_commons/data/model-aliases.yaml`:**
    *   Consolidated list of aliases from both existing projects. Ensure it's included as package data in `pyproject.toml` (using `[tool.hatch.build.targets.wheel]` or `[tool.setuptools]` config).

*   **`src/ai_commons/providers/base.py`:**
    *   Define an abstract base class `LLMProvider(ABC)`:
        *   `@abstractmethod def __init__(self, api_key: str, base_url: Optional[str] = None):`
        *   `@abstractmethod def create_completion(self, model: str, messages: list, **kwargs) -> str:` (Define common parameters, allow others via `**kwargs`)

*   **`src/ai_commons/providers/openai_provider.py`:**
    *   Implement `OpenAIProvider(LLMProvider)` (Handles OpenAI and DeepSeek-compatible APIs).
    *   Use the `openai` library.
    *   Handle `base_url` switching.
    *   Implement `create_completion`.

*   **`src/ai_commons/providers/openrouter_provider.py`:**
    *   Implement `OpenRouterProvider(LLMProvider)`.
    *   Use the `requests` library.
    *   Handle specific headers (`HTTP-Referer`, `X-Title`).
    *   Implement `create_completion`.

*   **`src/ai_commons/client.py`:**
    *   Define the main `LLMClient` class.
    *   **`__init__(self, model_identifier: str, api_key: Optional[str] = None)`:**
        *   Store `model_identifier`.
        *   Call internal `_resolve_alias_and_provider()` to set `self.resolved_model`, `self.provider_name`, `self.api_base_url`, `self.model_name_for_api`.
        *   Retrieve the correct API key using `_get_api_key()`. Handle `APIKeyError`.
        *   Instantiate the correct provider adapter (e.g., `self.provider = OpenAIProvider(api_key=self.api_key, base_url=self.api_base_url)`).
    *   **`_resolve_alias_and_provider(self) -> None`:** (Internal method called by `__init__`)
        *   Load aliases from the *packaged* `model-aliases.yaml` using `importlib.resources`. Handle `FileNotFoundError`, `yaml.YAMLError` -> `ConfigurationError`.
        *   Resolve alias if `model_identifier` doesn't contain `/`. Raise `ModelAliasError` if alias not found.
        *   Parse the `resolved_model` to determine `provider_name` (e.g., 'openrouter', 'openai', 'deepseek'), `api_base_url`, and the `model_name_for_api` (without the prefix). Raise `UnknownProviderError` if prefix is invalid.
    *   **`_get_api_key(self) -> str`:** (Internal method called by `__init__`)
        *   Based on `self.provider_name`, get the API key from the corresponding environment variable (e.g., `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `DEEPSEEK_API_KEY`).
        *   Raise `APIKeyError` if the required key is not set.
        *   *(Optional): Add basic format validation (e.g., starts with `sk-`).*
    *   **`create_completion(self, messages: list, **kwargs) -> str`:**
        *   Takes `messages` (list of dicts with 'role' and 'content').
        *   Accepts optional `**kwargs` (like `temperature`, `max_tokens`) to pass to the provider's method.
        *   Calls `self.provider.create_completion(model=self.model_name_for_api, messages=messages, **kwargs)`.
        *   Wraps the call in a try/except block to catch provider-specific errors and re-raise them as `APIRequestError`.
    *   **(Optional) `utils` module:** Could contain shared logging setup using `rich` if desired.

**6. Configuration Handling:**

*   **Model Aliases:** The canonical `model-aliases.yaml` lives *inside* the `ai_commons` package (`src/ai_commons/data/`) and is accessed using `importlib.resources`. This ensures it's always found relative to the installed package, regardless of where `aicoder` or `ai-git` are run from.
*   **API Keys:** Retrieved solely from environment variables (`OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `DEEPSEEK_API_KEY`). The library raises `APIKeyError` if a needed key is missing.

**7. Error Handling Strategy:**

*   Use the custom exceptions defined in `exceptions.py`.
*   The `LLMClient` should catch specific errors (e.g., `yaml.YAMLError`, provider API errors) and raise corresponding custom exceptions (`ConfigurationError`, `APIRequestError`).
*   This allows calling code (`aicoder`, `ai-git`) to handle errors granularly (e.g., inform the user about a missing API key vs. a temporary API outage).

**8. Testing Strategy:**

*   Use `pytest`.
*   **Unit Tests:**
    *   Test `_resolve_alias_and_provider` with various inputs (aliases, full IDs, unknown aliases, invalid prefixes). Mock file reading for `model-aliases.yaml`.
    *   Test `_get_api_key` for different providers, ensuring correct env vars are checked and `APIKeyError` is raised. Mock `os.getenv`.
    *   Test provider adapter instantiation.
    *   **(Advanced):** Mock the `requests.post` and `openai.ChatCompletion.create` calls to test the `create_completion` methods without actual API calls.

**9. Documentation Plan:**

*   **`README.md`:**
    *   Brief description of the library's purpose.
    *   Installation instructions.
    *   Basic usage example (`LLMClient`).
    *   Required environment variables for API keys.
    *   Explanation of the `model-aliases.yaml` configuration and how to contribute/modify it (if applicable).
    *   Overview of supported providers.
*   **Docstrings:** Add clear docstrings to all public classes, methods, and functions explaining parameters, return values, and potential exceptions raised.

**10. Next Steps (After Library Creation):**

*   Publish the library (even if just to a local/private index initially or using path dependencies).
*   Create separate, detailed migration plans for `aicoder` and `ai-git` to adopt this new `ai-commons` library.

This plan provides a solid foundation for building the shared `ai-commons` library, separating concerns effectively and preparing for cleaner integration with your existing projects.


