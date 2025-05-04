import pytest
from ai_commons.utils import strip_backticks

def test_strip_backticks_with_code_block():
    """Tests stripping backticks with a code block and language."""
    text = """
```python
print("hello")
```
"""
    expected = 'print("hello")'
    assert strip_backticks(text) == expected

def test_strip_backticks_with_code_block_no_language():
    """Tests stripping backticks with a code block but no language."""
    text = """
```
print("hello")
```
"""
    expected = 'print("hello")'
    assert strip_backticks(text) == expected

def test_strip_backticks_without_code_block():
    """Tests stripping backticks with text that does not contain a code block."""
    text = "This is just plain text."
    expected = "This is just plain text."
    assert strip_backticks(text) == expected

def test_strip_backticks_with_only_backticks():
    """Tests stripping backticks with only the surrounding backticks."""
    text = """
```
```
"""
    expected = ""
    assert strip_backticks(text) == expected

def test_strip_backticks_empty_string():
    """Tests stripping backticks with an empty string input."""
    text = ""
    expected = ""
    assert strip_backticks(text) == expected

def test_strip_backticks_none_input():
    """Tests stripping backticks with None input."""
    text = None
    expected = None
    assert strip_backticks(text) == expected

def test_strip_backticks_with_leading_trailing_whitespace():
    """Tests stripping backticks with leading/trailing whitespace around the block."""
    text = """
    ```python
    print("hello")
    ```
    """
    expected = 'print("hello")'
    assert strip_backticks(text) == expected

def test_strip_backticks_with_internal_whitespace():
    """Tests stripping backticks with internal whitespace within the block."""
    text = """
```
  line 1
    line 2
```
"""
    expected = """line 1
    line 2"""
    assert strip_backticks(text) == expected

def test_strip_backticks_multiple_blocks_only_first_stripped():
    """Tests that only the outermost block is stripped if multiple exist."""
    text = """
```
outer block
```python
inner block
```
"""
    # The current implementation only matches the full string as a single block.
    # If it doesn't match the full string pattern, it returns the original stripped text.
    # So, this input should not match the pattern and return the original text stripped.
    expected = """outer block
```python
inner block
```"""
    assert strip_backticks(text) == expected

def test_strip_backticks_partial_block():
    """Tests stripping backticks with only a partial block."""
    text = """
```python
print("hello")
"""
    expected = """
```python
print("hello")
"""
    assert strip_backticks(text) == expected