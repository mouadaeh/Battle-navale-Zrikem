from src.utils.constants import GRID_SIZE, CELL_SIZE

class Board:
    """Represents a game board with ships and attacks"""
    
    def __init__(self):
        self.grid = [['.' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.view = [['.' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.ships = []
        self.hits = []
        self.misses = []
        self.width = CELL_SIZE * GRID_SIZE
        self.height = CELL_SIZE * GRID_SIZE
    
    def place_ship(self, ship, row, col, is_horizontal):
        """Place a ship on the board"""
        # Check bounds
        if row < 0 or col < 0:
            return False
        
        # Check if placement is valid
        if is_horizontal and col + ship.size > GRID_SIZE:
            return False
        if not is_horizontal and row + ship.size > GRID_SIZE:
            return False
        
        # Check for overlap with other ships
        if is_horizontal:
            for i in range(ship.size):
                if self.grid[row][col + i] == 'S':
                    return False
        else:
            for i in range(ship.size):
                if self.grid[row + i][col] == 'S':
                    return False
        
        # Place the ship
        ship.place(row, col, is_horizontal)
        
        # Update the grid
        for r, c in ship.coordinates:
            self.grid[r][c] = 'S'
        
        # Add to ships list
        self.ships.append(ship)
        return True
    
    def receive_attack(self, row, col):
        """Receive an attack at the specified coordinates"""
        if self.view[row][col] != '.':
            return False  # Already attacked this cell
        
        if self.grid[row][col] == 'S':
            self.view[row][col] = 'X'
            self.hits.append((row, col))
            return True  # Hit
        else:
            self.view[row][col] = 'O'
            self.misses.append((row, col))
            return False  # Miss
    
    def all_ships_sunk(self):
        """Check if all ships have been sunk"""
        for ship in self.ships:
            if not ship.is_sunk(self.hits):
                return False
        return True