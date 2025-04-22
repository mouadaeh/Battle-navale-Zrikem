import pygame
import sys
from src.utils.constants import WHITE, GRAY, BLACK, GREEN, RED
from src.ui.buttons import draw_button

def draw_main_menu(screen, game_state, fonts, background, button_cooldown=0):
    """Draw the main menu screen with responsive layout"""
    # Draw background
    screen.blit(background, (0, 0))
    
    # Calculate dimensions
    screen_width, screen_height = screen.get_width(), screen.get_height()
    
    # Title at the top left
    big_bold_font = pygame.font.SysFont(None, 100, bold=True)
    title_text = big_bold_font.render("Bataille Navale", True, WHITE)
    
    # Position title at top left with padding
    title_x = screen_width * 0.1  # 10% from left
    title_y = screen_height * 0.1  # 10% from top
    screen.blit(title_text, (title_x, title_y))
    
    # Calculate button dimensions based on screen size
    button_width = min(300, screen_width * 0.25)  # 25% of screen width, max 300px
    button_height = min(80, screen_height * 0.1)   # 10% of screen height, max 80px
    button_margin = button_width * 0.2  # Space between buttons
    
    # Center the buttons horizontally at bottom of screen
    buttons_total_width = 2 * button_width + button_margin
    buttons_start_x = (screen_width - buttons_total_width) / 2
    buttons_y = screen_height * 0.75  # 75% down the screen
    
    # Single player button (left button)
    single_player_clicked = draw_button(
        screen,
        "Joueur vs IA",
        buttons_start_x,
        buttons_y,
        button_width,
        button_height,
        GRAY,
        WHITE,
        fonts["button"],
        game_state.start_single_player if button_cooldown == 0 else None,
    )
    
    # Multiplayer button (right button)
    draw_button(
        screen,
        "Deux Joueurs",
        buttons_start_x + button_width + button_margin,
        buttons_y,
        button_width,
        button_height,
        GRAY,
        WHITE,
        fonts["button"],
        game_state.start_multiplayer if button_cooldown == 0 else None,
    )

def draw_ship_selection(screen, game_state, fonts):
    """Draw the ship selection UI during placement phase with responsive layout"""
    screen_width, screen_height = screen.get_width(), screen.get_height()
    
    # Position the ship selection on the left side of the screen
    start_x = screen_width * 0.05  # 5% from left edge
    start_y = screen_height * 0.3   # 30% from top
    
    # Calculate panel dimensions based on content
    panel_width = screen_width * 0.25  # 25% of screen width
    panel_height = screen_height * 0.5  # 50% of screen height
    
    # Background rectangle for ship selection
    selection_bg = pygame.Rect(start_x, start_y, panel_width, panel_height)
    pygame.draw.rect(screen, (50, 50, 70), selection_bg, border_radius=10)
    
    # Title position relative to panel
    title_text = fonts["button"].render("Navires à placer:", True, WHITE)
    title_x = start_x + panel_width * 0.1  # 10% padding within panel
    title_y = start_y + panel_height * 0.05  # 5% padding from top of panel
    screen.blit(title_text, (title_x, title_y))
    
    # Calculate spacing for ships list
    ships_start_y = title_y + title_text.get_height() + panel_height * 0.05
    ship_spacing = (panel_height * 0.6) / len(game_state.ships)  # 60% of panel height divided by ships count
    
    # Draw ships list
    for index, ship in enumerate(game_state.ships):
        if index < game_state.current_ship_index:
            color = (100, 100, 100)  # Gray for placed ships
            status = "✓"
        elif index == game_state.current_ship_index:
            color = GREEN
            status = "→"
        else:
            color = WHITE
            status = " "
        
        text = fonts["button"].render(f"{status} {ship['name']} ({ship['size']})", True, color)
        ship_y = ships_start_y + index * ship_spacing
        screen.blit(text, (title_x, ship_y))
        
        # Show rotation info at bottom of panel
        if index == game_state.current_ship_index:
            orientation = "Horizontal" if game_state.horizontal else "Vertical"
            orient_text = pygame.font.Font(None, 30).render(
                f"Orientation: {orientation} (R to rotate)", True, WHITE)
            orient_x = start_x + panel_width * 0.1  # 10% padding within panel
            orient_y = start_y + panel_height * 0.85  # 85% down the panel
            screen.blit(orient_text, (orient_x, orient_y))

def draw_game_end(screen, winner, fonts, restart_action):
    """Draw the end game screen with responsive layout"""
    screen_width, screen_height = screen.get_width(), screen.get_height()
    
    # Fill background
    screen.fill(BLACK)
    
    # Win/lose message
    if winner == "player":
        win_text = fonts["large"].render("Vous avez gagné !", True, GREEN)
    else:
        win_text = fonts["large"].render("L'ordinateur a gagné !", True, RED)
    
    # Center message horizontally, position at 40% of screen height
    message_x = (screen_width - win_text.get_width()) / 2
    message_y = screen_height * 0.4
    screen.blit(win_text, (message_x, message_y))
    
    # Restart button dimensions
    button_width = min(300, screen_width * 0.25)  # 25% of screen width, max 300px
    button_height = min(80, screen_height * 0.1)   # 10% of screen height, max 80px
    
    # Center button horizontally, position at 60% of screen height
    button_x = (screen_width - button_width) / 2
    button_y = screen_height * 0.6
    
    # Add restart button
    draw_button(
        screen,
        "Nouvelle partie",
        button_x,
        button_y,
        button_width,
        button_height,
        GRAY,
        WHITE,
        fonts["button"],
        restart_action
    )