import pygame
import sys
import os

# Make sure the current directory is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules
from src.game_state import GameState
from src.animations import EffectsManager
from src.ui.screens import draw_main_menu, draw_ship_selection, draw_game_end
from src.ui.grid import draw_grid
from src.utils.constants import WHITE, GRAY, GREEN, RED, FPS
from src.utils.helpers import load_background, initialize_fonts

# Initialize pygame
pygame.init()

# Get screen resolution
resolution = [pygame.display.Info().current_w, pygame.display.Info().current_h - 72]
screen = pygame.display.set_mode((resolution[0], resolution[1]))
pygame.display.set_caption("Bataille navale")

# Load assets
background = load_background(resolution)
fonts = initialize_fonts()

# Initialize game state
game_state = GameState(resolution)

# Initialize effects manager
effects_manager = EffectsManager()

# Game variables
button_cooldown = 0
message_timer = 0
message_text = ""
message_color = WHITE
waiting_for_action = False

def handle_placement():
    """Handle the ship placement phase"""
    global button_cooldown, message_text, message_color, message_timer
    
    # Draw ship selection
    draw_ship_selection(screen, game_state, fonts)
    
    # Draw only player's grid in the center during placement
    player_x, player_y = draw_grid(screen, game_state.player_board, fonts, reveal=True, 
                                  is_player_grid=True, position="center")
    
    # Set a cooldown when entering placement state to prevent accidental clicks
    if button_cooldown > 0:
        # Show the message if needed
        if message_timer > 0:
            message = fonts["small"].render(message_text, True, message_color)
            screen.blit(message, (player_x, player_y + game_state.player_board.height + 20))
        return
    
    # Stocker les événements dans une variable locale pour éviter de les traiter plusieurs fois
    current_events = pygame.event.get()
    
    # Process events directly to fix input issues
    for event in current_events:
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
        # Handle key presses for rotation
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and game_state.rotation_cooldown == 0:
                game_state.horizontal = not game_state.horizontal
                game_state.rotation_cooldown = 15  # frames of cooldown
                # Show rotation message
                message_text = f"Rotation: {'Horizontale' if game_state.horizontal else 'Verticale'}"
                message_color = WHITE
                message_timer = 60
                
        # Handle mouse clicks for placement
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click
            mouse_pos = pygame.mouse.get_pos()
            
            cell_size = game_state.player_board.width / len(game_state.player_board.grid[0])
            
            if (player_x <= mouse_pos[0] < player_x + game_state.player_board.width and 
                player_y <= mouse_pos[1] < player_y + game_state.player_board.height):
                
                col = int((mouse_pos[0] - player_x) // cell_size)
                row = int((mouse_pos[1] - player_y) // cell_size)
                
                if game_state.current_ship_index < len(game_state.ships):
                    ship = game_state.ships[game_state.current_ship_index]
                    if game_state.place_player_ship(row, col, ship['size'], game_state.horizontal):
                        # Show placement success message
                        message_text = f"{ship['name']} placé!"
                        message_color = GREEN
                        message_timer = 60
                        
                        game_state.current_ship_index += 1
                        if game_state.current_ship_index >= len(game_state.ships):
                            # Add a delay and display a transition message
                            message_text = "Tous les navires sont placés! La partie commence..."
                            message_color = GREEN
                            message_timer = 60  # About 1.5 seconds at 60 FPS
                            button_cooldown = 90  # Same duration as message
                            # Change state after displaying message 
                            game_state.state = GameState.GAME
    
    # Handle ship rotation cooldown
    if game_state.rotation_cooldown > 0:
        game_state.rotation_cooldown -= 1
    
    # Display any active messages
    if message_timer > 0:
        message = fonts["small"].render(message_text, True, message_color)
        screen.blit(message, (player_x, player_y + game_state.player_board.height + 20))

def handle_game():
    """Handle the game phase (player turns, computer turns)"""
    global message_timer, message_text, message_color, waiting_for_action, button_cooldown
    
    # If we're in a cooldown period (transitioning from placement), show message but don't process game logic
    if button_cooldown > 0:
        # Draw both grids side by side
        player_x, player_y = draw_grid(screen, game_state.player_board, fonts, reveal=True, 
                                     is_player_grid=True, position="left")
        comp_x, comp_y = draw_grid(screen, game_state.computer_board, fonts, reveal=False, 
                                  is_player_grid=False, position="right")
        
        # Show transition message
        message = fonts["small"].render(message_text, True, message_color)
        screen.blit(message, (resolution[0] // 2 - message.get_width() // 2, 
                              max(player_y, comp_y) + game_state.player_board.height + 20))
        return
    
    # Handle game events
    events = pygame.event.get([pygame.MOUSEBUTTONDOWN])
    
    # In single player mode
    if game_state.game_mode == GameState.SINGLE_PLAYER:
        # Always draw both grids
        player_x, player_y = draw_grid(screen, game_state.player_board, fonts, reveal=True, 
                                     is_player_grid=True, position="left")
        comp_x, comp_y = draw_grid(screen, game_state.computer_board, fonts, reveal=False, 
                                  is_player_grid=False, position="right")
        
        # Player's turn
        if game_state.player_turn:
            # Highlight active grid with indicator - MOVED TO THE RIGHT
            turn_indicator = fonts["small"].render("Votre tour ←", True, GREEN)
            # Position the text to the right of the computer grid
            indicator_x = comp_x + game_state.computer_board.width - turn_indicator.get_width()
            screen.blit(turn_indicator, (indicator_x - 20, comp_y - 60))
            
            # Instructions - MOVED TO THE RIGHT
            instructions = fonts["small"].render("Cliquez ici pour attaquer", True, WHITE)
            # Position the text centered on the computer grid
            instructions_x = comp_x + (game_state.computer_board.width // 2) - (instructions.get_width() // 2)
            screen.blit(instructions, (instructions_x, comp_y - 30))
            
            # If a message is being displayed
            if message_timer > 0:
                message = fonts["small"].render(message_text, True, message_color)
                screen.blit(message, (resolution[0] // 2 - message.get_width() // 2, 
                                    max(player_y, comp_y) + game_state.player_board.height + 20))
                return
            
            # Process player click events
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = event.pos
                    
                    cell_size = game_state.computer_board.width / len(game_state.computer_board.grid[0])
                    
                    if (comp_x <= mouse_pos[0] < comp_x + game_state.computer_board.width and 
                        comp_y <= mouse_pos[1] < comp_y + game_state.computer_board.height):
                        
                        col = int((mouse_pos[0] - comp_x) // cell_size)
                        row = int((mouse_pos[1] - comp_y) // cell_size)
                        
                        if game_state.computer_board.view[row][col] == '.':
                            # Player attacks
                            hit = game_state.player_attack(row, col)
                            
                            # Add visual effect
                            effect_x = comp_x + col * cell_size + cell_size / 2
                            effect_y = comp_y + row * cell_size + cell_size / 2
                            
                            if hit:
                                effects_manager.create_hit_effect(effect_x, effect_y)
                                effects_manager.create_animated_message(
                                    "TOUCHÉ!", RED, 
                                    comp_x + game_state.computer_board.width // 2,
                                    comp_y + game_state.computer_board.height + 40, 
                                    duration=90
                                )
                                
                                message_text = "Vous rejouez"
                                message_color = WHITE
                                message_timer = 75
                                
                                # Check game end
                                if game_state.winner is not None:
                                    effects_manager.create_animated_message(
                                        "VICTOIRE!", GREEN, 
                                        resolution[0] // 2, 
                                        resolution[1] // 2, 
                                        duration=180
                                    )
                                    return
                            else:
                                effects_manager.create_miss_effect(effect_x, effect_y)
                                effects_manager.create_animated_message(
                                    "MANQUÉ!", WHITE, 
                                    comp_x + game_state.computer_board.width // 2,
                                    comp_y + game_state.computer_board.height + 40, 
                                    duration=90
                                )
                                
                                message_timer = 90
                                game_state.player_turn = False
        
        # Computer's turn
        else:
            # Highlight active grid with indicator - MOVED TO THE LEFT
            turn_indicator = fonts["small"].render("→ Tour de l'ordinateur", True, RED)
            screen.blit(turn_indicator, (player_x - 20, player_y - 60))
            
            # Add instructions for computer's turn
            instructions = fonts["small"].render("L'ordinateur attaque ici", True, WHITE)
            # Position the text centered on the player grid
            instructions_x = player_x + (game_state.player_board.width // 2) - (instructions.get_width() // 2)
            screen.blit(instructions, (instructions_x, player_y - 30))
            
            # If a message is being displayed
            if message_timer > 0:
                message = fonts["small"].render(message_text, True, message_color)
                screen.blit(message, (resolution[0] // 2 - message.get_width() // 2, 
                                    max(player_y, comp_y) + game_state.player_board.height + 20))
                return
            
            # Computer's turn logic
            if not waiting_for_action:
                # Show that the computer is thinking
                message_text = "L'ordinateur réfléchit..."
                message_color = WHITE
                message_timer = 90
                waiting_for_action = True
                
                # Add a "thinking" animation
                for i in range(3):
                    effects_manager.create_animated_message(
                        "⏳", WHITE, 
                        player_x + game_state.player_board.width // 2 + i*30 - 30, 
                        player_y - 90,
                        duration=90
                    )
                return
            
            # Reset waiting state
            waiting_for_action = False
            
            # Computer makes a move
            try:
                row, col, hit = game_state.computer_attack()
                
                if row is not None:
                    # Add visual effect
                    cell_size = game_state.player_board.width / len(game_state.player_board.grid[0])
                    effect_x = player_x + col * cell_size + cell_size / 2
                    effect_y = player_y + row * cell_size + cell_size / 2
                    
                    if hit:
                        effects_manager.create_hit_effect(effect_x, effect_y)
                        effects_manager.create_animated_message(
                            "TOUCHÉ!", RED, 
                            player_x + game_state.player_board.width // 2,
                            player_y + game_state.player_board.height + 40, 
                            duration=90
                        )
                        
                        message_text = "L'ordinateur rejoue"
                        message_color = WHITE
                        message_timer = 90
                        
                        # Check game end
                        if game_state.winner is not None:
                            effects_manager.create_animated_message(
                                "DÉFAITE!", RED, 
                                resolution[0] // 2, 
                                resolution[1] // 2, 
                                duration=180
                            )
                            return
                    else:
                        effects_manager.create_miss_effect(effect_x, effect_y)
                        effects_manager.create_animated_message(
                            "MANQUÉ!", WHITE, 
                            player_x + game_state.player_board.width // 2,
                            player_y + game_state.player_board.height + 40, 
                            duration=90
                        )
                        
                        message_text = "Votre tour"
                        message_color = WHITE
                        message_timer = 75
                        game_state.player_turn = True
                else:
                    # If no valid moves found
                    message_text = "Aucun coup possible - Votre tour"
                    message_color = WHITE
                    message_timer = 40
                    game_state.player_turn = True
            except Exception as e:
                print(f"Erreur pendant le tour de l'ordinateur: {e}")
                # In case of error, give turn to player
                message_text = "Erreur IA - Votre tour"
                message_color = RED
                message_timer = 40
                game_state.player_turn = True

    # Multiplayer mode (not fully implemented)
    else:
        # Placeholder UI for multiplayer
        multiplayer_text = fonts["large"].render("Mode multijoueur pas encore implémenté", True, WHITE)
        screen.blit(multiplayer_text, (resolution[0] // 2 - multiplayer_text.get_width() // 2, resolution[1] // 2))

# Main game loop
running = True
clock = pygame.time.Clock()
# Variable pour suivre si on vient de changer d'état
recently_changed_state = False
previous_state = None

while running:
    # Only handle quit events in the main loop
    for event in pygame.event.get([pygame.QUIT]):
        if event.type == pygame.QUIT:
            running = False
    
    # Clear screen
    screen.fill(GRAY)
    
    # Update timers
    if button_cooldown > 0:
        button_cooldown -= 1
    
    if message_timer > 0:
        message_timer -= 1
    
    # Vérifier si l'état a changé
    if previous_state != game_state.state:
        previous_state = game_state.state
        recently_changed_state = True
        # Force un cooldown long lors du changement d'état pour éviter les clics automatiques
        button_cooldown = 60  # Assez long pour éviter le clic automatique
        
        # Reset message when changing states to avoid old messages carrying over
        if game_state.state == GameState.GAME:
            message_text = ""
            message_timer = 0
            waiting_for_action = False
    
    # Handle game state
    if game_state.state == GameState.MENU:
        # Transmet le statut de changement d'état récent à la fonction du menu
        result = draw_main_menu(screen, game_state, fonts, background, button_cooldown)
        # Si on a appuyé sur start et qu'on change d'état, réinitialiser la variable
        if result and recently_changed_state == False:
            recently_changed_state = True
    elif game_state.state == GameState.PLACEMENT:
        handle_placement()
        # Après avoir traité l'état de placement, réinitialiser le statut de changement
        recently_changed_state = False
    elif game_state.state == GameState.GAME:
        handle_game()
        recently_changed_state = False
    elif game_state.state == GameState.END:
        draw_game_end(screen, game_state.winner, fonts, game_state.restart_game)
        recently_changed_state = False
    
    # Update effects
    effects_manager.update_effects(screen)
    effects_manager.update_animated_messages(screen)
    
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()