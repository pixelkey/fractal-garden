import pygame
import numpy as np
from typing import Tuple, Dict, List, Any, Optional

# Try importing OpenGL - if it fails, we'll use CPU rendering only
try:
    import pygame.opengl
    from OpenGL.GL import *
    from OpenGL.GLU import *
    from OpenGL.GL import shaders
    HAS_OPENGL = True
except ImportError:
    HAS_OPENGL = False
    print("Warning: PyOpenGL not available. GPU rendering disabled.")

class Renderer:
    """Base renderer interface that CPU and GPU renderers will implement"""
    
    def __init__(self, width: int, height: int, use_gpu: bool = True):
        self.width = width
        self.height = height
        self.use_gpu = use_gpu and HAS_OPENGL
        self.initialized = False
    
    def initialize(self) -> bool:
        """Initialize the renderer"""
        raise NotImplementedError("Subclasses must implement initialize()")
    
    def resize(self, width: int, height: int) -> bool:
        """Resize the renderer surface"""
        self.width = width
        self.height = height
        return True
    
    def clear(self, color: Tuple[int, int, int]) -> None:
        """Clear the renderer with specified color"""
        raise NotImplementedError("Subclasses must implement clear()")
    
    def present(self) -> None:
        """Present the rendered content to the screen"""
        raise NotImplementedError("Subclasses must implement present()")
    
    def draw_rect(self, rect: Tuple[int, int, int, int], color: Tuple[int, int, int, int], 
                  filled: bool = True) -> None:
        """Draw a rectangle"""
        raise NotImplementedError("Subclasses must implement draw_rect()")
    
    def draw_circle(self, pos: Tuple[int, int], radius: int, color: Tuple[int, int, int, int], 
                    filled: bool = True) -> None:
        """Draw a circle"""
        raise NotImplementedError("Subclasses must implement draw_circle()")
    
    def draw_line(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int], 
                  color: Tuple[int, int, int, int], width: int = 1) -> None:
        """Draw a line"""
        raise NotImplementedError("Subclasses must implement draw_line()")
    
    def draw_polygon(self, points: List[Tuple[int, int]], color: Tuple[int, int, int, int], 
                     filled: bool = True) -> None:
        """Draw a polygon"""
        raise NotImplementedError("Subclasses must implement draw_polygon()")
    
    def draw_surface(self, surface: pygame.Surface, pos: Tuple[int, int]) -> None:
        """Draw a pygame surface"""
        raise NotImplementedError("Subclasses must implement draw_surface()")
    
    def create_surface(self, width: int, height: int, alpha: bool = True) -> Any:
        """Create a new surface"""
        raise NotImplementedError("Subclasses must implement create_surface()")
    
    def get_screen_surface(self) -> Any:
        """Get the main screen surface"""
        raise NotImplementedError("Subclasses must implement get_screen_surface()")
        
    def blit(self, surface: pygame.Surface, pos: Tuple[int, int]) -> None:
        """Blit a surface to the screen (alias for draw_surface)"""
        self.draw_surface(surface, pos)

class CPURenderer(Renderer):
    """CPU-based renderer using Pygame's standard rendering APIs"""
    
    def __init__(self, width: int, height: int):
        super().__init__(width, height, use_gpu=False)
        self.screen = None
    
    def initialize(self) -> bool:
        """Initialize the CPU renderer"""
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        self.initialized = True
        return True
    
    def resize(self, width: int, height: int) -> bool:
        """Resize the CPU renderer"""
        super().resize(width, height)
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        return True
    
    def clear(self, color: Tuple[int, int, int]) -> None:
        """Clear the screen with specified color"""
        self.screen.fill(color)
    
    def present(self) -> None:
        """Update the display"""
        pygame.display.flip()
    
    def draw_rect(self, rect: Tuple[int, int, int, int], color: Tuple[int, int, int, int], 
                 filled: bool = True) -> None:
        """Draw a rectangle"""
        if filled:
            pygame.draw.rect(self.screen, color, rect)
        else:
            pygame.draw.rect(self.screen, color, rect, 1)
    
    def draw_circle(self, pos: Tuple[int, int], radius: int, color: Tuple[int, int, int, int], 
                   filled: bool = True) -> None:
        """Draw a circle"""
        if filled:
            pygame.draw.circle(self.screen, color, pos, radius)
        else:
            pygame.draw.circle(self.screen, color, pos, radius, 1)
    
    def draw_line(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int], 
                 color: Tuple[int, int, int, int], width: int = 1) -> None:
        """Draw a line"""
        pygame.draw.line(self.screen, color, start_pos, end_pos, width)
    
    def draw_polygon(self, points: List[Tuple[int, int]], color: Tuple[int, int, int, int], 
                    filled: bool = True) -> None:
        """Draw a polygon"""
        if filled:
            pygame.draw.polygon(self.screen, color, points)
        else:
            pygame.draw.polygon(self.screen, color, points, 1)
    
    def draw_surface(self, surface: pygame.Surface, pos: Tuple[int, int]) -> None:
        """Draw a pygame surface"""
        self.screen.blit(surface, pos)
    
    def create_surface(self, width: int, height: int, alpha: bool = True) -> pygame.Surface:
        """Create a new surface"""
        if alpha:
            return pygame.Surface((width, height), pygame.SRCALPHA)
        else:
            return pygame.Surface((width, height))
    
    def get_screen_surface(self) -> pygame.Surface:
        """Get the main screen surface"""
        return self.screen
        
    def blit(self, surface: pygame.Surface, pos: Tuple[int, int]) -> None:
        """Blit a surface to the screen (direct implementation for CPU)"""
        self.screen.blit(surface, pos)

class GPURenderer(Renderer):
    """GPU-based renderer using PyOpenGL"""
    
    def __init__(self, width: int, height: int):
        if not HAS_OPENGL:
            raise ImportError("PyOpenGL is required for GPU rendering")
        super().__init__(width, height, use_gpu=True)
        self.screen = None
        self.textures = {}  # Texture cache
        self.shaders = {}   # Shader cache
        self.current_shader = None
        self.frame_buffer = None
        self.frame_buffer_texture = None
    
    def initialize(self) -> bool:
        """Initialize the GPU renderer"""
        # Create an OpenGL context
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 4)
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 16)
        
        self.screen = pygame.display.set_mode(
            (self.width, self.height), 
            pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE
        )
        
        # Basic OpenGL setup
        glViewport(0, 0, self.width, self.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.width, self.height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Enable blending for transparency
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Setup default shaders
        self._setup_shaders()
        
        # Create a fallback CPU surface for transitions
        self.cpu_surface = pygame.Surface((self.width, self.height))
        
        self.initialized = True
        return True
    
    def _setup_shaders(self) -> None:
        """Set up the default shaders"""
        # Basic vertex shader
        vertex_shader = """
        #version 330 core
        layout(location = 0) in vec3 position;
        layout(location = 1) in vec2 texCoord;
        layout(location = 2) in vec4 color;
        
        out vec2 TexCoord;
        out vec4 Color;
        
        uniform mat4 projection;
        uniform mat4 model;
        
        void main() {
            gl_Position = projection * model * vec4(position, 1.0);
            TexCoord = texCoord;
            Color = color;
        }
        """
        
        # Basic fragment shader
        fragment_shader = """
        #version 330 core
        in vec2 TexCoord;
        in vec4 Color;
        
        out vec4 FragColor;
        
        uniform sampler2D tex;
        uniform bool useTexture;
        
        void main() {
            if (useTexture) {
                FragColor = texture(tex, TexCoord) * Color;
            } else {
                FragColor = Color;
            }
        }
        """
        
        # Compile shaders
        vert_shader = shaders.compileShader(vertex_shader, GL_VERTEX_SHADER)
        frag_shader = shaders.compileShader(fragment_shader, GL_FRAGMENT_SHADER)
        
        # Create shader program
        self.shaders['basic'] = shaders.compileProgram(vert_shader, frag_shader)
        self.current_shader = self.shaders['basic']
    
    def resize(self, width: int, height: int) -> bool:
        """Resize the GPU renderer"""
        super().resize(width, height)
        self.screen = pygame.display.set_mode(
            (self.width, self.height), 
            pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE
        )
        glViewport(0, 0, self.width, self.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.width, self.height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        
        # Create a new CPU surface for fallbacks
        self.cpu_surface = pygame.Surface((self.width, self.height))
        
        return True
    
    def clear(self, color: Tuple[int, int, int]) -> None:
        """Clear the screen with specified color"""
        r, g, b = color
        glClearColor(r/255.0, g/255.0, b/255.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    def present(self) -> None:
        """Swap the buffers to show the rendered content"""
        pygame.display.flip()
    
    def _create_texture_from_surface(self, surface: pygame.Surface) -> int:
        """Create an OpenGL texture from a pygame surface"""
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        
        # Set texture parameters
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        
        # Get surface data
        data = pygame.image.tostring(surface, "RGBA", 1)
        
        # Create texture
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGBA, 
            surface.get_width(), surface.get_height(), 
            0, GL_RGBA, GL_UNSIGNED_BYTE, data
        )
        
        return texture_id
    
    def draw_rect(self, rect: Tuple[int, int, int, int], color: Tuple[int, int, int, int], 
                 filled: bool = True) -> None:
        """Draw a rectangle with OpenGL"""
        x, y, width, height = rect
        r, g, b, a = [c/255.0 for c in color]
        
        # Set up quad vertices
        vertices = [
            (x, y),           # Bottom left
            (x + width, y),   # Bottom right
            (x + width, y + height),  # Top right
            (x, y + height),  # Top left
        ]
        
        if filled:
            glBegin(GL_QUADS)
        else:
            glBegin(GL_LINE_LOOP)
            
        glColor4f(r, g, b, a)
        for vertex in vertices:
            glVertex2f(*vertex)
            
        glEnd()
    
    def draw_circle(self, pos: Tuple[int, int], radius: int, color: Tuple[int, int, int, int], 
                   filled: bool = True) -> None:
        """Draw a circle with OpenGL"""
        x, y = pos
        r, g, b, a = [c/255.0 for c in color]
        
        # Set color
        glColor4f(r, g, b, a)
        
        # Draw circle using triangle fan or line loop
        segments = max(10, int(radius / 2))  # More segments for larger circles
        
        if filled:
            glBegin(GL_TRIANGLE_FAN)
            glVertex2f(x, y)  # Center point
        else:
            glBegin(GL_LINE_LOOP)
            
        for i in range(segments + 1):
            angle = 2.0 * np.pi * i / segments
            dx = radius * np.cos(angle)
            dy = radius * np.sin(angle)
            glVertex2f(x + dx, y + dy)
            
        glEnd()
    
    def draw_line(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int], 
                 color: Tuple[int, int, int, int], width: int = 1) -> None:
        """Draw a line with OpenGL"""
        r, g, b, a = [c/255.0 for c in color]
        
        # Set line width
        glLineWidth(width)
        
        # Draw line
        glBegin(GL_LINES)
        glColor4f(r, g, b, a)
        glVertex2f(*start_pos)
        glVertex2f(*end_pos)
        glEnd()
        
        # Reset line width
        glLineWidth(1)
    
    def draw_polygon(self, points: List[Tuple[int, int]], color: Tuple[int, int, int, int], 
                    filled: bool = True) -> None:
        """Draw a polygon with OpenGL"""
        r, g, b, a = [c/255.0 for c in color]
        
        if filled:
            glBegin(GL_POLYGON)
        else:
            glBegin(GL_LINE_LOOP)
            
        glColor4f(r, g, b, a)
        for point in points:
            glVertex2f(*point)
            
        glEnd()
    
    def draw_surface(self, surface: pygame.Surface, pos: Tuple[int, int]) -> None:
        """Draw a pygame surface using a texture"""
        # Create a texture if this surface hasn't been used before
        surface_id = id(surface)
        if surface_id not in self.textures:
            self.textures[surface_id] = self._create_texture_from_surface(surface)
        
        # Bind the texture
        texture_id = self.textures[surface_id]
        glBindTexture(GL_TEXTURE_2D, texture_id)
        
        # Draw textured quad
        x, y = pos
        width, height = surface.get_size()
        
        glEnable(GL_TEXTURE_2D)
        glBegin(GL_QUADS)
        glColor4f(1, 1, 1, 1)  # White color to not alter texture colors
        
        glTexCoord2f(0, 0)
        glVertex2f(x, y)
        
        glTexCoord2f(1, 0)
        glVertex2f(x + width, y)
        
        glTexCoord2f(1, 1)
        glVertex2f(x + width, y + height)
        
        glTexCoord2f(0, 1)
        glVertex2f(x, y + height)
        
        glEnd()
        glDisable(GL_TEXTURE_2D)
    
    def create_surface(self, width: int, height: int, alpha: bool = True) -> pygame.Surface:
        """Create a new pygame surface (for compatibility)"""
        if alpha:
            return pygame.Surface((width, height), pygame.SRCALPHA)
        else:
            return pygame.Surface((width, height))
    
    def get_screen_surface(self) -> pygame.Surface:
        """Get a pygame surface representing the current screen (compatibility)"""
        # We need to create a surface because we can't directly access the OpenGL framebuffer from Python
        # For real rendering, use the OpenGL drawing methods
        return self.cpu_surface
        
    def blit(self, surface: pygame.Surface, pos: Tuple[int, int]) -> None:
        """Blit a surface to the screen (alias for draw_surface)"""
        self.draw_surface(surface, pos)

class RendererManager:
    """Manages both CPU and GPU renderers and handles transitions between them"""
    
    def __init__(self, width: int, height: int, use_gpu: bool = True):
        self.width = width
        self.height = height
        self.use_gpu = use_gpu and HAS_OPENGL
        self.cpu_renderer = CPURenderer(width, height)
        self.gpu_renderer = None
        
        # Initialize CPU renderer as a fallback
        self.cpu_renderer.initialize()
        self.current_renderer = self.cpu_renderer
        
        # Try to initialize GPU renderer if requested
        if self.use_gpu:
            try:
                self.gpu_renderer = GPURenderer(width, height)
                if self.gpu_renderer.initialize():
                    self.current_renderer = self.gpu_renderer
            except Exception as e:
                print(f"Failed to initialize GPU renderer: {e}")
                print("Falling back to CPU renderer")
                self.use_gpu = False
    
    def resize(self, width: int, height: int) -> None:
        """Resize both renderers"""
        self.width = width
        self.height = height
        self.cpu_renderer.resize(width, height)
        if self.gpu_renderer:
            self.gpu_renderer.resize(width, height)
    
    def set_renderer(self, use_gpu: bool) -> bool:
        """Switch between GPU and CPU renderers"""
        if use_gpu == self.use_gpu:
            return True  # Already using the requested renderer
        
        if use_gpu and not self.gpu_renderer:
            # Try to initialize GPU renderer
            try:
                self.gpu_renderer = GPURenderer(self.width, self.height)
                if self.gpu_renderer.initialize():
                    self.current_renderer = self.gpu_renderer
                    self.use_gpu = True
                    return True
                else:
                    return False
            except Exception as e:
                print(f"Failed to initialize GPU renderer: {e}")
                return False
        
        # Switch to CPU renderer
        if not use_gpu:
            self.current_renderer = self.cpu_renderer
            self.use_gpu = False
            return True
        
        # Switch to GPU renderer
        self.current_renderer = self.gpu_renderer
        self.use_gpu = True
        return True
    
    def toggle_renderer(self) -> bool:
        """Toggle between GPU and CPU renderers"""
        return self.set_renderer(not self.use_gpu)
    
    def get_renderer(self) -> Renderer:
        """Get the current renderer"""
        return self.current_renderer
