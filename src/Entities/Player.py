import pygame

from Constants.Colors import Colors as col

# Physics constants
GRAVITY = 0.8
GRAVITY_BOOST = 0.5  # Additional gravity when down key is pressed
JUMP_STRENGTH = 15
PLAYER_SIZE = 40
PLAYER_DUCK_SIZE = 25


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = PLAYER_SIZE
        self.height = PLAYER_SIZE
        self.velocity_y = 0
        self.is_jumping = False
        self.is_ducking = False
        self.is_down_pressed = False  # Track if down key is held
        self.ground_bottom = y + PLAYER_SIZE  # Bottom position where feet touch ground

    def jump(self):
        if not self.is_jumping:
            self.velocity_y = -JUMP_STRENGTH
            self.is_jumping = True

    def start_duck(self):
        self.is_ducking = True
        self.is_down_pressed = True
        self.height = PLAYER_DUCK_SIZE

    def stop_duck(self):
        self.is_ducking = False
        self.is_down_pressed = False
        self.height = PLAYER_SIZE

    def update(self):
        # Apply gravity
        gravity = GRAVITY
        if self.is_down_pressed:
            gravity += GRAVITY_BOOST
        self.velocity_y += gravity
        self.y += self.velocity_y

        # Check if landed on ground (bottom of player hits ground)
        if self.y + self.height >= self.ground_bottom:
            self.y = self.ground_bottom - self.height
            self.velocity_y = 0
            self.is_jumping = False

    def draw(self, screen):
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(screen, col.GREEN, rect)
        # Draw border
        pygame.draw.rect(screen, col.BLACK, rect, 2)
