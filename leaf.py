from dataclasses import dataclass
from typing import List, Tuple, Optional
import pygame
import math
import random

@dataclass
class LeafShape:
    """Defines the shape characteristics of a leaf"""
    type: str  # 'simple', 'compound', 'needle', etc.
    length_ratio: float  # ratio of length to width
    edge_type: str  # 'smooth', 'serrated', 'lobed'
    vein_pattern: str  # 'parallel', 'pinnate', 'palmate'
    base_shape: str  # 'rounded', 'pointed', 'heart'
    tip_shape: str  # 'acute', 'obtuse', 'rounded'

@dataclass
class LeafColor:
    """Defines the color characteristics of a leaf"""
    base_color: Tuple[int, int, int]
    variation: int  # Amount of random variation allowed
    vein_color: Optional[Tuple[int, int, int]] = None
    seasonal_colors: Optional[List[Tuple[int, int, int]]] = None

class LeafGenerator:
    """Generates and renders leaves based on shape and color definitions"""
    
    def __init__(self, shape: LeafShape, color: LeafColor):
        self.shape = shape
        self.color = color
        
    def generate_points(self, size: float, angle: float) -> List[Tuple[float, float]]:
        """Generate points for leaf outline based on shape type"""
        points = []
        
        if self.shape.type == 'simple':
            points = self._generate_simple_leaf(size, angle)
        elif self.shape.type == 'compound':
            points = self._generate_compound_leaf(size, angle)
        elif self.shape.type == 'needle':
            points = self._generate_needle_leaf(size, angle)
            
        return points
        
    def _generate_simple_leaf(self, size: float, angle: float) -> List[Tuple[float, float]]:
        """Generate a simple leaf shape"""
        points = []
        width = size / self.shape.length_ratio
        num_points = 20
        
        for i in range(num_points + 1):
            t = i / num_points
            # Leaf shape formula using modified ellipse
            x = size * math.cos(math.pi * t)
            
            # Modify y based on edge_type
            if self.shape.edge_type == 'smooth':
                y = width * math.sin(math.pi * t)
            elif self.shape.edge_type == 'serrated':
                y = width * math.sin(math.pi * t) * (1 + 0.2 * math.sin(8 * math.pi * t))
            elif self.shape.edge_type == 'lobed':
                y = width * math.sin(math.pi * t) * (1 + 0.4 * math.sin(3 * math.pi * t))
                
            # Rotate points by angle
            rotated_x = x * math.cos(angle) - y * math.sin(angle)
            rotated_y = x * math.sin(angle) + y * math.cos(angle)
            
            points.append((rotated_x, rotated_y))
            
        return points
        
    def _generate_compound_leaf(self, size: float, angle: float) -> List[Tuple[float, float]]:
        """Generate a compound leaf with multiple leaflets"""
        points = []
        num_leaflets = 5  # Could be parameterized
        
        for i in range(num_leaflets):
            leaflet_size = size * 0.4
            leaflet_angle = angle + (i - num_leaflets//2) * math.pi/6
            leaflet_points = self._generate_simple_leaf(leaflet_size, leaflet_angle)
            
            # Offset leaflets along the main stem
            offset_x = size * 0.8 * (i / (num_leaflets-1) - 0.5)
            offset_y = 0
            
            # Apply offset to all points
            offset_points = [(x + offset_x, y + offset_y) for x, y in leaflet_points]
            points.extend(offset_points)
            
        return points
        
    def _generate_needle_leaf(self, size: float, angle: float) -> List[Tuple[float, float]]:
        """Generate a needle-like leaf"""
        width = size / 10  # Very narrow for needle leaves
        
        points = [
            (0, -width/2),
            (size, 0),
            (0, width/2)
        ]
        
        # Rotate points by angle
        rotated_points = []
        for x, y in points:
            rotated_x = x * math.cos(angle) - y * math.sin(angle)
            rotated_y = x * math.sin(angle) + y * math.cos(angle)
            rotated_points.append((rotated_x, rotated_y))
            
        return rotated_points
        
    def get_color(self, age: float = 1.0, season: str = 'summer') -> Tuple[int, int, int]:
        """Get leaf color based on age and season"""
        base_r, base_g, base_b = self.color.base_color
        
        # Add random variation
        var = lambda x: max(0, min(255, x + random.randint(-self.color.variation, self.color.variation)))
        color = (var(base_r), var(base_g), var(base_b))
        
        # Apply seasonal changes if defined
        if self.color.seasonal_colors and season != 'summer':
            seasonal_color = self.color.seasonal_colors[['spring', 'summer', 'fall', 'winter'].index(season)]
            # Interpolate between base color and seasonal color based on age
            blend = min(1.0, age * 2)  # Full seasonal color after age 0.5
            color = tuple(int(c1 * (1-blend) + c2 * blend) for c1, c2 in zip(color, seasonal_color))
            
        return color
        
    def draw(self, surface: pygame.Surface, pos: Tuple[float, float], 
            size: float, angle: float, age: float = 1.0, season: str = 'summer') -> None:
        """Draw the leaf on the given surface"""
        points = self.generate_points(size, angle)
        
        # Translate points to position
        translated_points = [(x + pos[0], y + pos[1]) for x, y in points]
        
        # Draw filled leaf
        if len(translated_points) >= 3:
            color = self.get_color(age, season)
            pygame.draw.polygon(surface, color, translated_points)
            
            # Draw veins if specified
            if self.color.vein_color and self.shape.vein_pattern != 'none':
                self._draw_veins(surface, translated_points, self.color.vein_color, 
                               self.shape.vein_pattern)
                
    def _draw_veins(self, surface: pygame.Surface, points: List[Tuple[float, float]], 
                    color: Tuple[int, int, int], pattern: str) -> None:
        """Draw leaf veins based on pattern type"""
        if len(points) < 2:
            return
            
        # Calculate leaf center and main vein
        center_x = sum(x for x, _ in points) / len(points)
        center_y = sum(y for _, y in points) / len(points)
        
        if pattern == 'pinnate':
            # Draw main vein
            start = points[0]
            end = points[len(points)//2]
            pygame.draw.line(surface, color, start, end, 1)
            
            # Draw side veins
            num_veins = 5
            for i in range(num_veins):
                t = (i + 1) / (num_veins + 1)
                main_point = (
                    start[0] + (end[0] - start[0]) * t,
                    start[1] + (end[1] - start[1]) * t
                )
                
                # Draw two side veins
                angle = math.atan2(end[1] - start[1], end[0] - start[0]) + math.pi/2
                length = 20  # Could be parameterized
                
                for side in [-1, 1]:
                    vein_end = (
                        main_point[0] + math.cos(angle) * length * side,
                        main_point[1] + math.sin(angle) * length * side
                    )
                    pygame.draw.line(surface, color, main_point, vein_end, 1)
                    
        elif pattern == 'palmate':
            # Draw veins radiating from base
            num_veins = 5
            for i in range(num_veins):
                angle = math.pi * (0.2 + 0.6 * i/(num_veins-1))  # 0.2π to 0.8π range
                length = 30  # Could be parameterized
                end = (
                    center_x + math.cos(angle) * length,
                    center_y + math.sin(angle) * length
                )
                pygame.draw.line(surface, color, (center_x, center_y), end, 1)
