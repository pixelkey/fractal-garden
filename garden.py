import pygame
import random
import os
from typing import List, Dict, Any
from plant_factory import PlantFactory, Plant
from environment import EnvironmentalFactors
from celestial import Sun, Moon, Star
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
        self.rain_drops = []
        self.rain_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rain_update_counter = 0
        self.drops_per_cloud = 15  # Number of drops to generate per cloud
        
        # Cloud system
        self.clouds = []
        self.max_clouds = 10
        self.cloud_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.wind_speed = 0.0
        self.target_wind_speed = 0.0
        self.wind_change_timer = 0
        
        # Celestial objects
        self.sun = Sun(self.width / 2, self.height / 2)
        self.moon = Moon(self.width / 2, self.height / 2)
        self.stars = [Star(random.randint(0, self.width), 
                         random.randint(0, int(self.height * 0.6)))
                     for _ in range(50)]
        
        # Background colors for different times of day
        self.sky_colors = {
            'night': (10, 20, 40),
            'pre_dawn': (40, 40, 60),
            'dawn': (90, 60, 90),           # Even darker purple/pink
            'sunrise': (160, 80, 70),       # Darker orange/red
            'morning': (180, 220, 255),
            'day': (135, 206, 235),
            'afternoon': (160, 210, 245),
            'sunset': (160, 70, 60),        # Darker red/orange
            'dusk': (70, 50, 90),           # Darker purple
            'post_dusk': (60, 70, 100)
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
        
        # Hills configuration
        self.hills = []
        self.generate_hills()
        
        # Initialize clock
        self.clock = pygame.time.Clock()
        
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
        if len(self.plants) >= 4:  # Limit total number of plants to 4
            return
            
        # Place plant at ground level with some horizontal spacing
        min_spacing = self.width / 5  # Adjust spacing based on screen width to accommodate 4 plants
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
        
        # Update wind
        self.wind_change_timer -= 1
        if self.wind_change_timer <= 0:
            # Set new target wind speed based on weather
            if self.current_weather == 'clear':
                self.target_wind_speed = random.uniform(0.2, 1.0)
            elif self.current_weather == 'cloudy':
                self.target_wind_speed = random.uniform(0.5, 1.5)
            elif self.current_weather == 'rain':
                self.target_wind_speed = random.uniform(1.0, 2.0)
            else:  # storm
                self.target_wind_speed = random.uniform(2.0, 3.0)
            self.wind_change_timer = random.randint(200, 400)
        
        # Smoothly interpolate wind speed
        self.wind_speed += (self.target_wind_speed - self.wind_speed) * 0.01
        
        # Calculate base light level based on time of day
        if day_progress < 0.2:  # Dawn
            phase_progress = day_progress / 0.2
            self.environment.light_level = 20 + 60 * phase_progress
            self._blend_sky_color(day_progress)
        elif day_progress < 0.8:  # Day
            self.environment.light_level = 80
            self._blend_sky_color(day_progress)
        elif day_progress < 1.0:  # Dusk to night
            phase_progress = (day_progress - 0.8) / 0.2
            self.environment.light_level = 80 - 60 * phase_progress
            self._blend_sky_color(day_progress)
        
        # Apply weather effects
        if self.current_weather == 'cloudy':
            self.environment.light_level *= 0.7
            self.environment.humidity += 0.1
        elif self.current_weather == 'rain':
            self.environment.light_level *= 0.5
            self.environment.humidity += 0.3
            self.environment.water_level = min(100, self.environment.water_level + 0.2)
        elif self.current_weather == 'storm':
            self.environment.light_level *= 0.3
            self.environment.humidity += 0.5
            self.environment.water_level = min(100, self.environment.water_level + 0.4)
        else:  # clear
            self.environment.water_level = max(0, self.environment.water_level - 0.1)
            
    def _change_weather(self) -> None:
        """Change the weather state"""
        # Clear weather is more common
        weights = [0.4, 0.3, 0.2, 0.1]  # Probabilities for clear, cloudy, rain, storm
        self.current_weather = random.choices(self.weather_states, weights=weights)[0]
        
        # Set weather duration
        self.weather_duration = random.randint(300, 600)
        
    def _blend_sky_color(self, time_of_day: float) -> None:
        """Update sky color based on time of day"""
        # Map time of day to sky colors
        if time_of_day < 0.1:  # Night to pre-dawn
            progress = time_of_day / 0.1
            self.bg_color = self._interpolate_color(self.sky_colors['night'], 
                                                  self.sky_colors['pre_dawn'], 
                                                  progress)
        elif time_of_day < 0.2:  # Pre-dawn to sunrise
            progress = (time_of_day - 0.1) / 0.1
            if progress < 0.5:
                # Pre-dawn to dawn
                p = progress * 2
                self.bg_color = self._interpolate_color(self.sky_colors['pre_dawn'],
                                                      self.sky_colors['dawn'],
                                                      p)
            else:
                # Dawn to sunrise
                p = (progress - 0.5) * 2
                self.bg_color = self._interpolate_color(self.sky_colors['dawn'],
                                                      self.sky_colors['sunrise'],
                                                      p)
        elif time_of_day < 0.3:  # Sunrise to morning
            progress = (time_of_day - 0.2) / 0.1
            self.bg_color = self._interpolate_color(self.sky_colors['sunrise'],
                                                  self.sky_colors['morning'],
                                                  progress)
        elif time_of_day < 0.4:  # Morning to day
            progress = (time_of_day - 0.3) / 0.1
            self.bg_color = self._interpolate_color(self.sky_colors['morning'],
                                                  self.sky_colors['day'],
                                                  progress)
        elif time_of_day < 0.6:  # Full day
            self.bg_color = self.sky_colors['day']
        elif time_of_day < 0.7:  # Day to afternoon
            progress = (time_of_day - 0.6) / 0.1
            self.bg_color = self._interpolate_color(self.sky_colors['day'],
                                                  self.sky_colors['afternoon'],
                                                  progress)
        elif time_of_day < 0.8:  # Afternoon to sunset
            progress = (time_of_day - 0.7) / 0.1
            self.bg_color = self._interpolate_color(self.sky_colors['afternoon'],
                                                  self.sky_colors['sunset'],
                                                  progress)
        elif time_of_day < 0.9:  # Sunset to dusk
            progress = (time_of_day - 0.8) / 0.1
            if progress < 0.5:
                # Sunset to dusk
                p = progress * 2
                self.bg_color = self._interpolate_color(self.sky_colors['sunset'],
                                                      self.sky_colors['dusk'],
                                                      p)
            else:
                # Dusk to post-dusk
                p = (progress - 0.5) * 2
                self.bg_color = self._interpolate_color(self.sky_colors['dusk'],
                                                      self.sky_colors['post_dusk'],
                                                      p)
        else:  # Post-dusk to night
            progress = (time_of_day - 0.9) / 0.1
            self.bg_color = self._interpolate_color(self.sky_colors['post_dusk'],
                                                  self.sky_colors['night'],
                                                  progress)

    def _interpolate_color(self, color1: tuple, color2: tuple, progress: float) -> tuple:
        """Interpolate between two colors"""
        return tuple(int(c1 + (c2 - c1) * progress) for c1, c2 in zip(color1, color2))

    def update(self) -> None:
        """Update all garden elements"""
        self.frame_count += 1
        
        # Only update every N frames
        if self.frame_count % self.update_interval != 0:
            return
            
        # Update environmental conditions
        self.update_environment()
        
        # Update celestial objects
        day_progress = self.current_time / self.day_length
        
        # Calculate sun and moon positions
        angle = day_progress * 2 * math.pi - math.pi/2  # Start at top
        orbit_center_y = self.height * 0.8  # Moved orbit center up
        orbit_radius_x = self.width * 0.6
        orbit_radius_y = self.height * 0.7  # Reduced vertical radius
        
        # Sun position (visible during day)
        sun_x = self.width/2 + math.cos(angle) * orbit_radius_x
        sun_y = orbit_center_y + math.sin(angle) * orbit_radius_y
        self.sun.x = sun_x
        self.sun.y = sun_y
        self.sun.update()
        
        # Moon position (opposite of sun)
        moon_angle = angle + math.pi
        moon_x = self.width/2 + math.cos(moon_angle) * orbit_radius_x
        moon_y = orbit_center_y + math.sin(moon_angle) * orbit_radius_y
        
        # Update moon position
        self.moon.x = moon_x
        self.moon.y = moon_y
        self.moon.update()
        
        # Update stars
        for star in self.stars:
            star.update()
        
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
        if self.current_weather in ['rain', 'storm']:
            # Only update rain positions every 3 frames for smoother animation
            if self.frame_count % 3 == 0:
                self.rain_surface.fill((0, 0, 0, 0))
                
                # Update or initialize rain drops
                if not self.rain_drops or self.rain_update_counter >= 15:
                    self.rain_drops = []
                    # Generate drops for each cloud
                    for cloud in self.clouds:
                        cloud_center_x = cloud['x'] + cloud['size'] / 2
                        cloud_bottom_y = cloud['y'] + cloud['size'] / 3
                        
                        # Number of drops based on rain intensity and cloud size
                        num_drops = int(self.drops_per_cloud * 0.2 * (cloud['size'] / 150))
                        
                        for _ in range(num_drops):
                            # Randomize starting position within cloud bounds
                            drop_x = random.gauss(cloud_center_x, cloud['size'] / 4)
                            drop_y = random.gauss(cloud_bottom_y, 10)
                            
                            # Vary drop sizes based on weather
                            if self.current_weather == 'storm':
                                size = random.uniform(3, 5)
                                speed = random.uniform(12, 15)
                            else:
                                size = random.uniform(2, 3)
                                speed = random.uniform(8, 10)
                            
                            # Add some horizontal movement based on wind
                            wind_effect = self.wind_speed * random.uniform(0.8, 1.2)
                            
                            self.rain_drops.append({
                                'x': drop_x,
                                'y': drop_y,
                                'size': size,
                                'speed': speed,
                                'wind': wind_effect
                            })
                    self.rain_update_counter = 0
                else:
                    # Move existing drops down and apply wind effect
                    new_drops = []
                    for drop in self.rain_drops:
                        # Update position with wind and speed
                        drop['y'] += drop['speed']
                        drop['x'] += drop['wind']
                        
                        # Keep drops that are still on screen
                        if drop['y'] < self.height:
                            new_drops.append(drop)
                    self.rain_drops = new_drops
                    self.rain_update_counter += 1
                
                # Draw all drops with trail effect
                for drop in self.rain_drops:
                    # Draw elongated raindrop
                    start_pos = (int(drop['x']), int(drop['y']))
                    end_pos = (int(drop['x'] - drop['wind']), 
                             int(drop['y'] - drop['speed'] * 0.5))
                    
                    # Make storms more visible
                    alpha = 150 if self.current_weather == 'storm' else 100
                    
                    pygame.draw.line(self.rain_surface, (150, 150, 255, alpha),
                                   start_pos, end_pos, int(drop['size']))
            
            # Blit the cached rain surface
            self.screen.blit(self.rain_surface, (0, 0))
            
    def generate_hills(self) -> None:
        """Generate procedural hills using Perlin noise"""
        self.hills = []
        num_hills = random.randint(4, 7)  # Random number of hills
        
        # Generate random offsets for variety
        offsets = []
        for i in range(num_hills):
            offset = {
                'x': random.uniform(-0.2, 0.2),  # Horizontal shift
                'height': random.uniform(0.15, 0.25),  # Height variation
                'width': random.uniform(1.2, 1.6),  # Width variation
                'detail': random.uniform(0.8, 1.2),  # Detail variation
            }
            offsets.append(offset)
        
        # Sort offsets by height to ensure taller hills are in the back
        offsets.sort(key=lambda x: x['height'], reverse=True)
        
        # Create hills with the offsets
        for i in range(num_hills):
            base_x = self.width * (i / (num_hills - 1))
            hill = {
                'center_x': base_x + (self.width * offsets[i]['x']),
                'height': self.height * offsets[i]['height'],
                'width': (self.width / (num_hills - 1)) * offsets[i]['width'],
                'detail': offsets[i]['detail'],
                'color': (
                    80 + random.randint(-10, 10),
                    100 + random.randint(-10, 10),
                    80 + random.randint(-10, 10)
                )
            }
            self.hills.append(hill)

    def _draw_hills(self) -> None:
        """Draw rolling hills on the horizon using smooth noise"""
        hills_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Draw hills from back to front
        for hill in self.hills:
            points = []
            # Use more points for smoother curves
            num_points = int(self.width / 5)  # One point every 5 pixels
            
            # Generate points with smooth noise
            for i in range(num_points):
                x = (i / (num_points - 1)) * (self.width + hill['width'])
                x -= hill['width'] / 2
                
                # Use multiple cosine waves with different frequencies for more natural look
                distance = (x - hill['center_x']) / (hill['width'] / 2)
                base_height = math.cos(distance * math.pi / 2)**2
                detail = math.cos(distance * math.pi * hill['detail'])**2 * 0.2
                
                height = (base_height + detail) * hill['height']
                y = self.height - height
                
                points.append((x, y))
            
            # Add bottom corners
            points.append((points[-1][0], self.height))
            points.append((points[0][0], self.height))
            
            # Draw hill
            pygame.draw.polygon(hills_surface, hill['color'], points)
        
        # Add subtle gradient shading at the base
        shade_height = int(self.height * 0.2)
        for i in range(shade_height):
            shade_alpha = int(20 * (1 - i / shade_height))
            shade_rect = pygame.Rect(0, self.height - i, self.width, 1)
            shade_color = (60, 80, 60)
            if shade_alpha > 0:  # Only draw if visible
                pygame.draw.rect(hills_surface, shade_color, shade_rect)
        
        self.screen.blit(hills_surface, (0, 0))
        
    def draw(self) -> None:
        """Draw all garden elements"""
        # Get time of day and update sky color
        day_progress = self.current_time / self.day_length
        self._blend_sky_color(day_progress)
        
        # Fill background
        self.screen.fill(self.bg_color)
        
        # Draw stars during night, dawn, and dusk
        is_transition = day_progress < 0.2 or day_progress > 0.8
        is_night = day_progress > 0.9 or day_progress < 0.1
        
        if is_transition or is_night:
            # Calculate star visibility
            if is_night:
                star_alpha = 255  # Full visibility at night
            else:
                # Fade during dawn/dusk
                if day_progress < 0.2:  # Dawn
                    progress = 1.0 - (day_progress / 0.2)  # 1.0 at start, 0.0 at end
                else:  # Dusk
                    progress = (day_progress - 0.8) / 0.2  # 0.0 at start, 1.0 at end
                star_alpha = int(255 * progress)
            
            # Update and draw stars - make them bigger and brighter
            for star in self.stars:
                # Make stars more visible
                star.size = random.uniform(1.5, 3.0)  # Slightly larger stars
                star.color = (255, 255, 255, star_alpha)  # Pure white with appropriate alpha
                star.update()  # Update twinkle animation
                star.draw(self.screen)
                
        # Draw celestial objects BEFORE hills so they appear behind them
        # Calculate celestial object positions
        horizon_y = self.height * 0.85  # Lower horizon line (was 0.75)
        max_height = self.height * 0.15  # Higher max height for more complete hiding (was 0.1)
        
        # Sun position follows a semicircle path
        if day_progress <= 0.8:  # Visible until dusk
            # Calculate sun position on arc
            sun_progress = (day_progress - 0.2) / 0.6  # Normalize to 0-1 for day period
            if sun_progress < 0:
                sun_progress = 0
            sun_angle = math.pi * sun_progress
            sun_x = self.width * 0.5 + math.cos(sun_angle) * (self.width * 0.4)
            sun_y = horizon_y - math.sin(sun_angle) * (horizon_y - max_height)
            
            # Smooth transition near horizon - use a gradual adjustment instead of a sudden jump
            edge_proximity = min(sun_progress, 1 - sun_progress) * 10  # 0 at edges, 1 when >= 0.1 from edge
            edge_proximity = max(0, min(1, edge_proximity))  # Clamp between 0 and 1
            
            # Apply smooth adjustment - more adjustment when closer to edge
            horizon_adjustment = self.height * 0.1 * (1 - edge_proximity)
            sun_y += horizon_adjustment
            
            # Update sun position
            self.sun.x = sun_x
            self.sun.y = sun_y
            
            # Calculate sun visibility
            sun_alpha = 255
            if day_progress < 0.2:  # Dawn fade in
                sun_alpha = int(255 * (day_progress / 0.2))
            elif day_progress > 0.6:  # Pre-dusk fade out
                sun_alpha = int(255 * (1.0 - (day_progress - 0.6) / 0.2))
            self.sun.color = (*self.sun.color[:3], sun_alpha)
            
            # Draw sun
            self.sun.draw(self.screen)
        
        # Moon position follows opposite semicircle path
        if day_progress >= 0.8 or day_progress <= 0.2:  # Visible from dusk to dawn
            # Calculate moon position on arc
            if day_progress >= 0.8:
                moon_progress = (day_progress - 0.8) / 0.4
            else:
                moon_progress = (day_progress + 0.2) / 0.4
            moon_angle = math.pi * moon_progress
            moon_x = self.width/2 + math.cos(moon_angle) * (self.width * 0.4)
            moon_y = horizon_y - math.sin(moon_angle) * (horizon_y - max_height)
            
            # Smooth transition near horizon - use a gradual adjustment instead of a sudden jump
            edge_proximity = min(moon_progress, 1 - moon_progress) * 10  # 0 at edges, 1 when >= 0.1 from edge
            edge_proximity = max(0, min(1, edge_proximity))  # Clamp between 0 and 1
            
            # Apply smooth adjustment - more adjustment when closer to edge
            horizon_adjustment = self.height * 0.1 * (1 - edge_proximity)
            moon_y += horizon_adjustment
            
            # Update moon position
            self.moon.x = moon_x
            self.moon.y = moon_y
            
            # Calculate moon visibility
            moon_alpha = 255
            if day_progress > 0.8:  # Dusk fade in
                moon_alpha = int(255 * ((day_progress - 0.8) / 0.2))
            elif day_progress < 0.2:  # Pre-dawn fade out
                moon_alpha = int(255 * (1.0 - day_progress / 0.2))
            self.moon.color = (*self.moon.color[:3], moon_alpha)
            
            # Draw moon
            self.moon.draw(self.screen)
            
        # Draw hills
        self._draw_hills()
        
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
        
        # Convert progress to hours and minutes (24-hour format)
        hours = int(24 * day_progress)
        minutes = int(60 * (24 * day_progress - hours))
        
        if day_progress < 0.2:  # Dawn (4:00 - 8:48)
            time_of_day = "Dawn"
        elif day_progress < 0.8:  # Day (8:48 - 19:12)
            time_of_day = "Day"
        elif day_progress < 0.9:  # Dusk (19:12 - 21:36)
            time_of_day = "Dusk"
        else:  # Night (21:36 - 4:00)
            time_of_day = "Night"
            
        # Format weather info
        weather_info = {
            'Time': f"{time_of_day} ({hours:02d}:{minutes:02d})",
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
        if self.frame_count % 2 == 0:  # Update more frequently
            self.cloud_surface.fill((0, 0, 0, 0))
            
            # Create new clouds if needed
            while len(self.clouds) < self.max_clouds:
                cloud = {
                    'x': random.randint(-100, self.width),
                    'y': random.randint(0, self.height // 3),
                    'size': random.randint(100, 250),  # Larger clouds
                    'speed': random.uniform(0.8, 1.2),  # Base speed multiplier
                    'height_offset': random.uniform(-5, 5)  # Vertical movement
                }
                self.clouds.append(cloud)
            
            # Update and draw clouds
            new_clouds = []
            for cloud in self.clouds:
                # Move cloud based on wind speed and cloud's own properties
                movement = self.wind_speed * cloud['speed']
                cloud['x'] += movement
                
                # Add slight vertical movement
                cloud['y'] += math.sin(self.frame_count * 0.02) * 0.2 + cloud['height_offset'] * 0.1
                
                # Keep y position within bounds
                cloud['y'] = max(0, min(self.height // 3, cloud['y']))
                
                # Wrap around when off screen
                if cloud['x'] - cloud['size'] > self.width:
                    cloud['x'] = -cloud['size']
                    cloud['y'] = random.randint(0, self.height // 3)
                    cloud['height_offset'] = random.uniform(-5, 5)
                
                # Draw cloud as a group of circles
                alpha = 180 if self.current_weather == 'cloudy' else 220
                if self.current_weather == 'storm':
                    alpha = 240
                
                # Draw main cloud body
                for i in range(5):  # Draw multiple overlapping circles for each cloud
                    offset_x = int(cloud['x'] + i * cloud['size'] * 0.2)
                    offset_y = int(cloud['y'] + math.sin(i + self.frame_count * 0.02) * 10)
                    pygame.draw.circle(self.cloud_surface, (200, 200, 200, alpha),
                                    (offset_x, offset_y), int(cloud['size'] * 0.5))
                    
                    # Add darker bottom for storm clouds
                    if self.current_weather == 'storm':
                        pygame.draw.circle(self.cloud_surface, (100, 100, 100, 180),
                                        (offset_x, offset_y + cloud['size'] * 0.3),
                                        int(cloud['size'] * 0.4))
                
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
