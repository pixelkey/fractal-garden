import pygame
import random
import os
from typing import List, Dict, Any
from plant_factory import PlantFactory, Plant
from environment import EnvironmentalFactors
import math

class Garden:
    def __init__(self):
        pygame.init()
        
        # Get the screen info
        screen_info = pygame.display.Info()
        self.width = int(screen_info.current_w * 1.5)
        self.height = int(screen_info.current_h * 1.5)
        
        # Calculate scaling factors for plants based on screen size
        # Use the smaller dimension to maintain proportions
        self.scale_factor = min(self.width, self.height) / 1000.0  # Base size of 1000 pixels
        
        # Create the window - use resizable flag to handle large dimensions
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("Fractal Garden")
        
        # Initialize clock
        self.clock = pygame.time.Clock()
        
        # Initialize components
        self.plants: List[Plant] = []
        self.plant_definitions = self._load_plant_definitions()
        
        # Environment state
        self.environment = EnvironmentalFactors(
            water_level=70.0,
            light_level=80.0,
            temperature=22.0,
            humidity=60.0,
            soil_quality=90.0
        )
        
        # Rain system
        self.rain_center = (random.randint(0, self.width), 0)
        self.rain_target = (random.randint(0, self.width), 0)
        self.rain_move_timer = 0
        self.rain_intensity = 0.5
        
        # Background color
        self.bg_color = (10, 20, 30)
        
        # FPS control
        self.target_fps = 60
        
        # Plant addition control
        self.time_since_last_plant = 0
        self.plant_add_interval = 120  # Frames between plant additions
        
    def _load_plant_definitions(self) -> Dict[str, Any]:
        """Load all plant definitions from the definitions directory"""
        definitions = {}
        definitions_dir = os.path.join('plants', 'definitions')
        print(f"Looking for plant definitions in: {os.path.abspath(definitions_dir)}")
        
        if not os.path.exists(definitions_dir):
            print(f"Error: Plant definitions directory not found!")
            return definitions
            
        for filename in os.listdir(definitions_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(definitions_dir, filename)
                print(f"Loading plant definition from: {filepath}")
                definition = PlantFactory.load_definition(filepath)
                if definition:
                    print(f"Successfully loaded plant: {definition.species}")
                    definitions[definition.species] = definition
                else:
                    print(f"Failed to load plant definition from: {filepath}")
                    
        print(f"Total plant definitions loaded: {len(definitions)}")
        return definitions
        
    def add_plant(self) -> None:
        """Add a new plant to the garden"""
        if len(self.plants) >= 10:  # Limit total number of plants
            return
            
        # Place plant at ground level with some horizontal spacing
        min_spacing = 100  # Minimum pixels between plants
        max_attempts = 10  # Maximum attempts to find a free spot
        
        for _ in range(max_attempts):
            x = random.randint(50, self.width - 50)
            y = self.height - 50  # Place slightly above bottom edge
            
            # Check if spot is free (no plants within min_spacing)
            spot_is_free = True
            for plant in self.plants:
                if abs(plant.x - x) < min_spacing:
                    spot_is_free = False
                    break
                    
            if spot_is_free:
                # Randomly choose a plant definition
                if self.plant_definitions:
                    definition = random.choice(list(self.plant_definitions.values()))
                    plant = PlantFactory.create_plant(definition, x, y)
                    self.plants.append(plant)
                    print(f"Added new plant: {plant.definition.species} at ({x}, {y})")
                return
                
    def update_environment(self) -> None:
        """Update environmental conditions"""
        # Update rain position
        self.rain_move_timer += 1
        if self.rain_move_timer > 100:
            self.rain_target = (random.randint(0, self.width), 0)
            self.rain_move_timer = 0
            self.rain_intensity = random.uniform(0.3, 0.8)
            
        # Interpolate rain position
        dx = (self.rain_target[0] - self.rain_center[0]) * 0.02
        self.rain_center = (self.rain_center[0] + dx, 0)
        
        # Update water level based on rain
        self.environment.water_level = max(0, min(100, 
            self.environment.water_level - 0.1 + self.rain_intensity * 0.2))
            
        # Simulate day/night cycle (simplified)
        day_cycle = math.sin(pygame.time.get_ticks() / 20000)  # Slower cycle
        self.environment.light_level = 60 + 20 * day_cycle
        
    def update(self) -> None:
        """Update all garden elements"""
        # Update environmental conditions
        self.update_environment()
        
        # Update plants
        for plant in self.plants[:]:
            # Update plant state
            plant.update(self.environment)
            
            # Remove dead plants
            if plant.is_dead():
                self.plants.remove(plant)
                
        # Add new plants periodically
        self.time_since_last_plant += 1
        if self.time_since_last_plant >= self.plant_add_interval:
            self.add_plant()
            self.time_since_last_plant = 0
            
    def draw_rain(self) -> None:
        """Draw rain effect"""
        if self.rain_intensity > 0:
            rain_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            num_drops = int(100 * self.rain_intensity)
            
            for _ in range(num_drops):
                x = random.gauss(self.rain_center[0], 100)
                y = random.randint(0, self.height)
                size = random.uniform(2, 4)
                pygame.draw.circle(rain_surface, (150, 150, 255, 100),
                                 (int(x), int(y)), int(size))
                                 
            self.screen.blit(rain_surface, (0, 0))
            
    def draw(self) -> None:
        """Draw all garden elements"""
        # Clear screen
        self.screen.fill(self.bg_color)
        
        # Draw plants
        for plant in self.plants:
            plant.draw(self.screen)
            
        # Draw rain
        self.draw_rain()
        
        # Update display
        pygame.display.flip()
        
    def run(self) -> None:
        """Main game loop"""
        running = True
        while running:
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                        
            # Update and draw
            self.update()
            self.draw()
            
            # Control frame rate
            self.clock.tick(self.target_fps)
            
        pygame.quit()
