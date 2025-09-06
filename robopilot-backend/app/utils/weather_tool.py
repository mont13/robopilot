"""
Weather Tool Example using BeeAI Framework.

This module demonstrates how to create a simple weather tool using the BeeAI @tool decorator.
This serves as an example of creating custom tools that can be used by agents.
"""

import logging
from datetime import datetime

from beeai_framework.tools import StringToolOutput, tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class WeatherToolInput(BaseModel):
    """Input schema for weather tool."""

    location: str = Field(
        ...,
        description="Location for weather query (e.g., 'New York', 'London', 'Tokyo')",
    )
    date: str | None = Field(
        default=None,
        description="Date for weather query in YYYY-MM-DD format. If not provided, returns current weather.",
    )
    units: str = Field(
        default="celsius",
        description="Temperature units - 'celsius' or 'fahrenheit'",
        pattern="^(celsius|fahrenheit)$",
    )


@tool
def get_weather(input_data: WeatherToolInput) -> StringToolOutput:
    """
    Get weather information for a specified location and date.

    This is a mock weather tool that returns simulated weather data.
    In a real implementation, this would connect to a weather API service.

    Args:
        input_data: Weather query parameters including location, date, and units

    Returns:
        StringToolOutput: Weather information as formatted text

    Example:
        The agent can call this tool like:
        "What's the weather in New York?"
        -> get_weather(location="New York", units="celsius")
    """
    try:
        location = input_data.location
        query_date = input_data.date
        units = input_data.units

        logger.info(f"Getting weather for {location} on {query_date or 'today'}")

        # Mock weather data - in real implementation, call actual weather API
        mock_weather_data = {
            "new york": {
                "temperature": 22 if units == "celsius" else 72,
                "condition": "Partly cloudy",
                "humidity": 65,
                "wind": "10 km/h NW",
            },
            "london": {
                "temperature": 15 if units == "celsius" else 59,
                "condition": "Light rain",
                "humidity": 80,
                "wind": "8 km/h SW",
            },
            "tokyo": {
                "temperature": 25 if units == "celsius" else 77,
                "condition": "Sunny",
                "humidity": 55,
                "wind": "5 km/h E",
            },
        }

        # Normalize location for lookup
        location_key = location.lower().strip()

        # Get weather data or use default
        weather_data = mock_weather_data.get(
            location_key,
            {
                "temperature": 20 if units == "celsius" else 68,
                "condition": "Clear",
                "humidity": 60,
                "wind": "7 km/h N",
            },
        )

        # Format date string
        date_str = query_date if query_date else datetime.now().strftime("%Y-%m-%d")

        # Format temperature unit
        temp_unit = "°C" if units == "celsius" else "°F"

        # Build response
        weather_report = f"""Weather for {location.title()} on {date_str}:

🌡️  Temperature: {weather_data["temperature"]}{temp_unit}
☁️  Condition: {weather_data["condition"]}
💧 Humidity: {weather_data["humidity"]}%
💨 Wind: {weather_data["wind"]}

Note: This is simulated weather data for demonstration purposes."""

        logger.info(f"Successfully retrieved weather for {location}")
        return StringToolOutput(weather_report)

    except Exception as e:
        error_msg = f"Error getting weather for {input_data.location}: {str(e)}"
        logger.error(error_msg)
        return StringToolOutput(
            f"Sorry, I couldn't get the weather information. {error_msg}"
        )


def get_weather_tool():
    """
    Get the weather tool instance.

    Returns:
        The weather tool function decorated with @tool
    """
    return get_weather


# Example of how to create multiple related tools
class WeatherForecastInput(BaseModel):
    """Input for weather forecast tool."""

    location: str = Field(..., description="Location for weather forecast")
    days: int = Field(
        default=3, description="Number of days to forecast (1-7)", ge=1, le=7
    )


@tool
def get_weather_forecast(input_data: WeatherForecastInput) -> StringToolOutput:
    """
    Get weather forecast for multiple days.

    Args:
        input_data: Forecast parameters

    Returns:
        StringToolOutput: Multi-day weather forecast
    """
    try:
        location = input_data.location
        days = input_data.days

        logger.info(f"Getting {days}-day forecast for {location}")

        # Mock forecast data
        conditions = ["Sunny", "Partly cloudy", "Cloudy", "Light rain", "Clear"]
        temperatures = [22, 20, 18, 16, 24]  # Celsius

        forecast_text = f"{days}-Day Weather Forecast for {location.title()}:\n\n"

        for i in range(days):
            forecast_date = datetime.now().replace(day=datetime.now().day + i)
            temp = temperatures[i % len(temperatures)]
            condition = conditions[i % len(conditions)]

            forecast_text += (
                f"📅 {forecast_date.strftime('%Y-%m-%d')}: {temp}°C, {condition}\n"
            )

        forecast_text += "\nNote: This is simulated forecast data for demonstration."

        return StringToolOutput(forecast_text)

    except Exception as e:
        error_msg = f"Error getting forecast: {str(e)}"
        logger.error(error_msg)
        return StringToolOutput(
            f"Sorry, I couldn't get the weather forecast. {error_msg}"
        )


# List of weather tools for easy import
WEATHER_TOOLS = [
    get_weather,
    get_weather_forecast,
]


def get_weather_tools():
    """
    Get all weather-related tools.

    Returns:
        List of weather tool functions
    """
    return WEATHER_TOOLS
