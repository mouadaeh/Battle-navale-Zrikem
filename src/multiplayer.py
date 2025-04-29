import pygame
from src.board import Board
from src.ship import Ship
from src.utils.constants import GRID_SIZE, SHIPS

class LocalMultiplayer:
    """Manages local multiplayer mode where two players use the same machine."""
    
    def __init__(self):
        self.player1_board = Board()
        self.player2_board = Board()
        self.current_player = 1  # 1 = Player 1's turn, 2 = Player 2's turn
        self.placement_phase = True  # True during ship placement, False during battle
        self.player1_ships_placed = False
        self.player2_ships_placed = False
        self.player1_ships = []  # To store placed ship data
        self.player2_ships = []
        self.winner = None
        self.transition_screen = False
        self.transition_timer = 0
        self.transition_duration = 180  # 3 seconds at 60 FPS
        self.transition_message = ""
    
    def reset(self):
        """Reset the game state for a new game."""
        self.__init__()
    
    def switch_player(self):
        """Switch the active player and show transition screen."""
        self.transition_screen = True
        self.transition_timer = self.transition_duration
        
        if self.placement_phase:
            if self.current_player == 1 and self.player1_ships_placed:
                self.current_player = 2
                self.transition_message = "Joueur 2, placez vos navires"
            elif self.current_player == 2 and self.player2_ships_placed:
                self.current_player = 1
                self.placement_phase = False
                self.transition_message = "Joueur 1, à vous d'attaquer"
        else:
            self.current_player = 3 - self.current_player  # Toggle between 1 and 2
            self.transition_message = f"Joueur {self.current_player}, à vous d'attaquer"
    
    def update_transition(self):
        """Update transition screen timer."""
        if self.transition_screen:
            self.transition_timer -= 1
            print(f"Transition timer: {self.transition_timer}")  # Debug
            if self.transition_timer <= 0:
                self.transition_screen = False
                print("Transition ended")  # Debug
                
                # Important: Si on a fini la phase de placement, passons immédiatement à la phase de jeu
                if not self.placement_phase and self.current_player == 1:
                    print("Starting game phase")  # Debug
    
    def get_current_board(self):
        """Return the current player's board."""
        return self.player1_board if self.current_player == 1 else self.player2_board
    
    def get_opponent_board(self):
        """Return the opponent's board."""
        return self.player2_board if self.current_player == 1 else self.player1_board
    
    def get_ships_list(self):
        """Return the list of ships for the current player."""
        return self.player1_ships if self.current_player == 1 else self.player2_ships
    
    def place_ship(self, row, col, ship_data, horizontal):
        """Place a ship on the current player's board."""
        board = self.get_current_board()
        
        # Create a ship object with the proper name
        ship_name = ""
        ship_size = 0
        
        # Find the corresponding ship in SHIPS
        for ship_info in SHIPS:
            if ship_info["size"] == ship_data:
                ship_name = ship_info["name"]
                ship_size = ship_info["size"]
                break
    
        # If we couldn't find a match, use generic data
        if not ship_name:
            ship_name = f"Ship_{ship_data}"
            ship_size = ship_data
            
        ship = Ship(ship_name, ship_size)
        
        # Try to place the ship
        result = board.place_ship(ship, row, col, horizontal)
        
        if result:
            # Add to player's ships list with the proper name
            ship_info = {
                'name': ship_name,
                'size': ship_size,
                'row': row,
                'col': col,
                'horizontal': horizontal
            }
            
            if self.current_player == 1:
                self.player1_ships.append(ship_info)
                # Check if all ships are placed
                if len(self.player1_ships) == len(SHIPS):  # Utiliser len(SHIPS) au lieu d'une valeur fixe
                    print("Player 1 has placed all ships")  # Debug
                    self.player1_ships_placed = True
                    self.switch_player()
            else:
                self.player2_ships.append(ship_info)
                # Check if all ships are placed
                if len(self.player2_ships) == len(SHIPS):  # Utiliser len(SHIPS) au lieu d'une valeur fixe
                    print("Player 2 has placed all ships")  # Debug
                    self.player2_ships_placed = True
                    self.switch_player()
                
            print(f"Ship placed: {ship_name} at ({row},{col}). Current player: {self.current_player}")  # Debug
            
        return result
    
    def attack(self, row, col):
        """Handle attack from current player to opponent's board."""
        target_board = self.get_opponent_board()
        
        # Check if the cell has already been attacked
        if target_board.view[row][col] != '.':
            return False, False
        
        # Get the grid value at that position before attack
        has_ship = target_board.grid[row][col] == 'S'
        
        # Process the attack by modifying ONLY the target board's view, not the grid
        if has_ship:
            # Mark as hit in view, but don't modify the actual grid
            target_board.view[row][col] = 'X'
            hit = True
        else:
            # Mark as miss in view
            target_board.view[row][col] = 'O'
            hit = False
        
        # Check for victory by counting remaining ships
        ships_remaining = 0
        for r in range(len(target_board.grid)):
            for c in range(len(target_board.grid[r])):
                # Check if there's a ship that hasn't been hit yet
                if target_board.grid[r][c] == 'S' and target_board.view[r][c] != 'X':
                    ships_remaining += 1
        
        victory = ships_remaining == 0
        
        if victory:
            self.winner = f"player{self.current_player}"
        elif not hit:
            # Switch players only on miss
            self.switch_player()
            
        return hit, victory