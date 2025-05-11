"""
Tools for use with the LM Studio API.
"""

from typing import Dict, Any, List, Callable
from pathlib import Path


def add(a: float, b: float) -> float:
    """Given two numbers a and b, returns the sum of them."""
    return a + b


def multiply(a: float, b: float) -> float:
    """Given two numbers a and b, returns the product of them."""
    return a * b


def create_json_from_text(text: str) -> Dict[str, Any]:
    """Convert the text into a JSON structure with key information extracted."""
    import json

    # This is a simplified example - in a real-world scenario,
    # you might use more sophisticated parsing logic
    try:
        # Try to parse the text as JSON directly
        return json.loads(text)
    except json.JSONDecodeError:
        # If it's not valid JSON, return a simple structure
        return {"text": text, "length": len(text), "words": len(text.split())}


def create_file(name: str, content: str) -> str:
    """Create a file with the given name and content."""
    dest_path = Path(name)
    if dest_path.exists():
        return "Error: File already exists."
    try:
        dest_path.write_text(content, encoding="utf-8")
    except Exception as exc:
        return f"Error: {exc!r}"
    return "File created."


# List of predefined tools that can be used with the LM Studio API
PREDEFINED_TOOLS: List[Callable] = [add, multiply, create_json_from_text, create_file]
