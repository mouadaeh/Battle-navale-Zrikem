from src.utils.constants import GRID_SIZE
import random
import os
import pickle

# Define direction constants
DIRECTIONS = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # right, down, left, up

class ReinforcementLearningAI:
    """AI using reinforcement learning to play Battleship"""
    
    def __init__(self, player_board, learning_rate=0.1, discount_factor=0.9, exploration_rate=0.2):
        self.player_board = player_board
        self.last_hit = None
        self.direction = None
        self.target_queue = []
        self.original_hit = None
        self.tried_opposite = False
        self.try_opposite = False
        self.current_ship_hits = 0
        
        # RL parameters
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate
        self.q_table = {}
        self.last_state = None
        self.last_action = None
        
        # Cache for valid moves
        self._valid_moves_cache = None
        self._last_board_state = None
        
        # Load pre-trained model if available
        self.load_model()
    
    def _get_current_state(self):
        """Get compact state representation for Q-learning"""
        # Simplified pattern recognition focused on rows and columns
        patterns = []
        for r in range(GRID_SIZE):
            patterns.append(''.join(self.player_board.view[r]))
        for c in range(GRID_SIZE):
            patterns.append(''.join(self.player_board.view[r][c] for r in range(GRID_SIZE)))
        return hash(tuple(patterns))
    
    def _get_valid_moves(self):
        """Get all valid moves with caching for performance"""
        current_state = ''.join(''.join(row) for row in self.player_board.view)
        if self._last_board_state == current_state and self._valid_moves_cache:
            return self._valid_moves_cache
        
        valid_moves = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) 
                      if self.player_board.view[r][c] == '.']
        
        self._valid_moves_cache = valid_moves
        self._last_board_state = current_state
        return valid_moves
    
    def get_attack_coordinates(self):
        """Get coordinates for the next attack based on AI strategy"""
        # Continue targeting if we have a hit
        if self.last_hit is not None:
            return self._target_ship()
        
        # Process queue if we have pending directions to check
        if self.target_queue:
            return self._process_hit_queue()
        
        # Q-learning strategy when no active targeting
        state = self._get_current_state()
        if random.random() > self.exploration_rate and state in self.q_table:
            valid_moves = self._get_valid_moves()
            best_value = -float('inf')
            best_moves = []
            
            for move, value in self.q_table[state].items():
                # Handle string tuples from serialized Q-table
                if isinstance(move, str) and move.startswith('('):
                    try:
                        nums = move.strip('()').split(',')
                        move = (int(nums[0].strip()), int(nums[1].strip()))
                    except:
                        continue
                
                if move in valid_moves and value >= best_value:
                    if value > best_value:
                        best_value = value
                        best_moves = [move]
                    else:
                        best_moves.append(move)
            
            if best_moves:
                return random.choice(best_moves)
        
        # Fallback to smart random attack
        return self._smart_random_attack()

    def _target_ship(self):
        """Target a ship after the first hit with smart direction detection"""
        if self.last_hit is None:
            return self._smart_random_attack()
        
        row, col = self.last_hit
        
        # Reset if we've hit max ship size
        if self.current_ship_hits >= 10:
            self._reset_targeting()
            return self._smart_random_attack()
        
        # Try opposite direction if needed
        if self.try_opposite and self.original_hit and self.direction:
            orig_row, orig_col = self.original_hit
            dr, dc = self.direction
            next_row, next_col = orig_row - dr, orig_col - dc
            
            if self._is_valid_cell(next_row, next_col):
                self.last_hit = self.original_hit
                self.direction = (-dr, -dc)
                self.try_opposite = False
                self.tried_opposite = True
                return (next_row, next_col)
            else:
                self._reset_targeting()
                return self._smart_random_attack()
        
        # Continue in established direction
        if self.direction:
            dr, dc = self.direction
            next_row, next_col = row + dr, col + dc
            
            if self._is_valid_cell(next_row, next_col) and self.current_ship_hits < 5:
                return (next_row, next_col)
        
        # Check adjacent cells for first hit
        if not self.target_queue and not self.direction:
            self._add_adjacent_to_queue(row, col)
            if not self.original_hit:
                self.original_hit = (row, col)
            if self.target_queue:
                return self._process_hit_queue()
        
        # Use remaining targets in queue
        if self.target_queue:
            return self._process_hit_queue()
        
        # Reset if we can't continue in any direction
        self._reset_targeting()
        return self._smart_random_attack()
    
    def _add_adjacent_to_queue(self, row, col):
        """Add all valid adjacent cells to the targeting queue"""
        self.target_queue = []
        for dr, dc in DIRECTIONS:
            next_row, next_col = row + dr, col + dc
            if self._is_valid_cell(next_row, next_col):
                self.target_queue.append((next_row, next_col))
    
    def _process_hit_queue(self):
        """Process the next target in the queue"""
        return self.target_queue.pop(0) if self.target_queue else self._smart_random_attack()

    def _is_valid_cell(self, row, col):
        """Check if a cell is valid for targeting"""
        return (0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE and 
                self.player_board.view[row][col] == '.')

    def _is_isolated_cell(self, row, col):
        """Check if a cell is isolated (surrounded by hits or misses)"""
        if self.player_board.view[row][col] != '.':
            return False
        
        return all(self.player_board.view[row+dr][col+dc] in ['X', 'O'] 
                  for dr, dc in DIRECTIONS 
                  if 0 <= row+dr < GRID_SIZE and 0 <= col+dc < GRID_SIZE)

    def _calculate_ship_potential(self, row, col):
        """Calculate potential for ship placement at this location"""
        # Count consecutive open cells horizontally and vertically
        h_count = 1
        v_count = 1
        
        # Check horizontally
        for dc in [-1, 1]:
            c = col + dc
            while 0 <= c < GRID_SIZE and self.player_board.view[row][c] == '.':
                h_count += 1
                c += dc
        
        # Check vertically
        for dr in [-1, 1]:
            r = row + dr
            while 0 <= r < GRID_SIZE and self.player_board.view[r][col] == '.':
                v_count += 1
                r += dr
        
        max_count = max(h_count, v_count)
        return 0 if max_count < 2 else (max_count - 1) / 4.0

    def _smart_random_attack(self):
        """Make intelligent random attacks prioritizing high-value cells"""
        valid_moves = self._get_valid_moves()
        if not valid_moves:
            return (0, 0)
        
        # Create a simple heatmap for cell selection
        heatmap = {}
        for r, c in valid_moves:
            score = 1.0
            if self._is_isolated_cell(r, c):
                score *= 0.1
            if (r + c) % 2 == 0:  # Prefer checkerboard pattern
                score *= 1.5
            score *= (1.0 + self._calculate_ship_potential(r, c))
            heatmap[(r, c)] = score
        
        # Select from top scoring moves
        top_moves = sorted(heatmap.items(), key=lambda x: x[1], reverse=True)[:3]
        return random.choice([move for move, _ in top_moves])

    def register_result(self, row, col, hit):
        """Process attack result and update targeting strategy"""
        # Update Q-values
        if self.last_state and self.last_action:
            reward = 2.0 if hit and self.current_ship_hits > 1 else (1.0 if hit else -0.1)
            self._update_q_value(self.last_state, self.last_action, reward)
        
        self.last_state = self._get_current_state()
        self.last_action = (row, col)
        
        # Handle targeting logic
        if hit:
            self.current_ship_hits = self.current_ship_hits + 1 if hasattr(self, 'current_ship_hits') else 1
            
            # First hit on this ship
            if not self.last_hit:
                self.last_hit = (row, col)
                self.original_hit = (row, col)
                self.previous_hit = (row, col)
            
            # Already have a direction, continue with it
            elif self.direction:
                self.last_hit = (row, col)
            
            # Second hit, establish direction
            elif self.last_hit != (row, col):
                prev_row, prev_col = self.last_hit
                
                # Calculate direction vector
                if row == prev_row:  # Horizontal
                    self.direction = (0, 1 if col > prev_col else -1)
                elif col == prev_col:  # Vertical
                    self.direction = (1 if row > prev_row else -1, 0)
                else:
                    self.direction = (0, 1)  # Default to horizontal
                
                self.previous_hit = self.last_hit
                self.last_hit = (row, col)
                self.target_queue = []  # Clear queue now that we have a direction
            
            # Reset after max ship size
            if self.current_ship_hits >= 5:
                self._reset_targeting()
        else:
            # Handle miss based on current targeting state
            if self.direction:
                if self.tried_opposite:
                    # Tried both directions - complete ship
                    self._reset_targeting()
                else:
                    # Try opposite direction next turn
                    self.try_opposite = True
    
    def _reset_targeting(self):
        """Reset all targeting variables after completing a ship"""
        self.last_hit = None
        self.original_hit = None
        self.direction = None
        self.current_ship_hits = 0
        self.tried_opposite = False
        self.try_opposite = False
        self.target_queue = []

    def _update_q_value(self, state, action, reward):
        """Update the Q-value for a state-action pair"""
        if state not in self.q_table:
            self.q_table[state] = {}
        if action not in self.q_table[state]:
            self.q_table[state][action] = 0.0
        
        self.q_table[state][action] += self.learning_rate * (reward - self.q_table[state][action])
    
    def load_model(self):
        """Load the Q-table from disk if available"""
        try:
            if os.path.exists('models/battleship_rl_model.pkl'):
                with open('models/battleship_rl_model.pkl', 'rb') as f:
                    self.q_table = pickle.load(f)
        except Exception:
            self.q_table = {}
    
    def save_model(self):
        """Save the Q-table to disk"""
        try:
            os.makedirs('models', exist_ok=True)
            with open('models/battleship_rl_model.pkl', 'wb') as f:
                pickle.dump(self.q_table, f)
        except Exception:
            pass
    
    def reset_game_state(self):
        """Reset the AI's state for a new game while preserving learning"""
        self.last_hit = None
        self.original_hit = None
        self.direction = None
        self.current_ship_hits = 0
        self.tried_opposite = False
        self.try_opposite = False
        self.target_queue = []
        self.last_state = None
        self.last_action = None