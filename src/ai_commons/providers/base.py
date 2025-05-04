from abc import ABC, abstractmethod
from typing import Optional

from ..exceptions import APIKeyError

class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    """

    @abstractmethod
    def get_api_credentials(self, api_key_override: Optional[str]) -> tuple:
        """
        Retrieves API credentials, handling overrides and validation.

        Args:
            api_key_override: Optional API key provided by the user,
                              overriding environment variables.

        Returns:
            A tuple containing (api_key, key_env_var, key_prefix, base_url).

        Raises:
            APIKeyError: If the API key is missing or invalid.
        """
        pass

    @abstractmethod
    def create_completion(self, model: str, messages: list, temperature: float, max_tokens: Optional[int], **kwargs) -> str:
        """
        Creates a text completion using the LLM.

        Args:
            model: The name of the LLM model to use.
            messages: A list of message dictionaries for the conversation.
            temperature: The sampling temperature to use.
            max_tokens: The maximum number of tokens to generate.
            **kwargs: Additional provider-specific parameters.

        Returns:
            The generated text completion.

        Raises:
            APIRequestError: If the API request fails.
        """
        pass