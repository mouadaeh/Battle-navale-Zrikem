from src.utils.constants import GRID_SIZE
import random
import os
import pickle

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
        
        # Initialize targeting variables
        self.consecutive_hits = 0
        self.previous_hit = None
        self.original_hit = None
        self.tried_opposite = False
        self.current_ship_hits = 0
        
        # Load pre-trained model if available
        self.load_model()
    
    def get_state_representation(self):
        """Get a representation of the current board state"""
        # More efficient string concatenation using join
        return ''.join(''.join(row) for row in self.player_board.view)

    def _get_current_state(self):
        """Get current board state representation for Q-learning"""
        return self.get_state_representation()
    
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
        """Get coordinates for the next attack based on AI strategy"""
        # Try to use the Q-table for more intelligent moves
        state = self._get_current_state()
        
        # Debug output to track targeting
        print(f"Last hit: {self.last_hit}, Target queue size: {len(self.target_queue)}")
        
        # If we have a recent hit that wasn't sunk, continue targeting that ship
        if self.last_hit is not None:
            return self._target_ship()
        
        # If targeting queue is not empty, continue with that
        if self.target_queue:
            return self._process_hit_queue()
        
        # Q-learning strategy (exploitation)
        if random.random() > self.exploration_rate and state in self.q_table:
            # Get valid moves
            valid_moves = self._get_valid_moves()
            
            # Find best move from Q-table
            best_value = -float('inf')
            best_moves = []
            
            for move, value in self.q_table[state].items():
                # Convert string tuple back to actual tuple if needed
                if isinstance(move, str) and move.startswith('(') and move.endswith(')'):
                    # Safer than eval - parse the tuple manually
                    try:
                        # Extract numbers from the string tuple format
                        nums = move.strip('()').split(',')
                        if len(nums) == 2:
                            move = (int(nums[0].strip()), int(nums[1].strip()))
                    except (ValueError, IndexError):
                        # If parsing fails, skip this move
                        continue
                        
                if move in valid_moves:
                    if value > best_value:
                        best_value = value
                        best_moves = [move]
                    elif value == best_value:
                        best_moves.append(move)
            
            if best_moves:
                move = random.choice(best_moves)
                return move
        
        # Fallback to more strategic exploration
        return self._smart_random_attack()

    def _target_ship(self):
        """Target a ship after the first hit"""
        # If we don't have a last hit, pick randomly
        if not hasattr(self, 'last_hit') or self.last_hit is None:
            return self._smart_random_attack()
        
        row, col = self.last_hit
        print(f"Targeting from last hit at {row},{col}")
        
        # Check if we've already hit 5 cells (max ship size)
        if hasattr(self, 'current_ship_hits') and self.current_ship_hits >= 5:
            print("Already hit 5 cells, max ship size reached. Resetting targeting.")
            self._reset_targeting()
            return self._smart_random_attack()
        
        # IMPORTANT FIX: Check if we should try the opposite direction
        if hasattr(self, 'try_opposite') and self.try_opposite:
            print("Missed in previous direction, trying opposite direction from original hit")
            if hasattr(self, 'original_hit') and hasattr(self, 'direction'):
                orig_row, orig_col = self.original_hit
                dr, dc = self.direction
                
                # Go in the opposite direction
                next_row, next_col = orig_row - dr, orig_col - dc
                
                if self._is_valid_cell(next_row, next_col):
                    print(f"Trying opposite direction to {next_row},{next_col}")
                    self.last_hit = self.original_hit  # Reset last hit to original hit
                    self.direction = (-dr, -dc)  # Reverse direction
                    self.try_opposite = False  # Clear the flag
                    self.tried_opposite = True  # Mark that we've tried the opposite direction
                    return (next_row, next_col)
                else:
                    # If we can't try opposite direction, reset and try random
                    print("Can't try opposite direction, resetting targeting")
                    self._reset_targeting()
                    return self._smart_random_attack()
        
        # If we've established a direction (after 2+ hits), continue in that direction
        if hasattr(self, 'direction') and self.direction is not None:
            dr, dc = self.direction
            next_row, next_col = row + dr, col + dc
            
            # If we can continue in the current direction AND we're still under 5 hits, do so
            if self._is_valid_cell(next_row, next_col) and (not hasattr(self, 'current_ship_hits') or self.current_ship_hits < 5):
                print(f"Following established direction {self.direction} to {next_row},{next_col}")
                return (next_row, next_col)
        
        # CRITICAL FIX: If this is the first hit and we don't have adjacent cells queued yet, do it now
        if not self.target_queue and (not hasattr(self, 'direction') or self.direction is None):
            print("First hit detected - adding adjacent cells to queue")
            self._add_adjacent_to_queue(row, col)
            
            # Store the original hit for later reference
            if not hasattr(self, 'original_hit') or self.original_hit is None:
                self.original_hit = (row, col)
            
            # Process the first direction from the queue
            if self.target_queue:
                return self._process_hit_queue()
        
        # If we still have targets in the queue, use them
        if self.target_queue:
            print("Using next cell from target queue")
            return self._process_hit_queue()
        
        # If we can't go in any direction and the queue is empty, reset targeting
        print("Can't continue in any direction and queue is empty, resetting targeting")
        self._reset_targeting()
        return self._smart_random_attack()
    
    def _add_adjacent_to_queue(self, row, col):
        """Add all valid adjacent cells to the targeting queue"""
        # Make sure we have a target queue
        if not hasattr(self, 'target_queue'):
            self.target_queue = []
        
        # Clear existing queue to avoid duplicates
        self.target_queue = []
        
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # right, down, left, up
        
        # Add all valid adjacent cells to the queue
        for dr, dc in directions:
            next_row, next_col = row + dr, col + dc
            if self._is_valid_cell(next_row, next_col):
                self.target_queue.append((next_row, next_col))
                print(f"Added adjacent cell {next_row},{next_col} to target queue")
        
        print(f"Target queue now has {len(self.target_queue)} cells")

    def _process_hit_queue(self):
        """Process the next target in the queue"""
        if not self.target_queue:
            return self._smart_random_attack()
            
        return self.target_queue.pop(0)

    def _is_valid_cell(self, row, col):
        """Check if a cell is valid for targeting"""
        # Make sure the cell is within the grid
        if row < 0 or row >= 10 or col < 0 or col >= 10:
            return False
        
        # Check if the cell has already been attacked
        try:
            board_view = self.player_board.view
            return board_view[row][col] == '.'
        except:
            # Fallback if there's an issue accessing the board
            return False

    def _smart_random_attack(self):
        """Make a smarter random attack using a checkerboard pattern and avoiding isolated cells"""
        valid_moves = self._get_valid_moves()
        
        if not valid_moves:
            return (0, 0)  # No valid moves left
        
        # Filter out isolated cells (single cells with hits or misses on all sides)
        non_isolated_moves = []
        for r, c in valid_moves:
            # Skip if this is an isolated cell
            if self._is_isolated_cell(r, c):
                continue
            non_isolated_moves.append((r, c))
        
        # If we have non-isolated moves, prefer those
        if non_isolated_moves:
            valid_moves = non_isolated_moves
        
        # Prefer checkerboard pattern for better ship finding
        checkerboard_moves = []
        for r, c in valid_moves:
            if (r + c) % 2 == 0:  # Chess/checkerboard pattern
                checkerboard_moves.append((r, c))
        
        # If we have checkerboard moves, choose one randomly
        if checkerboard_moves:
            return random.choice(checkerboard_moves)
        
        # Otherwise choose any valid move
        return random.choice(valid_moves)
    
    def _is_isolated_cell(self, row, col):
        """Check if a cell is isolated (surrounded by hits or misses on all sides)"""
        # Skip if this cell is already checked
        if self.player_board.view[row][col] != '.':
            return False
        
        # Count adjacent cells that are hits or misses
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        adjacent_count = 0
        adjacent_checked = 0
        
        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                adjacent_count += 1
                if self.player_board.view[nr][nc] in ['X', 'O']:  # Hit or miss
                    adjacent_checked += 1
        
        # If all adjacent cells are checked, this is an isolated cell
        return adjacent_count > 0 and adjacent_checked == adjacent_count

    def register_result(self, row, col, hit):
        """Process the result of an attack and update targeting strategy"""
        # Update Q-table
        if hasattr(self, 'last_state') and hasattr(self, 'last_action'):
            reward = 1.0 if hit else -0.1
            self._update_q_value(self.last_state, self.last_action, reward)
        
        # Store current state and action for next update
        self.last_state = self._get_current_state()
        self.last_action = (row, col)
        
        # Update ship targeting variables
        if hit:
            # Count consecutive hits
            if not hasattr(self, 'current_ship_hits'):
                self.current_ship_hits = 0
            self.current_ship_hits += 1
            
            # If this is the first hit on this ship
            if not hasattr(self, 'last_hit') or not self.last_hit:
                self.last_hit = (row, col)
                self.original_hit = (row, col)
                # Fix: Always update previous_hit with the first hit
                self.previous_hit = (row, col)
                print(f"First hit at {row},{col}")
            
            # If we already have a direction, continue with it
            elif hasattr(self, 'direction') and self.direction:
                self.last_hit = (row, col)
                print(f"Hit along direction {self.direction} at {row},{col}")
            
            # If this is a second hit, establish the direction and clear the queue
            elif hasattr(self, 'last_hit') and self.last_hit != (row, col):
                prev_row, prev_col = self.last_hit
                
                # Calculate direction vector
                if row == prev_row:  # Horizontal alignment
                    dc = 1 if col > prev_col else -1
                    self.direction = (0, dc)
                    print(f"Established horizontal direction {self.direction}")
                elif col == prev_col:  # Vertical alignment
                    dr = 1 if row > prev_row else -1
                    self.direction = (dr, 0)
                    print(f"Established vertical direction {self.direction}")
                else:
                    # This shouldn't happen normally, but handle it
                    print(f"Warning: Non-aligned hits at {self.last_hit} and {row},{col}.")
                    # Set a default direction
                    self.direction = (0, 1)  # Try horizontal first
                
                # Update previous_hit and last_hit
                self.previous_hit = self.last_hit
                self.last_hit = (row, col)
                
                # Clear the target queue as we now have a direction
                self.target_queue = []
                print("Cleared target queue to focus on established direction")
            
            # Check if we've hit the maximum ship size
            if self.current_ship_hits >= 5:
                print(f"Hit 5 squares - ship is maximum size, resetting targeting")
                self._reset_targeting()
        else:
            # Handle miss
            if hasattr(self, 'direction') and self.direction:
                # If we've already tried the opposite direction and missed
                if hasattr(self, 'tried_opposite') and self.tried_opposite:
                    # We've tried both directions and missed - COMPLETE RESET
                    print(f"Missed in both directions, ship of {self.current_ship_hits} length is found")
                    self._reset_targeting()
                else:
                    # IMPORTANT FIX: Set flag to try opposite direction on next move
                    print(f"Missed at {row},{col}, will try opposite direction on next move")
                    self.try_opposite = True
                    
                    # If we were in the middle of a series of hits along a direction,
                    # revert to the original hit before trying opposite direction
                    if hasattr(self, 'original_hit'):
                        print(f"Reverting to original hit at {self.original_hit}")
            else:
                # Regular miss with no established direction - just continue checking other directions
                print(f"Simple miss at {row},{col}")

    def _reset_targeting(self):
        """Reset all targeting variables after completing a ship"""
        # Instead of deleting attributes, set them to initial values
        self.last_hit = None
        self.original_hit = None
        self.direction = None
        self.current_ship_hits = 0
        self.tried_opposite = False
        self.try_opposite = False
        
        # IMPORTANT: Clear the target queue completely
        self.target_queue = []
        print("Reset targeting for next ship - cleared all targeting variables and queue")

    def _update_q_value(self, state, action, reward):
        """Update the Q-value for a state-action pair"""
        # Initialize state in Q-table if not already there
        if state not in self.q_table:
            self.q_table[state] = {}
        
        # Initialize action in state's Q-values if not already there
        if action not in self.q_table[state]:
            self.q_table[state][action] = 0.0
        
        # Q-learning update formula
        # Q(s,a) = Q(s,a) + learning_rate * (reward + discount_factor * max_a' Q(s',a') - Q(s,a))
        # For simplicity, we're using a basic update without the max future value
        self.q_table[state][action] += self.learning_rate * (reward - self.q_table[state][action])
    
    def load_model(self):
        """Load the Q-table from disk if available"""
        try:
            if os.path.exists('models/battleship_rl_model.pkl'):
                with open('models/battleship_rl_model.pkl', 'rb') as f:
                    self.q_table = pickle.load(f)
                print(f"Loaded AI model with {len(self.q_table)} states")
            else:
                print("No pre-trained model found, using new Q-table")
        except Exception as e:
            print(f"Error loading AI model: {e}")
            self.q_table = {}
    
    def save_model(self):
        """Save the Q-table to disk"""
        try:
            # Create directory if it doesn't exist
            os.makedirs('models', exist_ok=True)
            
            # Ensure the Q-table is in the correct format for serialization
            processed_q_table = {}
            for state, actions in self.q_table.items():
                # Convert any unhashable keys to strings
                state_key = state
                processed_actions = {}
                
                for action, value in actions.items():
                    # Ensure action is a tuple, not a list (lists aren't hashable)
                    if isinstance(action, list):
                        action_key = tuple(action)
                    else:
                        action_key = action
                    processed_actions[action_key] = value
                
                processed_q_table[state_key] = processed_actions
            
            # Save the processed Q-table
            with open('models/battleship_rl_model.pkl', 'wb') as f:
                pickle.dump(processed_q_table, f)
            
            print(f"Saved AI model with {len(processed_q_table)} states")
        except Exception as e:
            print(f"Error saving AI model: {e}")
    
    def reset_game_state(self):
        """Reset the AI's state for a new game while preserving learning"""
        print("Resetting AI game state")
        self.last_hit = None
        self.previous_hit = None
        self.original_hit = None
        self.direction = None
        self.consecutive_hits = 0
        self.current_ship_hits = 0
        self.tried_opposite = False
        self.target_queue = []
        self.last_state = None
        self.last_action = None
        # Keep the Q-table intact for learning

    def train_against_self(self, num_games=200, save_interval=20):
        """Train AI by playing against itself for many games"""
        import time
        from src.board import Board
        
        start_time = time.time()
        original_exploration = self.exploration_rate
        wins = 0
        
        print(f"Starting AI self-training for {num_games} games...")
        print(f"Initial Q-table size: {len(self.q_table)} states")
        
        for i in range(num_games):
            # Use higher exploration during training to discover new strategies
            self.exploration_rate = 0.5
            
            # Create boards for self-play
            board1 = Board()  # AI will attack this board
            board2 = Board()  # AI will use this board for defense
            
            # Place ships randomly on both boards
            self._place_ships_randomly(board1)
            self._place_ships_randomly(board2)
            
            # Game state tracking
            all_hits1 = []  # Hits on board 1
            all_hits2 = []  # Hits on board 2
            
            # Play until one side wins
            turn = 0
            while not self._all_ships_sunk(board1, all_hits1) and not self._all_ships_sunk(board2, all_hits2):
                turn += 1
                
                # Reset AI state for a clean game
                temp_board = self.player_board
                
                # AI attacks board1
                self.player_board = board1
                self.reset_game_state()
                
                # Choose a move and update results
                state1 = self._get_current_state()
                row, col = self.get_attack_coordinates()
                hit1 = board1.grid[row][col] == 'S'
                
                # Update board view
                board1.view[row][col] = 'X' if hit1 else 'O'
                
                # Process results
                if hit1:
                    all_hits1.append((row, col))
                    self._update_q_value(state1, (row, col), 1.0)
                else:
                    self._update_q_value(state1, (row, col), -0.1)
                
                # Check if board1 ships are all sunk
                if self._all_ships_sunk(board1, all_hits1):
                    # Higher reward for winning
                    self._update_q_value(state1, (row, col), 5.0)
                    wins += 1
                    break
                
                # Restore original board
                self.player_board = temp_board
            
            # Every few games, save progress and report
            if (i + 1) % save_interval == 0 or i == num_games - 1:
                elapsed = time.time() - start_time
                self.save_model()
                win_rate = (wins / (i + 1)) * 100
                print(f"Game {i+1}/{num_games}: Win rate {win_rate:.1f}%, " 
                      f"Q-table size: {len(self.q_table)} states ({elapsed:.1f}s)")
        
        # Reset exploration rate
        self.exploration_rate = original_exploration
        print(f"Training complete! Final Q-table has {len(self.q_table)} states")
        self.save_model()
    
    def _place_ships_randomly(self, board):
        """Place ships randomly on a board for training"""
        from src.utils.constants import SHIPS
        
        for ship_info in SHIPS:
            ship_size = ship_info["size"]
            placed = False
            
            # Try to place each ship up to 100 times
            for _ in range(100):
                row = random.randint(0, len(board.grid) - 1)
                col = random.randint(0, len(board.grid[0]) - 1)
                horizontal = random.choice([True, False])
                
                # Check if placement is valid
                valid = True
                if horizontal:
                    if col + ship_size > len(board.grid[0]):
                        valid = False
                    else:
                        for c in range(col, col + ship_size):
                            if board.grid[row][c] != '.':
                                valid = False
                                break
                else:
                    if row + ship_size > len(board.grid):
                        valid = False
                    else:
                        for r in range(row, row + ship_size):
                            if board.grid[r][col] != '.':
                                valid = False
                                break
                
                # If valid placement, place the ship
                if valid:
                    if horizontal:
                        for c in range(col, col + ship_size):
                            board.grid[row][c] = 'S'
                    else:
                        for r in range(row, row + ship_size):
                            board.grid[r][col] = 'S'
                    placed = True
                    break
            
            if not placed:
                print(f"Warning: Failed to place a ship of size {ship_size}")

    def _all_ships_sunk(self, board, hits):
        """Check if all ships on a board are sunk based on hits"""
        # Count total ship cells on the board
        ship_cells = 0
        for row in board.grid:
            ship_cells += row.count('S')
        
        # Check if all ship cells have been hit
        return len(hits) >= ship_cells