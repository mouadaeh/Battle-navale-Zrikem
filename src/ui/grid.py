import pygame
from src.utils.constants import RED, BLACK, WHITE, GREEN, SKY_BLUE, BLUE

def draw_grid(screen, board, fonts, reveal=False, is_player_grid=True, position="center"):
    """Draw a game board grid with ships and hits/misses"""
    # Setup - Move title higher up
    title = fonts["large"].render("Bataille Navale", True, BLUE)
    screen.blit(title, (screen.get_width() // 2 - title.get_width() // 2, 10))
    
    # Create subtitle
    if is_player_grid:
        subtitle = fonts["small"].render("Votre grille", True, WHITE)
    else:
        subtitle = fonts["small"].render("Grille adversaire", True, WHITE)
    
    # Calculate grid position based on position parameter
    if position == "left":
        start_x = screen.get_width() // 4 - board.width // 2
    elif position == "right":
        start_x = 3 * screen.get_width() // 4 - board.width // 2
    else:  # center
        start_x = (screen.get_width() - board.width) // 2
    
    # Move grids down by increasing the Y offset (was -20, now +20)
    start_y = (screen.get_height() - board.height) // 2 
    
    # Calculate cell size
    cell_width = board.width / len(board.grid[0])
    cell_height = board.height / len(board.grid)
    
    # Draw the grid
    for row in range(len(board.grid)):
        for col in range(len(board.grid[row])):
            rect = pygame.Rect(
                start_x + col * cell_width,
                start_y + row * cell_height,
                cell_width,
                cell_height,
            )
            
            # Draw cells based on state
            if board.view[row][col] == 'X':
                pygame.draw.rect(screen, RED, rect)
                pygame.draw.rect(screen, BLACK, rect, 2)  # Border
            elif board.view[row][col] == 'O':
                pygame.draw.rect(screen, WHITE, rect)
                pygame.draw.rect(screen, BLACK, rect, 2)  # Border
            elif board.grid[row][col] != '.' and reveal:
                pygame.draw.rect(screen, GREEN, rect)
                pygame.draw.rect(screen, BLACK, rect, 2)  # Border
            else:
                pygame.draw.rect(screen, SKY_BLUE, rect)
                pygame.draw.rect(screen, BLUE, rect, 2)  # Border
    
    # Draw subtitle BELOW the grid instead of above it
    screen.blit(subtitle, (start_x + board.width // 2 - subtitle.get_width() // 2, 
                          start_y + board.height + 15))  # Increased from 10 to 15 pixels below the grid
    
    return start_x, start_y