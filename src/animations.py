import pygame
import random
from src.utils.constants import RED, WHITE

class AnimatedMessage:
    """Class for animated floating messages"""
    def __init__(self, text, color, duration=60, start_size=20, max_size=30, fade_in=10, fade_out=20):
        self.text = text
        self.color = color
        self.duration = duration
        self.timer = duration
        self.start_size = start_size
        self.max_size = max_size
        self.current_size = start_size
        self.fade_in = fade_in
        self.fade_out = fade_out
        self.alpha = 128  # Start semi-transparent
        
    def update(self):
        """Update the message animation"""
        self.timer -= 1
        
        # Size animation
        if self.timer > self.duration - self.fade_in:
            # Fade in (grow)
            progress = (self.duration - self.timer) / self.fade_in
            self.current_size = self.start_size + (self.max_size - self.start_size) * progress
            self.alpha = min(255, int(128 + 127 * progress))
        elif self.timer < self.fade_out:
            # Fade out (shrink)
            progress = self.timer / self.fade_out
            self.current_size = self.max_size * progress
            self.alpha = max(0, int(255 * progress))
        else:
            # Stay at max size in the middle
            self.current_size = self.max_size
            self.alpha = 255
            
        return self.timer > 0
        
    def draw(self, screen, x, y):
        """Draw the message at the specified position"""
        # Create a font at the current size
        message_font = pygame.font.SysFont("Arial", int(self.current_size))
        text_surface = message_font.render(self.text, True, self.color)
        
        # Apply transparency
        text_surface.set_alpha(self.alpha)
        
        # Center the text at the position
        text_rect = text_surface.get_rect(center=(x, y))
        screen.blit(text_surface, text_rect)

class EffectsManager:
    """Manages visual effects like hits and misses"""
    def __init__(self):
        self.effects = []
        self.animated_messages = []
        self.victory_particles = []
    
    def create_hit_effect(self, x, y):
        """Create a hit effect at the specified position"""
        self.effects.append({"type": "hit", "x": x, "y": y, "radius": 5, "time": 20})
    
    def create_miss_effect(self, x, y):
        """Create a miss effect at the specified position"""
        self.effects.append({"type": "miss", "x": x, "y": y, "radius": 5, "time": 20})
    
    def create_animated_message(self, text, color, x, y, duration=60):
        """Create and add an animated message to the list"""
        self.animated_messages.append((AnimatedMessage(text, color, duration), x, y))
    
    def update_effects(self, screen):
        """Update and draw all visual effects"""
        expired_effects = []
        
        # Update effects
        for i, effect in enumerate(self.effects):
            if effect["type"] == "hit":
                pygame.draw.circle(screen, RED, (effect["x"], effect["y"]), effect["radius"])
            elif effect["type"] == "miss":
                pygame.draw.circle(screen, WHITE, (effect["x"], effect["y"]), effect["radius"], 2)
            effect["radius"] += 1
            effect["time"] -= 1
            if effect["time"] <= 0:
                expired_effects.append(i)
        
        # Remove expired effects in reverse order to maintain correct indices
        for i in sorted(expired_effects, reverse=True):
            self.effects.pop(i)
    
    def update_animated_messages(self, screen):
        """Update and draw all animated messages"""
        for msg_tuple in self.animated_messages[:]:
            msg, x, y = msg_tuple
            if not msg.update():
                self.animated_messages.remove(msg_tuple)
            else:
                msg.draw(screen, x, y)
    
    def start_turn_transition(self, resolution, is_player_turn, color_player, color_computer):
        """Create a visual effect for turn transition"""
        if is_player_turn:
            text = "À VOUS DE JOUER"
            color = color_player
        else:
            text = "TOUR DE L'ORDINATEUR"
            color = color_computer
        
        # Create a big animated message in the center of the screen
        self.create_animated_message(text, color, 
                                    resolution[0] // 2, 
                                    resolution[1] // 2, 
                                    duration=120)
    
    def create_victory_animation(self, screen_width, screen_height):
        """Create victory particles animation"""
        colors = [(0, 255, 0), (255, 223, 0), (255, 255, 255)]  # Vert, or, blanc
        for _ in range(100):  # Nombre de particules
            particle = {
                'x': random.randint(0, screen_width),
                'y': screen_height + 10,
                'speed': random.uniform(5, 15),
                'color': random.choice(colors),
                'size': random.randint(5, 15),
                'angle': random.uniform(-0.5, 0.5)
            }
            self.victory_particles.append(particle)
    
    def update_victory_animation(self, screen):
        """Update and draw victory particles"""
        for particle in self.victory_particles[:]:
            particle['y'] -= particle['speed']
            particle['x'] += particle['angle']
            
            # Dessiner la particule
            pygame.draw.circle(screen, particle['color'], 
                             (int(particle['x']), int(particle['y'])), 
                             particle['size'])
            
            # Supprimer les particules qui sont sorties de l'écran
            if particle['y'] < -20:
                self.victory_particles.remove(particle)