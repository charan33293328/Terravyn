from abc import ABC, abstractmethod
from typing import Dict, Any

class WeatherProvider(ABC):
    """
    Abstract interface for weather data providers.
    Allows easy pluggability for Open-Meteo, IMD, NOAA, etc.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the unique identifier of the provider."""
        pass

    @abstractmethod
    def fetch_weather(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Fetch current observations and forecasts for given coordinates.
        Returns a standardized dictionary with keys:
          - 'current': Dict of current metrics (temp, humidity, rain, wind, ET0, etc.)
          - 'daily': List[Dict] of daily forecast metrics (temp max/min, rain sum, ET0, etc.)
          - 'hourly': List[Dict] of hourly forecast metrics (temp, humidity, rain prob, ET0, etc.)
        """
        pass
