import random
import os
import pickle
from src.utils.constants import GRID_SIZE

# Define direction constants to avoid repeated tuples
DIRECTIONS = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # right, down, left, up

class ReinforcementLearningAI:
    """AI using reinforcement learning to play Battleship"""
    
    def __init__(self, player_board, learning_rate=0.1, discount_factor=0.9, exploration_rate=0.2):
        self.player_board = player_board
        self.last_hit = None
        self.direction = None
        self.target_queue = []
        
        # RL parameters
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate
        
        # Q-table and history tracking
        self.q_table = {}
        self.history = []
        self.last_state = None
        self.last_action = None
        
        # Cache for valid moves to avoid recalculating
        self._valid_moves_cache = None
        self._last_board_state = None
        
        # Load pre-trained model if available
        self.load_model()
    
    def get_state_representation(self):
        """Get a representation of the current board state"""
        # More efficient string concatenation using join
        return ''.join(''.join(row) for row in self.player_board.view)
    
    def _get_valid_moves(self):
        """Get all valid moves (cells that haven't been attacked yet)"""
        # Check if we can use the cached valid moves
        current_state = self.get_state_representation()
        if self._last_board_state == current_state and self._valid_moves_cache:
            return self._valid_moves_cache
        
        # Otherwise calculate and cache valid moves
        valid_moves = []
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.player_board.view[r][c] == '.':
                    valid_moves.append((r, c))
        
        # Update cache
        self._valid_moves_cache = valid_moves
        self._last_board_state = current_state
        
        return valid_moves
    
    def get_attack_coordinates(self):
        """Determine where to attack using reinforcement learning"""
        # Get current state and valid moves
        current_state = self.get_state_representation()
        self.last_state = current_state
        
        valid_moves = self._get_valid_moves()
        if not valid_moves:
            return None, None
        
        # Decide whether to explore or exploit
        if random.random() < self.exploration_rate:
            return self._explore_strategy(valid_moves)
        else:
            return self._exploit_strategy(current_state, valid_moves)
    
    def _explore_strategy(self, valid_moves):
        """Use heuristic-based exploration strategy"""
        # Check target queue first (from previous hits)
        if self.target_queue:
            action = self.target_queue.pop(0)
            self.last_action = action
            return action
        
        # If we have a last hit but no direction, explore around it
        if self.last_hit and not self.direction:
            self._explore_around_last_hit()
            if self.target_queue:
                action = self.target_queue.pop(0)
                self.last_action = action
                return action
        
        # If we have a hit and direction, continue in that direction
        if self.last_hit and self.direction:
            action = self._continue_in_direction()
            if action:
                self.last_action = action
                return action
            
            # Reset if we can't continue
            self.last_hit = None
            self.direction = None
        
        # Try cells adjacent to previous hits
        adjacent_hits = self._find_adjacent_to_hits()
        if adjacent_hits and random.random() < 0.8:
            action = random.choice(adjacent_hits)
            self.last_action = action
            return action
        
        # Random move as a fallback
        action = random.choice(valid_moves)
        self.last_action = action
        return action
    
    def _exploit_strategy(self, state, valid_moves):
        """Use Q-learning to choose the best action"""
        # Find the move with highest Q-value
        best_value = float('-inf')
        best_actions = []
        
        for action in valid_moves:
            q_value = self.q_table.get((state, action), 0)
            
            if q_value > best_value:
                best_value = q_value
                best_actions = [action]
            elif q_value == best_value:
                best_actions.append(action)
        
        # Fall back to heuristic if Q-table doesn't have useful information
        if best_value <= 0 and len(best_actions) == len(valid_moves):
            return self._explore_strategy(valid_moves)
        
        # Choose randomly among best actions
        action = random.choice(best_actions)
        self.last_action = action
        return action
    
    def _explore_around_last_hit(self):
        """Explore all four directions around the last hit"""
        row, col = self.last_hit
        
        # Check all four directions
        for dr, dc in DIRECTIONS:
            nr, nc = row + dr, col + dc
            if self._is_valid_cell(nr, nc):
                self.target_queue.append((nr, nc))
    
    def _continue_in_direction(self):
        """Continue attacking in the current direction"""
        row, col = self.last_hit
        dr, dc = self.direction
        
        # Try continuing in current direction
        nr, nc = row + dr, col + dc
        if self._is_valid_cell(nr, nc):
            return nr, nc
        
        # Try opposite direction
        nr, nc = row - dr, col - dc
        if self._is_valid_cell(nr, nc):
            self.direction = (-dr, -dc)
            return nr, nc
        
        return None
    
    def _is_valid_cell(self, row, col):
        """Check if a cell is within bounds and hasn't been attacked"""
        return (0 <= row < GRID_SIZE and 
                0 <= col < GRID_SIZE and 
                self.player_board.view[row][col] == '.')
    
    def _find_adjacent_to_hits(self):
        """Find all valid moves adjacent to previous hits"""
        adjacent_moves = set()  # Use a set to avoid duplicates
        
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.player_board.view[r][c] == 'X':
                    for dr, dc in DIRECTIONS:
                        nr, nc = r + dr, c + dc
                        if self._is_valid_cell(nr, nc):
                            adjacent_moves.add((nr, nc))
        
        return list(adjacent_moves)
    
    def register_result(self, row, col, hit):
        """Update AI based on attack result and learn from it"""
        # Clear the valid moves cache as the board has changed
        self._valid_moves_cache = None
        
        # Get the reward for this action
        reward = 10 if hit else -1
        
        # Update Q-table
        if self.last_state and self.last_action:
            self._update_q_value(self.last_state, self.last_action, reward)
        
        # Update targeting information
        if hit:
            self._update_targeting_after_hit(row, col)
        elif self.direction:
            # If miss and we were following a direction, try opposite
            self.direction = (-self.direction[0], -self.direction[1])
    
    def _update_q_value(self, state, action, reward):
        """Update the Q-value for a state-action pair"""
        state_action = (state, action)
        current_q = self.q_table.get(state_action, 0)
        
        # Get maximum Q-value for the next state
        next_state = self.get_state_representation()
        max_next_q = self._get_max_q_value(next_state)
        
        # Update Q-value using Q-learning formula
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_next_q - current_q)
        self.q_table[state_action] = new_q
        
        # Add to history
        self.history.append((state, action, reward, next_state))
    
    def _update_targeting_after_hit(self, row, col):
        """Update targeting strategy after a hit"""
        if not self.last_hit:
            # First hit in sequence
            self.last_hit = (row, col)
        else:
            # If we already had a last hit, determine direction
            last_row, last_col = self.last_hit
            
            if last_row == row:  # Horizontal
                self.direction = (0, 1 if col > last_col else -1)
            else:  # Vertical
                self.direction = (1 if row > last_row else -1, 0)
                
            self.last_hit = (row, col)
    
    def _get_max_q_value(self, state):
        """Get the maximum Q-value for all possible actions in a state"""
        try:
            max_q = 0
            # Only check valid moves instead of all possible cells
            for action in self._get_valid_moves():
                q_value = self.q_table.get((state, action), 0)
                max_q = max(max_q, q_value)
            return max_q
        except Exception as e:
            print(f"Error in _get_max_q_value: {e}")
            return 0
    
    def end_game(self, won):
        """Called at the end of a game for final learning updates"""
        # Add a final large reward if the AI won
        if won:
            self._reward_winning_sequence()
        
        # Save the learned model
        self.save_model()
        
        # Reset for next game
        self._reset_state()
    
    def _reward_winning_sequence(self):
        """Apply rewards to the sequence of moves that led to victory"""
        for i in range(len(self.history)-1, -1, -1):
            state, action, reward, next_state = self.history[i]
            # Decay the reward as we go back in history
            bonus = 50 * (0.9 ** (len(self.history) - i - 1))
            state_action = (state, action)
            
            # Update existing Q-value with bonus
            current_q = self.q_table.get(state_action, 0)
            self.q_table[state_action] = current_q + bonus
    
    def _reset_state(self):
        """Reset the AI state for a new game"""
        self.history = []
        self.last_hit = None
        self.direction = None
        self.target_queue = []
        self._valid_moves_cache = None
        self._last_board_state = None
    
    def save_model(self):
        """Save the Q-table to a file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs("models", exist_ok=True)
            
            # Prune the Q-table before saving to reduce file size
            pruned_q_table = {k: v for k, v in self.q_table.items() if v > 0}
            
            # Use a more efficient binary protocol
            with open("models/battleship_rl_model.pkl", "wb") as f:
                pickle.dump(pruned_q_table, f, protocol=pickle.HIGHEST_PROTOCOL)
            print(f"Saved AI model successfully ({len(pruned_q_table)} states)")
        except Exception as e:
            print(f"Error saving AI model: {e}")
    
    def load_model(self):
        """Load a previously trained Q-table"""
        try:
            with open("models/battleship_rl_model.pkl", "rb") as f:
                self.q_table = pickle.load(f)
            print(f"Loaded AI model successfully with {len(self.q_table)} learned states")
        except FileNotFoundError:
            print("No pre-trained model found. Starting fresh.")
        except Exception as e:
            print(f"Error loading AI model: {e}")

    def get_next_move(self):
        """Alias for get_attack_coordinates for compatibility"""
        return self.get_attack_coordinates()