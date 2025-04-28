import pygame
import os

# Screen settings
def get_screen_resolution():
    """Get the screen resolution minus a small offset for taskbar"""
    display_w = pygame.display.Info().current_w
    display_h = pygame.display.Info().current_h
    return [display_w, display_h - 72]

# Colors
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
DARK_BLUE = (0, 0, 139)
GRAY = (200, 200, 200)
SKY_BLUE = (135, 206, 235)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)


# Grid settings
CELL_SIZE = 50
GRID_SIZE = 10

# Ships configuration
SHIPS = [
    {"name": "Porte-avions", "size": 5},
    {"name": "Croiseur", "size": 4},
    {"name": "Destroyer", "size": 3},
    {"name": "Sous-marin", "size": 3},
    {"name": "Torpilleur", "size": 2},
]

# Game speed
FPS = 60

# Background path
BACKGROUND_PATH = os.path.join("assets", "background", "background1.jpg")
GAMEPLAY_BACKGROUND_PATH = os.path.join("assets", "background", "background2.jpg")

WATER_PATH = os.path.join("assets", "map", "tiled_sea1.png")  # Adjust path as needed

# Timing constants
BUTTON_COOLDOWN = 60  # Standard cooldown for buttons
MESSAGE_DURATION = 60  # Standard duration for messages
ROTATION_COOLDOWN = 15  # Cooldown for ship rotation
TRANSITION_DELAY = 90  # Delay for state transitions

# AI constants
AI_THINKING_DELAY = 90  # Delay to simulate AI thinking