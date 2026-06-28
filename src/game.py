import random

import pygame

from Constants.Colors import Colors as col
from Constants.Keybinds import Keybinds as keyb
from Entities.Enemy import Enemy
from Entities.Player import Player

# Game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GROUND_LEVEL = 450

PLAYER_SIZE = 40
PLAYER_DUCK_SIZE = 25

ENEMY_WIDTH = 30
ENEMY_HEIGHT = 50
ENEMY_MIN_GAP = 220  # Minimum horizontal gap between enemies
ENEMY_MIN_SPAWN_DELAY = 60  # Minimum frames between spawn attempts
ENEMY_MAX_SPAWN_DELAY = 120  # Maximum frames between spawn attempts


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Dino Game - Test Window")
        self.clock = pygame.time.Clock()
        self.running = True
        self.font = pygame.font.Font(None, 36)
        self.player = Player(100, GROUND_LEVEL)
        self.enemies = []
        self.game_over = False
        self.score = 0
        self.current_speed = (
            5  # Initial speed of the game (pixels per frame/update cycle)
        )
        self.spawn_timer = random.randint(ENEMY_MIN_SPAWN_DELAY, ENEMY_MAX_SPAWN_DELAY)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == keyb.PAUSE:
                    self.running = False
                elif event.key == keyb.JUMP:
                    self.player.jump()
                elif event.key == keyb.DUCK:
                    self.player.start_duck()
                elif event.key == keyb.RESET and self.game_over:
                    self.restart_game()
            elif event.type == pygame.KEYUP:
                if event.key == keyb.DUCK:
                    self.player.stop_duck()

    def restart_game(self):
        self.player = Player(100, GROUND_LEVEL)
        self.enemies = []
        self.game_over = False
        self.score = 0
        self.current_speed = 5  # Reset speed on restart

    def update(self):
        if self.game_over:
            return

        # --- DIFFICULTY SCALING (Speed Increase) ---
        # Gradually increase the speed based on elapsed time/score
        # Speed increases by 0.01 every second of gameplay
        speed_increase = self.score / 5000.0  # Slow, continuous increase
        self.current_speed = min(20, self.current_speed + speed_increase)

        self.player.update()

        # Spawn enemies with a minimum interval and spacing so the game remains fair.
        self.spawn_timer -= 1
        if self.spawn_timer <= 0:
            if self.can_spawn_enemy():
                self.spawn_enemy()
                self.spawn_timer = random.randint(
                    ENEMY_MIN_SPAWN_DELAY, ENEMY_MAX_SPAWN_DELAY
                )
            else:
                self.spawn_timer = 10

        # Update all enemies using the global speed
        for enemy in self.enemies:
            enemy.update(self.current_speed)

        # Remove off-screen enemies and update score
        initial_len = len(self.enemies)
        self.enemies = [e for e in self.enemies if not e.is_off_screen()]

        passed_count = initial_len - len(self.enemies)
        self.score += passed_count * 1  # Score increases based on successful passes

        # Check collision with enemies
        self.check_collisions()

    def spawn_enemy(self):
        # Use obstacle spacing and a little variety for a more Chrome-style feel.
        enemy_type = random.choice(["cactus", "cactus", "cactus", "ptero"])

        if enemy_type == "ptero" and self.current_speed >= 8:
            width = 35
            height = 30
            y = GROUND_LEVEL + PLAYER_SIZE - height - random.choice([80, 110])
            color = col.GRAY
        else:
            width = ENEMY_WIDTH + random.randint(-5, 10)
            height = ENEMY_HEIGHT + random.randint(-20, 10)
            height = max(20, height)
            y = GROUND_LEVEL + PLAYER_SIZE - height
            color = col.RED

        enemy = Enemy(SCREEN_WIDTH, y, width=width, height=height, color=color)
        self.enemies.append(enemy)

    def can_spawn_enemy(self):
        if not self.enemies:
            return True
        last_enemy = self.enemies[-1]
        distance_from_spawn = SCREEN_WIDTH - (last_enemy.x + last_enemy.width)
        required_gap = max(ENEMY_MIN_GAP, int(self.current_speed * 35))
        return distance_from_spawn >= required_gap

    def check_collisions(self):
        player_rect = pygame.Rect(
            self.player.x, self.player.y, self.player.width, self.player.height
        )
        for enemy in self.enemies:
            if player_rect.colliderect(enemy.get_rect()):
                self.game_over = True

    def draw(self):
        self.screen.fill(col.WHITE)

        # Draw ground
        pygame.draw.line(
            self.screen,
            col.BLACK,
            (0, GROUND_LEVEL + PLAYER_SIZE),
            (SCREEN_WIDTH, GROUND_LEVEL + PLAYER_SIZE),
            3,
        )

        # Draw player
        self.player.draw(self.screen)

        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(self.screen)

        # Draw title
        title = self.font.render("Dino Game - Test Window", True, col.BLACK)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 20))
        self.screen.blit(title, title_rect)

        # Draw info text
        info_font = pygame.font.Font(None, 20)
        info_text = info_font.render(
            "UP: Jump | DOWN: Duck | ESC: Exit", True, col.GRAY
        )
        info_rect = info_text.get_rect(topleft=(10, 50))
        self.screen.blit(info_text, info_rect)

        # Draw score
        score_text = info_font.render(f"Score: {self.score}", True, col.BLACK)
        self.screen.blit(score_text, (10, 75))

        # Draw FPS
        fps_text = info_font.render(
            f"FPS: {int(self.clock.get_fps())}", True, col.BLACK
        )
        self.screen.blit(fps_text, (SCREEN_WIDTH - 100, 10))

        # Draw game over message
        if self.game_over:
            game_over_text = self.font.render(
                "GAME OVER! Press R to restart", True, col.RED
            )
            game_over_rect = game_over_text.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            )
            self.screen.blit(game_over_text, game_over_rect)

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
