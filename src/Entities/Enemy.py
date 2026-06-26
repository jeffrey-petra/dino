import pygame

from Constants.Colors import Colors as col

ENEMY_SPAWN_RATE = (
    0.012  # Probability per frame to spawn enemy (supplemented by spawn delay)
)
ENEMY_SPEED = 7
ENEMY_WIDTH = 30
ENEMY_HEIGHT = 50


class Enemy:
    def __init__(
        self,
        x,
        y,
        width=ENEMY_WIDTH,
        height=ENEMY_HEIGHT,
        speed=ENEMY_SPEED,
        color=col.RED,
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self._base_speed = speed  # Store the initial base speed (though it will be overridden by game speed)
        self.color = color

    def update(self, current_game_speed):
        # Use the external game speed for movement
        self.x -= current_game_speed

    def is_off_screen(self):
        return self.x + self.width < 0

    def draw(self, screen):
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(screen, self.color, rect)
        # Draw border
        pygame.draw.rect(screen, col.BLACK, rect, 2)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
