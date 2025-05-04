import pytest
import os
import requests
import openai
from unittest.mock import MagicMock, patch

from ai_commons.providers.openai_provider import OpenAIProvider
from ai_commons.providers.openrouter_provider import OpenRouterProvider
from ai_commons.exceptions import APIKeyError, APIRequestError

# --- Tests for OpenAIProvider ---

class MockOpenAIClient:
    """Mock class for openai.OpenAI client."""
    def __init__(self, api_key=None, base_url=None):
        self.api_key = api_key
        self.base_url = base_url
        self.chat = MagicMock()

    def models(self):
        # Mock models.list() if needed for validation tests
        return MagicMock()

@pytest.fixture
def mock_openai_client(mocker):
    """Fixture to mock the openai.OpenAI client instantiation."""
    mock_client = MockOpenAIClient()
    mocker.patch("openai.OpenAI", return_value=mock_client)
    return mock_client

def test_openai_get_api_credentials_override(mocker, mock_openai_client):
    """Tests get_api_credentials with API key override."""
    mock_getenv = mocker.patch("os.getenv", return_value="env_key")
    provider = OpenAIProvider()
    api_key, env_var, prefix, base_url = provider.get_api_credentials("override_key")

    assert api_key == "override_key"
    assert env_var == "OPENAI_API_KEY"
    assert prefix == "sk-"
    assert base_url == "default OpenAI URL" # Mock client default
    mock_getenv.assert_not_called()
    mock_openai_client.chat.completions.create.assert_not_called() # Ensure no API call on init


def test_openai_get_api_credentials_env_var(mocker, mock_openai_client):
    """Tests get_api_credentials with API key from environment variable."""
    mock_getenv = mocker.patch("os.getenv", return_value="sk-env_key")
    provider = OpenAIProvider()
    api_key, env_var, prefix, base_url = provider.get_api_credentials(None)

    assert api_key == "sk-env_key"
    assert env_var == "OPENAI_API_KEY"
    assert prefix == "sk-"
    assert base_url == "default OpenAI URL"
    mock_getenv.assert_called_once_with("OPENAI_API_KEY")
    mock_openai_client.chat.completions.create.assert_not_called()


def test_openai_get_api_credentials_deepseek_env_var(mocker, mock_openai_client):
    """Tests get_api_credentials with DeepSeek base URL and env var."""
    mock_getenv = mocker.patch("os.getenv", return_value="ds-env_key")
    provider = OpenAIProvider(base_url="https://api.deepseek.com/v1")
    api_key, env_var, prefix, base_url = provider.get_api_credentials(None)

    assert api_key == "ds-env_key"
    assert env_var == "DEEPSEEK_API_KEY"
    assert prefix == "ds-"
    assert base_url == "https://api.deepseek.com/v1" # Mock client uses provided base_url
    mock_getenv.assert_called_once_with("DEEPSEEK_API_KEY")
    mock_openai_client.chat.completions.create.assert_not_called()


def test_openai_get_api_credentials_missing_key(mocker):
    """Tests raising APIKeyError when API key is missing."""
    mock_getenv = mocker.patch("os.getenv", return_value=None)
    provider = OpenAIProvider()
    with pytest.raises(APIKeyError, match="OPENAI_API_KEY not set or provided."):
        provider.get_api_credentials(None)
    mock_getenv.assert_called_once_with("OPENAI_API_KEY")


def test_openai_get_api_credentials_invalid_format(mocker):
    """Tests raising APIKeyError for invalid API key format."""
    mock_getenv = mocker.patch("os.getenv", return_value="invalid_key")
    provider = OpenAIProvider()
    with pytest.raises(APIKeyError, match="Invalid API key format for OPENAI_API_KEY."):
        provider.get_api_credentials(None)
    mock_getenv.assert_called_once_with("OPENAI_API_KEY")


def test_openai_get_api_credentials_authentication_error(mocker, mock_openai_client):
    """Tests wrapping openai.AuthenticationError in APIKeyError."""
    mock_getenv = mocker.patch("os.getenv", return_value="sk-valid_key")
    mocker.patch("openai.OpenAI", side_effect=openai.AuthenticationError("Auth failed", response=None, body=None))
    provider = OpenAIProvider()
    with pytest.raises(APIKeyError, match="Authentication failed for OPENAI_API_KEY: Auth failed"):
        provider.get_api_credentials(None)
    mock_getenv.assert_called_once_with("OPENAI_API_KEY")


def test_openai_get_api_credentials_connection_error(mocker, mock_openai_client):
    """Tests wrapping openai.APIConnectionError in APIKeyError."""
    mock_getenv = mocker.patch("os.getenv", return_value="sk-valid_key")
    mocker.patch("openai.OpenAI", side_effect=openai.APIConnectionError(request=None))
    provider = OpenAIProvider()
    with pytest.raises(APIKeyError, match="Could not connect to API endpoint"):
        provider.get_api_credentials(None)
    mock_getenv.assert_called_once_with("OPENAI_API_KEY")


def test_openai_get_api_credentials_unexpected_error(mocker, mock_openai_client):
    """Tests wrapping unexpected errors during client init in APIKeyError."""
    mock_getenv = mocker.patch("os.getenv", return_value="sk-valid_key")
    mocker.patch("openai.OpenAI", side_effect=Exception("Unexpected init error"))
    provider = OpenAIProvider()
    with pytest.raises(APIKeyError, match="Failed to initialize OpenAI client for OPENAI_API_KEY: Unexpected init error"):
        provider.get_api_credentials(None)
    mock_getenv.assert_called_once_with("OPENAI_API_KEY")


def test_openai_create_completion_success(mocker, mock_openai_client):
    """Tests successful create_completion call for OpenAIProvider."""
    provider = OpenAIProvider()
    provider.client = mock_openai_client # Manually set the mock client

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Successful completion"
    mock_openai_client.chat.completions.create.return_value = mock_response

    model = "gpt-4o"
    messages = [{"role": "user", "content": "Test message"}]
    temperature = 0.7
    max_tokens = 150
    extra_kwargs = {"stop": ["\n"]}

    completion = provider.create_completion(model, messages, temperature, max_tokens, **extra_kwargs)

    mock_openai_client.chat.completions.create.assert_called_once_with(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stop=["\n"]
    )
    assert completion == "Successful completion"


def test_openai_create_completion_no_client():
    """Tests raising RuntimeError if client is not initialized."""
    provider = OpenAIProvider()
    with pytest.raises(RuntimeError, match="Client not initialized. Call get_api_credentials first."):
        provider.create_completion("model", [], 0.7, 100)


@pytest.mark.parametrize("openai_exception", [
    openai.APIError("API error", response=None, body=None),
    openai.RateLimitError("Rate limit", response=None, body=None),
    openai.APIConnectionError(request=None),
    openai.InvalidRequestError("Invalid request", param=None, code=None, response=None, body=None),
])
def test_openai_create_completion_api_errors(mocker, mock_openai_client, openai_exception):
    """Tests wrapping various openai API errors in APIRequestError."""
    provider = OpenAIProvider()
    provider.client = mock_openai_client

    mock_openai_client.chat.completions.create.side_effect = openai_exception

    with pytest.raises(APIRequestError):
        provider.create_completion("model", [], 0.7, 100)


def test_openai_create_completion_unexpected_error(mocker, mock_openai_client):
    """Tests wrapping unexpected errors during create_completion in APIRequestError."""
    provider = OpenAIProvider()
    provider.client = mock_openai_client

    mock_openai_client.chat.completions.create.side_effect = Exception("Unexpected completion error")

    with pytest.raises(APIRequestError, match="An unexpected error occurred during OpenAI API request: Unexpected completion error"):
        provider.create_completion("model", [], 0.7, 100)


def test_openai_create_completion_empty_response(mocker, mock_openai_client):
    """Tests handling empty response from OpenAI API."""
    provider = OpenAIProvider()
    provider.client = mock_openai_client

    mock_response = MagicMock()
    mock_response.choices = [] # Empty choices list
    mock_openai_client.chat.completions.create.return_value = mock_response

    with pytest.raises(APIRequestError, match="API returned an empty response."):
        provider.create_completion("model", [], 0.7, 100)


def test_openai_create_completion_none_content(mocker, mock_openai_client):
    """Tests handling response with None content."""
    provider = OpenAIProvider()
    provider.client = mock_openai_client

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = None # Content is None
    mock_openai_client.chat.completions.create.return_value = mock_response

    with pytest.raises(APIRequestError, match="API returned non-text content or empty message."):
        provider.create_completion("model", [], 0.7, 100)


# --- Tests for OpenRouterProvider ---

@pytest.fixture
def mock_requests_post(mocker):
    """Fixture to mock requests.post."""
    return mocker.patch("requests.post")

def test_openrouter_get_api_credentials_override(mocker):
    """Tests get_api_credentials with API key override for OpenRouter."""
    mock_getenv = mocker.patch("os.getenv", return_value="sk-or-v1-env_key")
    provider = OpenRouterProvider()
    api_key, env_var, prefix, base_url = provider.get_api_credentials("sk-or-v1-override_key")

    assert api_key == "sk-or-v1-override_key"
    assert env_var == "OPENROUTER_API_KEY"
    assert prefix == "sk-or-v1-"
    assert base_url == "https://openrouter.ai/api/v1"
    mock_getenv.assert_not_called()


def test_openrouter_get_api_credentials_env_var(mocker):
    """Tests get_api_credentials with API key from environment variable for OpenRouter."""
    mock_getenv = mocker.patch("os.getenv", return_value="sk-or-v1-env_key")
    provider = OpenRouterProvider()
    api_key, env_var, prefix, base_url = provider.get_api_credentials(None)

    assert api_key == "sk-or-v1-env_key"
    assert env_var == "OPENROUTER_API_KEY"
    assert prefix == "sk-or-v1-"
    assert base_url == "https://openrouter.ai/api/v1"
    mock_getenv.assert_called_once_with("OPENROUTER_API_KEY")


def test_openrouter_get_api_credentials_missing_key(mocker):
    """Tests raising APIKeyError when OpenRouter API key is missing."""
    mock_getenv = mocker.patch("os.getenv", return_value=None)
    provider = OpenRouterProvider()
    with pytest.raises(APIKeyError, match="OPENROUTER_API_KEY not set or provided."):
        provider.get_api_credentials(None)
    mock_getenv.assert_called_once_with("OPENROUTER_API_KEY")


def test_openrouter_get_api_credentials_invalid_format(mocker):
    """Tests raising APIKeyError for invalid OpenRouter API key format."""
    mock_getenv = mocker.patch("os.getenv", return_value="invalid_key")
    provider = OpenRouterProvider()
    with pytest.raises(APIKeyError, match="Invalid API key format for OPENROUTER_API_KEY. Expected prefix 'sk-or-v1-'."):
        provider.get_api_credentials(None)
    mock_getenv.assert_called_once_with("OPENROUTER_API_KEY")


def test_openrouter_create_completion_success(mocker, mock_requests_post):
    """Tests successful create_completion call for OpenRouterProvider."""
    mocker.patch("os.getenv", return_value="sk-or-v1-valid_key") # Mock get_api_credentials internally

    provider = OpenRouterProvider(http_referer="test_referer", x_title="test_title")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "OpenRouter completion"}}]
    }
    mock_requests_post.return_value = mock_response

    model = "openrouter/test/model"
    messages = [{"role": "user", "content": "Test message"}]
    temperature = 0.9
    max_tokens = 200
    extra_kwargs = {"stream": False}

    completion = provider.create_completion(model, messages, temperature, max_tokens, **extra_kwargs)

    expected_url = "https://openrouter.ai/api/v1/chat/completions"
    expected_headers = {
        "Authorization": "Bearer sk-or-v1-valid_key",
        "HTTP-Referer": "test_referer",
        "X-Title": "test_title",
        "Content-Type": "application/json"
    }
    expected_payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }

    mock_requests_post.assert_called_once_with(
        expected_url,
        headers=expected_headers,
        json=expected_payload,
        timeout=60
    )
    assert completion == "OpenRouter completion"


def test_openrouter_create_completion_request_exception(mocker, mock_requests_post):
    """Tests handling requests.exceptions.RequestException for OpenRouter."""
    mocker.patch("os.getenv", return_value="sk-or-v1-valid_key")
    provider = OpenRouterProvider()

    mock_requests_post.side_effect = requests.exceptions.RequestException("Connection error")

    with pytest.raises(APIRequestError, match="OpenRouter API request failed: Connection error"):
        provider.create_completion("model", [], 0.7, 100)


def test_openrouter_create_completion_non_200_status(mocker, mock_requests_post):
    """Tests handling non-200 status code response for OpenRouter."""
    mocker.patch("os.getenv", return_value="sk-or-v1-valid_key")
    provider = OpenRouterProvider()

    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    mock_requests_post.return_value = mock_response

    with pytest.raises(APIRequestError, match="OpenRouter API error \(400\): Bad Request"):
        provider.create_completion("model", [], 0.7, 100)


def test_openrouter_create_completion_json_decode_error(mocker, mock_requests_post):
    """Tests handling requests.exceptions.JSONDecodeError for OpenRouter."""
    mocker.patch("os.getenv", return_value="sk-or-v1-valid_key")
    provider = OpenRouterProvider()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = requests.exceptions.JSONDecodeError("Invalid JSON", doc="invalid", pos=0)
    mock_response.text = "invalid json response"
    mock_requests_post.return_value = mock_response

    with pytest.raises(APIRequestError, match="OpenRouter API returned invalid JSON: invalid json response"):
        provider.create_completion("model", [], 0.7, 100)


@pytest.mark.parametrize("missing_key_path", [
    ["choices"],
    ["choices", 0, "message"],
    ["choices", 0, "message", "content"],
])
def test_openrouter_create_completion_missing_data_in_response(mocker, mock_requests_post, missing_key_path):
    """Tests handling missing keys/indices in the OpenRouter API response."""
    mocker.patch("os.getenv", return_value="sk-or-v1-valid_key")
    provider = OpenRouterProvider()

    mock_response_data = {"choices": [{"message": {"content": "OpenRouter completion"}}]}
    # Remove keys/indices based on the parameter
    current_level = mock_response_data
    for i, key in enumerate(missing_key_path):
        if i == len(missing_key_path) - 1:
            if isinstance(current_level, list):
                del current_level[key]
            else:
                del current_level[key]
        else:
            current_level = current_level[key]

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_requests_post.return_value = mock_response

    with pytest.raises(APIRequestError, match="OpenRouter API response missing expected data:"):
        provider.create_completion("model", [], 0.7, 100)