import random
import pygame
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
        self.placed_ships = []  # Liste des bateaux placés
        
        # Game turn
        self.player_turn = True
        
        # Winner
        self.winner = None
        
        # Computer AI - Initialize it later when needed
        self.computer_ai = None

        self.menu_music = None
        self.game_music = None

        self.victory_animation_started = False
    
    def start_single_player(self):
        """Start single player game"""
        self.game_mode = self.SINGLE_PLAYER
        self.state = self.PLACEMENT
        self.reset_game()
    
    def start_multiplayer(self):
        """Start multiplayer game"""
        from src.multiplayer import LocalMultiplayer
        self.game_mode = self.MULTIPLAYER
        self.multiplayer = LocalMultiplayer()
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
        """Reset game state to start a new game"""
        self.state = GameState.MENU
        self.player_turn = True
        self.winner = None
        self.current_ship_index = 0
        self.horizontal = True
        
        self.player_board = Board()  # Créer un nouveau plateau vide
        
        # Si on était en mode multijoueur, computer_ai sera None
        if self.game_mode == GameState.SINGLE_PLAYER and self.computer_ai is not None:
            self.computer_ai.reset_game_state()
        elif self.game_mode == GameState.MULTIPLAYER and self.multiplayer is not None:
            from src.multiplayer import LocalMultiplayer
            # Reset the multiplayer state
            self.multiplayer = LocalMultiplayer()
        
        # Réinitialiser le drapeau d'animation
        if hasattr(self, 'victory_animation_started'):
            self.victory_animation_started = False
    
    def handle_cell_hit(self, cell_value, row, col, cell_size, cell_x, cell_y, screen, boom_image):
        """Handle the event when a cell is hit"""
        if cell_value == 'X':  # Case touchée
            print(f"Case touchée à la position ({row}, {col})")
            scaled_boom = pygame.transform.scale(boom_image, (int(cell_size), int(cell_size)))
            screen.blit(scaled_boom, (cell_x, cell_y))

    # Add or update the set_winner method

    def set_winner(self, winner):
        """Set the winner and end the game"""
        self.winner = winner
        self.state = self.END
        
        # Save AI learning data if it exists and we're in single player mode
        if self.game_mode == self.SINGLE_PLAYER and self.computer_ai:
            try:
                print("Saving AI model...")
                self.computer_ai.save_model()
            except Exception as e:
                print(f"Error saving AI model: {e}")

    def train_ai(self):
        """Train the AI by playing against itself"""
        import tkinter as tk
        from tkinter import simpledialog, messagebox
        
        try:
            # Initialize AI if not already done
            if not hasattr(self, 'computer_ai') or self.computer_ai is None:
                self.computer_ai = ReinforcementLearningAI(self.player_board)
            
            # Create popup dialog to ask for number of training games
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            
            # Show info about current AI state
            current_states = len(self.computer_ai.q_table) if hasattr(self.computer_ai, 'q_table') else 0
            
            num_games = simpledialog.askinteger(
                "AI Training", 
                f"Current AI knowledge: {current_states} states\n\n"
                "Enter number of games to train (100-1000):",
                minvalue=100, maxvalue=1000, initialvalue=200
            )
            
            if num_games:
                # Show progress dialog
                messagebox.showinfo(
                    "Training Started",
                    f"Training AI for {num_games} games.\n"
                    "This may take a few minutes.\n"
                    "Check the console for progress updates."
                )
                
                # Start training
                self.computer_ai.train_against_self(num_games=num_games, save_interval=20)
                
                # Show completion message
                messagebox.showinfo(
                    "Training Complete", 
                    f"AI training complete!\n"
                    f"The AI now knows {len(self.computer_ai.q_table)} different game states."
                )
        except Exception as e:
            print(f"Error during AI training: {e}")
            
            # Show error message
            try:
                messagebox.showerror("Training Error", f"Error during training: {e}")
            except:
                pass  # If messagebox fails, continue
        finally:
            try:
                root.destroy()
            except:
                pass