import pygame
import sys
import os
import pygame.mixer

# Make sure the current directory is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules
from src.game_state import GameState
from src.animations import EffectsManager
from src.ui.screens import draw_main_menu, draw_ship_selection, draw_game_end
from src.ui.grid import draw_grid
from src.utils.constants import WHITE, GRAY, GREEN, RED, FPS
from src.utils.helpers import initialize_fonts, load_assets
from src.board import Board

# Initialize pygame
pygame.init()

# Initialize mixer for music
pygame.mixer.init()

# After pygame.init() and mixer initialization
# Add these variables
music_muted = False
mute_button_rect = pygame.Rect(10, 10, 100, 30)  # Position and size of mute button

# Load and start background music
def initialize_music():
    global music_muted
    try:
        music_path = os.path.join(os.path.dirname(__file__), '..', 'SFX', 'background.mp3')
        print(f"Loading music from: {music_path}")  # Debug print
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(0.5)
        if not music_muted:
            pygame.mixer.music.play(-1)
    except Exception as e:
        print(f"Error loading music: {e}")
        print(f"Current working directory: {os.getcwd()}")  # Debug print

def toggle_music():
    global music_muted
    music_muted = not music_muted
    if music_muted:
        pygame.mixer.music.pause()
    else:
        pygame.mixer.music.unpause()

# Initialize music
initialize_music()  # Add this line here

# Get screen resolution
resolution = [pygame.display.Info().current_w, pygame.display.Info().current_h - 72]
screen = pygame.display.set_mode((resolution[0], resolution[1]))
pygame.display.set_caption("Bataille navale")

# Load assets
assets = load_assets(resolution)
background = assets["background"]
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
    
    # Determine which player's board to show
    active_board = game_state.player_board if game_state.current_placing_player == 1 else game_state.player2_board
    player_text = f"Placement du Joueur {game_state.current_placing_player}" if game_state.game_mode == game_state.MULTIPLAYER else "Placement de vos navires"
    player_label = fonts["large"].render(player_text, True, WHITE)
    screen.blit(player_label, (resolution[0] // 2 - player_label.get_width() // 2, 50))
    
    # Draw the active player's grid in the center
    player_x, player_y = draw_grid(screen, active_board, fonts, reveal=True, 
                                  is_player_grid=True, position="center")
    
    if button_cooldown > 0:
        if message_timer > 0:
            message = fonts["small"].render(message_text, True, message_color)
            screen.blit(message, (player_x, player_y + active_board.height + 20))
        return
    
    current_events = pygame.event.get()
    
    for event in current_events:
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and game_state.rotation_cooldown == 0:
                game_state.horizontal = not game_state.horizontal
                game_state.rotation_cooldown = 15
                message_text = f"Rotation: {'Horizontale' if game_state.horizontal else 'Verticale'}"
                message_color = WHITE
                message_timer = 60
                
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            
            cell_size = active_board.width / len(active_board.grid[0])
            
            if (player_x <= mouse_pos[0] < player_x + active_board.width and 
                player_y <= mouse_pos[1] < player_y + active_board.height):
                
                col = int((mouse_pos[0] - player_x) // cell_size)
                row = int((mouse_pos[1] - player_y) // cell_size)
                
                if game_state.current_ship_index < len(game_state.ships):
                    ship = game_state.ships[game_state.current_ship_index]
                    if game_state.place_player_ship(row, col, ship['size'], game_state.horizontal):
                        message_text = f"{ship['name']} placé!"
                        message_color = GREEN
                        message_timer = 60
                        
                        game_state.current_ship_index += 1
                        if game_state.current_ship_index >= len(game_state.ships):
                            if game_state.game_mode == game_state.MULTIPLAYER and game_state.current_placing_player == 1:
                                game_state.current_placing_player = 2
                                game_state.current_ship_index = 0
                                message_text = "Tour du Joueur 2 pour placer les navires"
                                message_color = GREEN
                                message_timer = 90
                                button_cooldown = 90
                            else:
                                message_text = "Tous les navires sont placés! La partie commence..."
                                message_color = GREEN
                                message_timer = 90
                                button_cooldown = 90
                                game_state.state = game_state.GAME
    
    if game_state.rotation_cooldown > 0:
        game_state.rotation_cooldown -= 1
    
    if message_timer > 0:
        message = fonts["small"].render(message_text, True, message_color)
        screen.blit(message, (player_x, player_y + active_board.height + 20))

def handle_game():
    """Handle the game phase (player turns, computer turns)"""
    global message_timer, message_text, message_color, waiting_for_action, button_cooldown
    
    if button_cooldown > 0:
        if game_state.game_mode == game_state.SINGLE_PLAYER:
            player_x, player_y = draw_grid(screen, game_state.player_board, fonts, reveal=True, 
                                         is_player_grid=True, position="left")
            comp_x, comp_y = draw_grid(screen, game_state.computer_board, fonts, reveal=False, 
                                      is_player_grid=False, position="right")
            max_y = max(player_y, comp_y)
        else:
            player1_x, player1_y = draw_grid(screen, game_state.player_board, fonts, reveal=game_state.current_attacking_player == 1, 
                                            is_player_grid=True, position="left")
            player2_x, player2_y = draw_grid(screen, game_state.player2_board, fonts, reveal=game_state.current_attacking_player == 2, 
                                            is_player_grid=True, position="right")
            max_y = max(player1_y, player2_y)
        
        message = fonts["small"].render(message_text, True, message_color)
        screen.blit(message, (resolution[0] // 2 - message.get_width() // 2, 
                              max_y + game_state.player_board.height + 20))
        return
    
    events = pygame.event.get([pygame.MOUSEBUTTONDOWN])
    
    if game_state.game_mode == game_state.SINGLE_PLAYER:
        player_x, player_y = draw_grid(screen, game_state.player_board, fonts, reveal=True, 
                                     is_player_grid=True, position="left")
        comp_x, comp_y = draw_grid(screen, game_state.computer_board, fonts, assets, reveal=False, 
                                  is_player_grid=False, position="right")
        
        if game_state.player_turn:
            turn_indicator = fonts["small"].render("Votre tour ←", True, GREEN)
            indicator_x = comp_x + game_state.computer_board.width - turn_indicator.get_width()
            screen.blit(turn_indicator, (indicator_x - 20, comp_y - 50))  # Changed from -60 to -50
            
            instructions = fonts["small"].render("Cliquez ici pour attaquer", True, WHITE)
            instructions_x = comp_x + (game_state.computer_board.width // 2) - (instructions.get_width() // 2)
            screen.blit(instructions, (instructions_x, comp_y - 25))  # Changed from -30 to -25
            
            if message_timer > 0:
                message = fonts["small"].render(message_text, True, message_color)
                screen.blit(message, (resolution[0] // 2 - message.get_width() // 2, 
                                    max(player_y, comp_y) + game_state.player_board.height + 30))  # Increased from 20 to 30
                return
            
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = event.pos
                    
                    cell_size = game_state.computer_board.width / len(game_state.computer_board.grid[0])
                    
                    if (comp_x <= mouse_pos[0] < comp_x + game_state.computer_board.width and 
                        comp_y <= mouse_pos[1] < comp_y + game_state.computer_board.height):
                        
                        col = int((mouse_pos[0] - comp_x) // cell_size)
                        row = int((mouse_pos[1] - comp_y) // cell_size)
                        
                        if game_state.computer_board.view[row][col] == '.':
                            hit = game_state.player_attack(row, col)
                            
                            effect_x = comp_x + col * cell_size + cell_size / 2
                            effect_y = comp_y + row * cell_size + cell_size / 2
                            
                            if hit:
                                effects_manager.create_hit_effect(effect_x, effect_y)
                                # Adjust position of hit message (moved down by 5px)
                                effects_manager.create_animated_message(
                                    "TOUCHÉ!", RED, 
                                    comp_x + game_state.computer_board.width // 2,
                                    comp_y + game_state.computer_board.height + 45,  # Changed from 40 to 45
                                    duration=90
                                )
                                
                                message_text = "Vous rejouez"
                                message_color = WHITE
                                message_timer = 75
                                
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
                                # Adjust position of miss message (moved down by 5px)
                                effects_manager.create_animated_message(
                                    "MANQUÉ!", WHITE, 
                                    comp_x + game_state.computer_board.width // 2,
                                    comp_y + game_state.computer_board.height + 45,  # Changed from 40 to 45
                                    duration=90
                                )
                                
                                message_timer = 90
                                game_state.player_turn = False
                                effects_manager.start_turn_transition(resolution, False, GREEN, RED)
        
        else:
            turn_indicator = fonts["small"].render("→ Tour de l'ordinateur", True, RED)
            screen.blit(turn_indicator, (player_x - 20, player_y - 60))
            
            instructions = fonts["small"].render("L'ordinateur attaque ici", True, WHITE)
            instructions_x = player_x + (game_state.player_board.width // 2) - (instructions.get_width() // 2)
            screen.blit(instructions, (instructions_x, player_y - 25))  # Changed from -30 to -25
            
            if message_timer > 0:
                message = fonts["small"].render(message_text, True, message_color)
                screen.blit(message, (resolution[0] // 2 - message.get_width() // 2, 
                                    max(player_y, comp_y) + game_state.player_board.height + 30))  # Increased from 20 to 30
                return
            
            if not waiting_for_action:
                message_text = "L'ordinateur réfléchit..."
                message_color = WHITE
                message_timer = 90
                waiting_for_action = True
                
                for i in range(3):
                    effects_manager.create_animated_message(
                        "⏳", WHITE, 
                        player_x + game_state.player_board.width // 2 + i*30 - 30, 
                        player_y - 90,
                        duration=90
                    )
                return
            
            waiting_for_action = False
            
            try:
                row, col, hit = game_state.computer_attack()
                
                if row is not None:
                    cell_size = game_state.player_board.width / len(game_state.player_board.grid[0])
                    effect_x = player_x + col * cell_size + cell_size / 2
                    effect_y = player_y + row * cell_size + cell_size / 2
                    
                    if hit:
                        effects_manager.create_hit_effect(effect_x, effect_y)
                        # Adjust position of hit message (moved down by 5px)
                        effects_manager.create_animated_message(
                            "TOUCHÉ!", RED, 
                            player_x + game_state.player_board.width // 2,
                            player_y + game_state.player_board.height + 45,  # Changed from 40 to 45
                            duration=90
                        )
                        
                        message_text = "L'ordinateur rejoue"
                        message_color = WHITE
                        message_timer = 90
                        
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
                        # Adjust position of miss message (moved down by 5px)
                        effects_manager.create_animated_message(
                            "MANQUÉ!", WHITE, 
                            player_x + game_state.player_board.width // 2,
                            player_y + game_state.player_board.height + 45,  # Changed from 40 to 45
                            duration=90
                        )
                        
                        message_text = "Votre tour"
                        message_color = WHITE
                        message_timer = 75
                        game_state.player_turn = True
                        effects_manager.start_turn_transition(resolution, True, GREEN, RED)
                else:
                    message_text = "Aucun coup possible - Votre tour"
                    message_color = WHITE
                    message_timer = 40
                    game_state.player_turn = True
                    effects_manager.start_turn_transition(resolution, True, GREEN, RED)
            except Exception as e:
                print(f"Erreur pendant le tour de l'ordinateur: {e}")
                message_text = "Erreur IA - Votre tour"
                message_color = RED
                message_timer = 90
                game_state.player_turn = True
                effects_manager.start_turn_transition(resolution, True, GREEN, RED)
    
    else:
        # Multiplayer mode
        player1_x, player1_y = draw_grid(screen, game_state.player_board, fonts, reveal=game_state.current_attacking_player == 1, 
                                        is_player_grid=True, position="left")
        player2_x, player2_y = draw_grid(screen, game_state.player2_board, fonts, reveal=game_state.current_attacking_player == 2, 
                                        is_player_grid=True, position="right")
        
        active_player = game_state.current_attacking_player
        opponent_board = game_state.player2_board if active_player == 1 else game_state.player_board
        opponent_x, opponent_y = (player2_x, player2_y) if active_player == 1 else (player1_x, player1_y)
        
        turn_indicator = fonts["small"].render(f"Tour du Joueur {active_player} ←", True, GREEN if active_player == 1 else RED)
        indicator_x = opponent_x + opponent_board.width - turn_indicator.get_width()
        screen.blit(turn_indicator, (indicator_x - 20, opponent_y - 60))
        
        instructions = fonts["small"].render("Cliquez ici pour attaquer", True, WHITE)
        instructions_x = opponent_x + (opponent_board.width // 2) - (instructions.get_width() // 2)
        screen.blit(instructions, (instructions_x, opponent_y - 30))
        
        if message_timer > 0:
            message = fonts["small"].render(message_text, True, message_color)
            screen.blit(message, (resolution[0] // 2 - message.get_width() // 2, 
                                max(player1_y, player2_y) + game_state.player_board.height + 20))
            return
        
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                
                cell_size = opponent_board.width / len(opponent_board.grid[0])
                
                if (opponent_x <= mouse_pos[0] < opponent_x + opponent_board.width and 
                    opponent_y <= mouse_pos[1] < opponent_y + opponent_board.height):
                    
                    col = int((mouse_pos[0] - opponent_x) // cell_size)
                    row = int((mouse_pos[1] - opponent_y) // cell_size)
                    
                    if opponent_board.view[row][col] == '.':
                        hit = game_state.player_attack(row, col)
                        
                        effect_x = opponent_x + col * cell_size + cell_size / 2
                        effect_y = opponent_y + row * cell_size + cell_size / 2
                        
                        if hit:
                            effects_manager.create_hit_effect(effect_x, effect_y)
                            effects_manager.create_animated_message(
                                "TOUCHÉ!", RED, 
                                opponent_x + opponent_board.width // 2,
                                opponent_y + opponent_board.height + 40, 
                                duration=90
                            )
                            
                            message_text = f"Joueur {active_player} rejoue"
                            message_color = WHITE
                            message_timer = 75
                            
                            if game_state.winner is not None:
                                effects_manager.create_animated_message(
                                    f"VICTOIRE JOUEUR {active_player}!", GREEN, 
                                    resolution[0] // 2, 
                                    resolution[1] // 2, 
                                    duration=180
                                )
                                return
                        else:
                            effects_manager.create_miss_effect(effect_x, effect_y)
                            effects_manager.create_animated_message(
                                "MANQUÉ!", WHITE, 
                                opponent_x + opponent_board.width // 2,
                                opponent_y + opponent_board.height + 40, 
                                duration=90
                            )
                            
                            message_text = f"Tour du Joueur {2 if active_player == 1 else 1}"
                            message_color = WHITE
                            message_timer = 75
                            game_state.current_attacking_player = 2 if active_player == 1 else 1
                            effects_manager.start_turn_transition(resolution, active_player == 2, GREEN, RED)

# Main game loop
running = True
clock = pygame.time.Clock()
recently_changed_state = False
previous_state = None

while running:
    for event in pygame.event.get([pygame.QUIT]):
        if event.type == pygame.QUIT:
            running = False
    
    screen.fill(GRAY)
    
    if button_cooldown > 0:
        button_cooldown -= 1
    
    if message_timer > 0:
        message_timer -= 1
    
    if previous_state != game_state.state:
        previous_state = game_state.state
        recently_changed_state = True
        button_cooldown = 60
        
        if game_state.state == game_state.GAME:
            message_text = ""
            message_timer = 0
            waiting_for_action = False
    
    if game_state.state == game_state.MENU:
        result = draw_main_menu(screen, game_state, fonts, background, button_cooldown)
        if result and not recently_changed_state:
            recently_changed_state = True
    elif game_state.state == game_state.PLACEMENT:
        handle_placement()
        recently_changed_state = False
    elif game_state.state == game_state.GAME:
        handle_game()
        recently_changed_state = False
    elif game_state.state == game_state.END:
        draw_game_end(screen, game_state.winner, fonts, game_state.restart_game)
        recently_changed_state = False
    
    effects_manager.update_effects(screen)
    effects_manager.update_animated_messages(screen)
    
    # Draw mute button
    pygame.draw.rect(screen, WHITE if not music_muted else RED, mute_button_rect)
    mute_text = fonts["small"].render("🔊 ON" if not music_muted else "🔇 OFF", True, GRAY)
    text_rect = mute_text.get_rect(center=mute_button_rect.center)
    screen.blit(mute_text, text_rect)

    # Handle mute button clicks
    for event in pygame.event.get([pygame.MOUSEBUTTONDOWN]):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if mute_button_rect.collidepoint(event.pos):
                toggle_music()
    
    pygame.display.flip()
    clock.tick(FPS)

pygame.mixer.music.stop()  # Stop music before quitting
pygame.quit()
sys.exit()