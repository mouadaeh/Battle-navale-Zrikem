import random
from src.utils.constants import GRID_SIZE

class ComputerAI:
    """AI for computer player"""
    
    def __init__(self, player_board):
        self.player_board = player_board
        self.last_hit = None
        self.direction = None
        self.target_queue = []
    
    def get_attack_coordinates(self):
        """Determine where the computer should attack next"""
        # If we have a queue of target positions from previous hits
        if self.target_queue:
            return self.target_queue.pop(0)
        
        # If we have a last hit but no direction yet, try all directions
        if self.last_hit and not self.direction:
            row, col = self.last_hit
            # Check all four directions around the hit
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nr, nc = row + dr, col + dc
                if (0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE and 
                    self.player_board.view[nr][nc] == '.'):
                    self.target_queue.append((nr, nc))
            
            if self.target_queue:
                return self.target_queue.pop(0)
        
        # If we have a hit and a direction, continue in that direction
        if self.last_hit and self.direction:
            row, col = self.last_hit
            dr, dc = self.direction
            nr, nc = row + dr, col + dc
            
            if (0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE and 
                self.player_board.view[nr][nc] == '.'):
                return nr, nc
            
            # If we can't continue, try the opposite direction
            nr, nc = row - dr, col - dc
            if (0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE and 
                self.player_board.view[nr][nc] == '.'):
                self.direction = (-dr, -dc)
                return nr, nc
            
            # If we can't continue in either direction, reset
            self.last_hit = None
            self.direction = None
        
        # If no targeted attack, find all valid moves
        valid_moves = []
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.player_board.view[r][c] == '.':
                    valid_moves.append((r, c))
        
        if not valid_moves:
            return None, None  # No valid moves available
        
        # Prioritize positions adjacent to hits
        adjacent_to_hit = []
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.player_board.view[r][c] == 'X':
                    for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                        nr, nc = r + dr, c + dc
                        if (0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE and 
                            self.player_board.view[nr][nc] == '.'):
                            adjacent_to_hit.append((nr, nc))
        
        # Try to attack adjacent to a hit with high probability
        if adjacent_to_hit and random.random() < 0.8:
            return random.choice(adjacent_to_hit)
        
        # Otherwise, pick a random valid move
        return random.choice(valid_moves)
    
    def register_result(self, row, col, hit):
        """Register the result of an attack"""
        if hit:
            # If this is a new hit (not part of a sequence)
            if not self.last_hit:
                self.last_hit = (row, col)
            else:
                # If we already had a last hit, we can determine direction
                last_row, last_col = self.last_hit
                if last_row == row:  # Horizontal
                    self.direction = (0, 1 if col > last_col else -1)
                else:  # Vertical
                    self.direction = (1 if row > last_row else -1, 0)
                self.last_hit = (row, col)
        else:
            # If miss and we were following a direction, try opposite
            if self.direction:
                self.direction = (-self.direction[0], -self.direction[1])