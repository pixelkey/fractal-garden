import pygame
import random
import math

class CelestialObject:
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

class Sun(CelestialObject):
    def __init__(self, x: float, y: float):
        # Warm yellow-orange color for the sun
        super().__init__(x, y, 60, (255, 220, 100, 255))
        self.ray_lengths = [random.uniform(0.8, 1.2) for _ in range(12)]  # More rays
        self.ray_speed = [random.uniform(0.01, 0.02) for _ in range(12)]
        self.glow_size = self.size * 1.5
        
    def draw(self, screen: pygame.Surface):
        # Draw outer glow directly on screen
        center = (int(self.x), int(self.y))
        for i in range(3):
            glow_size = self.glow_size * (1 + i * 0.5)
            alpha = 100 - i * 30
            glow_color = (255, 200, 50, alpha)
            glow_surface = pygame.Surface((int(glow_size * 2), int(glow_size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, glow_color, 
                            (int(glow_size), int(glow_size)), int(glow_size))
            screen.blit(glow_surface, 
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
            screen.blit(rotated_ray, ray_rect)
        
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
            screen.blit(sun_circle, 
                      (center[0] - int(self.size * size_factor), 
                       center[1] - int(self.size * size_factor)))
        
        # Draw happy face
        if random.random() < 0.95:  # 95% chance to show face
            eye_color = (255, 180, 0, self.color[3])
            mouth_color = (255, 180, 0, self.color[3])
            
            # Eyes
            eye_offset = self.size * 0.2
            eye_size = self.size * 0.15
            if self.is_winking:
                pygame.draw.line(screen, eye_color, 
                              (center[0] - eye_offset, center[1] - eye_offset),
                              (center[0] - eye_offset + eye_size, center[1] - eye_offset), 3)
                pygame.draw.circle(screen, eye_color, 
                                (int(center[0] + eye_offset), int(center[1] - eye_offset)), 
                                int(eye_size))
            else:
                pygame.draw.circle(screen, eye_color, 
                                (int(center[0] - eye_offset), int(center[1] - eye_offset)), 
                                int(eye_size))
                pygame.draw.circle(screen, eye_color, 
                                (int(center[0] + eye_offset), int(center[1] - eye_offset)), 
                                int(eye_size))
            
            # Smile
            smile_rect = pygame.Rect(center[0] - self.size * 0.3, center[1] - self.size * 0.1,
                                   self.size * 0.6, self.size * 0.6)
            pygame.draw.arc(screen, mouth_color, smile_rect, math.pi, 2 * math.pi, 3)

class Moon(CelestialObject):
    def __init__(self, x: float, y: float):
        # Soft blue-white color for the moon
        super().__init__(x, y, 50, (230, 235, 255, 255))
        self.craters = [(random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3), 
                        random.uniform(0.1, 0.15)) for _ in range(5)]  # More craters
        self.glow_size = self.size * 1.3
        
    def draw(self, screen: pygame.Surface):
        center = (int(self.x), int(self.y))
        
        # Draw outer glow
        for i in range(3):
            glow_size = self.glow_size * (1 + i * 0.3)
            alpha = 60 - i * 15
            glow_color = (200, 220, 255, alpha)
            glow_surface = pygame.Surface((int(glow_size * 2), int(glow_size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, glow_color, 
                            (int(glow_size), int(glow_size)), int(glow_size))
            screen.blit(glow_surface, 
                      (center[0] - int(glow_size), center[1] - int(glow_size)))
        
        # Draw main moon circle with slight gradient
        for i in range(2):
            size_factor = 1 - i * 0.1
            color_bright = 230 - i * 10
            moon_color = (color_bright, color_bright + 5, color_bright + 20, self.color[3])
            moon_circle = pygame.Surface((int(self.size * 2 * size_factor), 
                                       int(self.size * 2 * size_factor)), pygame.SRCALPHA)
            pygame.draw.circle(moon_circle, moon_color, 
                            (int(self.size * size_factor), int(self.size * size_factor)), 
                            int(self.size * size_factor))
            screen.blit(moon_circle, 
                      (center[0] - int(self.size * size_factor), 
                       center[1] - int(self.size * size_factor)))
        
        # Draw craters with subtle shading
        for cx, cy, cr in self.craters:
            crater_pos = (int(center[0] + cx * self.size), int(center[1] + cy * self.size))
            # Crater shadow
            shadow_color = (200, 205, 225, self.color[3])
            crater_shadow = pygame.Surface((int(cr * self.size * 2.2), 
                                         int(cr * self.size * 2.2)), pygame.SRCALPHA)
            pygame.draw.circle(crater_shadow, shadow_color, 
                            (int(cr * self.size * 1.1), int(cr * self.size * 1.1)), 
                            int(cr * self.size * 1.1))
            screen.blit(crater_shadow, 
                      (crater_pos[0] - int(cr * self.size * 1.1), 
                       crater_pos[1] - int(cr * self.size * 1.1)))
            
            # Crater highlight
            highlight_color = (240, 245, 255, self.color[3])
            crater_highlight = pygame.Surface((int(cr * self.size * 1.8), 
                                            int(cr * self.size * 1.8)), pygame.SRCALPHA)
            pygame.draw.circle(crater_highlight, highlight_color, 
                            (int(cr * self.size * 0.9), int(cr * self.size * 0.9)), 
                            int(cr * self.size * 0.9))
            screen.blit(crater_highlight, 
                      (crater_pos[0] - int(cr * self.size * 0.9) - 1, 
                       crater_pos[1] - int(cr * self.size * 0.9) - 1))
        
        # Draw happy face (more subtle than sun)
        if random.random() < 0.95:  # 95% chance to show face
            eye_color = (180, 185, 205, self.color[3])
            mouth_color = (180, 185, 205, self.color[3])
            
            # Eyes
            eye_offset = self.size * 0.2
            eye_size = self.size * 0.12  # Slightly smaller eyes
            if self.is_winking:
                pygame.draw.line(screen, eye_color, 
                              (center[0] - eye_offset, center[1] - eye_offset),
                              (center[0] - eye_offset + eye_size, center[1] - eye_offset), 2)
                pygame.draw.circle(screen, eye_color, 
                                (int(center[0] + eye_offset), int(center[1] - eye_offset)), 
                                int(eye_size))
            else:
                pygame.draw.circle(screen, eye_color, 
                                (int(center[0] - eye_offset), int(center[1] - eye_offset)), 
                                int(eye_size))
                pygame.draw.circle(screen, eye_color, 
                                (int(center[0] + eye_offset), int(center[1] - eye_offset)), 
                                int(eye_size))
            
            # Gentle smile
            smile_rect = pygame.Rect(center[0] - self.size * 0.25, center[1] - self.size * 0.05,
                                   self.size * 0.5, self.size * 0.4)
            pygame.draw.arc(screen, mouth_color, smile_rect, math.pi, 2 * math.pi, 2)

class Star(CelestialObject):
    def __init__(self, x: float, y: float):
        size = random.uniform(2, 4)
        super().__init__(x, y, size, (255, 255, 255, 255))
        
    def draw(self, screen: pygame.Surface):
        # Calculate current size based on blinking
        current_size = self.size * (0.5 + self.blink_state * 0.5)
        
        # Draw star with glow
        alpha = int(128 + 127 * self.blink_state)
        glow_surface = pygame.Surface((int(current_size * 4), int(current_size * 4)), 
                                    pygame.SRCALPHA)
        
        # Draw outer glow
        glow_color = (*self.color[:3], alpha // 4)
        pygame.draw.circle(glow_surface, glow_color, 
                         (int(current_size * 2), int(current_size * 2)), 
                         int(current_size * 2))
        
        # Draw inner star
        star_color = (*self.color[:3], alpha)
        pygame.draw.circle(glow_surface, star_color, 
                         (int(current_size * 2), int(current_size * 2)), 
                         int(current_size))
        
        # Draw on screen
        screen.blit(glow_surface, 
                   (int(self.x - current_size * 2), 
                    int(self.y - current_size * 2)))
