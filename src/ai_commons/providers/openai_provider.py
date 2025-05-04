import os
import openai
from typing import Optional, Any, Dict, List, Tuple

from .base import LLMProvider
from ..exceptions import APIKeyError, APIRequestError

class OpenAIProvider(LLMProvider):
    """
    Provider for OpenAI and compatible APIs (like DeepSeek) using the openai library.
    """
    def __init__(self, base_url: Optional[str] = None):
        """
        Initializes the OpenAIProvider.

        Args:
            base_url: Optional base URL for the API endpoint. Defaults to OpenAI's
                      if not provided.
        """
        self.base_url = base_url
        self.client: Optional[openai.OpenAI] = None

    def get_api_credentials(self, api_key_override: Optional[str]) -> Tuple[str, str, str, str]:
        """
        Determines and validates the API key and initializes the client.

        Args:
            api_key_override: An optional API key provided directly, overriding
                              environment variables.

        Returns:
            A tuple containing:
            - The API key used.
            - The name of the environment variable checked (if override not used).
            - The expected key prefix.
            - The base URL used by the client.

        Raises:
            APIKeyError: If the API key is missing, invalid, or authentication fails.
        """
        key_env_var = "OPENAI_API_KEY"
        key_prefix = "sk-"

        if self.base_url and 'deepseek' in self.base_url.lower():
            key_env_var = "DEEPSEEK_API_KEY"
            key_prefix = "ds-"

        api_key = api_key_override or os.getenv(key_env_var)

        if not api_key:
            raise APIKeyError(f"{key_env_var} not set or provided.")

        if not api_key.startswith(key_prefix):
            raise APIKeyError(f"Invalid API key format for {key_env_var}.")

        try:
            # Instantiate the client
            self.client = openai.OpenAI(api_key=api_key, base_url=self.base_url)

            # Optional: Perform a simple check to validate the key/endpoint early
            # try:
            #     self.client.models.list()
            # except Exception as e:
            #      # Catch any error during the list call and wrap it
            #      raise APIKeyError(f"Failed to validate API key or connect to endpoint ({self.base_url or 'default OpenAI'}): {e}") from e

        except openai.AuthenticationError as e:
            raise APIKeyError(f"Authentication failed for {key_env_var}: {e}") from e
        except openai.APIConnectionError as e:
             raise APIKeyError(f"Could not connect to API endpoint ({self.base_url or 'default OpenAI'}): {e}") from e
        except Exception as e: # Catch broader errors during init
             raise APIKeyError(f"Failed to initialize OpenAI client for {key_env_var}: {e}") from e

        # Return the actual base_url used by the client if self.base_url was None
        actual_base_url = self.client.base_url if self.client else (self.base_url or "default OpenAI URL")

        return (api_key, key_env_var, key_prefix, actual_base_url)

    def create_completion(self, model: str, messages: List[Dict[str, str]], temperature: float, max_tokens: Optional[int], **kwargs: Any) -> str:
        """
        Creates a chat completion using the OpenAI API.

        Args:
            model: The model name to use (e.g., "gpt-4o", "deepseek-coder").
            messages: A list of message dictionaries for the conversation.
            temperature: The sampling temperature.
            max_tokens: The maximum number of tokens to generate.
            **kwargs: Additional parameters for the API call.

        Returns:
            The content of the generated message.

        Raises:
            RuntimeError: If the client is not initialized.
            APIRequestError: If the API call fails.
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Call get_api_credentials first.")

        params: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            **kwargs # Include any additional kwargs
        }
        if max_tokens is not None:
            params["max_tokens"] = max_tokens

        try:
            response = self.client.chat.completions.create(**params)
            if not response.choices:
                 raise APIRequestError("API returned an empty response.")

            content = response.choices[0].message.content
            if content is None:
                 # Handle cases where content might be None (e.g., function calls)
                 # For this specific task, we expect text content.
                 raise APIRequestError("API returned non-text content or empty message.")

            return content

        except (openai.APIError,
                openai.RateLimitError,
                openai.APIConnectionError,
                openai.InvalidRequestError) as e:
            raise APIRequestError(f"OpenAI API request failed: {e}") from e
        except Exception as e: # Catch any other unexpected errors during the API call
            raise APIRequestError(f"An unexpected error occurred during OpenAI API request: {e}") from e