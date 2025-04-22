import pygame
import sys
from src.utils.constants import WHITE, GRAY, BLACK, GREEN, RED
from src.ui.buttons import draw_button

def draw_main_menu(screen, game_state, fonts, background, button_cooldown=0):
    """Draw the main menu screen"""
    screen.blit(background, (0, 0))
    big_bold_font=pygame.font.SysFont(None,100,bold=True)
    title_text = big_bold_font.render("Bataille Navale", True, WHITE)
    screen.blit(title_text, (screen.get_width() // 6 - title_text.get_width() // 2, 80))
    
    # Supprimer ou commenter ces lignes pour enlever le message "Veuillez patienter"
    # if button_cooldown > 0:
    #     cooldown_text = fonts["small"].render("Veuillez patienter...", True, WHITE)
    #     screen.blit(cooldown_text, (screen.get_width() // 2 - cooldown_text.get_width() // 2, 
    #                               screen.get_height() // 2 - 140))
    
    # Single player button
    single_player_clicked = draw_button(
        screen,
        "Joueur vs IA",
        600,
        screen.get_height() - 60 - 90,
        300,
        80,
        GRAY,
        WHITE,
        fonts["button"],
        game_state.start_single_player if button_cooldown == 0 else None,
    )
    
    # Multiplayer button
    draw_button(
        screen,
        "Deux Joueurs",
        screen.get_width() -800 - 50,
        screen.get_height() - 60 - 90,
        300,
        80,
        GRAY,
        WHITE,
        fonts["button"],
        game_state.start_multiplayer if button_cooldown == 0 else None,
    )

def draw_ship_selection(screen, game_state, fonts):
    """Draw the ship selection UI during placement phase"""
    # Position the ship selection on the left side of the screen
    start_x = 50
    start_y = screen.get_height() // 2 - 100
    
    # Background rectangle for ship selection
    selection_bg = pygame.Rect(start_x - 40, start_y - 50, 370, len(game_state.ships) * 50 + 100)
    pygame.draw.rect(screen, (50, 50, 70), selection_bg, border_radius=10)
    
    # Title
    title_text = fonts["button"].render("Navires à placer:", True, WHITE)
    screen.blit(title_text, (start_x, start_y - 50))
    
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
        screen.blit(text, (start_x, start_y + index * 50))
        
        # Show rotation info
        if index == game_state.current_ship_index:
            orientation = "Horizontal" if game_state.horizontal else "Vertical"
            orient_text = pygame.font.Font(None, 30).render(
                f"Orientation: {orientation} (R to rotate)", True, WHITE)
            screen.blit(orient_text, (start_x-30, start_y + len(game_state.ships) * 50 + 20))

def draw_game_end(screen, winner, fonts, restart_action):
    """Draw the end game screen"""
    screen.fill(BLACK)
    
    # Fix the condition to match what game_state.py actually sets
    if winner == "player":  # This should match what you set in game_state.py
        win_text = fonts["large"].render("Vous avez gagné !", True, GREEN)  # Changed to GREEN
    else:
        win_text = fonts["large"].render("L'ordinateur a gagné !", True, RED)  # Changed to RED
    
    screen.blit(win_text, (screen.get_width() // 2 - win_text.get_width() // 2, screen.get_height() // 2 - 50))
    
    # Add restart button
    draw_button(
        screen,
        "Nouvelle partie",
        screen.get_width() // 2 - 150,
        screen.get_height() // 2 + 50,
        300,
        80,
        GRAY,
        WHITE,
        fonts["button"],
        restart_action
    )