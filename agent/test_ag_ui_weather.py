#!/usr/bin/env python3
"""
Test script for AG-UI weather data passing functionality
"""
import os
import sys
sys.path.append('.')

from tools.weather import get_weather_data_for_ui

def test_weather_data_for_ui():
    """Test the weather data for UI tool"""
    print("Testing weather data for UI tool...")
    
    # Test with Beijing
    print("\nTesting with Beijing...")
    result = get_weather_data_for_ui("北京")
    print("Result:", result)
    
    # Test with Shanghai
    print("\nTesting with Shanghai...")
    result = get_weather_data_for_ui("上海")
    print("Result:", result)
    
    # Test with Guangzhou
    print("\nTesting with Guangzhou...")
    result = get_weather_data_for_ui("广州")
    print("Result:", result)

if __name__ == "__main__":
    test_weather_data_for_ui()
