from dataclasses import dataclass, field
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
class FloweringCharacteristics:
    min_maturity: float = 0.7
    chance: float = 0.8
    min_delay: int = 100
    max_delay: int = 500
    bloom_duration: int = 800

@dataclass
class GrowthCharacteristics:
    max_height: float
    growth_rate: float
    lifespan: int
    flowering: FloweringCharacteristics = field(default_factory=FloweringCharacteristics)

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
    type: str = 'flower'  # Added plant type field

class Plant:
    """A single instance of a plant"""
    
    def __init__(self, definition: PlantDefinition, x: float, y: float, scale_factor: float = 1.0):
        """Initialize a new plant"""
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
        
        # Cache for leaf placement decisions
        self._leaf_placement_cache = {}
        
        # Apply type-based scaling
        type_scale_factors = {
            'tree': 2.5,
            'grass': 0.7,
            'ground_cover': 0.4,
            'herb': 0.6,
            'shrub': 1.0,
            'flower': 1.0
        }
        plant_type = definition.type
        type_scale = type_scale_factors.get(plant_type, 1.0)
        
        # Apply combined scaling
        self.scale_factor = scale_factor * type_scale
        
        # Initialize components
        self.stem_system = StemSystem(definition.stem_system.properties,
                                    definition.stem_system.appearance)
        self.leaf_generator = definition.leaf_generator
        self.flower_generator = definition.flower_generator
        self.environment_system = EnvironmentSystem(definition.environmental_requirements,
                                                  definition.growth_characteristics)
        
        # Store flower data for each branch
        self.flower_data = {}  # Dictionary to store flower info by branch ID
        
        # Cache for text rendering
        self._name_surfaces = None
        self._last_health = None
        self._last_growth = None
        
    def update(self, environment: EnvironmentalFactors) -> None:
        """Update plant state based on environmental conditions"""
        # Only update every other frame to reduce CPU load
        self.age += 1
        if self.age % 2 != 0:
            return
            
        if self.is_withering:
            # When withering, shrink the plant and decrease health
            self.wither_time += 1
            wither_progress = self.wither_time / self.max_wither_time
            self.health = max(0, self.health - 0.5)  # Continue decreasing health
            
            # Shrink the plant as it withers
            if hasattr(self, 'stem_system'):
                self.stem_system.properties.thickness *= (1 - wither_progress * 0.01)
            return
            
        # Start withering if the plant is too old or unhealthy
        if self.age >= self.max_age or self.health <= 20:
            self.is_withering = True
            return
            
        # Calculate stress factors
        water_stress = self._calculate_stress(environment.water_level,
                                       self.definition.environmental_requirements.optimal_water)
        light_stress = self._calculate_stress(environment.light_level,
                                        self.definition.environmental_requirements.optimal_light)
                                        
        # Most limiting factor determines growth
        stress = max(water_stress, light_stress)
        
        # Update health based on stress
        health_change = -0.2 * stress if stress > 0.5 else 0.1 * (1 - stress)
        self.health = max(0, min(100, self.health + health_change))
        
        # Update growth stage if relatively healthy
        if self.health > 50:
            growth_amount = 0.005 * (1 - stress) * self.definition.growth_characteristics.growth_rate
            self.growth_stage = min(1.0, self.growth_stage + growth_amount)
            
            # Only update stem if there's meaningful growth
            if self.growth_stage > 0:
                self.stem_system.grow(growth_amount * 2)  # Double growth rate for more visible growth
                
        # Update health based on stress, but less frequently
        if self.age % 5 == 0:
            self.health = max(0, self.health - stress * 0.1)
            
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
        
        # Calculate alpha based on withering state
        alpha = 255
        if self.is_withering:
            alpha = int(255 * (1 - (self.wither_time / self.max_wither_time)))
        
        # Only draw leaves and flowers if plant is somewhat healthy
        if self.health > 30:
            # Draw leaves on branches with withering effect
            self._draw_leaves_on_branch(screen, self.stem_system.main_stem, alpha)
            
            # Draw flowers when mature
            if self.growth_stage > 0.7:  # Only draw flowers when plant is mature
                self._draw_flowers(screen, alpha)
        
        # Draw plant name with caching
        if self.health > 10:  # Only show name if plant is somewhat alive
            # Check if we need to update the cached surfaces
            if (self._name_surfaces is None or 
                self._last_health != self.health or 
                self._last_growth != self.growth_stage):
                
                # Create font (use a system font since we don't want to depend on specific fonts)
                font_size = int(24 * (0.8 + 0.2 * self.growth_stage))
                try:
                    font = pygame.font.SysFont('Arial', font_size)
                except:
                    font = pygame.font.Font(None, font_size)
                
                # Create name text with both common and scientific names
                name_text = f"{self.definition.common_name}"
                scientific_text = f"({self.definition.species})"
                
                # Render text with a shadow for better visibility
                text_color = (0, 0, 0, alpha)
                shadow_color = (255, 255, 255, alpha)
                
                # Render main name
                name_surface = font.render(name_text, True, text_color)
                name_shadow = font.render(name_text, True, shadow_color)
                
                # Render scientific name in italics if possible
                try:
                    italic_font = pygame.font.SysFont('Arial', int(font_size * 0.8), italic=True)
                except:
                    italic_font = font
                scientific_surface = italic_font.render(scientific_text, True, text_color)
                scientific_shadow = italic_font.render(scientific_text, True, shadow_color)
                
                # Cache the surfaces and current state
                self._name_surfaces = (name_surface, name_shadow, scientific_surface, scientific_shadow)
                self._last_health = self.health
                self._last_growth = self.growth_stage
            
            # Use cached surfaces
            name_surface, name_shadow, scientific_surface, scientific_shadow = self._name_surfaces
            
            # Calculate positions - moved closer to stem base
            # Find the lowest point of the plant's stem system
            lowest_y = self.y
            for branch in self.stem_system.get_all_branches():
                lowest_y = max(lowest_y, branch.end_pos[1])
            
            # Position text above the lowest point
            name_x = self.x - name_surface.get_width() // 2
            name_y = min(lowest_y + 10, pygame.display.get_surface().get_height() - name_surface.get_height() - scientific_surface.get_height() - 20)
            scientific_x = self.x - scientific_surface.get_width() // 2
            scientific_y = name_y + name_surface.get_height() + 2
            
            # Draw shadows then text
            screen.blit(name_shadow, (name_x + 1, name_y + 1))
            screen.blit(name_surface, (name_x, name_y))
            screen.blit(scientific_shadow, (scientific_x + 1, scientific_y + 1))
            screen.blit(scientific_surface, (scientific_x, scientific_y))
            
    def _should_place_leaf(self, branch_id: int, leaf_index: int) -> bool:
        """Determine if a leaf should be placed at this position based on plant type"""
        cache_key = (branch_id, leaf_index)
        if cache_key not in self._leaf_placement_cache:
            # Use branch_id and leaf_index to seed random
            random.seed(hash(cache_key))
            
            # Adjust leaf placement probability based on plant type
            base_probability = {
                'tree': 0.6,  # Trees have fewer leaves per branch
                'grass': 0.9,  # Grasses have dense leaf placement
                'ground_cover': 0.85,
                'herb': 0.8,
                'shrub': 0.7,
                'flower': 0.75
            }.get(self.definition.type, 0.8)
            
            self._leaf_placement_cache[cache_key] = random.random() < base_probability
            random.seed()  # Reset random seed
        return self._leaf_placement_cache[cache_key]
        
    def _draw_leaves_on_branch(self, screen: pygame.Surface, branch: Branch, alpha: int = 255) -> None:
        """Draw leaves along a branch"""
        # Check if this is the main stem
        is_main_stem = branch.start_pos == self.stem_system.main_stem.start_pos
        
        # Different maturity thresholds based on plant type and whether it's main stem
        maturity_thresholds = {
            'tree': 0.7 if not is_main_stem else 0.9,  # Trees rarely have leaves on main trunk
            'grass': 0.3,  # Grasses can have leaves early
            'ground_cover': 0.3,
            'herb': 0.4,
            'shrub': 0.5,
            'flower': 0.4
        }
        maturity_threshold = maturity_thresholds.get(self.definition.type, 0.4)
        
        if branch.growth < maturity_threshold:
            return
            
        # Adjust leaf density based on plant type
        leaf_spacing = {
            'tree': 25,  # Fewer leaves per branch for trees
            'grass': 8,   # Dense leaf placement for grasses
            'ground_cover': 10,
            'herb': 12,
            'shrub': 18,
            'flower': 15
        }.get(self.definition.type, 15)
        
        # Don't place leaves on main stem for certain plant types
        if is_main_stem and self.definition.type in ['tree', 'shrub']:
            leaf_spacing *= 2  # Reduce leaf density on main stem
            if branch.growth < 0.9:  # Only allow leaves on very mature main stems
                return
        
        # Get branch vector for leaf orientation
        branch_vector = (
            branch.end_pos[0] - branch.start_pos[0],
            branch.end_pos[1] - branch.start_pos[1]
        )
        
        # Calculate base leaf angle perpendicular to branch
        branch_angle = math.atan2(branch_vector[1], branch_vector[0])
        base_leaf_angle = branch_angle + math.pi/2  # Make leaves perpendicular to branch
        
        # Draw leaves along the branch
        num_leaves = int(branch.length / leaf_spacing)  # More leaves per branch
        for i in range(num_leaves):
            if self._should_place_leaf(id(branch), i):
                # Add some natural variation to position along branch
                random.seed(hash((id(branch), i, "pos")))
                t = (i + 0.3 * (random.random() - 0.5)) / num_leaves  # Vary position by ±15%
                t = max(0, min(1, t))  # Clamp to valid range
                random.seed()
                
                # Calculate leaf position with some natural offset from branch
                random.seed(hash((id(branch), i, "offset")))
                offset_dist = 2.0 * (random.random() - 0.5)  # ±1 pixel perpendicular offset
                random.seed()
                
                perp_vector = (-branch_vector[1], branch_vector[0])  # Perpendicular to branch
                perp_length = math.sqrt(perp_vector[0]**2 + perp_vector[1]**2)
                if perp_length > 0:
                    norm_perp = (perp_vector[0]/perp_length, perp_vector[1]/perp_length)
                    leaf_pos = (
                        branch.start_pos[0] + branch_vector[0] * t + norm_perp[0] * offset_dist,
                        branch.start_pos[1] + branch_vector[1] * t + norm_perp[1] * offset_dist
                    )
                else:
                    leaf_pos = (
                        branch.start_pos[0] + branch_vector[0] * t,
                        branch.start_pos[1] + branch_vector[1] * t
                    )
                
                # Add natural variation to the leaf angle
                # Use leaf position to seed the random variation for consistency
                random.seed(hash((int(leaf_pos[0]), int(leaf_pos[1]))))
                angle_variation = math.pi/4 * (random.random() - 0.5)  # ±45 degrees variation
                random.seed()
                
                # Alternate leaves left and right with varying angles
                side_offset = math.pi/3 if i % 2 == 0 else -math.pi/3  # ±60 degrees from perpendicular
                
                # Final angle combines base perpendicular angle, side alternation, and natural variation
                final_angle = base_leaf_angle + side_offset + angle_variation
                
                # Vary leaf size slightly
                random.seed(hash((id(branch), i, "size")))
                size_variation = 0.3 * (random.random() - 0.5)  # ±15% size variation
                leaf_size = 20.0 * self.scale_factor * (1 + size_variation)
                random.seed()
                
                # Draw the leaf
                self.leaf_generator.draw(screen, leaf_pos, leaf_size, final_angle, alpha=alpha)
                
        # Recursively draw leaves on sub-branches
        for child in branch.children:
            self._draw_leaves_on_branch(screen, child, alpha)
            
    def _should_flower(self, branch: Branch) -> bool:
        """Determine if a branch should have a flower"""
        branch_id = id(branch)
        
        # Only consider branches that are fully grown
        if branch.growth < 0.95:  # Increased from 0.5 to ensure stem is mature
            return False
            
        # Only start flowering when plant is mature enough
        if self.growth_stage < self.definition.growth_characteristics.flowering.min_maturity:
            return False
            
        # If branch hasn't been evaluated for flowering, initialize its data
        if branch_id not in self.flower_data:
            flowering = self.definition.growth_characteristics.flowering
            should_flower = random.random() < flowering.chance
            self.flower_data[branch_id] = {
                'should_flower': should_flower,
                'flower_time': self.age + random.randint(flowering.min_delay, flowering.max_delay),
                'bloom_end': None,  # Will be set when flower is fully bloomed
                'size': self.stem_system.properties.thickness * 7.5 * (0.8 + 0.4 * random.random()),
                'stage': 'bud',  # Stages: 'bud', 'opening', 'bloomed', 'withering'
                'stage_progress': 0.0,  # Progress through current stage (0.0 to 1.0)
                'bud_start': None  # Will be set when bud appears
            }
            
        data = self.flower_data[branch_id]
        
        # If this branch is meant to flower and it's time
        if data['should_flower'] and self.age >= data['flower_time']:
            # Initialize bud if not started
            if data['bud_start'] is None:
                data['bud_start'] = self.age
                data['stage'] = 'bud'
                data['stage_progress'] = 0.0
                
            # Calculate time in current stage
            time_in_stage = self.age - data['bud_start']
            
            # Update flower stages
            if data['stage'] == 'bud':
                # Bud takes 100 frames to develop
                data['stage_progress'] = min(1.0, time_in_stage / 100)
                if data['stage_progress'] >= 1.0:
                    data['stage'] = 'opening'
                    data['stage_progress'] = 0.0
                    data['bud_start'] = self.age
                    
            elif data['stage'] == 'opening':
                # Opening takes 150 frames
                data['stage_progress'] = min(1.0, time_in_stage / 150)
                if data['stage_progress'] >= 1.0:
                    data['stage'] = 'bloomed'
                    data['stage_progress'] = 0.0
                    data['bud_start'] = self.age
                    data['bloom_end'] = self.age + self.definition.growth_characteristics.flowering.bloom_duration
                    
            elif data['stage'] == 'bloomed':
                # Check if it's time to start withering
                if self.age > data['bloom_end']:
                    data['stage'] = 'withering'
                    data['stage_progress'] = 0.0
                    data['bud_start'] = self.age
                    
            elif data['stage'] == 'withering':
                # Withering takes 100 frames
                data['stage_progress'] = min(1.0, time_in_stage / 100)
                if data['stage_progress'] >= 1.0:
                    # 30% chance to start a new flower cycle
                    if random.random() < 0.3:
                        data['flower_time'] = self.age + random.randint(300, 600)
                        data['bud_start'] = None
                    return False
            
            return True
            
        return False
        
    def _draw_flowers(self, screen: pygame.Surface, alpha: int = 255) -> None:
        """Draw flowers on branch tips"""
        def draw_flower_on_branch(branch: Branch):
            # Check if branch should have a flower
            if self._should_flower(branch):
                # Draw flower at branch tip
                flower_pos = branch.end_pos
                data = self.flower_data[id(branch)]
                
                # Calculate flower size based on stage
                if data['stage'] == 'bud':
                    # Buds are small and grow slightly
                    size = data['size'] * 0.3 * (0.8 + 0.2 * data['stage_progress'])
                elif data['stage'] == 'opening':
                    # Flower grows from 30% to full size while opening
                    size = data['size'] * (0.3 + 0.7 * data['stage_progress'])
                elif data['stage'] == 'bloomed':
                    # Full size when bloomed
                    size = data['size']
                else:  # withering
                    # Slightly shrink while withering
                    size = data['size'] * (1.0 - 0.2 * data['stage_progress'])
                    
                size *= self.growth_stage  # Apply overall plant growth
                
                # Draw with stage-specific modifications
                if data['stage'] == 'bud':
                    # Draw a simple green circle for bud
                    bud_alpha = min(alpha, 255)
                    bud_color = (34, 139, 34, bud_alpha)
                    pygame.draw.circle(screen, bud_color,
                                    (int(flower_pos[0]), int(flower_pos[1])),
                                    int(size * 0.5))
                else:
                    # Draw flower with stage-specific alpha
                    flower_alpha = min(alpha, 255)
                    if data['stage'] == 'opening':
                        flower_alpha = min(alpha, int(128 + 127 * data['stage_progress']))
                    elif data['stage'] == 'withering':
                        flower_alpha = min(alpha, int(255 * (1.0 - data['stage_progress'])))
                    
                    self.flower_generator.draw(screen, flower_pos, size, branch.angle,
                                            alpha=flower_alpha)
                
            # Recursively draw on child branches
            for child in branch.children:
                draw_flower_on_branch(child)
                
        # Draw flowers starting from main stem
        draw_flower_on_branch(self.stem_system.main_stem)
        
    def reset_flower_data(self) -> None:
        """Reset flower data when plant is pruned or branches change"""
        self.flower_data.clear()
        
    def is_dead(self) -> bool:
        """Check if the plant is dead and should be removed"""
        # Plant is dead if health is 0 or it has completed withering
        return self.health <= 0 or (self.is_withering and self.wither_time >= self.max_wither_time)

class PlantFactory:
    """Creates plant instances from JSON definitions"""
    
    @staticmethod
    def load_definition(json_path: str) -> Optional[PlantDefinition]:
        """Load a plant definition from a JSON file"""
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
                
            # Create growth characteristics
            growth_chars = GrowthCharacteristics(
                max_height=data['growth_characteristics']['max_height'],
                growth_rate=data['growth_characteristics']['growth_rate'],
                lifespan=data['growth_characteristics']['lifespan'],
                flowering=FloweringCharacteristics(
                    min_maturity=data['growth_characteristics']['flowering']['min_maturity'],
                    chance=data['growth_characteristics']['flowering']['chance'],
                    min_delay=data['growth_characteristics']['flowering']['min_delay'],
                    max_delay=data['growth_characteristics']['flowering']['max_delay'],
                    bloom_duration=data['growth_characteristics']['flowering']['bloom_duration']
                )
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
            
            # Create stem system definition
            stem_system = StemSystemDefinition(stem_props, stem_appear)
            
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
            
            # Create flower generator
            flower_generator = FlowerGenerator(petal_shape, flower_structure, flower_colors)
            
            # Create final plant definition
            plant_def = PlantDefinition(
                species=data['species'],
                common_name=data['common_name'],
                growth_characteristics=growth_chars,
                environmental_requirements=env_reqs,
                stem_system=stem_system,
                leaf_generator=leaf_generator,
                flower_generator=flower_generator,
                type=data.get('type', 'flower')  # Default to 'flower' if not specified
            )
            
            return plant_def
            
        except Exception as e:
            print(f"Error loading plant definition from {json_path}: {str(e)}")
            return None
            
    @staticmethod
    def create_plant(definition: PlantDefinition, x: float, y: float, scale_factor: float = 1.0) -> 'Plant':
        """Create a new plant instance from a definition"""
        plant = Plant(definition, x, y, scale_factor)
        # Create stem system from definition
        plant.stem_system = StemSystem(definition.stem_system.properties,
                                     definition.stem_system.appearance)
        # Set up leaf generator
        plant.leaf_generator = definition.leaf_generator
        # Set up flower generator if defined
        plant.flower_generator = definition.flower_generator
        return plant
