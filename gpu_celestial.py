import pygame
import random
import math
from renderer import Renderer

class GPUCelestialObject:
    def __init__(self, x: float, y: float, size: float, color: tuple):
        self.x = x
        self.y = y
        self.size = size
        self.color = color  # Now expects (r,g,b,a) format
        self.blink_state = 1.0
        self.blink_speed = random.uniform(0.02, 0.05)
        self.expression_timer = 0
        self.is_winking = False
        
    def update(self):
        # Update blink state for twinkling stars
        self.blink_state += self.blink_speed
        if self.blink_state > 1.0:
            self.blink_state = 0.0
            
        # Update expression
        self.expression_timer += 1
        if self.expression_timer > 200:  # Change expression every few seconds
            self.is_winking = random.random() < 0.3  # 30% chance to wink
            self.expression_timer = 0

class GPUSun(GPUCelestialObject):
    def __init__(self, x: float, y: float):
        # Warm yellow-orange color for the sun
        super().__init__(x, y, 60, (255, 220, 100, 255))
        self.ray_lengths = [random.uniform(0.8, 1.2) for _ in range(12)]  # More rays
        self.ray_speed = [random.uniform(0.01, 0.02) for _ in range(12)]
        self.glow_size = self.size * 1.5
        
    def draw(self, renderer):
        """Draw the sun using the renderer interface"""
        # Get renderer's screen (either CPU or GPU)
        screen = renderer.get_screen_surface()
        center = (int(self.x), int(self.y))
        
        # Draw outer glow
        for i in range(3):
            glow_size = self.glow_size * (1 + i * 0.5)
            alpha = 100 - i * 30
            glow_color = (255, 200, 50, alpha)
            glow_surface = pygame.Surface((int(glow_size * 2), int(glow_size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, glow_color, 
                            (int(glow_size), int(glow_size)), int(glow_size))
            renderer.draw_surface(glow_surface, 
                            (center[0] - int(glow_size), center[1] - int(glow_size)))
        
        # Draw rays
        for i in range(12):
            angle = i * math.pi / 6
            self.ray_lengths[i] += self.ray_speed[i]
            if self.ray_lengths[i] > 1.2:
                self.ray_speed[i] = -abs(self.ray_speed[i])
            elif self.ray_lengths[i] < 0.8:
                self.ray_speed[i] = abs(self.ray_speed[i])
                
            ray_length = self.size * 1.2 * self.ray_lengths[i]
            end_x = center[0] + math.cos(angle) * ray_length
            end_y = center[1] + math.sin(angle) * ray_length
            ray_color = (255, 200, 50, 150)
            ray_surface = pygame.Surface((int(ray_length * 2), 4), pygame.SRCALPHA)
            pygame.draw.line(ray_surface, ray_color, (0, 2), (ray_length * 2, 2), 4)
            
            # Rotate and position the ray
            rotated_ray = pygame.transform.rotate(ray_surface, -math.degrees(angle))
            ray_rect = rotated_ray.get_rect()
            ray_rect.center = center
            renderer.draw_surface(rotated_ray, ray_rect)
        
        # Draw main sun circle with gradient
        for i in range(3):
            size_factor = 1 - i * 0.2
            color_temp = 255 - i * 20
            inner_color = (color_temp, color_temp - 35, color_temp - 155, self.color[3])
            sun_circle = pygame.Surface((int(self.size * 2 * size_factor), 
                                      int(self.size * 2 * size_factor)), pygame.SRCALPHA)
            pygame.draw.circle(sun_circle, inner_color, 
                            (int(self.size * size_factor), int(self.size * size_factor)), 
                            int(self.size * size_factor))
            renderer.draw_surface(sun_circle, 
                          (center[0] - int(self.size * size_factor), 
                           center[1] - int(self.size * size_factor)))
        
        # Draw happy face - directly using renderer drawing methods
        if random.random() < 0.95:  # 95% chance to show face
            eye_color = (255, 180, 0, self.color[3])
            mouth_color = (255, 180, 0, self.color[3])
            
            # Eyes
            eye_offset = self.size * 0.2
            eye_size = self.size * 0.15
            if self.is_winking:
                renderer.draw_line(
                    (center[0] - eye_offset, center[1] - eye_offset),
                    (center[0] - eye_offset + eye_size, center[1] - eye_offset), 
                    eye_color, 3)
            else:
                renderer.draw_circle(
                    (center[0] - eye_offset, center[1] - eye_offset),
                    int(eye_size / 2), eye_color)
                
            # Always draw right eye normally
            renderer.draw_circle(
                (center[0] + eye_offset, center[1] - eye_offset),
                int(eye_size / 2), eye_color)
            
            # Smile
            curve_points = []
            for i in range(9):
                angle = math.pi * i / 8 
                offset_x = math.cos(angle) * (self.size * 0.3)
                offset_y = math.sin(angle) * (self.size * 0.3)
                curve_points.append((center[0] + offset_x, center[1] + offset_y))
            
            # Draw only the bottom half of the circle as a smile
            for i in range(4):
                renderer.draw_line(
                    curve_points[i], curve_points[i+1], 
                    mouth_color, 3)

class GPUMoon(GPUCelestialObject):
    def __init__(self, x: float, y: float):
        # Soft blue-white color for the moon
        super().__init__(x, y, 50, (200, 205, 220, 255))
        
        # Generate craters with more random placement
        self.craters = []
        
        # Create fewer, more randomly placed craters
        num_craters = 6  # Fewer craters
        attempts = 0
        min_distance = 0.25  # Minimum distance between craters
        
        while len(self.craters) < num_craters and attempts < 50:
            cx = random.uniform(-0.45, 0.45)
            cy = random.uniform(-0.45, 0.45)
            
            # Only avoid the direct eye and mouth positions
            eye_area = (abs(cx - 0.2) < 0.15 and abs(cy + 0.2) < 0.15) or \
                      (abs(cx + 0.2) < 0.15 and abs(cy + 0.2) < 0.15)
            mouth_area = abs(cx) < 0.2 and abs(cy - 0.05) < 0.15
            
            # Check distance from existing craters
            too_close = False
            for existing_cx, existing_cy, _ in self.craters:
                dist = ((cx - existing_cx) ** 2 + (cy - existing_cy) ** 2) ** 0.5
                if dist < min_distance:
                    too_close = True
                    break
            
            if not (eye_area or mouth_area) and not too_close:
                # Smaller craters
                self.craters.append((cx, cy, random.uniform(0.06, 0.1)))
            
            attempts += 1
        
        self.glow_size = self.size * 1.1  # Glow size
    
    def draw(self, renderer):
        """Draw the moon using the renderer interface"""
        center = (int(self.x), int(self.y))
        
        # Draw outer glow
        glow_color = (180, 180, 200, 50)
        glow_surface = pygame.Surface((int(self.glow_size * 2), int(self.glow_size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, glow_color, 
                        (int(self.glow_size), int(self.glow_size)), int(self.glow_size))
        renderer.draw_surface(glow_surface, 
                      (center[0] - int(self.glow_size), center[1] - int(self.glow_size)))
        
        # Draw main moon circle
        alpha = self.color[3]
        moon_surface = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        
        # Draw the main moon circle with a blue-white gradient
        for i in range(3):
            size_factor = 1 - i * 0.1
            color_factor = 1 - i * 0.1
            moon_color = (
                int(200 * color_factor), 
                int(205 * color_factor), 
                int(220 * color_factor), 
                alpha
            )
            pygame.draw.circle(moon_surface, moon_color, 
                            (int(self.size), int(self.size)), 
                            int(self.size * size_factor))
        
        # Draw craters (darker spots) on the surface
        for crater_x, crater_y, crater_size in self.craters:
            crater_pos = (int(self.size + crater_x * self.size), int(self.size + crater_y * self.size))
            crater_radius = int(self.size * crater_size)
            crater_color = (160, 165, 180, alpha)  # Slightly darker than the moon
            pygame.draw.circle(moon_surface, crater_color, crater_pos, crater_radius)
        
        renderer.draw_surface(moon_surface, 
                      (center[0] - self.size, center[1] - self.size))
        
        # Draw face features directly using renderer methods
        if random.random() < 0.95:  # 95% chance to show face
            eye_color = (160, 165, 180, alpha)
            
            # Eyes
            eye_offset = self.size * 0.2
            eye_size = self.size * 0.12
            if self.is_winking:
                renderer.draw_line(
                    (center[0] - eye_offset, center[1] - eye_offset),
                    (center[0] - eye_offset + eye_size, center[1] - eye_offset), 
                    eye_color, 3)
            else:
                renderer.draw_circle(
                    (center[0] - eye_offset, center[1] - eye_offset),
                    int(eye_size / 2), eye_color)
                
            # Always draw right eye normally
            renderer.draw_circle(
                (center[0] + eye_offset, center[1] - eye_offset),
                int(eye_size / 2), eye_color)
            
            # Draw sleeping "zzz" or smile
            if random.random() < 0.3:  # 30% chance for zzz
                # Draw a crescent smile
                smile_points = []
                for i in range(5):
                    t = i / 4
                    angle = math.pi * (0.2 + 0.6 * t)  # 0.2π to 0.8π
                    offset_x = math.cos(angle) * (self.size * 0.3)
                    offset_y = math.sin(angle) * (self.size * 0.2)
                    smile_points.append((center[0] + offset_x, center[1] + offset_y))
                
                for i in range(4):
                    renderer.draw_line(
                        smile_points[i], smile_points[i+1], 
                        eye_color, 2)
            else:
                # Draw zzz's for sleeping
                text_x = center[0] + self.size * 0.4
                text_y = center[1] - self.size * 0.3
                zs = "z" * random.randint(2, 3)  # Random number of z's
                
                # Create a surface for the text
                font = pygame.font.SysFont(None, int(self.size * 0.3))
                text_surface = font.render(zs, True, eye_color)
                renderer.draw_surface(text_surface, (text_x, text_y))

class GPUStar(GPUCelestialObject):
    def __init__(self, x: float, y: float):
        size = random.uniform(2, 4)
        super().__init__(x, y, size, (255, 255, 255, 255))
    
    def draw(self, renderer):
        """Draw a star using the renderer interface"""
        # Make the star twinkle
        current_size = self.size * (0.7 + 0.3 * self.blink_state)
        alpha = int(max(100, 255 * self.blink_state))
        
        # Create a surface for the star with glow
        center = (int(self.x), int(self.y))
        
        # Draw star glow
        glow_surface = pygame.Surface((int(current_size * 4), int(current_size * 4)), pygame.SRCALPHA)
        glow_color = (*self.color[:3], alpha // 4)
        pygame.draw.circle(glow_surface, glow_color, (int(current_size * 2), int(current_size * 2)), int(current_size * 2))
        renderer.draw_surface(glow_surface, (center[0] - int(current_size * 2), center[1] - int(current_size * 2)))
        
        # Draw star core
        star_color = (*self.color[:3], alpha)
        renderer.draw_circle(center, int(current_size), star_color)
