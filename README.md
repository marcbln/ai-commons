# ai-commons

Shared Python library for interacting with Large Language Models (LLMs). Provides a common interface for different providers and handles configuration like model aliases and API keys.


## Testing

To run the tests for the `ai-commons` library, follow these steps:

1.  **Install Poetry** (if not already installed):
    ```bash
    curl -sSL https://install.python-poetry.org | python3 -
    ```
    *(Note: Ensure Poetry's bin directory is in your PATH after installation)*

2.  **Navigate to the project root**:
    ```bash
    cd /path/to/ai-commons 
    ``` 
    *(Replace `/path/to/ai-commons` with the actual path to the project directory)*

3.  **Install dependencies** (including development dependencies):
    ```bash
    poetry install
    ```

4.  **Run tests** using pytest (managed by Poetry):
    ```bash
    poetry run pytest tests/
    ```