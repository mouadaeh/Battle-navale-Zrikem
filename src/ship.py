class Ship:
    """Represents a ship in the Battleship game"""
    
    def __init__(self, name, size):
        self.name = name
        self.size = size
        self.coordinates = []
        self.is_horizontal = True
        
    def place(self, row, col, is_horizontal):
        """Calculate the coordinates when placing the ship"""
        self.coordinates = []
        self.is_horizontal = is_horizontal
        
        if is_horizontal:
            for i in range(self.size):
                self.coordinates.append((row, col + i))
        else:
            for i in range(self.size):
                self.coordinates.append((row + i, col))
                
    def is_hit(self, row, col):
        """Check if a given position hits this ship"""
        return (row, col) in self.coordinates
    
    def is_sunk(self, hits):
        """Check if all coordinates of the ship have been hit"""
        return all((r, c) in hits for r, c in self.coordinates)