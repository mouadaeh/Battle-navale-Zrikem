import pygame
import os
from src.utils.constants import BACKGROUND_PATH, WATER_PATH

def load_assets(resolution):
    """Load all game assets"""
    assets = {}
    
    # Load background
    try:
        background = pygame.image.load(BACKGROUND_PATH)
        background = pygame.transform.scale(background, resolution)
        assets["background"] = background
    except:
        # Create a fallback background
        bg = pygame.Surface(resolution)
        bg.fill((30, 50, 90))  # Dark blue
        assets["background"] = bg
    
     # Load water image for grid
    try:
        water = pygame.image.load(WATER_PATH)
        # No need to scale it here - we'll tile it in the grid drawing function
        assets["water"] = water
        print("Water image loaded successfully")
    except Exception as e:
        print(f"Error loading water image: {e}")
        # We'll fall back to the default sky blue if this fails
    
    # Load ship images
    try:
        ship_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "ships")
        assets["ships"] = {}
        for ship_name in ["carrier", "battleship", "cruiser", "submarine", "destroyer"]:
            ship_path = os.path.join(ship_folder, f"{ship_name}.png")
            if os.path.exists(ship_path):
                ship_img = pygame.image.load(ship_path)
                assets["ships"][ship_name] = ship_img
    except Exception as e:
        print(f"Error loading ship assets: {e}")
    
    # Load UI elements
    try:
        ui_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "ui")
        assets["ui"] = {}
        for ui_element in ["button", "panel"]:
            ui_path = os.path.join(ui_folder, f"{ui_element}.png")
            if os.path.exists(ui_path):
                ui_img = pygame.image.load(ui_path)
                assets["ui"][ui_element] = ui_img
    except Exception as e:
        print(f"Error loading UI assets: {e}")
    
    return assets

def initialize_fonts():
    """Initialize and return the fonts used in the game"""
    fonts = {
        "medium": pygame.font.SysFont("Times New Roman", 40),
        "large": pygame.font.SysFont("Times New Roman", 60),
        "button": pygame.font.Font(None, 50),
        "small": pygame.font.Font(None, 30)
    }
    return fonts