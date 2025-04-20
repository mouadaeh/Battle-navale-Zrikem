import pygame
from src.utils.constants import BLACK

def draw_button(screen, text, x, y, width, height, color, hover_color, font, action=None):
    """Draw an interactive button"""
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    button_rect = pygame.Rect(x, y, width, height)

    if button_rect.collidepoint(mouse):
        pygame.draw.rect(screen, hover_color, button_rect)
        if click[0] == 1 and action:
            action()
    else:
        pygame.draw.rect(screen, color, button_rect)

    text_surface = font.render(text, True, BLACK)
    text_rect = text_surface.get_rect(center=(x + width // 2, y + height // 2))
    screen.blit(text_surface, text_rect)