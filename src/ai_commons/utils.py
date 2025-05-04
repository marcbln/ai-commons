import re
from typing import Optional

def strip_backticks(text: Optional[str]) -> Optional[str]:
    """
    Removes surrounding markdown code fences (```...```) and strips whitespace.

    Args:
        text: The input string, potentially containing markdown code fences.

    Returns:
        The string with surrounding code fences removed and whitespace stripped,
        or None if the input is None.
    """
    if text is None:
        return None

    text = text.strip()

    # Pattern to find ``` ``` blocks, capturing the content inside
    # Handles optional language identifier and leading/trailing whitespace around the block
    # Using re.DOTALL to match across lines and re.MULTILINE for ^ and $ to match start/end of lines
    pattern = r"^\s*```(?:\w+)?\s*\n(.*?)\n\s*```\s*$"
    match = re.match(pattern, text, re.DOTALL | re.MULTILINE)

    if match:
        # If a block is found, return the captured content, stripped
        return match.group(1).strip()
    else:
        # If no block pattern matches, return the stripped original text.
        # This handles cases where the input doesn't contain ``` blocks.
        return text