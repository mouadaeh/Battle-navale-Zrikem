import pygame
from src.utils.constants import WHITE, GRAY, GREEN, RED

def draw_main_menu(screen, game_state, fonts, background, button_cooldown):
    """Draw the main menu screen"""
    screen.blit(background, (0, 0))
    
    title = fonts["large"].render("Bataille Navale", True, WHITE)
    title_rect = title.get_rect(center=(screen.get_width() // 2, 100))
    screen.blit(title, title_rect)
    
    single_button_rect = pygame.Rect(screen.get_width() // 2 - 150, 300, 300, 50)
    pygame.draw.rect(screen, GREEN, single_button_rect)
    single_text = fonts["medium"].render("Joueur Solo", True, WHITE)
    single_text_rect = single_text.get_rect(center=single_button_rect.center)
    screen.blit(single_text, single_text_rect)
    
    multi_button_rect = pygame.Rect(screen.get_width() // 2 - 150, 400, 300, 50)
    pygame.draw.rect(screen, GREEN, multi_button_rect)
    multi_text = fonts["medium"].render("Multijoueur", True, WHITE)
    multi_text_rect = multi_text.get_rect(center=multi_button_rect.center)
    screen.blit(multi_text, multi_text_rect)
    
    exit_button_rect = pygame.Rect(screen.get_width() // 2 - 150, 500, 300, 50)
    pygame.draw.rect(screen, RED, exit_button_rect)
    exit_text = fonts["medium"].render("Quitter", True, WHITE)
    exit_text_rect = exit_text.get_rect(center=exit_button_rect.center)
    screen.blit(exit_text, exit_text_rect)
    
    if button_cooldown > 0:
        return False
    
    for event in pygame.event.get([pygame.MOUSEBUTTONDOWN]):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if single_button_rect.collidepoint(mouse_pos):
                game_state.start_single_player()
                return True
            elif multi_button_rect.collidepoint(mouse_pos):
                game_state.start_multiplayer()
                return True
            elif exit_button_rect.collidepoint(mouse_pos):
                pygame.quit()
                sys.exit()
    
    return False

def draw_ship_selection(screen, game_state, fonts):
    """Draw the ship selection UI"""
    if game_state.current_ship_index < len(game_state.ships):
        ship = game_state.ships[game_state.current_ship_index]
        ship_text = fonts["medium"].render(f"Placement: {ship['name']} (Taille: {ship['size']})", True, WHITE)
        screen.blit(ship_text, (screen.get_width() // 2 - ship_text.get_width() // 2, 150))
        
        rotation_text = fonts["small"].render("Appuyez sur 'R' pour tourner", True, WHITE)
        screen.blit(rotation_text, (screen.get_width() // 2 - rotation_text.get_width() // 2, 200))

def draw_game_end(screen, winner, fonts, restart_callback):
    """Draw the game end screen"""
    if winner == "player":
        winner_text = "Joueur gagne!"
    elif winner == "computer":
        winner_text = "Ordinateur gagne!"
    else:
        winner_text = f"Joueur {winner[-1]} gagne!"  # e.g., "player1" or "player2"
    winner_surface = fonts["large"].render(winner_text, True, WHITE)
    winner_rect = winner_surface.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 - 50))
    screen.blit(winner_surface, winner_rect)
    
    restart_text = fonts["medium"].render("Rejouer (R)", True, WHITE)
    restart_rect = restart_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 + 50))
    screen.blit(restart_text, restart_rect)
    
    quit_text = fonts["medium"].render("Quitter (Q)", True, WHITE)
    quit_rect = quit_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 + 100))
    screen.blit(quit_text, quit_rect)
    
    for event in pygame.event.get([pygame.KEYDOWN]):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                restart_callback()
            elif event.key == pygame.K_q:
                pygame.quit()
                sys.exit()