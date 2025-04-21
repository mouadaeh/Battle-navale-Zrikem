import pygame
import os
from src.utils.constants import BACKGROUND_PATH

def load_background(resolution):
    """Load the background image or create a fallback"""
    try:
        background = pygame.image.load(BACKGROUND_PATH)
        background = pygame.transform.scale(background, (resolution[0], resolution[1]))
    except pygame.error:
        print("Warning: Could not load background image. Using solid color instead.")
        background = pygame.Surface((resolution[0], resolution[1]))
        background.fill((30, 70, 130))  # Navy blue fallback
    return background

def initialize_fonts():
    """Initialize and return the fonts used in the game"""
    fonts = {
        "medium": pygame.font.SysFont("Times New Roman", 40),
        "large": pygame.font.SysFont("Times New Roman", 60),
        "button": pygame.font.Font(None, 50),
        "small": pygame.font.Font(None, 30)
    }
    return fonts