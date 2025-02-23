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
        
        # Time system
        self.day_length = 1200  # frames per day
        self.current_time = 0  # 0 to day_length
        self.time_speed = 1.0  # Time multiplier
        
        # Weather system
        self.weather_states = ['clear', 'cloudy', 'rain', 'storm']
        self.current_weather = 'clear'
        self.weather_duration = 0
        self.min_weather_duration = 300  # Minimum frames for weather to last
        self.weather_transition = 0.0  # For smooth transitions
        
        # Rain system optimization
        self.rain_center = (random.randint(0, self.width), 0)
        self.rain_target = (random.randint(0, self.width), 0)
        self.rain_move_timer = 0
        self.rain_intensity = 0.0
        self.rain_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rain_drops = []
        self.rain_update_counter = 0
        
        # Cloud system
        self.clouds = []
        self.max_clouds = 10
        self.cloud_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Background colors for different times of day
        self.sky_colors = {
            'dawn': (255, 200, 150),
            'day': (135, 206, 235),
            'dusk': (255, 150, 100),
            'night': (10, 20, 30)
        }
        self.current_sky_color = self.sky_colors['day']
        self.bg_color = self.current_sky_color  # Initialize bg_color
        
        # Performance optimizations
        self.update_interval = 2
        self.frame_count = 0
        
        # Plant addition control
        self.time_since_last_plant = 0
        self.plant_add_interval = 120
        
        # Font for stats
        try:
            self.stats_font = pygame.font.SysFont('Arial', 20)
        except:
            self.stats_font = pygame.font.Font(None, 20)
        
        # Cache for stats surfaces
        self._stats_surfaces = {}
        self._last_stats = {}
        
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
        """Update environmental conditions based on time and weather"""
        # Update time
        self.current_time = (self.current_time + self.time_speed) % self.day_length
        day_progress = self.current_time / self.day_length
        
        # Update weather
        self.weather_duration -= 1
        if self.weather_duration <= 0:
            self._change_weather()
        
        # Calculate base light level based on time of day
        if day_progress < 0.2:  # Dawn
            phase_progress = day_progress / 0.2
            self.environment.light_level = 20 + 60 * phase_progress
            self._blend_sky_color('dawn', phase_progress)
        elif day_progress < 0.8:  # Day
            self.environment.light_level = 80
            self._blend_sky_color('day', 1.0)
        elif day_progress < 1.0:  # Dusk to night
            phase_progress = (day_progress - 0.8) / 0.2
            self.environment.light_level = 80 - 60 * phase_progress
            self._blend_sky_color('dusk' if phase_progress < 0.5 else 'night', phase_progress)
        
        # Apply weather effects
        if self.current_weather == 'cloudy':
            self.environment.light_level *= 0.7
            self.environment.humidity += 0.1
        elif self.current_weather == 'rain':
            self.environment.light_level *= 0.5
            self.environment.humidity += 0.3
            self.environment.water_level = min(100, self.environment.water_level + self.rain_intensity * 0.2)
        elif self.current_weather == 'storm':
            self.environment.light_level *= 0.3
            self.environment.humidity += 0.5
            self.environment.water_level = min(100, self.environment.water_level + self.rain_intensity * 0.4)
        else:  # clear
            self.environment.water_level = max(0, self.environment.water_level - 0.1)
            
        # Update rain position if raining
        if self.current_weather in ['rain', 'storm']:
            self.rain_move_timer += 1
            if self.rain_move_timer > 100:
                self.rain_target = (random.randint(0, self.width), 0)
                self.rain_move_timer = 0
                
            # Interpolate rain position
            dx = (self.rain_target[0] - self.rain_center[0]) * 0.02
            self.rain_center = (self.rain_center[0] + dx, 0)
        
    def _change_weather(self) -> None:
        """Change the weather state"""
        # Clear weather is more common
        weights = [0.4, 0.3, 0.2, 0.1]  # Probabilities for clear, cloudy, rain, storm
        self.current_weather = random.choices(self.weather_states, weights=weights)[0]
        
        # Set weather duration
        self.weather_duration = random.randint(self.min_weather_duration, self.min_weather_duration * 2)
        
        # Set rain intensity based on weather
        if self.current_weather == 'rain':
            self.rain_intensity = random.uniform(0.3, 0.6)
        elif self.current_weather == 'storm':
            self.rain_intensity = random.uniform(0.7, 1.0)
        else:
            self.rain_intensity = 0.0
            
    def _blend_sky_color(self, target_time: str, progress: float) -> None:
        """Blend sky colors for smooth transitions"""
        target_color = self.sky_colors[target_time]
        current_color = self.current_sky_color
        
        # Smoothly interpolate colors
        self.current_sky_color = tuple(
            int(current + (target - current) * progress)
            for current, target in zip(current_color, target_color)
        )
        
        # Update background color
        self.bg_color = self.current_sky_color
        
    def update(self) -> None:
        """Update all garden elements"""
        self.frame_count += 1
        
        # Only update every N frames
        if self.frame_count % self.update_interval != 0:
            return
            
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
        """Draw rain effect with optimizations"""
        if self.rain_intensity > 0:
            # Only update rain positions every 5 frames
            if self.frame_count % 5 == 0:
                self.rain_surface.fill((0, 0, 0, 0))
                
                # Update or initialize rain drops
                if not self.rain_drops or self.rain_update_counter >= 20:
                    self.rain_drops = []
                    num_drops = int(100 * self.rain_intensity)
                    for _ in range(num_drops):
                        x = random.gauss(self.rain_center[0], 100)
                        y = random.randint(0, self.height)
                        size = random.uniform(2, 4)
                        self.rain_drops.append((x, y, size))
                    self.rain_update_counter = 0
                else:
                    # Move existing drops down
                    new_drops = []
                    for x, y, size in self.rain_drops:
                        y = (y + 5) % self.height  # Wrap around when reaching bottom
                        new_drops.append((x, y, size))
                    self.rain_drops = new_drops
                    self.rain_update_counter += 1
                
                # Draw all drops
                for x, y, size in self.rain_drops:
                    pygame.draw.circle(self.rain_surface, (150, 150, 255, 100),
                                     (int(x), int(y)), int(size))
            
            # Blit the cached rain surface
            self.screen.blit(self.rain_surface, (0, 0))
            
    def draw(self) -> None:
        """Draw all garden elements"""
        # Clear screen with current sky color
        self.screen.fill(self.bg_color)
        
        # Draw clouds if weather is cloudy or rainy
        if self.current_weather in ['cloudy', 'rain', 'storm']:
            self._draw_clouds()
        
        # Draw plants
        for plant in self.plants:
            plant.draw(self.screen)
        
        # Draw rain if weather is rainy
        if self.current_weather in ['rain', 'storm']:
            self.draw_rain()
            
        # Draw weather stats
        self._draw_weather_stats()
        
        # Update display
        pygame.display.flip()
        
    def _draw_weather_stats(self) -> None:
        """Draw weather statistics in the top-left corner"""
        # Get time of day
        day_progress = self.current_time / self.day_length
        if day_progress < 0.2:
            time_of_day = "Dawn"
        elif day_progress < 0.8:
            time_of_day = "Day"
        elif day_progress < 0.9:
            time_of_day = "Dusk"
        else:
            time_of_day = "Night"
            
        # Format weather info
        weather_info = {
            'Time': time_of_day,
            'Weather': self.current_weather.title(),
            'Light': f"{self.environment.light_level:.1f}%",
            'Water': f"{self.environment.water_level:.1f}%",
            'Humidity': f"{self.environment.humidity:.1f}%",
            'Temperature': f"{self.environment.temperature:.1f}°C"
        }
        
        # Render stats with caching
        y_offset = 10
        x_offset = 10
        line_height = 25
        
        for label, value in weather_info.items():
            # Check if we need to update the cached surface
            cache_key = f"{label}:{value}"
            if cache_key not in self._stats_surfaces or self._last_stats.get(label) != value:
                # Create text with shadow for better visibility
                text = f"{label}: {value}"
                shadow_surface = self.stats_font.render(text, True, (0, 0, 0))
                text_surface = self.stats_font.render(text, True, (255, 255, 255))
                
                # Store both surfaces in cache
                self._stats_surfaces[cache_key] = (shadow_surface, text_surface)
                self._last_stats[label] = value
            
            # Draw from cache
            shadow_surface, text_surface = self._stats_surfaces[cache_key]
            
            # Draw shadow then text
            self.screen.blit(shadow_surface, (x_offset + 1, y_offset + 1))
            self.screen.blit(text_surface, (x_offset, y_offset))
            
            y_offset += line_height
            
    def _draw_clouds(self) -> None:
        """Draw cloud cover based on weather"""
        # Only update cloud positions periodically
        if self.frame_count % 10 == 0:
            self.cloud_surface.fill((0, 0, 0, 0))
            
            # Create new clouds if needed
            while len(self.clouds) < self.max_clouds:
                cloud = {
                    'x': random.randint(0, self.width),
                    'y': random.randint(0, self.height // 3),
                    'size': random.randint(50, 150),
                    'speed': random.uniform(0.2, 0.5)
                }
                self.clouds.append(cloud)
            
            # Update and draw clouds
            new_clouds = []
            for cloud in self.clouds:
                # Move cloud
                cloud['x'] += cloud['speed']
                if cloud['x'] - cloud['size'] > self.width:
                    cloud['x'] = -cloud['size']
                
                # Draw cloud as a group of circles
                alpha = 100 if self.current_weather == 'cloudy' else 150
                for i in range(5):  # Draw multiple overlapping circles for each cloud
                    offset_x = int(cloud['x'] + i * cloud['size'] * 0.2)
                    offset_y = int(cloud['y'] + math.sin(i) * 10)
                    pygame.draw.circle(self.cloud_surface, (200, 200, 200, alpha),
                                    (offset_x, offset_y), int(cloud['size'] * 0.5))
                
                new_clouds.append(cloud)
            
            self.clouds = new_clouds
            
        # Draw the cloud surface
        self.screen.blit(self.cloud_surface, (0, 0))
        
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
            self.clock.tick(60)
            
        pygame.quit()
