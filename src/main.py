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

# Get screen resolution first
resolution = [pygame.display.Info().current_w, pygame.display.Info().current_h - 72]

# After pygame.init() and mixer initialization
# Add these variables
music_muted = False
mute_button_rect = pygame.Rect(10, 10, 100, 30)  # Position and size of mute button

# Add these near your other global variables
last_click_pos = None
click_processed = False

# Now initialize game state after resolution is defined
game_state = GameState(resolution)

# Initialize display
screen = pygame.display.set_mode((resolution[0], resolution[1]))
pygame.display.set_caption("Bataille navale")

# Load and start background music
def initialize_music():
    global music_muted
    try:
        # Load all music files
        game_music_path = os.path.join(os.path.dirname(__file__), '..', 'SFX', 'background.mp3')
        menu_music_path = os.path.join(os.path.dirname(__file__), '..', 'SFX', 'menu.mp3')
        victory_music_path = os.path.join(os.path.dirname(__file__), '..', 'SFX', 'Victory-music.mp3')
        
        # Store paths for later use
        game_state.menu_music = menu_music_path
        game_state.game_music = game_music_path
        game_state.victory_music = victory_music_path
        
        # Start with menu music
        pygame.mixer.music.load(menu_music_path)
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

def change_music(music_path):
    global music_muted
    try:
        pygame.mixer.music.fadeout(1000)  # Fade out current music
        pygame.time.wait(1000)  # Wait for fadeout
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(0.5)
        
        if not music_muted:
            # Play victory music just once if it's the victory music
            if music_path == game_state.victory_music:
                pygame.mixer.music.play(0)  # The 0 means play once and stop
            else:
                pygame.mixer.music.play(-1)  # -1 means loop indefinitely
                
    except Exception as e:
        print(f"Error changing music: {e}")

# Initialize music after game_state is created
initialize_music()

# Load assets
assets = load_assets(resolution)
background = assets["background"]
fonts = initialize_fonts()

def load_ship_images():
    """Load ship images from the assets/ships directory."""
    ship_images = {}
    ships_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'ships')
    for ship_name in os.listdir(ships_path):
        if ship_name.endswith('.png'):
            ship_key = os.path.splitext(ship_name)[0]  # Remove file extension
            ship_images[ship_key] = pygame.image.load(os.path.join(ships_path, ship_name)).convert_alpha()
    return ship_images

# Charger les images des bateaux après avoir chargé les assets
ship_images = load_ship_images()

# Initialize effects manager
effects_manager = EffectsManager()

# Ajouter après l'initialisation de effects_manager (ligne 116 environ)
def create_hit_effect(self, x, y):
    """Create a hit effect at the specified position"""
    self.create_fire_animation(x, y, 40)  # Fixed size for fire effect

# Attacher la méthode à l'instance EffectsManager
effects_manager.create_hit_effect = create_hit_effect.__get__(effects_manager)

# Game variables
button_cooldown = 0
message_timer = 0
message_text = ""
message_color = WHITE
waiting_for_action = False

def handle_placement():
    """Handle the ship placement phase"""
    global button_cooldown, message_text, message_color, message_timer
    
    # Draw the gameplay background first
    if "gameplay_background" in assets:
        screen.blit(assets["gameplay_background"], (0, 0))
    
    # Draw ship selection
    draw_ship_selection(screen, game_state, fonts)
    
    # Draw only player's grid in the center during placement
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
        return
    
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

def handle_multiplayer_placement():
    """Handle ship placement for multiplayer"""
    global button_cooldown, message_text, message_color, message_timer
    
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
        privacy = fonts["small"].render("Passez le contrôle à l'autre joueur", True, WHITE)
        privacy_rect = privacy.get_rect(center=(resolution[0]//2, resolution[1]//2 + 80))
        screen.blit(privacy, privacy_rect)
        
        # Important: Process events here to continue counting down even during transition
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        # Skip the rest of the function so no boards are drawn during transition
        return
    
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
    draw_ship_selection(screen, game_state, fonts)
    
    # Draw player's grid in the center
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
        return
    
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
                                game_state.state = GameState.GAME

def handle_multiplayer_game():
    """Handle the multiplayer game phase"""
    global message_timer, message_text, message_color, waiting_for_action, button_cooldown, click_processed
    
    # Draw the gameplay background
    if "gameplay_background" in assets:
        screen.blit(assets["gameplay_background"], (0, 0))
    
    # Get current player info
    current_player = game_state.multiplayer.current_player
    current_board = game_state.multiplayer.get_current_board()
    opponent_board = game_state.multiplayer.get_opponent_board()
    
    # Draw title showing both players, with current player highlighted
    player1_color = GREEN if current_player == 1 else WHITE
    player2_color = RED if current_player == 2 else WHITE
    
    # Draw player titles
    title1 = fonts["medium"].render("Joueur 1", True, player1_color)
    title2 = fonts["medium"].render("Joueur 2", True, player2_color)
    
    # Calculate positions for titles (left and right boards)
    player1_title_x = resolution[0] // 4 - title1.get_width() // 2
    player2_title_x = (resolution[0] * 3) // 4 - title2.get_width() // 2
    
    # Draw titles
    screen.blit(title1, (player1_title_x, 10))
    screen.blit(title2, (player2_title_x, 10))
    
    # Draw main turn indicator
    # turn_text = fonts["large"].render(f"Tour du Joueur {current_player}", True, GREEN if current_player == 1 else RED)
    # screen.blit(turn_text, (resolution[0]//2 - turn_text.get_width()//2, 60))
    
    # Draw both player boards side by side (always in the same position)
    player1_x, player1_y = draw_grid(screen, game_state.multiplayer.player1_board, fonts, assets, 
                                    reveal=True, is_player_grid=True, position="left")
    player2_x, player2_y = draw_grid(screen, game_state.multiplayer.player2_board, fonts, assets, 
                                    reveal=True, is_player_grid=False, position="right")
    
    # Draw ships on player 1's board
    cell_size_p1 = game_state.multiplayer.player1_board.width / len(game_state.multiplayer.player1_board.grid[0])
    for ship in game_state.multiplayer.player1_ships:
        ship_image = ship_images.get(ship['name'].lower())
        if ship_image:
            scaled_image = pygame.transform.scale(ship_image, (int(cell_size_p1 * ship['size']), int(cell_size_p1)))
            if ship['horizontal']:
                screen.blit(scaled_image, (player1_x + ship['col'] * cell_size_p1, player1_y + ship['row'] * cell_size_p1))
            else:
                rotated_image = pygame.transform.rotate(scaled_image, 90)
                screen.blit(rotated_image, (player1_x + ship['col'] * cell_size_p1, player1_y + ship['row'] * cell_size_p1))
    
    # Draw ships on player 2's board
    cell_size_p2 = game_state.multiplayer.player2_board.width / len(game_state.multiplayer.player2_board.grid[0])
    for ship in game_state.multiplayer.player2_ships:
        ship_image = ship_images.get(ship['name'].lower())
        if ship_image:
            scaled_image = pygame.transform.scale(ship_image, (int(cell_size_p2 * ship['size']), int(cell_size_p2)))
            if ship['horizontal']:
                screen.blit(scaled_image, (player2_x + ship['col'] * cell_size_p2, player2_y + ship['row'] * cell_size_p2))
            else:
                rotated_image = pygame.transform.rotate(scaled_image, 90)
                screen.blit(rotated_image, (player2_x + ship['col'] * cell_size_p2, player2_y + ship['row'] * cell_size_p2))
    
    # # Clear existing animations to prevent buildup
    # effects_manager.fire_animations.clear()
    # if hasattr(effects_manager, 'water_animations'):
    #     effects_manager.water_animations.clear()
    
    # Render hits and misses on both boards
    for row in range(len(game_state.multiplayer.player1_board.grid)):
        for col in range(len(game_state.multiplayer.player1_board.grid[row])):
            cell_value = game_state.multiplayer.player1_board.view[row][col]
            cell_x = player1_x + col * cell_size_p1
            cell_y = player1_y + row * cell_size_p1
            
            if cell_value == 'X':  # Case touchée
                # Vérifier si une animation n'existe pas déjà à cette position
                if not any(fire.x == cell_x and fire.y == cell_y for fire in effects_manager.fire_animations):
                    effects_manager.create_fire_animation(cell_x, cell_y, int(cell_size_p1))
            elif cell_value == 'O':  # Case manquée
                # Vérifier si une animation d'eau n'existe pas déjà
                if not hasattr(effects_manager, 'water_animations') or not any(water.x == cell_x and water.y == cell_y for water in effects_manager.water_animations):
                    effects_manager.create_water_animation(cell_x, cell_y, int(cell_size_p1))
    
    for row in range(len(game_state.multiplayer.player2_board.grid)):
        for col in range(len(game_state.multiplayer.player2_board.grid[row])):
            cell_value = game_state.multiplayer.player2_board.view[row][col]
            cell_x = player2_x + col * cell_size_p2
            cell_y = player2_y + row * cell_size_p2
            
            if cell_value == 'X':  # Case touchée
                # Vérifier si une animation n'existe pas déjà à cette position
                if not any(fire.x == cell_x and fire.y == cell_y for fire in effects_manager.fire_animations):
                    effects_manager.create_fire_animation(cell_x, cell_y, int(cell_size_p2))
            elif cell_value == 'O':  # Case manquée
                # Vérifier si une animation d'eau n'existe pas déjà
                if not hasattr(effects_manager, 'water_animations') or not any(water.x == cell_x and water.y == cell_y for water in effects_manager.water_animations):
                    effects_manager.create_water_animation(cell_x, cell_y, int(cell_size_p2))
    
    # Reset click_processed flag
    click_processed = False
    
    # Draw attack instructions
    target_board_x = player2_x if current_player == 1 else player1_x
    target_board_y = player2_y if current_player == 1 else player1_y
    target_board = game_state.multiplayer.player2_board if current_player == 1 else game_state.multiplayer.player1_board
    cell_size = cell_size_p2 if current_player == 1 else cell_size_p1
    
    instructions = fonts["small"].render("Cliquez ici pour attaquer", True, WHITE)
    instructions_x = target_board_x + (target_board.width // 2) - (instructions.get_width() // 2)
    screen.blit(instructions, (instructions_x, target_board_y - 25))
    
    # Handle messages
    if message_timer > 0:
        message = fonts["small"].render(message_text, True, message_color)
        screen.blit(message, (resolution[0]//2 - message.get_width()//2, 
                             max(player1_y, player2_y) + game_state.multiplayer.player1_board.height + 30))
        return
    
    # Process player's attack
    mouse_pressed = pygame.mouse.get_pressed()
    mouse_pos = pygame.mouse.get_pos()
    
    target_x = player2_x if current_player == 1 else player1_x
    target_y = player2_y if current_player == 1 else player1_y
    
    if mouse_pressed[0] and not click_processed:
        if target_x <= mouse_pos[0] < target_x + target_board.width and target_y <= mouse_pos[1] < target_y + target_board.height:
            col = int((mouse_pos[0] - target_x) // cell_size)
            row = int((mouse_pos[1] - target_y) // cell_size)
            
            if target_board.view[row][col] == '.':
                click_processed = True
                
                # Process attack
                hit, victory = game_state.multiplayer.attack(row, col)
                
                # Add visual effect
                effect_x = target_x + col * cell_size + cell_size / 2
                effect_y = target_y + row * cell_size + cell_size / 2
                
                if hit:
                    effects_manager.create_hit_effect(effect_x, effect_y)
                    message_text = f"Touché! Le Joueur {current_player} rejouera."
                    message_color = WHITE
                    message_timer = 75
                    
                    # Check for victory
                    if victory:
                        game_state.winner = f"player{current_player}"
                        game_state.state = GameState.END
                        # Play victory music
                        change_music(game_state.victory_music)
                        
                        # Add victory animation
                        if not hasattr(game_state, 'victory_animation_started') or not game_state.victory_animation_started:
                            effects_manager.clear_fire_animations()
                            effects_manager.create_victory_animation(resolution[0], resolution[1])
                            game_state.victory_animation_started = True
                else:
                    effects_manager.create_water_animation(target_x + col * cell_size, target_y + row * cell_size, int(cell_size))
                    next_player = 2 if current_player == 1 else 1
                    message_text = f"Manqué! Au tour du Joueur {next_player}."
                    message_color = WHITE
                    message_timer = 90
    
    # Also handle click events
    for event in pygame.event.get([pygame.MOUSEBUTTONDOWN]):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not click_processed:
            mouse_pos = event.pos
            
            if target_x <= mouse_pos[0] < target_x + target_board.width and target_y <= mouse_pos[1] < target_y + target_board.height:
                col = int((mouse_pos[0] - target_x) // cell_size)
                row = int((mouse_pos[1] - target_y) // cell_size)
                
                if target_board.view[row][col] == '.':
                    click_processed = True
                    
                    # Process attack
                    hit, victory = game_state.multiplayer.attack(row, col)
                    
                    # Add visual effect
                    effect_x = target_x + col * cell_size + cell_size / 2
                    effect_y = target_y + row * cell_size + cell_size / 2
                    
                    if hit:
                        effects_manager.create_hit_effect(effect_x, effect_y)
                        message_text = f"Touché! Le Joueur {current_player} rejouera."
                        message_color = WHITE
                        message_timer = 75
                        
                        if victory:
                            game_state.winner = f"player{current_player}"
                            game_state.state = GameState.END
                            change_music(game_state.victory_music)
                            
                            # Add victory animation
                            if not hasattr(game_state, 'victory_animation_started') or not game_state.victory_animation_started:
                                effects_manager.clear_fire_animations()
                                effects_manager.create_victory_animation(resolution[0], resolution[1])
                                game_state.victory_animation_started = True
                    else:
                        effects_manager.create_water_animation(target_x + col * cell_size, target_y + row * cell_size, int(cell_size))
                        next_player = 2 if current_player == 1 else 1
                        message_text = f"Manqué! Au tour du Joueur {next_player}."
                        message_color = WHITE
                        message_timer = 90

def handle_game():
    """Handle the game phase (player turns, computer turns)"""
    global message_timer, message_text, message_color, waiting_for_action, button_cooldown, last_click_pos, click_processed
    
    # Draw the gameplay background first
    if "gameplay_background" in assets:
        screen.blit(assets["gameplay_background"], (0, 0))
    
    # Always draw the player's grid with placed ships
    player_x, player_y = draw_grid(screen, game_state.player_board, fonts, assets, reveal=True, 
                                   is_player_grid=True, position="left")
    
    # Draw already placed ships on the player's grid
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
    
    # Draw the computer's grid
    comp_x, comp_y = draw_grid(screen, game_state.computer_board, fonts, assets, reveal=True, 
                               is_player_grid=False, position="right")
    
    # Render hit and miss cells
    for row in range(len(game_state.player_board.grid)):
        for col in range(len(game_state.player_board.grid[row])):
            cell_value = game_state.player_board.view[row][col]
            cell_x = player_x + col * cell_size
            cell_y = player_y + row * cell_size

            if cell_value == 'X':  # Case touchée
                # Create fire animation if one doesn't already exist at this position
                if not any(fire.x == cell_x and fire.y == cell_y for fire in effects_manager.fire_animations):
                    effects_manager.create_fire_animation(cell_x, cell_y, int(cell_size))
            elif cell_value == 'O':  # Case manquée
                # Create water animation if one doesn't already exist at this position
                if not hasattr(effects_manager, 'water_animations') or not any(water.x == cell_x and water.y == cell_y for water in effects_manager.water_animations):
                    effects_manager.create_water_animation(cell_x, cell_y, int(cell_size))
    
    # Add this to render hits on computer's board too:
    for row in range(len(game_state.computer_board.grid)):
        for col in range(len(game_state.computer_board.grid[row])):
            cell_value = game_state.computer_board.view[row][col]
            cell_x = comp_x + col * cell_size
            cell_y = comp_y + row * cell_size
            
            if cell_value == 'X':  # Case touchée
                # Create fire animation if one doesn't already exist at this position
                if not any(fire.x == cell_x and fire.y == cell_y for fire in effects_manager.fire_animations):
                    effects_manager.create_fire_animation(cell_x, cell_y, int(cell_size))
            elif cell_value == 'O':  # Case manquée
                # Create water animation if one doesn't already exist at this position
                if not hasattr(effects_manager, 'water_animations') or not any(water.x == cell_x and water.y == cell_y for water in effects_manager.water_animations):
                    effects_manager.create_water_animation(cell_x, cell_y, int(cell_size))
    
    # Reset click processed flag at the beginning of each frame when in player's turn
    if game_state.game_mode == GameState.SINGLE_PLAYER and game_state.player_turn and message_timer == 0:
        click_processed = False
    
    # If we're in a cooldown period (transitioning from placement), show message but don't process game logic
    if button_cooldown > 0:
        # Show transition message
        message = fonts["small"].render(message_text, True, message_color)
        screen.blit(message, (resolution[0] // 2 - message.get_width() // 2, 
                              max(player_y, comp_y) + game_state.player_board.height + 30))
        return
    
    # Handle game events - check for clicks each frame
    mouse_pressed = pygame.mouse.get_pressed()
    mouse_pos = pygame.mouse.get_pos()
    
    # In single player mode
    if game_state.game_mode == GameState.SINGLE_PLAYER:
        # Player's turn
        if game_state.player_turn:
            # Draw turn indicators and instructions
            turn_indicator = fonts["small"].render("Votre tour", True, GREEN)
            indicator_x = comp_x + game_state.computer_board.width - turn_indicator.get_width()
            screen.blit(turn_indicator, (indicator_x - 20, comp_y - 50))
            
            instructions = fonts["small"].render("Cliquez ici pour attaquer", True, WHITE)
            instructions_x = comp_x + (game_state.computer_board.width // 2) - (instructions.get_width() // 2)
            screen.blit(instructions, (instructions_x, comp_y - 25))
            
            # If a message is being displayed
            if message_timer > 0:
                message = fonts["small"].render(message_text, True, message_color)
                screen.blit(message, (resolution[0] // 2 - message.get_width() // 2, 
                                    max(player_y, comp_y) + game_state.player_board.height + 30))
                return
            
            # Process player click - check if mouse is pressed and the click hasn't been processed yet
            if mouse_pressed[0] and not click_processed:  # Left mouse button
                cell_size = game_state.computer_board.width / len(game_state.computer_board.grid[0])
                
                if (comp_x <= mouse_pos[0] < comp_x + game_state.computer_board.width and 
                    comp_y <= mouse_pos[1] < comp_y + game_state.computer_board.height):
                    
                    col = int((mouse_pos[0] - comp_x) // cell_size)
                    row = int((mouse_pos[1] - comp_y) // cell_size)
                    
                    if game_state.computer_board.view[row][col] == '.':
                        # Mark this click as processed to prevent multiple registrations
                        click_processed = True
                        
                        # Player attacks
                        hit = game_state.player_attack(row, col)
                        
                        # Add visual effect
                        effect_x = comp_x + col * cell_size + cell_size / 2
                        effect_y = comp_y + row * cell_size + cell_size / 2
                        
                        if hit:
                            effects_manager.create_hit_effect(effect_x, effect_y) 
                            message_text = "Vous rejouez"
                            message_color = WHITE
                            message_timer = 75
                            
                            # Check game end
                            if game_state.winner is not None and not game_state.victory_animation_started:
                                # Clear fire animations before starting victory animation
                                effects_manager.clear_fire_animations()
                                effects_manager.create_victory_animation(resolution[0], resolution[1])
                                game_state.victory_animation_started = True
                                # Play victory music
                                change_music(game_state.victory_music)
                                return
                        else:
                            effects_manager.create_water_animation(comp_x + col * cell_size, comp_y + row * cell_size, int(cell_size)) 
                            message_text = "Manqué! Au tour de votre adversaire."
                            message_color = WHITE
                            message_timer = 90
                            game_state.player_turn = False
            
            # Also check for pygame events to ensure we don't miss any clicks
            for event in pygame.event.get([pygame.MOUSEBUTTONDOWN]):
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not click_processed:
                    mouse_pos = event.pos
                    
                    cell_size = game_state.computer_board.width / len(game_state.computer_board.grid[0])
                    
                    if (comp_x <= mouse_pos[0] < comp_x + game_state.computer_board.width and 
                        comp_y <= mouse_pos[1] < comp_y + game_state.computer_board.height):
                        
                        col = int((mouse_pos[0] - comp_x) // cell_size)
                        row = int((mouse_pos[1] - comp_y) // cell_size)
                        
                        if game_state.computer_board.view[row][col] == '.':
                            click_processed = True
                            
                            # Player attacks
                            hit = game_state.player_attack(row, col)
                            
                            # Add visual effect
                            effect_x = comp_x + col * cell_size + cell_size / 2
                            effect_y = comp_y + row * cell_size + cell_size / 2
                            
                            if hit:
                                effects_manager.create_hit_effect(effect_x, effect_y)
                                message_text = "Vous rejouez"
                                message_color = WHITE
                                message_timer = 75
                                
                                # Check game end
                                if game_state.winner is not None and not game_state.victory_animation_started:
                                    # Clear fire animations before starting victory animation
                                    effects_manager.clear_fire_animations()
                                    effects_manager.create_victory_animation(resolution[0], resolution[1])
                                    game_state.victory_animation_started = True
                                    # Play victory music
                                    change_music(game_state.victory_music)
                                    return
                            else:
                                effects_manager.create_water_animation(comp_x + col * cell_size, comp_y + row * cell_size, int(cell_size))
                                message_text = "Manqué! Au tour de votre adversaire."
                                message_color = WHITE
                                message_timer = 90
                                game_state.player_turn = False
        
        # Computer's turn
        else:
            # Adjusted Y position for turn indicator (increased by 10px)
            turn_indicator = fonts["small"].render("Tour de l'ordinateur", True, RED)
            screen.blit(turn_indicator, (player_x + 50, player_y - 50))  # Changed from -60 to -50
            
            # Adjusted Y position for instructions (increased by 5px)
            instructions = fonts["small"].render("L'ordinateur attaque ici", True, WHITE)
            instructions_x = player_x + (game_state.player_board.width // 2) - (instructions.get_width() // 2)
            screen.blit(instructions, (instructions_x, player_y - 25))  # Changed from -30 to -25
            
            # If a message is being displayed
            if message_timer > 0:
                message = fonts["small"].render(message_text, True, message_color)
                screen.blit(message, (resolution[0] // 2 - message.get_width() // 2, 
                                    max(player_y, comp_y) + game_state.player_board.height + 30))  # Increased from 20 to 30
                return
            
            # Computer's turn logic
            if not waiting_for_action:
                # Show that the computer is thinking
                message_text = "L'ordinateur réfléchit..."
                message_color = WHITE
                message_timer = 90
                waiting_for_action = True
                
                # ADD THIS: Return to give the thinking animation time to display
                return  # This is critical - allows the thinking message to appear

            # Reset waiting state only after message has been shown
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
                        message_text = "L'ordinateur rejoue"
                        message_color = WHITE
                        message_timer = 90
                        
                    else:
                        effects_manager.create_water_animation(player_x + col * cell_size, player_y + row * cell_size, int(cell_size))
                        message_text = "Votre tour"
                        message_color = WHITE
                        message_timer = 75
                        game_state.player_turn = True
            except Exception as e:
                print(f"Error during computer's turn: {e}")
                # Recover gracefully by switching back to player's turn
                message_text = "Erreur lors du tour de l'ordinateur. Votre tour."
                message_color = RED
                message_timer = 90
                game_state.player_turn = True

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
    
    if game_state.rotation_cooldown > 0:
        game_state.rotation_cooldown -= 1
    
    # Vérifier si l'état a changé
    if previous_state != game_state.state:
        previous_state = game_state.state
        recently_changed_state = True
        
        # Save AI model when transitioning to END state
        if game_state.state == GameState.END and game_state.computer_ai:
            try:
                print("Saving AI model at game end...")
                game_state.computer_ai.save_model()
            except Exception as e:
                print(f"Error saving AI model: {e}")
        
        # Clear fire animations when game ends or restarts
        if game_state.state == GameState.END or (game_state.state == GameState.MENU and previous_state == GameState.END):
            effects_manager.clear_fire_animations()
            if hasattr(effects_manager, 'clear_water_animations'):
                effects_manager.clear_water_animations()
        
        # Change music based on state
        if game_state.state == GameState.MENU:
            change_music(game_state.menu_music)
        elif game_state.state in [GameState.PLACEMENT, GameState.GAME]:
            change_music(game_state.game_music)
        
        # Force a longer cooldown when changing to placement state
        if game_state.state == GameState.PLACEMENT:
            button_cooldown = 120
            game_state.player_board = Board()
            game_state.current_ship_index = 0
        else:
            button_cooldown = 60
        
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
        if game_state.game_mode == GameState.SINGLE_PLAYER:
            handle_placement()
        else:  # Multiplayer mode
            handle_multiplayer_placement()
        recently_changed_state = False
    elif game_state.state == GameState.GAME:
        if game_state.game_mode == GameState.SINGLE_PLAYER:
            handle_game()
        else:  # Multiplayer mode
            handle_multiplayer_game()
        recently_changed_state = False
    elif game_state.state == GameState.END:
        draw_game_end(screen, game_state.winner, fonts, game_state.restart_game)
        recently_changed_state = False
    
    # Update effects
    effects_manager.update_effects(screen)
    effects_manager.update_animated_messages(screen)
    if game_state.winner is not None and game_state.victory_animation_started:
        if len(effects_manager.victory_particles) > 0:  # Ne met à jour que s'il reste des particules
            effects_manager.update_victory_animation(screen)
    
    # Draw mute button
    pygame.draw.rect(screen, WHITE if not music_muted else RED, mute_button_rect)
    mute_text = fonts["small"].render("ON" if not music_muted else "OFF", True, GRAY)
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