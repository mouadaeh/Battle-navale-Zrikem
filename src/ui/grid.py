import pygame
from src.utils.constants import RED, BLACK, WHITE, GREEN, SKY_BLUE, BLUE

def draw_grid(screen, board, fonts, reveal=False, is_player_grid=True):
    """Draw a game board grid with ships and hits/misses"""
    # Setup
    title = fonts["large"].render("Bataille Navale", True, BLUE)
    screen.blit(title, (screen.get_width() // 2 - title.get_width() // 2, 10))
    
    # Subtitle
    if is_player_grid:
        subtitle = fonts["small"].render("Votre grille", True, WHITE)
    else:
        subtitle = fonts["small"].render("Grille adversaire", True, WHITE)
    
    # Calculate grid position
    start_x = (screen.get_width() - board.width) // 2
    start_y = (screen.get_height() - board.height) // 2
    
    # Draw subtitle
    screen.blit(subtitle, (start_x, start_y - 50))
    
    # Draw column labels (A-J)
    for col in range(len(board.grid[0])):
        label = chr(65 + col)  # ASCII 'A' starts at 65
        col_text = pygame.font.Font(None, 24).render(label, True, WHITE)
        screen.blit(col_text, (start_x + col * board.width / len(board.grid[0]) + board.width / len(board.grid[0]) / 2 - 5, 
                              start_y - 25))
    
    # Draw row labels (1-10)
    for row in range(len(board.grid)):
        label = str(row + 1)
        row_text = pygame.font.Font(None, 24).render(label, True, WHITE)
        screen.blit(row_text, (start_x - 25, 
                              start_y + row * board.height / len(board.grid) + board.height / len(board.grid) / 2 - 5))
    
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
            elif board.grid[row][col] == 'S' and reveal:
                pygame.draw.rect(screen, GREEN, rect)
                pygame.draw.rect(screen, BLACK, rect, 2)  # Border
            else:
                pygame.draw.rect(screen, SKY_BLUE, rect)
                pygame.draw.rect(screen, BLUE, rect, 2)  # Border
    
    return start_x, start_y