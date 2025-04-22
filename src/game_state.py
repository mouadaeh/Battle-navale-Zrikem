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
        self.player_board = Board()  # Player 1 board
        self.computer_board = Board()  # Used in single-player
        self.player2_board = Board()  # Used in multiplayer for Player 2
        
        # Ship placement
        self.current_ship_index = 0
        self.horizontal = True
        self.rotation_cooldown = 0
        self.current_placing_player = 1  # 1 for Player 1, 2 for Player 2
        
        # Game turn
        self.player_turn = True  # True for Player 1, False for Computer or Player 2
        self.current_attacking_player = 1  # 1 for Player 1, 2 for Player 2
        
        # Winner
        self.winner = None
        
        # Computer AI (used only in single-player)
        self.computer_ai = ReinforcementLearningAI(self.player_board)  # Use RL AI for better gameplay
    
    def start_single_player(self):
        """Start single player game"""
        self.game_mode = self.SINGLE_PLAYER
        self.state = self.PLACEMENT
        self.current_placing_player = 1
        self.current_attacking_player = 1
        self.reset_game()
    
    def start_multiplayer(self):
        """Start multiplayer game"""
        self.game_mode = self.MULTIPLAYER
        self.state = self.PLACEMENT
        self.current_placing_player = 1
        self.current_attacking_player = 1
        self.reset_game()
    
    def reset_game(self):
        """Reset the game state for a new game"""
        # Reset boards
        self.player_board = Board()
        self.computer_board = Board()
        self.player2_board = Board()
        
        # Reset ship placement
        self.current_ship_index = 0
        self.horizontal = True
        self.rotation_cooldown = 0
        self.current_placing_player = 1
        
        # Generate computer ships for single player
        if self.game_mode == self.SINGLE_PLAYER:
            self.generate_computer_ships()
        
        # Reset turn
        self.player_turn = True
        self.current_attacking_player = 1
        
        # Reset winner
        self.winner = None
        
        # Reset AI for single player
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
        
        # Place on the appropriate player's board
        if self.game_mode == self.MULTIPLAYER:
            target_board = self.player_board if self.current_placing_player == 1 else self.player2_board
            return target_board.place_ship(ship, row, col, is_horizontal)
        else:
            return self.player_board.place_ship(ship, row, col, is_horizontal)
    
    def player_attack(self, row, col):
        """Player attacks the opponent's grid"""
        hit = False
        if self.game_mode == self.MULTIPLAYER:
            # Player 1 attacks Player 2's board, or vice versa
            target_board = self.player2_board if self.current_attacking_player == 1 else self.player_board
            hit = target_board.receive_attack(row, col)
            
            # Check if all opponent ships are sunk
            if target_board.all_ships_sunk():
                self.winner = f"player{self.current_attacking_player}"
                self.state = self.END
        else:
            # Single player: attack computer board
            hit = self.computer_board.receive_attack(row, col)
            if self.computer_board.all_ships_sunk():
                self.winner = "player"
                self.state = self.END
        
        return hit
    
    def computer_attack(self):
        """Computer attacks the player's grid"""
        if self.game_mode != self.SINGLE_PLAYER:
            return None, None, False
        
        row, col = self.computer_ai.get_attack_coordinates()
        
        if row is None or col is None:
            return None, None, False
        
        # If we have an AI, get its suggestion
        if self.computer_ai:
            row, col = self.computer_ai.get_attack_coordinates()
            
            # Check if the AI-suggested position has already been attacked
            # If so, pick a random available position instead
            if self.player_board.view[row][col] != '.':
                import random
                available_positions = [
                    (r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE)
                    if self.player_board.view[r][c] == '.'
                ]
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
            self.computer_ai.end_game(True)
        else:
            self.computer_ai.end_game(False)
        
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
        self.current_placing_player = 1
        self.current_attacking_player = 1
        self.reset_game()