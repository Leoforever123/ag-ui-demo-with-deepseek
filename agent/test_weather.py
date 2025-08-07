#!/usr/bin/env python3
"""
Test script for weather tools
"""
import os
import dotenv
import sys
sys.path.append('.')
dotenv.load_dotenv()

from tools.weather import get_weather, AmapWeatherService

def test_weather_service():
    """Test the weather service"""
    print("Testing weather service...")
    
    # Test with API key from environment
    api_key = os.getenv("AMAP_API_KEY")
    if not api_key:
        print("Warning: AMAP_API_KEY not set in environment")
        print("Please set AMAP_API_KEY environment variable")
        return
    
    try:
        # Test the weather service directly
        service = AmapWeatherService(api_key)
        
        # Test with Beijing
        print("\nTesting with Beijing...")
        weather = service.get_current_weather("北京市")
        print(service.format_weather_response(weather))
        
        # Test with Shanghai
        print("\nTesting with Shanghai...")
        weather = service.get_current_weather("上海")
        print(service.format_weather_response(weather))
        
    except Exception as e:
        print(f"Error testing weather service: {e}")

def test_weather_tool():
    """Test the weather tool"""
    print("\nTesting weather tool...")
    
    try:
        # Test the tool function using invoke method instead of __call__
        result = get_weather.invoke({"location": "北京"})
        print(f"Tool result: {result}")
        
    except Exception as e:
        print(f"Error testing weather tool: {e}")

if __name__ == "__main__":
    test_weather_service()
    test_weather_tool()
