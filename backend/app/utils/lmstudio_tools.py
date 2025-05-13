"""
Tools for use with the LM Studio API and PraisonAI integration.

This module contains predefined tools that can be used with LM Studio and PraisonAI agents.
Tools are implemented as Python functions with docstrings that describe their functionality.
"""

import logging
from typing import Callable, List

# Set up logging
logger = logging.getLogger(__name__)


def add(a: float, b: float) -> float:
    """
    Given two numbers a and b, returns the sum of them.

    Args:
        a (float): First number
        b (float): Second number

    Returns:
        float: The sum of a and b
    """
    result = a + b
    logger.info(f"Adding {a} + {b} = {result}")
    return result


def multiply(a: float, b: float) -> float:
    """
    Given two numbers a and b, returns the product of them.

    Args:
        a (float): First number
        b (float): Second number

    Returns:
        float: The product of a and b
    """
    result = a * b
    logger.info(f"Multiplying {a} * {b} = {result}")
    return result


# List of predefined tools that can be used with the LM Studio API and PraisonAI agents
PREDEFINED_TOOLS: List[Callable] = [
    add,
    multiply,
]
