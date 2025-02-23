from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import pygame
import random
import math
import json
import os

from stem import StemProperties, StemAppearance, StemSystem, Branch, StemSystemDefinition
from leaf import LeafShape, LeafColor, LeafGenerator
from flower import PetalShape, FlowerStructure, FlowerColors, FlowerGenerator
from environment import GrowthRequirements, EnvironmentSystem, EnvironmentalFactors, GrowthCharacteristics

@dataclass
class PlantDefinition:
    """Complete definition of a plant species"""
    species: str
    common_name: str
    growth_characteristics: GrowthCharacteristics
    environmental_requirements: GrowthRequirements
    stem_system: StemSystemDefinition
    leaf_generator: LeafGenerator
    flower_generator: FlowerGenerator

class Plant:
    """A single instance of a plant"""
    
    def __init__(self, definition: PlantDefinition, x: float, y: float):
        self.definition = definition
        self.x = x
        self.y = y
        self.growth_stage = 0.0
        self.health = 100.0
        self.age = 0
        self.max_age = definition.growth_characteristics.lifespan
        self.is_withering = False
        self.wither_time = 0
        self.max_wither_time = 300  # Takes 300 frames to fully wither
        
        # Initialize components
        self.stem_system = StemSystem(definition.stem_system.properties,
                                    definition.stem_system.appearance)
        self.leaf_generator = definition.leaf_generator
        self.flower_generator = definition.flower_generator
        self.environment_system = EnvironmentSystem(definition.environmental_requirements,
                                                  definition.growth_characteristics)
        
        # Store flower sizes for each branch to prevent flickering
        self.flower_sizes = {}  # Dictionary to store flower sizes by branch ID
        
    def update(self, environment: EnvironmentalFactors) -> None:
        """Update plant state based on environmental conditions"""
        if self.is_withering:
            # When withering, just count down until removal
            self.wither_time += 1
            self.health = max(0, self.health - 0.5)  # Continue decreasing health
            return
            
        # Calculate stress factors
        water_stress = self._calculate_stress(environment.water_level,
                                           self.definition.environmental_requirements.optimal_water)
        light_stress = self._calculate_stress(environment.light_level,
                                            self.definition.environmental_requirements.optimal_light)
                                            
        # Most limiting factor determines growth
        stress = max(water_stress, light_stress)
        
        # Update growth stage
        if self.health > 50:  # Only grow if relatively healthy
            growth_amount = 0.005 * (1 - stress) * self.definition.growth_characteristics.growth_rate
            self.growth_stage = min(1.0, self.growth_stage + growth_amount)
            
            # Grow stem system
            if self.growth_stage > 0:
                self.stem_system.grow(growth_amount * 2)  # Double growth rate for more visible growth
                
            # Log growth progress
            if self.age % 100 == 0:  # Log every 100 frames
                print(f"Plant {self.definition.species} at ({self.x}, {self.y}):")
                print(f"  Age: {self.age}, Health: {self.health:.1f}%, Growth: {self.growth_stage:.2f}")
                print(f"  Branches: {len(self.stem_system.main_stem.children)}")
                print(f"  Stress - Water: {water_stress:.2f}, Light: {light_stress:.2f}")
                print(f"  Growth Amount: {growth_amount:.4f}")
                
        # Update health based on stress
        self.health = max(0, self.health - stress * 0.1)
        
        # Age the plant
        self.age += 1
        
        # Check if plant should start withering
        if self.health < 10 or self.age > self.max_age:
            if not self.is_withering:
                print(f"Plant {self.definition.species} is starting to wither! Health: {self.health:.1f}%")
                self.is_withering = True
                
    def _calculate_stress(self, value: float, optimal_range: Tuple[float, float]) -> float:
        """Calculate stress level (0.0 to 1.0) based on how far a value is from optimal range"""
        if optimal_range[0] <= value <= optimal_range[1]:
            return 0.0
            
        # Calculate distance from optimal range
        if value < optimal_range[0]:
            deviation = optimal_range[0] - value
            max_deviation = optimal_range[0]  # Distance to zero
        else:
            deviation = value - optimal_range[1]
            max_deviation = 100 - optimal_range[1]  # Distance to maximum
            
        # Convert to stress value (0-1)
        return min(1.0, deviation / max_deviation)
        
    def draw(self, screen: pygame.Surface) -> None:
        """Draw the complete plant"""
        if self.growth_stage <= 0:
            return
            
        # Update stem system health
        self.stem_system.set_health(self.health)
            
        # Draw stem system
        self.stem_system.draw(screen, (self.x, self.y))
        
        # Only draw leaves and flowers if plant is somewhat healthy
        if self.health > 30:
            # Draw leaves on branches
            self._draw_leaves_on_branch(screen, self.stem_system.main_stem)
            
            # Draw flowers when mature
            if self.growth_stage > 0.7:  # Only draw flowers when plant is mature
                print(f"Drawing flowers for plant at ({self.x}, {self.y})")
                print(f"  Growth stage: {self.growth_stage:.2f}")
                print(f"  Health: {self.health:.1f}")
                print(f"  Main stem growth: {self.stem_system.main_stem.growth:.2f}")
                print(f"  Num branches: {len(self.stem_system.main_stem.children)}")
                self._draw_flowers(screen)
                
    def _draw_leaves_on_branch(self, screen: pygame.Surface, branch: Branch) -> None:
        """Draw leaves along a branch"""
        if branch.growth < 0.3:  # Only draw leaves on mature enough branches
            return
            
        # Get branch vector for leaf orientation
        branch_vector = (
            branch.end_pos[0] - branch.start_pos[0],
            branch.end_pos[1] - branch.start_pos[1]
        )
        
        # Calculate leaf angle based on branch direction
        leaf_angle = math.atan2(branch_vector[1], branch_vector[0])
        
        # Draw leaves along the branch
        num_leaves = int(branch.length / 20)  # One leaf every 20 pixels
        for i in range(num_leaves):
            if random.random() < 0.8:  # 80% chance to draw each leaf
                t = i / num_leaves
                # Calculate leaf position relative to branch
                leaf_pos = (
                    branch.start_pos[0] + branch_vector[0] * t + self.x,
                    branch.start_pos[1] + branch_vector[1] * t + self.y
                )
                
                # Alternate leaves on each side
                side_angle = math.pi/2 if i % 2 == 0 else -math.pi/2
                final_angle = leaf_angle + side_angle
                
                # Draw the leaf
                self.leaf_generator.draw(screen, leaf_pos, 20.0, final_angle)
                
        # Recursively draw leaves on sub-branches
        for child in branch.children:
            self._draw_leaves_on_branch(screen, child)
            
    def _draw_flowers(self, screen: pygame.Surface) -> None:
        """Draw flowers on branch tips"""
        def draw_flower_on_branch(branch: Branch):
            # Draw flowers on branch tips that are grown enough
            if branch.growth > 0.5:  # Lower threshold for flowers
                # Get or generate flower size for this branch
                branch_id = id(branch)
                if branch_id not in self.flower_sizes:
                    # Base flower size is proportional to branch thickness
                    base_size = self.stem_system.properties.thickness * 7.5  # Scale based on stem thickness
                    self.flower_sizes[branch_id] = base_size * (0.8 + 0.4 * random.random())
                
                # Draw flower at branch tip
                flower_pos = branch.end_pos
                flower_size = self.flower_sizes[branch_id] * self.growth_stage
                self.flower_generator.draw(screen, flower_pos, flower_size, branch.angle)
                
            # Recursively draw on child branches
            for child in branch.children:
                draw_flower_on_branch(child)
                
        # Draw flowers starting from main stem
        draw_flower_on_branch(self.stem_system.main_stem)
        
    def reset_flower_sizes(self) -> None:
        """Reset flower sizes when plant is pruned or branches change"""
        self.flower_sizes.clear()
        
    def is_dead(self) -> bool:
        """Check if plant should be removed"""
        return self.is_withering and self.wither_time >= self.max_wither_time

class PlantFactory:
    """Creates plant instances from JSON definitions"""
    
    @staticmethod
    def load_definition(json_path: str) -> Optional[PlantDefinition]:
        """Load a plant definition from a JSON file"""
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
                print("Successfully loaded JSON data")
                
            # Create growth characteristics
            growth_chars = GrowthCharacteristics(
                max_height=data['growth_characteristics']['max_height'],
                growth_rate=data['growth_characteristics']['growth_rate'],
                lifespan=data['growth_characteristics']['lifespan']
            )
            
            # Create environmental requirements
            env_reqs = GrowthRequirements(
                optimal_water=tuple(data['environmental_requirements']['optimal_water']),
                optimal_light=tuple(data['environmental_requirements']['optimal_light']),
                optimal_temp=tuple(data['environmental_requirements']['optimal_temp']),
                optimal_humidity=tuple(data['environmental_requirements']['optimal_humidity']),
                drought_tolerance=data['environmental_requirements']['drought_tolerance'],
                heat_tolerance=data['environmental_requirements']['heat_tolerance']
            )
            
            # Create stem system properties
            stem_props = StemProperties(
                thickness=data['stem']['properties']['thickness'],
                flexibility=data['stem']['properties']['flexibility'],
                branching_angle=data['stem']['properties']['branching_angle'],
                branching_variance=data['stem']['properties']['branching_variance'],
                max_branches=data['stem']['properties']['max_branches'],
                growth_rate=data['stem']['properties']['growth_rate'],
                branch_spacing=data['stem']['properties']['branch_spacing']
            )
            
            # Create stem appearance
            stem_appear = StemAppearance(
                color=tuple(data['stem']['appearance']['color']),
                texture=data['stem']['appearance']['texture'],
                node_visibility=data['stem']['appearance']['node_visibility'],
                thorn_frequency=data['stem']['appearance']['thorn_frequency']
            )
            
            # Create flower components
            petal_shape = PetalShape(
                type=data['flower']['petal_shape']['type'],
                length_ratio=data['flower']['petal_shape']['length_ratio'],
                tip_shape=data['flower']['petal_shape']['tip_shape'],
                edge_type=data['flower']['petal_shape']['edge_type'],
                curve=data['flower']['petal_shape']['curve']
            )
            
            flower_structure = FlowerStructure(
                arrangement=data['flower']['structure']['arrangement'],
                num_petals=data['flower']['structure']['num_petals'],
                petal_layers=data['flower']['structure']['petal_layers'],
                symmetry=data['flower']['structure']['symmetry'],
                center_type=data['flower']['structure']['center_type'],
                center_size_ratio=data['flower']['structure']['center_size_ratio']
            )
            
            flower_colors = FlowerColors(
                petal_colors=[tuple(c) for c in data['flower']['colors']['petal_colors']],
                center_color=tuple(data['flower']['colors']['center_color']),
                color_variation=data['flower']['colors']['color_variation'],
                has_patterns=data['flower']['colors']['has_patterns']
            )
            
            # Create leaf components
            leaf_shape = LeafShape(
                type=data['leaves']['shape']['type'],
                length_ratio=data['leaves']['shape']['length_ratio'],
                edge_type=data['leaves']['shape']['edge_type'],
                vein_pattern=data['leaves']['shape']['vein_pattern'],
                base_shape=data['leaves']['shape']['base_shape'],
                tip_shape=data['leaves']['shape']['tip_shape']
            )
            
            leaf_color = LeafColor(
                base_color=tuple(data['leaves']['color']['base_color']),
                variation=data['leaves']['color']['variation'],
                vein_color=tuple(data['leaves']['color']['vein_color']),
                seasonal_colors=[tuple(c) for c in data['leaves']['color']['seasonal_colors']]
            )
            
            # Create leaf generator
            leaf_generator = LeafGenerator(leaf_shape, leaf_color)
            
            # Create flower generator
            flower_generator = FlowerGenerator(
                petal_shape,
                flower_structure,
                flower_colors
            )
            
            # Create stem system definition
            stem_system = StemSystemDefinition(stem_props, stem_appear)
            
            # Create complete plant definition
            definition = PlantDefinition(
                species=data['species'],
                common_name=data['common_name'],
                growth_characteristics=growth_chars,
                environmental_requirements=env_reqs,
                stem_system=stem_system,
                leaf_generator=leaf_generator,
                flower_generator=flower_generator
            )
            
            print(f"Successfully loaded plant: {definition.species}")
            return definition
            
        except Exception as e:
            print(f"Error loading plant definition: {e}")
            return None
            
    @staticmethod
    def create_plant(definition: PlantDefinition, x: float, y: float) -> 'Plant':
        """Create a new plant instance from a definition"""
        plant = Plant(definition, x, y)
        # Create stem system from definition
        plant.stem_system = StemSystem(definition.stem_system.properties,
                                     definition.stem_system.appearance)
        return plant
