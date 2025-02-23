from dataclasses import dataclass
from typing import Dict, Tuple, Optional
import random
import math

@dataclass
class EnvironmentalFactors:
    """Defines environmental conditions affecting plant growth"""
    water_level: float  # 0-100
    light_level: float  # 0-100
    temperature: float  # in Celsius
    humidity: float  # 0-100
    soil_quality: float  # 0-100

@dataclass
class GrowthRequirements:
    """Defines a plant's optimal growing conditions"""
    optimal_water: Tuple[float, float]  # min, max
    optimal_light: Tuple[float, float]
    optimal_temp: Tuple[float, float]
    optimal_humidity: Tuple[float, float]
    drought_tolerance: float  # 0-1
    heat_tolerance: float  # 0-1

@dataclass
class GrowthCharacteristics:
    """Defines the basic growth characteristics of a plant"""
    max_height: float
    growth_rate: float
    lifespan: int

class EnvironmentSystem:
    """Manages environmental interactions and their effects on plant growth"""
    
    def __init__(self, requirements: GrowthRequirements, characteristics: GrowthCharacteristics):
        self.requirements = requirements
        self.characteristics = characteristics
        self.stress_factors: Dict[str, float] = {
            'water': 0.0,
            'light': 0.0,
            'temperature': 0.0,
            'humidity': 0.0
        }
        self.overall_health = 100.0
        self.growth_rate_modifier = 1.0
        
    def update(self, environment: EnvironmentalFactors) -> None:
        """Update plant's response to current environmental conditions"""
        # Calculate stress for each environmental factor
        self.stress_factors['water'] = self._calculate_water_stress(
            environment.water_level)
        self.stress_factors['light'] = self._calculate_light_stress(
            environment.light_level)
        self.stress_factors['temperature'] = self._calculate_temperature_stress(
            environment.temperature)
        self.stress_factors['humidity'] = self._calculate_humidity_stress(
            environment.humidity)
            
        # Update overall health based on stress factors and soil quality
        self._update_health(environment.soil_quality)
        
        # Update growth rate modifier
        self._update_growth_rate()
        
    def _calculate_water_stress(self, water_level: float) -> float:
        """Calculate water stress based on current water level"""
        min_water, max_water = self.requirements.optimal_water
        
        if water_level < min_water:
            # Water deficit stress
            deficit = (min_water - water_level) / min_water
            return deficit * (1 - self.requirements.drought_tolerance)
        elif water_level > max_water:
            # Over-watering stress
            excess = (water_level - max_water) / (100 - max_water)
            return excess
        return 0.0
        
    def _calculate_light_stress(self, light_level: float) -> float:
        """Calculate light stress based on current light level"""
        min_light, max_light = self.requirements.optimal_light
        
        if light_level < min_light:
            return (min_light - light_level) / min_light
        elif light_level > max_light:
            return (light_level - max_light) / (100 - max_light)
        return 0.0
        
    def _calculate_temperature_stress(self, temperature: float) -> float:
        """Calculate temperature stress based on current temperature"""
        min_temp, max_temp = self.requirements.optimal_temp
        
        if temperature < min_temp:
            return (min_temp - temperature) / min_temp
        elif temperature > max_temp:
            excess = (temperature - max_temp) / max_temp
            return excess * (1 - self.requirements.heat_tolerance)
        return 0.0
        
    def _calculate_humidity_stress(self, humidity: float) -> float:
        """Calculate humidity stress based on current humidity level"""
        min_humidity, max_humidity = self.requirements.optimal_humidity
        
        if humidity < min_humidity:
            return (min_humidity - humidity) / min_humidity
        elif humidity > max_humidity:
            return (humidity - max_humidity) / (100 - max_humidity)
        return 0.0
        
    def _update_health(self, soil_quality: float) -> None:
        """Update overall health based on stress factors and soil quality"""
        # Calculate average stress
        avg_stress = sum(self.stress_factors.values()) / len(self.stress_factors)
        
        # Soil quality affects recovery rate
        recovery_rate = 0.1 * (soil_quality / 100)
        
        # Update health
        if avg_stress > 0:
            self.overall_health = max(0, self.overall_health - avg_stress * 2)
        else:
            self.overall_health = min(100, self.overall_health + recovery_rate)
            
    def _update_growth_rate(self) -> None:
        """Update growth rate modifier based on health and stress"""
        # Base growth rate depends on overall health
        base_rate = self.overall_health / 100
        
        # Stress factors can further reduce growth
        stress_modifier = 1 - (sum(self.stress_factors.values()) / 4)
        
        self.growth_rate_modifier = max(0, base_rate * stress_modifier)
        
    def get_growth_modifier(self) -> float:
        """Get the current growth rate modifier"""
        return self.growth_rate_modifier
        
    def is_flourishing(self) -> bool:
        """Check if the plant is in optimal growing conditions"""
        return self.overall_health > 90 and self.growth_rate_modifier > 0.9
        
    def is_stressed(self) -> bool:
        """Check if the plant is under significant stress"""
        return self.overall_health < 50 or self.growth_rate_modifier < 0.5
        
    def get_dominant_stress_factor(self) -> Optional[str]:
        """Get the environmental factor causing the most stress"""
        if not any(self.stress_factors.values()):
            return None
            
        return max(self.stress_factors.items(), key=lambda x: x[1])[0]
        
    def should_wither(self) -> bool:
        """Determine if conditions are severe enough to cause withering"""
        return self.overall_health < 20 or self.growth_rate_modifier < 0.1
