from dataclasses import dataclass
from typing import List, Tuple
import pygame
import random
import math

@dataclass
class PetalShape:
    type: str
    length_ratio: float
    tip_shape: str
    edge_type: str
    curve: float

@dataclass
class FlowerStructure:
    arrangement: str
    num_petals: int
    petal_layers: int
    symmetry: str
    center_type: str
    center_size_ratio: float

@dataclass
class FlowerColors:
    petal_colors: List[Tuple[int, int, int]]
    center_color: Tuple[int, int, int]
    color_variation: int
    has_patterns: bool

class FlowerGenerator:
    def __init__(self, petal_shape: PetalShape, structure: FlowerStructure, colors: FlowerColors):
        self.petal_shape = petal_shape
        self.structure = structure
        self.colors = colors
        
    def draw(self, surface: pygame.Surface, pos: Tuple[float, float], size: float, angle: float) -> None:
        """Draw a flower on the surface"""
        # Draw petals in layers, from back to front
        for layer in range(self.structure.petal_layers - 1, -1, -1):
            layer_size = size * (1 - 0.15 * layer)  # Layers closer in size
            layer_angle_offset = layer * math.pi / (self.structure.petal_layers * 2)
            self._draw_petal_layer(surface, pos, layer_size, angle + layer_angle_offset, layer)
            
        # Draw center
        center_size = size * self.structure.center_size_ratio
        # Draw a larger dark center first for depth
        pygame.draw.circle(surface, (0, 0, 0),
                         (int(pos[0]), int(pos[1])), int(center_size * 1.2))
        # Draw the actual center
        pygame.draw.circle(surface, self.colors.center_color,
                         (int(pos[0]), int(pos[1])), int(center_size))
                         
    def _draw_petal_layer(self, surface: pygame.Surface, pos: Tuple[float, float],
                         size: float, base_angle: float, layer: int) -> None:
        """Draw a layer of petals"""
        num_petals = self.structure.num_petals
        petal_color = self._get_petal_color(layer)
        
        for i in range(num_petals):
            # Calculate petal angle
            angle = base_angle + (2 * math.pi * i / num_petals)
            
            # Generate petal points
            points = self._generate_petal_points(pos, size, angle)
            
            # Draw petal
            if len(points) > 2:
                pygame.draw.polygon(surface, petal_color, points)
                # Draw petal outline
                pygame.draw.polygon(surface, (0, 0, 0), points, max(1, int(size/20)))
                
    def _get_petal_color(self, layer: int) -> Tuple[int, int, int]:
        """Get color for petal with variation"""
        base_color = self.colors.petal_colors[layer % len(self.colors.petal_colors)]
        if not self.colors.color_variation:
            return base_color
            
        r, g, b = base_color
        var = self.colors.color_variation
        return (
            max(0, min(255, r + random.randint(-var, var))),
            max(0, min(255, g + random.randint(-var, var))),
            max(0, min(255, b + random.randint(-var, var)))
        )
        
    def _generate_petal_points(self, pos: Tuple[float, float],
                             size: float, angle: float) -> List[Tuple[float, float]]:
        """Generate points for a petal"""
        points = []
        num_points = 20
        
        # Petal shape parameters
        width = size * 0.5
        curve = self.petal_shape.curve * 1.5
        
        for i in range(num_points):
            t = i / (num_points - 1)
            
            # Calculate petal shape
            if self.petal_shape.type == "round":
                # Round petal shape using sine curve
                r = size * (1 - t * 0.8)
                w = width * math.sin(t * math.pi)
                # Add wave pattern to petal edge
                w += width * 0.2 * math.sin(t * math.pi * 4) * t
            else:  # pointed
                # Pointed petal shape
                r = size * (1 - t)
                w = width * (1 - t)
                
            # Add curve to petal
            x_offset = curve * size * math.sin(t * math.pi)
            
            # Calculate final position
            x = pos[0] + math.cos(angle) * r - math.sin(angle) * w + math.cos(angle + math.pi/2) * x_offset
            y = pos[1] + math.sin(angle) * r + math.cos(angle) * w + math.sin(angle + math.pi/2) * x_offset
            
            points.append((x, y))
            
        # Add points for the other side of the petal
        for i in range(num_points - 1, -1, -1):
            t = i / (num_points - 1)
            
            if self.petal_shape.type == "round":
                r = size * (1 - t * 0.8)
                w = width * math.sin(t * math.pi)
                w += width * 0.2 * math.sin(t * math.pi * 4) * t
            else:
                r = size * (1 - t)
                w = width * (1 - t)
                
            x_offset = curve * size * math.sin(t * math.pi)
            
            x = pos[0] + math.cos(angle) * r + math.sin(angle) * w + math.cos(angle + math.pi/2) * x_offset
            y = pos[1] + math.sin(angle) * r - math.cos(angle) * w + math.sin(angle + math.pi/2) * x_offset
            
            points.append((x, y))
            
        return points
