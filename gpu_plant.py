import pygame
from plant_factory import Plant
from renderer import Renderer

class GPUPlantAdapter:
    """Adapter class that allows Plant to work with the renderer interface"""
    
    def __init__(self, plant: Plant):
        """Initialize the GPU plant adapter"""
        self.plant = plant
        print(f"Created GPU adapter for plant: {plant.definition.common_name}")
    
    def draw(self, renderer: Renderer) -> None:
        """Draw the plant using the renderer interface"""
        print(f"Drawing plant {self.plant.definition.common_name} with GPU renderer")
        
        # We need to actually use the renderer's drawing capabilities directly
        # rather than passing the screen surface
        
        # This is the issue - we're not actually using GPU rendering for the plants
        # because we're just passing the screen surface to the plant's draw method,
        # which uses Pygame's CPU-based drawing functions.
        
        # For a proper implementation, we would need to rewrite all the plant's drawing
        # code to use the renderer's drawing methods directly, similar to what we did 
        # with the celestial objects.
        
        # For now, we'll use this approach as a temporary solution
        self.plant.draw(renderer.get_screen_surface())
    
    def __getattr__(self, name):
        """Forward any other attribute access to the wrapped plant"""
        return getattr(self.plant, name)
