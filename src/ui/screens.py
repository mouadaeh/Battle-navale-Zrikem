import pygame
import sys
import os
from src.utils.constants import WHITE, GRAY, BLACK, GREEN, RED
from src.ui.buttons import draw_button

def draw_main_menu(screen, game_state, fonts, background, button_cooldown=0):
    """Draw the main menu screen with responsive layout"""
    # Draw background
    screen.blit(background, (0, 0))
    
    # Calculate dimensions
    screen_width, screen_height = screen.get_width(), screen.get_height()
    
    # Render title with shadow using the previous font
    title_text = "Bataille Navale"
    big_bold_font = pygame.font.SysFont(None, 100, bold=True)
    
    # Shadow text - slightly offset and in dark color
    shadow_color = (20, 20, 20)  # Dark grey for shadow
    shadow_offset = 4  # Pixels to offset the shadow
    title_shadow = big_bold_font.render(title_text, True, shadow_color)
    
    # Main text
    title = big_bold_font.render(title_text, True, WHITE)
    
    # Calculate positions - Example positions (adjust these values as needed)
    title_x = screen_width * 0.1  # 10% from left edge
    title_y = screen_height * 0.1  # 10% from top edge
    
    # Draw shadow first
    screen.blit(title_shadow, (title_x + shadow_offset, title_y + shadow_offset))
    # Draw main text on top
    screen.blit(title, (title_x, title_y))
    
    
    # Calculate button dimensions
    button_width = min(300, screen_width * 0.25)
    button_height = min(80, screen_height * 0.1)
    button_margin = button_width * 0.2
    
    # Center buttons horizontally
    buttons_total_width = 2 * button_width + button_margin
    buttons_start_x = (screen_width - buttons_total_width) / 2
    buttons_y = screen_height * 0.75
    
    # Main buttons (keep existing ones)
    draw_button(
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
    # Move further left and make wider
    start_x = screen_width * 0.03  # 3% from left edge (was 5%)
    start_y = screen_height * 0.3   # 30% from top
    
    # Make panel wider and slightly taller
    panel_width = screen_width * 0.30  # 30% of screen width (was 25%)
    panel_height = screen_height * 0.55  # 55% of screen height (was 50%)
    
    # Background rectangle for ship selection
    selection_bg = pygame.Rect(start_x, start_y, panel_width-50, panel_height)
    pygame.draw.rect(screen, (50, 50, 70), selection_bg, border_radius=10)
    
    # Title position relative to panel
    title_text = fonts["button"].render("Navires à placer:", True, WHITE)
    title_x = start_x + panel_width * 0.05  # 5% padding (was 10%)
    title_y = start_y + panel_height * 0.05  # 5% padding from top of panel
    screen.blit(title_text, (title_x, title_y))
    
    # Calculate spacing for ships list
    ships_start_y = title_y + title_text.get_height() + panel_height * 0.05
    ship_spacing = (panel_height * 0.6) / len(game_state.ships)
    
    # Draw ships list
    for index, ship in enumerate(game_state.ships):
        if index < game_state.current_ship_index:
            color = (100, 100, 100)  # Gray for placed ships
            status = " "
        elif index == game_state.current_ship_index:
            color = GREEN
            status = " "
        else:
            color = WHITE
            status = " "
        
        text = fonts["button"].render(f"{status} {ship['name']} ({ship['size']})", True, color)
        ship_y = ships_start_y + index * ship_spacing
        screen.blit(text, (title_x, ship_y))
        
        # Show rotation info at bottom of panel
        if index == game_state.current_ship_index:
            orientation = "Horizontal" if game_state.horizontal else "Vertical"
            
            # Create a better orientation display
            orient_text = pygame.font.Font(None, 30).render(
                f"Orientation: {orientation}", True, WHITE)
            rotate_text = pygame.font.Font(None, 30).render(
                f"Appuyez sur R pour rotation", True, (255, 255, 0))  # Yellow for emphasis
            
            # Move texts further left and adjust vertical position
            orient_x = start_x + panel_width * 0.05  # 5% padding (was 10%)
            orient_y = start_y + panel_height * 0.80  # 80% down the panel
            rotate_y = orient_y + orient_text.get_height() + 5  # Below orientation text
            
            # Display both texts
            screen.blit(orient_text, (orient_x, orient_y))
            screen.blit(rotate_text, (orient_x, rotate_y))

def draw_game_end(screen, winner, fonts, restart_function):
    """Draw the end game screen with responsive layout and victory/defeat images"""
    # Fill the screen with a semi-transparent background
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))  # Semi-transparent black background
    screen.blit(overlay, (0, 0))

    # --- OPTIMISATION: Cache image in game_state ---
    if not hasattr(draw_game_end, "cached_image") or draw_game_end.cached_image_winner != winner or draw_game_end.cached_image_size != screen.get_size():
        assets_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'end')
        image_path = None

        if winner == "player":
            image_path = os.path.join(assets_dir, "victory.png")
        elif winner == "computer":
            image_path = os.path.join(assets_dir, "defeat.png")
        elif winner == "joueur1":
            victory_path = os.path.join(assets_dir, "victory1.png")
            image_path = victory_path if os.path.exists(victory_path) else os.path.join(assets_dir, "victory.png")
        elif winner == "joueur2":
            victory_path = os.path.join(assets_dir, "victory2.png")
            image_path = victory_path if os.path.exists(victory_path) else os.path.join(assets_dir, "victory.png")

        if image_path and os.path.exists(image_path):
            img = pygame.image.load(image_path).convert_alpha()
            img = pygame.transform.scale(img, screen.get_size())
            draw_game_end.cached_image = img
        else:
            draw_game_end.cached_image = None
        draw_game_end.cached_image_winner = winner
        draw_game_end.cached_image_size = screen.get_size()

    # Affiche l'image si elle existe
    if draw_game_end.cached_image:
        screen.blit(draw_game_end.cached_image, (0, 0))

    # (Optional) Draw restart button as before
    button_width = min(300, screen.get_width() * 0.25)
    button_height = min(80, screen.get_height() * 0.1)
    button_x = (screen.get_width() - button_width) / 2
    button_y = screen.get_height() * 0.75

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
        restart_function
    )

def draw_pause_screen(screen, fonts, resolution, resume_action, quit_action):
    """Affiche l'écran de pause avec un fond personnalisé et un style d'écriture."""
    # Dessiner un fond opaque (noir solide)
    overlay = pygame.Surface((resolution[0], resolution[1]))
    overlay.fill((0, 0, 0))  # Noir solide
    screen.blit(overlay, (0, 0))

    # Texte principal "Pause"
    pause_text = fonts["large"].render("Pause", True, (255, 255, 255))  # Blanc
    pause_bg_rect = pygame.Rect(
        resolution[0] // 2 - pause_text.get_width() // 2 - 20,
        resolution[1] // 3 - 70,
        pause_text.get_width() + 40,
        pause_text.get_height() + 20
    )
    pygame.draw.rect(screen, (50, 50, 50), pause_bg_rect)  # Fond gris foncé
    pygame.draw.rect(screen, (255, 255, 255), pause_bg_rect, 2)  # Bordure blanche
    screen.blit(pause_text, (pause_bg_rect.x + 20, pause_bg_rect.y + 10))

    # Boutons
    button_width = 300
    button_height = 60
    button_margin = 20

    # Bouton "Reprendre"
    resume_y = resolution[1] // 2
    draw_button(
        screen,
        "Reprendre",
        resolution[0] // 2 - button_width // 2,
        resume_y,
        button_width,
        button_height,
        GRAY,
        WHITE,
        fonts["button"],
        resume_action
    )

    # Bouton "Quitter"
    quit_y = resume_y + button_height + button_margin
    draw_button(
        screen,
        "Quitter",
        resolution[0] // 2 - button_width // 2,
        quit_y,
        button_width,
        button_height,
        GRAY,
        WHITE,
        fonts["button"],
        quit_action
    )