import pygame
from src.utils.constants import RED, BLACK, WHITE, GREEN, SKY_BLUE, BLUE, WATER_PATH,GRAY

def draw_grid(screen, board, fonts, assets=None, reveal=False, is_player_grid=True, position="center"):
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
    
    # Draw water background if available
    has_water_image = assets and "water" in assets
    if has_water_image:
        # Get the water image
        water_img = assets["water"]
        water_width = water_img.get_width()
        water_height = water_img.get_height()
        
        # Create a temporary surface for the entire grid and tile the water image
        grid_surface = pygame.Surface((board.width, board.height))
        
        # Tile the water image across the grid
        for y in range(0, int(board.height), water_height):
            for x in range(0, int(board.width), water_width):
                grid_surface.blit(water_img, (x, y))
        
        # Draw the tiled water background
        screen.blit(grid_surface, (start_x, start_y))
    
    # Draw the grid cells and content
    for row in range(len(board.grid)):
        for col in range(len(board.grid[row])):
            rect = pygame.Rect(
                start_x + col * cell_width,
                start_y + row * cell_height,
                cell_width,
                cell_height,
            )
            
            # Only draw sky blue background if we don't have a water image
            if not has_water_image:
                pygame.draw.rect(screen, SKY_BLUE, rect)
            
            # Always draw grid lines
            pygame.draw.rect(screen, GRAY, rect, 1)
            
            # Draw ships, hits and misses
            if board.view[row][col] == 'X':
                # Hit marker
                pygame.draw.line(screen, RED, 
                               (rect.left + 5, rect.top + 5), 
                               (rect.right - 5, rect.bottom - 5), 3)
                pygame.draw.line(screen, RED, 
                               (rect.right - 5, rect.top + 5), 
                               (rect.left + 5, rect.bottom - 5), 3)
            elif board.view[row][col] == 'O':
                # Miss marker
                pygame.draw.circle(screen, WHITE, rect.center, min(rect.width, rect.height) // 3, 2)
            elif board.grid[row][col] != '.' and reveal:
                # Ship marker
                ship_rect = rect.inflate(-4, -4)  # Make ship slightly smaller than cell
                pygame.draw.rect(screen, GREEN, ship_rect)
    
    # Draw subtitle BELOW the grid instead of above it
    screen.blit(subtitle, (start_x + board.width // 2 - subtitle.get_width() // 2, 
                          start_y + board.height + 15))  # Increased from 10 to 15 pixels below the grid
    
    return start_x, start_y