"""Custom exceptions for the ai-commons library."""

class LLMClientError(Exception):
    """Base exception for ai-commons library errors."""
    pass

class ConfigurationError(LLMClientError):
    """For errors related to configuration loading or validation."""
    pass

class ModelAliasError(ConfigurationError):
    """For errors specifically related to model alias resolution."""
    pass

class APIKeyError(LLMClientError):
    """For errors related to missing or invalid API keys."""
    pass

class UnknownProviderError(LLMClientError):
    """For errors when a model identifier doesn't match a known provider prefix."""
    pass

class APIRequestError(LLMClientError):
    """For errors occurring during an API call to an LLM provider."""
    pass