# Refined Plan: Create Shared LLM Library (`ai-commons`)

**1. Goal:**
Create a standalone Python library named `ai-commons` that encapsulates shared functionality for interacting with LLMs, including model alias resolution, provider handling (OpenAI, OpenRouter, DeepSeek-compatible), API client logic, and configuration management.

**2. Library Name & Purpose:**
*   **Project/Repo Name:** `ai-commons`
*   **Python Package Name:** `ai_commons`
*   **Purpose:** Provide a robust, reusable core for LLM interactions.

**3. Directory Structure:**
```
ai-commons/
├── src/
│   └── ai_commons/
│       ├── __init__.py
│       ├── client.py           # Main LLMClient class
│       ├── exceptions.py       # Custom exception classes
│       ├── providers/          # Provider-specific adapters
│       │   ├── __init__.py
│       │   ├── base.py         # Abstract LLMProvider base class
│       │   ├── openai_provider.py # Handles OpenAI & DeepSeek-like APIs
│       │   └── openrouter_provider.py
│       ├── data/               # Packaged data files
│       │   └── model-aliases.yaml # Consolidated aliases
│       └── utils.py            # Optional: Shared utilities (e.g., strip_backticks)
├── tests/                  # Unit tests
│   ├── __init__.py
│   ├── test_client.py
│   ├── test_providers.py
│   └── test_utils.py       # If utils.py is included
├── .gitignore
├── LICENSE                 # e.g., MIT or your preferred license
├── pyproject.toml          # Project definition and dependencies
└── README.md               # Library documentation
```

**4. Dependencies (`pyproject.toml`):**
*   **Core:**
    *   `openai>=1.0.0` (For OpenAI/DeepSeek adapters)
    *   `requests>=2.31.0` (For OpenRouter adapter - consider `httpx` if async is a future goal)
    *   `PyYAML>=6.0.1` (For loading `model-aliases.yaml`)
    *   `typing-extensions` (Often needed by `openai` or `pydantic`-like structures if used internally)
*   **Development:**
    *   `pytest`
    *   `pytest-cov`
    *   `pytest-mock` (Likely needed for testing API interactions)

**5. Core Components Implementation Details:**

*   **`src/ai_commons/exceptions.py`:**
    *   `LLMClientError(Exception)`
    *   `ConfigurationError(LLMClientError)`
    *   `ModelAliasError(ConfigurationError)`
    *   `APIKeyError(LLMClientError)`
    *   `UnknownProviderError(LLMClientError)`
    *   `APIRequestError(LLMClientError)`

*   **`src/ai_commons/data/model-aliases.yaml`:**
    *   **Action:** Consolidate aliases from `aicoder/config/model-aliases.yaml` and `ai-git-summarize/config/model-aliases.yaml`. Resolve any conflicts if necessary.
    *   Ensure it's included as package data in `pyproject.toml` (e.g., using `[tool.setuptools.package-data]` or `[tool.hatch.build.targets.wheel]`).

*   **`src/ai_commons/providers/base.py`:**
    *   Define abstract base class `LLMProvider(ABC)`.
    *   `@abstractmethod def get_api_credentials(self, api_key_override: Optional[str]) -> tuple:`
        *   Returns `(api_key: str, key_env_var: str, key_prefix: str, base_url: str)`
        *   Handles fetching the key from env var or using the override.
        *   Validates key presence and basic format (e.g., prefix). Raises `APIKeyError` if invalid/missing.
    *   `@abstractmethod def create_completion(self, model: str, messages: list, temperature: float, max_tokens: Optional[int], **kwargs) -> str:`
        *   Takes core parameters, allows provider-specific ones via `**kwargs`.
        *   Handles the actual API call logic.
        *   Should catch provider-specific exceptions and raise `APIRequestError`.

*   **`src/ai_commons/providers/openai_provider.py`:**
    *   Implement `OpenAIProvider(LLMProvider)`.
    *   `__init__(self, base_url: Optional[str] = None)`: Store the specific base URL (e.g., for DeepSeek).
    *   `get_api_credentials`: Implement logic similar to `aicoder`'s adapter, determining env var (`OPENAI_API_KEY` or `DEEPSEEK_API_KEY`) based on `self.base_url`. Instantiate `openai.OpenAI` client here and store as `self.client`.
    *   `create_completion`: Use `self.client.chat.completions.create`, passing `model`, `messages`, `temperature`, `max_tokens`.

*   **`src/ai_commons/providers/openrouter_provider.py`:**
    *   Implement `OpenRouterProvider(LLMProvider)`.
    *   `__init__`: Set default `base_url` to OpenRouter's API.
    *   `get_api_credentials`: Fetch `OPENROUTER_API_KEY`.
    *   `create_completion`: Use `requests.post` (or `httpx`). Construct headers (`Authorization`, `Referer`, `X-Title` - make Referer/Title potentially configurable or use generic defaults). Construct JSON payload. Handle response parsing and errors.

*   **`src/ai_commons/utils.py`:** (Optional)
    *   Define `strip_backticks(text: Optional[str]) -> Optional[str]`: Implement the robust logic seen in `ai-git-summarize` to remove surrounding backticks and standalone backtick lines.

*   **`src/ai_commons/client.py`:** (`LLMClient`)
    *   **`__init__(self, model_identifier: str, api_key_override: Optional[str] = None, temperature: float = 0.0, max_tokens: Optional[int] = None)`:**
        *   Store `temperature`, `max_tokens`.
        *   Call internal `_resolve_alias()` to get `resolved_model_id`.
        *   Call internal `_determine_provider()` using `resolved_model_id` to get `provider_name`, `model_name_for_api`, `base_url`. Store these.
        *   Instantiate the correct provider adapter based on `provider_name` (e.g., `self.provider = OpenAIProvider(base_url=base_url)`).
        *   Call `self.provider.get_api_credentials(api_key_override)` to validate/get the key and confirm config. Store the validated `api_key`.
    *   **`_resolve_alias(self, model_identifier: str) -> str`:** (Internal helper)
        *   If `/` in `model_identifier`, return it.
        *   Load aliases from *packaged* `data/model-aliases.yaml` using `importlib.resources`. Handle `FileNotFoundError`, `yaml.YAMLError` -> `ConfigurationError`.
        *   If alias exists, return resolved ID. Log the resolution.
        *   If alias doesn't exist, raise `ModelAliasError`.
    *   **`_determine_provider(self, resolved_model_id: str) -> tuple`:** (Internal helper)
        *   Iterate through provider configurations (similar to `PROVIDER_CONFIGS` in `aicoder`).
        *   Match prefix (e.g., `openrouter/`, `openai/`, `deepseek/`).
        *   Return `(provider_name: str, model_name_for_api: str, base_url: Optional[str])`.
        *   Raise `UnknownProviderError` if no prefix matches.
    *   **`create_completion(self, messages: list, **kwargs) -> str`:**
        *   Takes `messages`.
        *   Allows overriding `temperature` and `max_tokens` via `kwargs`, otherwise uses values from `__init__`.
        *   Passes `self.model_name_for_api`, `messages`, `temperature`, `max_tokens`, and any other relevant `kwargs` to `self.provider.create_completion`.

**6. Configuration Handling:**
*   **Model Aliases:** Canonical `model-aliases.yaml` lives inside the package (`src/ai_commons/data/`) and is accessed via `importlib.resources`.
*   **API Keys:** Retrieved solely from environment variables (`OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `DEEPSEEK_API_KEY`) or optional override in `LLMClient.__init__`. Handled within provider adapters.
*   **Base URLs:** Managed internally by provider adapters based on the resolved model prefix.
*   **Temperature/Max Tokens:** Configured via `LLMClient.__init__` or overridden in `create_completion`.

**7. Error Handling Strategy:**
*   Use custom exceptions from `exceptions.py`.
*   `LLMClient` raises `ConfigurationError`, `ModelAliasError`, `UnknownProviderError`, `APIKeyError`.
*   Provider adapters raise `APIRequestError` for API call failures.

**8. Testing Strategy:**
*   Use `pytest` and `pytest-mock`.
*   **Unit Tests:**
    *   Test `_resolve_alias` with various inputs (aliases, full IDs, unknown aliases, invalid file). Mock `importlib.resources`.
    *   Test `_determine_provider` for all supported prefixes and invalid ones.
    *   Test `get_api_credentials` in each provider adapter (mock `os.getenv`, test key validation).
    *   Test `create_completion` in each provider adapter by mocking the underlying API call (`requests.post`, `openai.Client.chat.completions.create`). Verify correct payload/headers and response parsing.
    *   Test `LLMClient.__init__` logic for provider selection and credential fetching.
    *   Test `LLMClient.create_completion` correctly passes parameters to the provider.
    *   Test `utils.strip_backticks` if included.

**9. Documentation Plan:**
*   **`README.md`:** Purpose, installation, basic usage (`LLMClient`), required env vars, alias explanation, supported providers.
*   **Docstrings:** Clear docstrings for public classes/methods (`LLMClient`, `create_completion`, exceptions).

**10. Next Steps (After Library Creation):**
*   Publish the library (privately or publicly).
*   Create migration plans for `aicoder` and `ai-git-summarize` to use `ai-commons`.