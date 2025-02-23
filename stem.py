from dataclasses import dataclass
from typing import List, Tuple, Optional
import pygame
import math
import random

@dataclass
class StemProperties:
    """Defines the physical properties of a stem"""
    thickness: float
    flexibility: float  # How much the stem bends
    branching_angle: float  # Base angle for branches
    branching_variance: float  # Random variance in branch angles
    max_branches: int
    growth_rate: float
    branch_spacing: float  # How far apart branches are

@dataclass
class StemAppearance:
    """Defines the visual properties of a stem"""
    color: Tuple[int, int, int]
    texture: str  # 'smooth', 'woody', 'thorny'
    node_visibility: float  # How visible nodes are (0-1)
    thorn_frequency: float = 0.0  # For thorny stems

@dataclass
class StemSystemDefinition:
    """Complete definition of a stem system"""
    properties: StemProperties
    appearance: StemAppearance

class Branch:
    """Represents a single branch in the plant"""
    def __init__(self, start_pos: Tuple[float, float], angle: float, length: float = 0.0):
        self.start_pos = start_pos
        self.angle = angle
        self.length = length
        self.growth = 0.0  # 0.0 to 1.0
        self.children: List['Branch'] = []
        self.end_pos = (0, 0)  # New attribute
        self._update_end_pos()
        
    def _update_end_pos(self):
        """Update end position based on growth"""
        dx = math.cos(self.angle) * self.length * self.growth
        dy = -math.sin(self.angle) * self.length * self.growth  # Negative to grow upward
        self.end_pos = (
            self.start_pos[0] + dx,
            self.start_pos[1] + dy
        )
        
    def grow(self, amount: float) -> None:
        """Grow the branch and all its children"""
        self.growth = min(1.0, self.growth + amount)
        self._update_end_pos()
        
        # Grow existing children
        for child in self.children:
            child.grow(amount)
            
    def add_child(self, angle_offset: float, length: float) -> None:
        """Add a new child branch at the given angle offset"""
        # Calculate absolute angle for child
        child_angle = self.angle + angle_offset
        
        # Create new branch starting from current end
        child = Branch(self.end_pos, child_angle, length)
        self.children.append(child)

    def draw(self, surface: pygame.Surface, color: Tuple[int, int, int],
            thickness: float) -> None:
        """Draw the branch and all its children"""
        if self.growth <= 0:
            return
            
        # Draw current branch
        if self.length > 0:
            pygame.draw.line(surface, color,
                           (int(self.start_pos[0]), int(self.start_pos[1])),
                           (int(self.end_pos[0]), int(self.end_pos[1])),
                           max(1, int(thickness)))
                           
        # Draw children
        for child in self.children:
            child.draw(surface, color, thickness * 0.8)  # Children slightly thinner

class StemSystem:
    """Manages the growth and rendering of a plant's stem system"""
    
    def __init__(self, properties: StemProperties, appearance: StemAppearance):
        self.properties = properties
        self.appearance = appearance
        self.main_stem = Branch((0, 0), math.pi/2, 100.0)  # Start growing upward
        self.branch_side = 1  # Start with right side
        self.last_branch_height = 0  # Track height of last branch
        self.health = 100.0  # Track health for visual effects
        
    def grow(self, amount: float) -> None:
        """Grow the stem system"""
        # Grow existing branches
        self.main_stem.grow(amount * self.properties.growth_rate)
        
        # Add new branches if conditions are met
        current_height = abs(self.main_stem.end_pos[1] - self.main_stem.start_pos[1])
        min_spacing = self.properties.branch_spacing * self.main_stem.length
        
        # Only add branches if we've grown enough since the last branch
        if (current_height - self.last_branch_height >= min_spacing and
            len(self.main_stem.children) < self.properties.max_branches):
            
            # Add branches on both sides
            for side in [-1, 1]:
                # Calculate branch angle with variance
                base_angle = self.properties.branching_angle * side
                variance = random.uniform(-self.properties.branching_variance,
                                       self.properties.branching_variance)
                branch_angle = base_angle + variance
                
                # Add branch with random length variation
                length_variation = random.uniform(0.4, 0.8)
                branch_length = self.main_stem.length * length_variation
                self.main_stem.add_child(branch_angle, branch_length)
                
                # Log branch creation
                print(f"Added branch: angle={branch_angle:.2f}, length={branch_length:.1f}")
            
            # Update tracking variables
            self.last_branch_height = current_height
            
    def set_health(self, health: float) -> None:
        """Update health for visual effects"""
        self.health = health
        
    def draw(self, surface: pygame.Surface, pos: Tuple[float, float]) -> None:
        """Draw the stem system with health effects"""
        # Update main stem position
        self.main_stem.start_pos = pos
        self.main_stem._update_end_pos()
        
        def draw_branch_with_health(branch: Branch, thickness: float):
            if branch.growth <= 0:
                return
                
            # Calculate withering effect based on health
            wither_offset = 0
            if self.health < 50:
                # Add increasing random offsets as health decreases
                wither_amount = (50 - self.health) / 50.0  # 0 to 1
                wither_offset = random.uniform(-5, 5) * wither_amount
                
            # Calculate positions with wither effect
            start_pos = (int(branch.start_pos[0]), int(branch.start_pos[1]))
            end_pos = (
                int(branch.end_pos[0] + wither_offset),
                int(branch.end_pos[1] + wither_offset)
            )
            
            # Calculate color based on health
            color = list(self.appearance.color)
            if self.health < 70:
                # Gradually turn brown as health decreases
                brown_factor = (70 - self.health) / 70.0
                color = [
                    int(c * (1 - brown_factor) + (101 if i == 0 else 67 if i == 1 else 33) * brown_factor)
                    for i, c in enumerate(color)
                ]
            
            # Draw the branch
            pygame.draw.line(surface, color, start_pos, end_pos,
                           max(1, int(thickness)))
            
            # Draw child branches
            for child in branch.children:
                draw_branch_with_health(child, thickness * 0.8)
                
        # Start drawing from main stem
        draw_branch_with_health(self.main_stem, self.properties.thickness)
