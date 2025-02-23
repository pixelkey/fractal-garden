import pygame
from garden import Garden

def main():
    # Initialize Pygame
    pygame.init()
    
    # Create and run the garden
    garden = Garden()
    garden.run()

if __name__ == "__main__":
    main()
