import pygame
import sys
from src.game_state import GameState
from src.utils.constants import WHITE

def handle_placement(screen, game_state, fonts, assets, ship_images, player_x=None, player_y=None, 
                    button_cooldown=0, message_timer=0, message_text="", message_color=WHITE):
    """Handle the ship placement phase for single player"""
    
    # Draw the gameplay background first
    if "gameplay_background" in assets:
        screen.blit(assets["gameplay_background"], (0, 0))
    
    # Draw ship selection
    from src.ui.screens import draw_ship_selection
    draw_ship_selection(screen, game_state, fonts)
    
    # Draw only player's grid in the center during placement
    from src.ui.grid import draw_grid
    player_x, player_y = draw_grid(screen, game_state.player_board, fonts, assets, reveal=True, 
                                  is_player_grid=True, position="center")
    
    # Draw already placed ships
    cell_size = game_state.player_board.width / len(game_state.player_board.grid[0])
    for ship in game_state.placed_ships:
        ship_image = ship_images.get(ship['name'].lower())
        if ship_image:
            scaled_image = pygame.transform.scale(ship_image, (int(cell_size * ship['size']), int(cell_size)))
            if ship['horizontal']:
                screen.blit(scaled_image, (player_x + ship['col'] * cell_size, player_y + ship['row'] * cell_size))
            else:
                rotated_image = pygame.transform.rotate(scaled_image, 90)
                screen.blit(rotated_image, (player_x + ship['col'] * cell_size, player_y + ship['row'] * cell_size))
    
    # Set a cooldown when entering placement state to prevent accidental clicks
    if button_cooldown > 0:
        # Show an instruction message during cooldown
        message_text = "Placez vos navires en cliquant sur la grille. Touche R pour pivoter."
        message_color = WHITE
        message_timer = 60  # Keep the message visible
        message = fonts["small"].render(message_text, True, message_color)
        screen.blit(message, (player_x + game_state.player_board.width//2 - message.get_width()//2, 
                             player_y + game_state.player_board.height + 40))
        return message_timer, message_text, message_color
    
    # Get current ship to place
    current_ship = None
    if game_state.current_ship_index < len(game_state.ships):
        current_ship = game_state.ships[game_state.current_ship_index]
    
    # Get mouse position for preview
    mouse_pos = pygame.mouse.get_pos()
    
    # Draw ship preview at mouse position
    if current_ship and player_x <= mouse_pos[0] < player_x + game_state.player_board.width and player_y <= mouse_pos[1] < player_y + game_state.player_board.height:
        # Calculate grid position from mouse
        col = int((mouse_pos[0] - player_x) // cell_size)
        row = int((mouse_pos[1] - player_y) // cell_size)
        
        # Check if ship can be placed here
        valid_placement = True
        preview_coords = []
        if game_state.horizontal:
            if col + current_ship['size'] > 10:  # Out of bounds check
                valid_placement = False
            else:
                for i in range(current_ship['size']):
                    if row < 0 or row >= 10 or col + i < 0 or col + i >= 10 or game_state.player_board.grid[row][col + i] == 'S':
                        valid_placement = False
                        break
                    preview_coords.append((row, col + i))
        else:  # Vertical
            if row + current_ship['size'] > 10:  # Out of bounds check
                valid_placement = False
            else:
                for i in range(current_ship['size']):
                    if row + i < 0 or row + i >= 10 or col < 0 or col >= 10 or game_state.player_board.grid[row + i][col] == 'S':
                        valid_placement = False
                        break
                    preview_coords.append((row + i, col))
        
        # Draw the preview using the ship image
        ship_image = ship_images.get(current_ship['name'].lower())
        if ship_image:
            scaled_image = pygame.transform.scale(ship_image, (int(cell_size * current_ship['size']), int(cell_size)))
            if valid_placement:
                # Draw the ship image on the grid
                if game_state.horizontal:
                    screen.blit(scaled_image, (player_x + col * cell_size, player_y + row * cell_size))
                else:
                    rotated_image = pygame.transform.rotate(scaled_image, 90)
                    screen.blit(rotated_image, (player_x + col * cell_size, player_y + row * cell_size))
            else:
                # Draw a semi-transparent red overlay for invalid placement
                overlay = pygame.Surface((scaled_image.get_width(), scaled_image.get_height()), pygame.SRCALPHA)
                overlay.fill((255, 0, 0, 128))  # Semi-transparent red
                if game_state.horizontal:
                    screen.blit(scaled_image, (player_x + col * cell_size, player_y + row * cell_size))
                    screen.blit(overlay, (player_x + col * cell_size, player_y + row * cell_size))
                else:
                    rotated_image = pygame.transform.rotate(scaled_image, 90)
                    screen.blit(rotated_image, (player_x + col * cell_size, player_y + row * cell_size))
                    overlay = pygame.transform.rotate(overlay, 90)
                    screen.blit(overlay, (player_x + col * cell_size, player_y + row * cell_size))
    
    # Handle mouse clicks for placement
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r and game_state.rotation_cooldown == 0:
            game_state.horizontal = not game_state.horizontal
            game_state.rotation_cooldown = 15
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if (player_x <= mouse_pos[0] < player_x + game_state.player_board.width and 
                player_y <= mouse_pos[1] < player_y + game_state.player_board.height):
                col = int((mouse_pos[0] - player_x) // cell_size)
                row = int((mouse_pos[1] - player_y) // cell_size)
                if game_state.current_ship_index < len(game_state.ships):
                    ship = game_state.ships[game_state.current_ship_index]
                    if game_state.place_player_ship(row, col, ship['size'], game_state.horizontal):
                        game_state.placed_ships.append({
                            'name': ship['name'],
                            'size': ship['size'],
                            'row': row,
                            'col': col,
                            'horizontal': game_state.horizontal
                        })
                        game_state.current_ship_index += 1
                        if game_state.current_ship_index >= len(game_state.ships):
                            game_state.state = GameState.GAME
    
    return message_timer, message_text, message_color

def handle_multiplayer_placement(screen, game_state, fonts, assets, ship_images, resolution, 
                                button_cooldown=0, message_timer=0, message_text="", message_color=WHITE, 
                                click_processed=False):
    """Handle ship placement for multiplayer"""
    
    # Important: Always update transition timer here
    if game_state.multiplayer.transition_screen:
        game_state.multiplayer.update_transition()
        
        # COMPLETELY clear the screen with solid black
        screen.fill((0, 0, 0))
        
        # Create transition overlay
        overlay = pygame.Surface(resolution, pygame.SRCALPHA)
        overlay.fill((0, 0, 50, 200))  # Dark blue semi-transparent
        screen.blit(overlay, (0, 0))
        
        # Draw transition message
        msg = fonts["large"].render(game_state.multiplayer.transition_message, True, WHITE)
        msg_rect = msg.get_rect(center=(resolution[0]//2, resolution[1]//2 - 50))
        screen.blit(msg, msg_rect)
        
        # Draw countdown
        seconds = game_state.multiplayer.transition_timer // 60 + 1
        countdown = fonts["medium"].render(f"Changement dans {seconds}...", True, WHITE)
        countdown_rect = countdown.get_rect(center=(resolution[0]//2, resolution[1]//2 + 30))
        screen.blit(countdown, countdown_rect)
        
        # Add privacy message
        privacy = fonts["small"].render("Préparez-vous à jouer!", True, WHITE)
        privacy_rect = privacy.get_rect(center=(resolution[0]//2, resolution[1]//2 + 80))
        screen.blit(privacy, privacy_rect)
        
        # Vérifier si la transition est terminée et s'il existe un callback à appeler
        if game_state.multiplayer.transition_timer <= 0 and hasattr(game_state.multiplayer, 'start_game_callback'):
            game_state.multiplayer.start_game_callback()
            delattr(game_state.multiplayer, 'start_game_callback')  # Supprimer le callback après utilisation
        
        # Important: Process events here to continue counting down even during transition
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        # Skip the rest of the function so no boards are drawn during transition
        return message_timer, message_text, message_color, click_processed
    
    # Continue with normal placement once transition is over...
    # Draw the gameplay background
    if "gameplay_background" in assets:
        screen.blit(assets["gameplay_background"], (0, 0))
    
    # Get current player info
    current_player = game_state.multiplayer.current_player
    current_board = game_state.multiplayer.get_current_board()
    
    # Draw player indicator title
    title = fonts["large"].render(f"Joueur {current_player} - Placement", True, WHITE)
    screen.blit(title, (resolution[0]//2 - title.get_width()//2, 20))
    
    # Draw ship selection
    from src.ui.screens import draw_ship_selection
    draw_ship_selection(screen, game_state, fonts)
    
    # Draw player's grid in the center
    from src.ui.grid import draw_grid
    player_x, player_y = draw_grid(screen, current_board, fonts, assets, reveal=True, 
                                  is_player_grid=True, position="center")
    
    # Draw already placed ships
    cell_size = current_board.width / len(current_board.grid[0])
    ships_list = game_state.multiplayer.get_ships_list()
    for ship in ships_list:
        ship_image = ship_images.get(ship['name'].lower())
        if ship_image:
            scaled_image = pygame.transform.scale(ship_image, (int(cell_size * ship['size']), int(cell_size)))
            if ship['horizontal']:
                screen.blit(scaled_image, (player_x + ship['col'] * cell_size, player_y + ship['row'] * cell_size))
            else:
                rotated_image = pygame.transform.rotate(scaled_image, 90)
                screen.blit(rotated_image, (player_x + ship['col'] * cell_size, player_y + ship['row'] * cell_size))
    
    # Handle cooldown
    if button_cooldown > 0:
        message_text = f"Joueur {current_player}, placez vos navires. Touche R pour pivoter."
        message_color = WHITE
        message_timer = 60
        message = fonts["small"].render(message_text, True, message_color)
        screen.blit(message, (player_x + current_board.width//2 - message.get_width()//2, 
                             player_y + current_board.height + 40))
        return message_timer, message_text, message_color, click_processed
    
    # Get current ship to place
    current_ship = None
    if game_state.current_ship_index < len(game_state.ships):
        current_ship = game_state.ships[game_state.current_ship_index]
    
    # Handle ship placement preview and interaction
    mouse_pos = pygame.mouse.get_pos()
    
    # Draw ship preview
    if current_ship and player_x <= mouse_pos[0] < player_x + current_board.width and player_y <= mouse_pos[1] < player_y + current_board.height:
        col = int((mouse_pos[0] - player_x) // cell_size)
        row = int((mouse_pos[1] - player_y) // cell_size)
        
        valid_placement = True
        if game_state.horizontal:
            if col + current_ship['size'] > 10:
                valid_placement = False
            else:
                for i in range(current_ship['size']):
                    if row < 0 or row >= 10 or col + i < 0 or col + i >= 10 or current_board.grid[row][col + i] == 'S':
                        valid_placement = False
                        break
        else:  # Vertical
            if row + current_ship['size'] > 10:
                valid_placement = False
            else:
                for i in range(current_ship['size']):
                    if row + i < 0 or row + i >= 10 or col < 0 or col >= 10 or current_board.grid[row + i][col] == 'S':
                        valid_placement = False
                        break
        
        # Draw the preview
        ship_image = ship_images.get(current_ship['name'].lower())
        if ship_image:
            scaled_image = pygame.transform.scale(ship_image, (int(cell_size * current_ship['size']), int(cell_size)))
            if valid_placement:
                if game_state.horizontal:
                    screen.blit(scaled_image, (player_x + col * cell_size, player_y + row * cell_size))
                else:
                    rotated_image = pygame.transform.rotate(scaled_image, 90)
                    screen.blit(rotated_image, (player_x + col * cell_size, player_y + row * cell_size))
            else:
                # Invalid placement overlay
                overlay = pygame.Surface((scaled_image.get_width(), scaled_image.get_height()), pygame.SRCALPHA)
                overlay.fill((255, 0, 0, 128))
                if game_state.horizontal:
                    screen.blit(scaled_image, (player_x + col * cell_size, player_y + row * cell_size))
                    screen.blit(overlay, (player_x + col * cell_size, player_y + row * cell_size))
                else:
                    rotated_image = pygame.transform.rotate(scaled_image, 90)
                    screen.blit(rotated_image, (player_x + col * cell_size, player_y + row * cell_size))
                    overlay = pygame.transform.rotate(overlay, 90)
                    screen.blit(overlay, (player_x + col * cell_size, player_y + row * cell_size))
    
    # Handle mouse clicks for placement
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r and game_state.rotation_cooldown == 0:
            game_state.horizontal = not game_state.horizontal
            game_state.rotation_cooldown = 15
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if (player_x <= mouse_pos[0] < player_x + current_board.width and 
                player_y <= mouse_pos[1] < player_y + current_board.height):
                col = int((mouse_pos[0] - player_x) // cell_size)
                row = int((mouse_pos[1] - player_y) // cell_size)
                if game_state.current_ship_index < len(game_state.ships):
                    ship = game_state.ships[game_state.current_ship_index]
                    if game_state.multiplayer.place_ship(row, col, ship['size'], game_state.horizontal):
                        game_state.current_ship_index += 1
                        
                        # Check if all ships are placed for current player
                        if game_state.current_ship_index >= len(game_state.ships):
                            # Reset for next player or game phase
                            game_state.current_ship_index = 0
                            
                            # If we're no longer in placement phase, move to game
                            if not game_state.multiplayer.placement_phase:
                                game_state.multiplayer.transition_screen = True
                                game_state.multiplayer.transition_timer = 180  # 3 secondes à 60 FPS
                                game_state.multiplayer.transition_message = "La partie va commencer !"
                                
                                def start_game_after_transition():
                                    game_state.state = GameState.GAME
                                    nonlocal message_timer, message_text, click_processed
                                    message_timer = 0
                                    message_text = ""
                                    click_processed = False
                                    button_cooldown = 60
                                
                                game_state.multiplayer.start_game_callback = start_game_after_transition
    
    return message_timer, message_text, message_color, click_processed