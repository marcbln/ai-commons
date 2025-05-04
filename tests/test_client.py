import pytest
import importlib.resources
import yaml
import os
from unittest.mock import MagicMock, patch

from ai_commons.client import LLMClient, PROVIDER_MAP
from ai_commons.exceptions import (
    LLMClientError,
    ConfigurationError,
    ModelAliasError,
    UnknownProviderError,
    APIKeyError,
    APIRequestError,
)
from ai_commons.providers.base import LLMProvider
from ai_commons.providers.openai_provider import OpenAIProvider
from ai_commons.providers.openrouter_provider import OpenRouterProvider

# Mock data for model aliases
MOCK_ALIASES_CONTENT = """
gpt4: openai/gpt-4o
deepseek_coder: deepseek/deepseek-coder
"""

# Mock API credentials object
class MockApiCredentials:
    def __init__(self, api_key: str):
        self.api_key = api_key

@pytest.fixture
def mock_provider_instance(mocker):
    """Fixture to provide a mock LLMProvider instance."""
    mock_provider = mocker.MagicMock(spec=LLMProvider)
    mock_provider.get_api_credentials.return_value = MockApiCredentials("mock_api_key")
    mock_provider.create_completion.return_value = "Mock completion response"
    return mock_provider

@pytest.fixture
def mock_provider_class(mocker, mock_provider_instance):
    """Fixture to provide a mock LLMProvider class that returns a mock instance."""
    mock_class = mocker.MagicMock(return_value=mock_provider_instance)
    return mock_class

@pytest.fixture(autouse=True)
def mock_provider_map(mocker, mock_provider_class):
    """Fixture to mock the PROVIDER_MAP in the client module."""
    mocker.patch.dict(
        "ai_commons.client.PROVIDER_MAP",
        {
            "openai": {"class": mock_provider_class, "base_url": None},
            "deepseek": {"class": mock_provider_class, "base_url": "https://api.deepseek.com/v1"},
            "openrouter": {"class": mock_provider_class, "base_url": None},
        },
        clear=True,
    )


# --- Tests for _resolve_alias ---

def test_resolve_alias_known_alias(mocker):
    """Tests resolving a known model alias."""
    mock_read_text = mocker.patch(
        "importlib.resources.files.return_value.joinpath.return_value.read_text"
    )
    mock_read_text.return_value = MOCK_ALIASES_CONTENT
    mock_safe_load = mocker.patch("yaml.safe_load")
    mock_safe_load.return_value = yaml.safe_load(MOCK_ALIASES_CONTENT)

    client = LLMClient("gpt4")
    assert client.resolved_model_id == "openai/gpt-4o"
    mock_read_text.assert_called_once()
    mock_safe_load.assert_called_once_with(MOCK_ALIASES_CONTENT)


def test_resolve_alias_full_id(mocker):
    """Tests resolving a full model ID (no alias resolution needed)."""
    # Ensure alias resolution is NOT attempted
    mock_read_text = mocker.patch(
        "importlib.resources.files.return_value.joinpath.return_value.read_text"
    )
    mock_safe_load = mocker.patch("yaml.safe_load")

    client = LLMClient("openai/gpt-4")
    assert client.resolved_model_id == "openai/gpt-4"
    mock_read_text.assert_not_called()
    mock_safe_load.assert_not_called()


def test_resolve_alias_unknown_alias(mocker):
    """Tests raising ModelAliasError for an unknown alias."""
    mock_read_text = mocker.patch(
        "importlib.resources.files.return_value.joinpath.return_value.read_text"
    )
    mock_read_text.return_value = MOCK_ALIASES_CONTENT
    mock_safe_load = mocker.patch("yaml.safe_load")
    mock_safe_load.return_value = yaml.safe_load(MOCK_ALIASES_CONTENT)

    with pytest.raises(ModelAliasError, match="Model alias 'unknown_alias' not found."):
        LLMClient("unknown_alias")

    mock_read_text.assert_called_once()
    mock_safe_load.assert_called_once_with(MOCK_ALIASES_CONTENT)


def test_resolve_alias_file_not_found(mocker):
    """Tests raising ConfigurationError on FileNotFoundError."""
    mock_read_text = mocker.patch(
        "importlib.resources.files.return_value.joinpath.return_value.read_text"
    )
    mock_read_text.side_effect = FileNotFoundError

    with pytest.raises(ConfigurationError, match="Model alias file not found."):
        LLMClient("gpt4")

    mock_read_text.assert_called_once()


def test_resolve_alias_yaml_error(mocker):
    """Tests raising ConfigurationError on yaml.YAMLError."""
    mock_read_text = mocker.patch(
        "importlib.resources.files.return_value.joinpath.return_value.read_text"
    )
    mock_read_text.return_value = "invalid yaml: -"
    mock_safe_load = mocker.patch("yaml.safe_load")
    mock_safe_load.side_effect = yaml.YAMLError("YAML parse error")

    with pytest.raises(ConfigurationError, match="Error parsing model alias file."):
        LLMClient("gpt4")

    mock_read_text.assert_called_once()
    mock_safe_load.assert_called_once_with("invalid yaml: -")


# --- Tests for _determine_provider ---

def test_determine_provider_openai():
    """Tests determining provider for openai prefix."""
    client = LLMClient("openai/gpt-4o")
    provider_name, model_name, base_url = client._determine_provider("openai/gpt-4o")
    assert provider_name == "openai"
    assert model_name == "gpt-4o"
    assert base_url is None


def test_determine_provider_deepseek():
    """Tests determining provider for deepseek prefix."""
    client = LLMClient("deepseek/deepseek-coder")
    provider_name, model_name, base_url = client._determine_provider("deepseek/deepseek-coder")
    assert provider_name == "deepseek"
    assert model_name == "deepseek-coder"
    assert base_url == "https://api.deepseek.com/v1"


def test_determine_provider_openrouter():
    """Tests determining provider for openrouter prefix."""
    client = LLMClient("openrouter/any/model") # OpenRouter uses a different model ID format
    provider_name, model_name, base_url = client._determine_provider("openrouter/any/model")
    assert provider_name == "openrouter"
    assert model_name == "any/model"
    assert base_url is None # Base URL is handled internally by OpenRouterProvider


def test_determine_provider_unknown_prefix():
    """Tests raising UnknownProviderError for an unknown prefix."""
    client = LLMClient("openai/gpt-4o") # Initialize with a valid model first
    with pytest.raises(UnknownProviderError, match="Could not determine provider for model ID: unknown/model"):
        client._determine_provider("unknown/model")


# --- Tests for __init__ ---

def test_init_success(mocker, mock_provider_class, mock_provider_instance):
    """Tests successful LLMClient initialization."""
    mock_resolve_alias = mocker.patch.object(LLMClient, "_resolve_alias")
    mock_resolve_alias.return_value = "openai/gpt-4o"

    mock_determine_provider = mocker.patch.object(LLMClient, "_determine_provider")
    mock_determine_provider.return_value = ("openai", "gpt-4o", None)

    client = LLMClient("gpt4", temperature=0.5, max_tokens=100)

    mock_resolve_alias.assert_called_once_with("gpt4")
    mock_determine_provider.assert_called_once_with("openai/gpt-4o")
    mock_provider_class.assert_called_once_with() # Called with no base_url for openai
    mock_provider_instance.get_api_credentials.assert_called_once_with(None)

    assert client.default_temperature == 0.5
    assert client.default_max_tokens == 100
    assert client.resolved_model_id == "openai/gpt-4o"
    assert client.provider_name == "openai"
    assert client.model_name_for_api == "gpt-4o"
    assert client.api_key == "mock_api_key"
    assert client.provider == mock_provider_instance


def test_init_with_api_key_override(mocker, mock_provider_class, mock_provider_instance):
    """Tests LLMClient initialization with an API key override."""
    mock_resolve_alias = mocker.patch.object(LLMClient, "_resolve_alias")
    mock_resolve_alias.return_value = "openai/gpt-4o"

    mock_determine_provider = mocker.patch.object(LLMClient, "_determine_provider")
    mock_determine_provider.return_value = ("openai", "gpt-4o", None)

    override_key = "override_api_key"
    client = LLMClient("gpt4", api_key_override=override_key)

    mock_provider_instance.get_api_credentials.assert_called_once_with(override_key)
    assert client.api_key == "mock_api_key" # The mock provider returns this


def test_init_provider_instantiation_error(mocker, mock_provider_class):
    """Tests handling of provider instantiation errors during init."""
    mock_resolve_alias = mocker.patch.object(LLMClient, "_resolve_alias")
    mock_resolve_alias.return_value = "openai/gpt-4o"

    mock_determine_provider = mocker.patch.object(LLMClient, "_determine_provider")
    mock_determine_provider.return_value = ("openai", "gpt-4o", None)

    mock_provider_class.side_effect = Exception("Instantiation failed")

    with pytest.raises(LLMClientError, match="Failed to instantiate provider MagicMock: Instantiation failed"):
        LLMClient("gpt4")

    mock_provider_class.assert_called_once_with()


def test_init_get_api_credentials_error(mocker, mock_provider_instance):
    """Tests handling of APIKeyError during get_api_credentials call in init."""
    mock_resolve_alias = mocker.patch.object(LLMClient, "_resolve_alias")
    mock_resolve_alias.return_value = "openai/gpt-4o"

    mock_determine_provider = mocker.patch.object(LLMClient, "_determine_provider")
    mock_determine_provider.return_value = ("openai", "gpt-4o", None)

    mock_provider_instance.get_api_credentials.side_effect = APIKeyError("Missing key")

    with pytest.raises(APIKeyError, match="Missing key"):
        LLMClient("gpt4")

    mock_provider_instance.get_api_credentials.assert_called_once_with(None)


def test_init_get_api_credentials_unexpected_error(mocker, mock_provider_instance):
    """Tests handling of unexpected errors during get_api_credentials call in init."""
    mock_resolve_alias = mocker.patch.object(LLMClient, "_resolve_alias")
    mock_resolve_alias.return_value = "openai/gpt-4o"

    mock_determine_provider = mocker.patch.object(LLMClient, "_determine_provider")
    mock_determine_provider.return_value = ("openai", "gpt-4o", None)

    mock_provider_instance.get_api_credentials.side_effect = Exception("Unexpected error")

    with pytest.raises(LLMClientError, match="Failed to get API credentials for provider openai: Unexpected error"):
        LLMClient("gpt4")

    mock_provider_instance.get_api_credentials.assert_called_once_with(None)


# --- Tests for create_completion ---

def test_create_completion_success(mocker, mock_provider_instance):
    """Tests successful create_completion call."""
    mock_resolve_alias = mocker.patch.object(LLMClient, "_resolve_alias")
    mock_resolve_alias.return_value = "openai/gpt-4o"

    mock_determine_provider = mocker.patch.object(LLMClient, "_determine_provider")
    mock_determine_provider.return_value = ("openai", "gpt-4o", None)

    client = LLMClient("gpt4", temperature=0.5, max_tokens=100)

    messages = [{"role": "user", "content": "Hello"}]
    completion_text = client.create_completion(messages)

    mock_provider_instance.create_completion.assert_called_once_with(
        model="gpt-4o",
        messages=messages,
        temperature=0.5, # Uses default temperature
        max_tokens=100, # Uses default max_tokens
    )
    assert completion_text == "Mock completion response"


def test_create_completion_override_params(mocker, mock_provider_instance):
    """Tests create_completion with overridden temperature and max_tokens."""
    mock_resolve_alias = mocker.patch.object(LLMClient, "_resolve_alias")
    mock_resolve_alias.return_value = "openai/gpt-4o"

    mock_determine_provider = mocker.patch.object(LLMClient, "_determine_provider")
    mock_determine_provider.return_value = ("openai", "gpt-4o", None)

    client = LLMClient("gpt4", temperature=0.5, max_tokens=100)

    messages = [{"role": "user", "content": "Hello"}]
    completion_text = client.create_completion(messages, temperature=0.8, max_tokens=200, extra_arg="test")

    mock_provider_instance.create_completion.assert_called_once_with(
        model="gpt-4o",
        messages=messages,
        temperature=0.8, # Uses overridden temperature
        max_tokens=200, # Uses overridden max_tokens
        extra_arg="test" # Passes through extra kwargs
    )
    assert completion_text == "Mock completion response"


def test_create_completion_provider_error(mocker, mock_provider_instance):
    """Tests handling of provider errors during create_completion call."""
    mock_resolve_alias = mocker.patch.object(LLMClient, "_resolve_alias")
    mock_resolve_alias.return_value = "openai/gpt-4o"

    mock_determine_provider = mocker.patch.object(LLMClient, "_determine_provider")
    mock_determine_provider.return_value = ("openai", "gpt-4o", None)

    client = LLMClient("gpt4")

    messages = [{"role": "user", "content": "Hello"}]
    mock_provider_instance.create_completion.side_effect = APIRequestError("API call failed")

    with pytest.raises(APIRequestError, match="API call failed"):
        client.create_completion(messages)

    mock_provider_instance.create_completion.assert_called_once_with(
        model="gpt-4o",
        messages=messages,
        temperature=0.0, # Uses default temperature
        max_tokens=None, # Uses default max_tokens
    )