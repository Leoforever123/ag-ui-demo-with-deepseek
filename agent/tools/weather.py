import os
import csv
import requests
from typing import Dict, Optional, List
from dataclasses import dataclass
from langchain.tools import tool

@dataclass
class WeatherInfo:
    """Weather information data class"""
    city: str
    temperature: str
    weather: str
    humidity: str
    wind_direction: str
    wind_power: str
    report_time: str
    province: str = ""
    adcode: str = ""

class CityCodeMapper:
    """Map city names to adcodes using the CSV file"""
    
    def __init__(self, csv_path: str = "./tools/AMap_adcode_citycode.CSV"):
        self.city_to_adcode = {}
        self._load_city_codes(csv_path)
    
    def _load_city_codes(self, csv_path: str):
        """Load city codes from CSV file"""
        try:
            with open(csv_path, 'r', encoding='GBK') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    city_name = row['中文名']
                    adcode = row['adcode']
                    if adcode and adcode != '\\N':
                        self.city_to_adcode[city_name] = adcode
        except FileNotFoundError:
            print(f"Warning: City code file not found at {csv_path}")
        except Exception as e:
            print(f"Error loading city codes: {e}")
    
    def get_adcode(self, city_name: str) -> Optional[str]:
        """Get adcode for a city name"""
        # Direct lookup
        if city_name in self.city_to_adcode:
            return self.city_to_adcode[city_name]
        
        # Try partial matches
        for city, adcode in self.city_to_adcode.items():
            if city_name in city or city in city_name:
                return adcode
        
        return None

class AmapWeatherService:
    """Weather service using Amap (高德地图) API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the weather service
        
        Args:
            api_key: Amap API key. If not provided, will try to get from AMAP_API_KEY env var
        """
        self.api_key = api_key or os.getenv("AMAP_API_KEY")
        if not self.api_key:
            raise ValueError("Amap API key is required. Set AMAP_API_KEY environment variable or pass api_key parameter.")
        
        self.base_url = "https://restapi.amap.com/v3/weather/weatherInfo"
        self.city_mapper = CityCodeMapper()
    
    def get_current_weather(self, location: str) -> WeatherInfo:
        """
        Get current weather for a location
        
        Args:
            location: City name or adcode
            
        Returns:
            WeatherInfo object with weather data
        """
        # Get adcode for the location
        adcode = self._get_adcode(location)
        if not adcode:
            raise Exception(f"Location not found: {location}")
        
        # Prepare request parameters according to API documentation
        params = {
            "city": adcode,
            "extensions": "base",  # base for current weather
            "key": self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "1":
                raise Exception(f"Weather API error: {data.get('info', 'Unknown error')}")
            
            lives = data.get("lives", [])
            if not lives:
                raise Exception(f"No weather data found for location: {location}")
            
            live_data = lives[0]
            
            return WeatherInfo(
                city=live_data.get("city", ""),
                temperature=live_data.get("temperature", ""),
                weather=live_data.get("weather", ""),
                humidity=live_data.get("humidity", ""),
                wind_direction=live_data.get("winddirection", ""),
                wind_power=live_data.get("windpower", ""),
                report_time=live_data.get("reporttime", ""),
                province=live_data.get("province", ""),
                adcode=live_data.get("adcode", "")
            )
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to make request to Amap API: {e}")
    
    def _get_adcode(self, location: str) -> Optional[str]:
        """
        Get adcode for a location
        
        Args:
            location: City name or location string
            
        Returns:
            Adcode string or None if not found
        """
        # If location is already an adcode (6 digits), return it
        if location.isdigit() and len(location) == 6:
            return location
        
        # Try to get adcode from city mapper
        return self.city_mapper.get_adcode(location)
    
    def format_weather_response(self, weather: WeatherInfo) -> str:
        """
        Format weather information into a readable string
        
        Args:
            weather: WeatherInfo object
            
        Returns:
            Formatted weather string
        """
        return f"""📍 {weather.city} ({weather.province})
🌡️ 温度: {weather.temperature}°C
🌤️ 天气: {weather.weather}
💧 湿度: {weather.humidity}%
🌬️ 风向: {weather.wind_direction}
💨 风力: {weather.wind_power}
⏰ 更新时间: {weather.report_time}"""

# Initialize weather service
try:
    weather_service = AmapWeatherService()
except ValueError as e:
    print(f"Warning: {e}")
    weather_service = None

@tool
def get_weather(location: str):
    """
    Get the current weather for a given location using Amap (高德地图) API.
    
    Args:
        location: City name in Chinese (e.g., "北京", "上海", "广州") or adcode
        
    Returns:
        Formatted weather information string
    """
    if not weather_service:
        return "错误: 未配置高德地图API密钥。请设置AMAP_API_KEY环境变量。"
    
    try:
        weather = weather_service.get_current_weather(location)
        return weather_service.format_weather_response(weather)
    except Exception as e:
        return f"获取天气信息失败: {str(e)}"

@tool
def get_weather_forecast(location: str, days: int = 3):
    """
    Get weather forecast for a given location using Amap (高德地图) API.
    
    Args:
        location: City name in Chinese (e.g., "北京", "上海", "广州") or adcode
        days: Number of days to forecast (1-3, default 3)
        
    Returns:
        Formatted weather forecast string
    """
    if not weather_service:
        return "错误: 未配置高德地图API密钥。请设置AMAP_API_KEY环境变量。"
    
    try:
        # Limit days to 1-3
        days = max(1, min(3, days))
        forecasts = weather_service.get_weather_forecast(location, days)
        return weather_service.format_forecast_response(forecasts)
    except Exception as e:
        return f"获取天气预报失败: {str(e)}"

@tool
def get_weather_data_for_ui(location: str):
    """
    Get weather data for UI components. This tool returns structured weather data
    that can be used by frontend components to display dynamic weather cards.
    
    Args:
        location: City name in Chinese (e.g., "北京", "上海", "广州") or adcode
        
    Returns:
        Dictionary containing weather data for UI display
    """
    if not weather_service:
        return {
            "error": "未配置高德地图API密钥。请设置AMAP_API_KEY环境变量。"
        }
    
    try:
        weather = weather_service.get_current_weather(location)
        
        # Return structured data for frontend use
        return {
            "success": True,
            "location": location,
            "data": {
                "city": weather.city,
                "province": weather.province,
                "temperature": weather.temperature,
                "weather": weather.weather,
                "humidity": weather.humidity,
                "wind_direction": weather.wind_direction,
                "wind_power": weather.wind_power,
                "report_time": weather.report_time
            }
        }
        
    except Exception as e:
        return {
            "error": f"获取天气信息失败: {str(e)}"
        }
    