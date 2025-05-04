import os
import requests
from typing import Optional, List, Dict, Any
from .base import LLMProvider
from ..exceptions import APIKeyError, APIRequestError

OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
HTTP_REFERER = "http://localhost"  # Default referer
X_TITLE = "ai-commons"  # Default title

class OpenRouterProvider(LLMProvider):
    """
    LLM Provider for the OpenRouter API.
    """
    def __init__(self, http_referer: Optional[str] = None, x_title: Optional[str] = None):
        """
        Initializes the OpenRouterProvider.

        Args:
            http_referer (Optional[str]): The HTTP Referer header value. Defaults to HTTP_REFERER constant.
            x_title (Optional[str]): The X-Title header value. Defaults to X_TITLE constant.
        """
        self.http_referer = http_referer if http_referer is not None else HTTP_REFERER
        self.x_title = x_title if x_title is not None else X_TITLE
        self.base_url = OPENROUTER_API_BASE

    def get_api_credentials(self, api_key_override: Optional[str]) -> tuple:
        """
        Retrieves the OpenRouter API key from environment variables or override.

        Args:
            api_key_override (Optional[str]): An optional API key provided directly.

        Returns:
            tuple: A tuple containing (api_key, key_env_var, key_prefix, base_url).

        Raises:
            APIKeyError: If the API key is not found or has an invalid format.
        """
        key_env_var = "OPENROUTER_API_KEY"
        key_prefix = "sk-or-v1-"

        api_key = api_key_override or os.getenv(key_env_var)

        if not api_key:
            raise APIKeyError(f"{key_env_var} not set or provided.")

        if not api_key.startswith(key_prefix):
            raise APIKeyError(f"Invalid API key format for {key_env_var}. Expected prefix '{key_prefix}'.")

        return (api_key, key_env_var, key_prefix, self.base_url)

    def create_completion(self, model: str, messages: List[Dict[str, str]], temperature: float, max_tokens: Optional[int], **kwargs) -> str:
        """
        Creates a chat completion using the OpenRouter API.

        Args:
            model (str): The model name to use (e.g., "openai/gpt-4o").
            messages (List[Dict[str, str]]): A list of message dictionaries.
            temperature (float): The sampling temperature.
            max_tokens (Optional[int]): The maximum number of tokens to generate.
            **kwargs: Additional provider-specific arguments to pass in the payload.

        Returns:
            str: The content of the generated completion.

        Raises:
            APIKeyError: If the API key is missing or invalid.
            APIRequestError: If the API request fails or returns an error.
        """
        try:
            api_key = self.get_api_credentials(None)[0]
        except APIKeyError as e:
            # Re-raise the APIKeyError from get_api_credentials
            raise e

        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": self.http_referer,
            "X-Title": self.x_title,
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            **({"max_tokens": max_tokens} if max_tokens is not None else {}),
            **kwargs
        }

        url = f"{self.base_url}/chat/completions"

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
        except requests.exceptions.RequestException as e:
            raise APIRequestError(f"OpenRouter API request failed: {e}") from e

        if response.status_code != 200:
            raise APIRequestError(f"OpenRouter API error ({response.status_code}): {response.text}")

        try:
            response_data = response.json()
        except requests.exceptions.JSONDecodeError:
             raise APIRequestError(f"OpenRouter API returned invalid JSON: {response.text}")

        try:
            content = response_data['choices'][0]['message']['content']
        except (KeyError, IndexError):
            raise APIRequestError(f"OpenRouter API response missing expected data: {response_data}")

        return content