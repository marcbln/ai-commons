import yaml
import importlib.resources
import logging
from typing import Optional, List, Dict, Any

from .exceptions import LLMClientError, ConfigurationError, ModelAliasError, UnknownProviderError, APIKeyError
from .providers.base import LLMProvider
from .providers.openai_provider import OpenAIProvider
from .providers.openrouter_provider import OpenRouterProvider

logger = logging.getLogger(__name__)

PROVIDER_MAP = {
    "openai": {"class": OpenAIProvider, "base_url": None},
    "deepseek": {"class": OpenAIProvider, "base_url": "https://api.deepseek.com/v1"}, # Example DeepSeek URL
    "openrouter": {"class": OpenRouterProvider, "base_url": None}, # Base URL handled within OpenRouterProvider
    # Add other providers if needed
}

class LLMClient:
    """
    A client for interacting with various Large Language Models (LLMs) via different providers.

    Handles model alias resolution, provider determination, and delegates completion calls.
    """
    def __init__(self, model_identifier: str, api_key_override: Optional[str] = None, temperature: float = 0.0, max_tokens: Optional[int] = None):
        """
        Initializes the LLMClient.

        Args:
            model_identifier: The alias or full ID of the model to use (e.g., "gpt4", "openai/gpt-4o").
            api_key_override: Optional API key to use instead of environment variables.
            temperature: The default temperature for completions (0.0 to 1.0).
            max_tokens: The default maximum number of tokens for completions.

        Raises:
            ModelAliasError: If the model alias is not found.
            UnknownProviderError: If the provider for the model ID is unknown.
            ConfigurationError: If the model alias file cannot be loaded or parsed.
            APIKeyError: If the API key is missing or invalid for the determined provider.
        """
        self.default_temperature = temperature
        self.default_max_tokens = max_tokens

        logger.debug(f"Initializing LLMClient with model_identifier: {model_identifier}")

        self.resolved_model_id = self._resolve_alias(model_identifier)
        logger.debug(f"Resolved model ID: {self.resolved_model_id}")

        self.provider_name, self.model_name_for_api, base_url = self._determine_provider(self.resolved_model_id)
        logger.debug(f"Determined provider: {self.provider_name}, model for API: {self.model_name_for_api}, base_url: {base_url}")

        provider_info = PROVIDER_MAP.get(self.provider_name)
        if not provider_info:
            raise UnknownProviderError(f"Provider '{self.provider_name}' not found in PROVIDER_MAP.")

        provider_class = provider_info["class"]

        try:
            if base_url:
                self.provider: LLMProvider = provider_class(base_url=base_url)
            else:
                self.provider: LLMProvider = provider_class()
            logger.debug(f"Instantiated provider: {provider_class.__name__}")
        except Exception as e:
             raise LLMClientError(f"Failed to instantiate provider {provider_class.__name__}: {e}") from e


        # Validate and get API key using the provider
        try:
            api_credentials = self.provider.get_api_credentials(api_key_override)
            self.api_key = api_credentials.api_key # Store the validated key
            logger.debug(f"Successfully obtained API key for provider {self.provider_name}")
        except APIKeyError as e:
            logger.error(f"API key error for provider {self.provider_name}: {e}")
            raise e # Re-raise the specific APIKeyError
        except Exception as e:
             raise LLMClientError(f"Failed to get API credentials for provider {self.provider_name}: {e}") from e


        logger.info(f"LLMClient initialized for model '{model_identifier}' (resolved to '{self.resolved_model_id}') using provider '{self.provider_name}'")


    def _resolve_alias(self, model_identifier: str) -> str:
        """
        Resolves a model alias to a full provider/model ID.

        Args:
            model_identifier: The alias or full ID.

        Returns:
            The resolved full model ID (e.g., "openai/gpt-4o").

        Raises:
            ConfigurationError: If the alias file cannot be loaded or parsed.
            ModelAliasError: If the alias is not found.
        """
        if "/" in model_identifier:
            logger.debug(f"Model identifier '{model_identifier}' contains '/', assuming it's a full ID.")
            return model_identifier # Assume it's already a full ID like "provider/model"

        logger.debug(f"Attempting to resolve model alias: {model_identifier}")
        try:
            # Use importlib.resources to access the data file
            alias_file_content = importlib.resources.files('ai_commons.data').joinpath('model-aliases.yaml').read_text()
        except FileNotFoundError:
            logger.error("Model alias file 'model-aliases.yaml' not found in 'ai_commons.data'.")
            raise ConfigurationError("Model alias file not found.")
        except Exception as e:
             logger.error(f"Error reading model alias file: {e}")
             raise ConfigurationError(f"Error reading model alias file: {e}") from e


        try:
            aliases = yaml.safe_load(alias_file_content)
            if not isinstance(aliases, dict):
                 logger.error("Model alias file content is not a dictionary.")
                 raise ConfigurationError("Model alias file content is not a dictionary.")
        except yaml.YAMLError as e:
            logger.error(f"Error parsing model alias file: {e}")
            raise ConfigurationError("Error parsing model alias file.") from e
        except Exception as e:
             logger.error(f"Unexpected error parsing model alias file: {e}")
             raise ConfigurationError(f"Unexpected error parsing model alias file: {e}") from e


        resolved_id = aliases.get(model_identifier)
        if resolved_id:
            logger.debug(f"Resolved alias '{model_identifier}' to '{resolved_id}'")
            return resolved_id
        else:
            logger.warning(f"Model alias '{model_identifier}' not found in aliases.")
            raise ModelAliasError(f"Model alias '{model_identifier}' not found.")

    def _determine_provider(self, resolved_model_id: str) -> tuple[str, str, Optional[str]]:
        """
        Determines the provider name, model name for the API, and base URL from a resolved model ID.

        Args:
            resolved_model_id: The full model ID (e.g., "openai/gpt-4o").

        Returns:
            A tuple containing (provider_name, model_name_for_api, base_url).

        Raises:
            UnknownProviderError: If the provider prefix is not recognized.
        """
        for prefix, provider_info in PROVIDER_MAP.items():
            if resolved_model_id.startswith(f"{prefix}/"):
                model_name_for_api = resolved_model_id[len(f"{prefix}/"):]
                base_url = provider_info.get("base_url")
                return (prefix, model_name_for_api, base_url)

        logger.error(f"Could not determine provider for model ID: {resolved_model_id}")
        raise UnknownProviderError(f"Could not determine provider for model ID: {resolved_model_id}")

    def create_completion(self, messages: List[Dict[str, str]], temperature: Optional[float] = None, max_tokens: Optional[int] = None, **kwargs) -> str:
        """
        Creates a completion using the configured LLM provider.

        Args:
            messages: A list of message dictionaries (e.g., [{"role": "user", "content": "Hello"}]).
            temperature: The temperature for this specific completion. Overrides the default if not None.
            max_tokens: The maximum number of tokens for this specific completion. Overrides the default if not None.
            **kwargs: Additional arguments to pass through to the provider's create_completion method.

        Returns:
            The generated completion text.

        Raises:
            APIRequestError: If the provider's API call fails.
            LLMClientError: For other potential errors during the completion process.
        """
        effective_temperature = temperature if temperature is not None else self.default_temperature
        effective_max_tokens = max_tokens if max_tokens is not None else self.default_max_tokens

        logger.debug(f"Calling provider '{self.provider_name}' create_completion for model '{self.model_name_for_api}' with temperature={effective_temperature}, max_tokens={effective_max_tokens}")

        try:
            # Pass the stored api_key to the provider's create_completion method
            # Note: Provider's create_completion should handle using this key
            # or its own internal key logic if api_key_override was used during init.
            # Assuming provider.create_completion expects the key or handles it internally.
            # If the provider's create_completion needs the key explicitly, it should be added here.
            # Based on the plan, the provider handles key validation in get_api_credentials,
            # and subsequent calls likely use an internal client configured with the key.
            # So, we just pass the required completion parameters.
            completion_text = self.provider.create_completion(
                model=self.model_name_for_api,
                messages=messages,
                temperature=effective_temperature,
                max_tokens=effective_max_tokens,
                **kwargs
            )
            logger.debug("Provider create_completion call successful.")
            return completion_text
        except Exception as e:
            logger.error(f"Error during provider create_completion call: {e}")
            # Re-raise provider-specific exceptions or wrap in LLMClientError
            # Assuming provider exceptions like APIRequestError propagate correctly
            raise # Let provider exceptions propagate