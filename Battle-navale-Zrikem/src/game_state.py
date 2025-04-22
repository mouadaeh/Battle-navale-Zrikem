import random
import os
from src.utils.constants import SHIPS, GRID_SIZE
from src.board import Board
from src.ship import Ship
from src.ai import ReinforcementLearningAI

class GameState:
    """Manages the state of the battleship game"""
    
    # Game states
    MENU = "menu"
    PLACEMENT = "placement"
    GAME = "game"
    END = "end"
    
    # Game modes
    SINGLE_PLAYER = "single"
    MULTIPLAYER = "multi"
    
    def __init__(self, resolution):
        self.resolution = resolution
        self.state = self.MENU
        self.game_mode = None
        
        # Ships configuration
        self.ships = SHIPS.copy()
        
        # Boards
        self.player_board = Board()
        self.computer_board = Board()
        
        # Ship placement
        self.current_ship_index = 0
        self.horizontal = True
        self.rotation_cooldown = 0
        
        # Game turn
        self.player_turn = True
        
        # Winner
        self.winner = None
        
        # Computer AI - Initialize it later when needed
        self.computer_ai = None

        self.menu_music = None
        self.game_music = None
    
    def start_single_player(self):
        """Start single player game"""
        self.game_mode = self.SINGLE_PLAYER
        self.state = self.PLACEMENT
        self.reset_game()
    
    def start_multiplayer(self):
        """Start multiplayer game"""
        self.game_mode = self.MULTIPLAYER
        self.state = self.PLACEMENT
        self.reset_game()
    
    def reset_game(self):
        """Reset the game state for a new game"""
        # Reset boards
        self.player_board = Board()
        self.computer_board = Board()
        
        # Reset ship placement
        self.current_ship_index = 0
        self.horizontal = True
        self.rotation_cooldown = 0
        
        # Generate computer ships
        self.generate_computer_ships()
        
        # Reset turn
        self.player_turn = True
        
        # Reset winner
        self.winner = None
        
        # Reset AI only if in single player mode
        if self.game_mode == self.SINGLE_PLAYER:
            self.computer_ai = ReinforcementLearningAI(self.player_board)
    
    def generate_computer_ships(self):
        """Generate ships for the computer"""
        for ship_data in self.ships:
            ship = Ship(ship_data["name"], ship_data["size"])
            placed = False
            while not placed:
                row = random.randint(0, GRID_SIZE - 1)
                col = random.randint(0, GRID_SIZE - 1)
                is_horizontal = random.choice([True, False])
                placed = self.computer_board.place_ship(ship, row, col, is_horizontal)
    
    def place_player_ship(self, row, col, size, is_horizontal):
        """Place a player ship on the board"""
        if self.current_ship_index >= len(self.ships):
            return False
        
        ship_data = self.ships[self.current_ship_index]
        ship = Ship(ship_data["name"], ship_data["size"])
        
        return self.player_board.place_ship(ship, row, col, is_horizontal)
    
    def player_attack(self, row, col):
        """Player attacks the computer's grid"""
        hit = self.computer_board.receive_attack(row, col)
        
        # Check if all computer ships are sunk
        if self.computer_board.all_ships_sunk():
            self.winner = "player"
            self.state = self.END
        
        return hit
    
    def computer_attack(self):
        """Computer attacks the player's grid"""
        # First, collect all available (not yet attacked) positions
        available_positions = []
        for row in range(len(self.player_board.grid)):
            for col in range(len(self.player_board.grid[row])):
                # Only consider positions that haven't been attacked yet
                if self.player_board.view[row][col] == '.':
                    available_positions.append((row, col))
        
        # If no positions available, return None (game should be over already)
        if not available_positions:
            return None, None, False
        
        # If we have an AI, get its suggestion
        if self.computer_ai:
            row, col = self.computer_ai.get_attack_coordinates()
            
            # Check if the AI-suggested position has already been attacked
            # If so, pick a random available position instead
            if self.player_board.view[row][col] != '.':
                import random
                row, col = random.choice(available_positions)
        else:
            # No AI, just pick a random available position
            import random
            row, col = random.choice(available_positions)
        
        # Now we're guaranteed to have an unattacked position
        # Make the attack
        hit = self.player_board.receive_attack(row, col)
        
        # Update AI if we have one
        if self.computer_ai:
            self.computer_ai.register_result(row, col, hit)
        
        # Check if all player ships are sunk
        if self.player_board.all_ships_sunk():
            self.winner = "computer"
            self.state = self.END
        
        return row, col, hit
    
    def restart_game(self):
        """Restart the game"""
        # Save AI model before resetting if we were in single player mode
        if self.game_mode == self.SINGLE_PLAYER and self.computer_ai:
            try:
                os.makedirs("models", exist_ok=True)  # Create directory if it doesn't exist
                self.computer_ai.save_model()
                print("AI model saved successfully")
            except Exception as e:
                print(f"Could not save AI model: {e}")
        
        self.state = self.MENU
        self.game_mode = None
        self.winner = None
        self.player_turn = True
        self.reset_game()