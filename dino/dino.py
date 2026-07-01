# Ensure pygame is installed and import it
import importlib
import subprocess
import sys
import random

def ensure_pygame():
    try:
        return importlib.import_module('pygame')
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pygame'])
        return importlib.import_module('pygame')

pygame = ensure_pygame()

# Game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
GREEN = (0, 200, 0)
BLUE = (0, 0, 255)
GROUND_LEVEL = 450

# Physics constants
GRAVITY = 0.8
GRAVITY_BOOST = 0.5
JUMP_STRENGTH = 15
PLAYER_SIZE = 40
PLAYER_DUCK_SIZE = 25

# Enemy constants
ENEMY_SPEED = 7
ENEMY_WIDTH = 30
ENEMY_HEIGHT = 50
ENEMY_MIN_GAP = 220
ENEMY_MIN_SPAWN_DELAY = 25
ENEMY_MAX_SPAWN_DELAY = 100

class FuzzyDinoAI:
    def __init__(self):
        self.last_debug = {}

    def fuzzify_trapezoid(self, x, a, b, c, d):
        """Creates a fuzzy membership value between 0.0 and 1.0 based on a trapezoidal curve."""
        if x <= a or x >= d: return 0.0
        if b <= x <= c: return 1.0
        if a < x < b: return (x - a) / (b - a)
        if c < x < d: return (d - x) / (d - c)

    def process(self, distance, obstacle_width, obstacle_height, speed, is_bird, bird_position):
        # 1. FUZZIFICATION
        ttc = distance / speed if speed > 0 else 999
        w_narrow = self.fuzzify_trapezoid(obstacle_width, 0, 0, 40, 65)
        w_wide = self.fuzzify_trapezoid(obstacle_width, 45, 75, 999, 999)
        h_short = self.fuzzify_trapezoid(obstacle_height, 0, 0, 50, 70)
        h_tall = self.fuzzify_trapezoid(obstacle_height, 50, 75, 999, 999)

        # 2. RULE EVALUATION
        timing_early = min(h_short, w_narrow)
        timing_mid = min(h_tall, w_narrow)
        timing_late = w_wide

        # 3. DEFUZZIFICATION
        ttc_early, ttc_mid, ttc_late = 24.0, 16.0, 10.0
        sum_weights = timing_early + timing_mid + timing_late
        target_jump_ttc = (timing_early * ttc_early + timing_mid * ttc_mid + timing_late * ttc_late) / sum_weights if sum_weights > 0 else ttc_mid

        # 4. FIXED DUCKING & JUMPING LOGIC
        # bird_position: 0 = Low (Jump), 1 = Middle (Duck), 2 = High (Duck)
        should_duck = False
        should_jump = False

        duck_ttc_limit = 22.0
        if obstacle_width > 40:
            duck_ttc_limit += min(18.0, (obstacle_width - 40) * 0.2)

        if is_bird:
            # Low birds should be jumped over; higher birds should be ducked under.
            if bird_position == 0 and ttc <= target_jump_ttc:
                should_jump = True
            elif bird_position in (1, 2) and ttc <= duck_ttc_limit:
                should_duck = True
        else:
            # Standard Cactus logic
            if 0 < ttc <= target_jump_ttc:
                should_jump = True

        self.last_debug = {
            'distance': round(distance, 2),
            'ttc': round(ttc, 2),
            'obstacle_width': obstacle_width,
            'obstacle_height': obstacle_height,
            'target_jump_ttc': round(target_jump_ttc, 2),
            'duck_ttc_limit': round(duck_ttc_limit, 2),
            'is_bird': is_bird,
            'bird_position': bird_position,
            'decision': 'jump' if should_jump else 'duck' if should_duck else 'none',
            'should_jump': should_jump,
            'should_duck': should_duck,
        }

        return should_jump, should_duck


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = PLAYER_SIZE
        self.height = PLAYER_SIZE
        self.velocity_y = 0
        self.is_jumping = False
        self.is_ducking = False
        self.is_down_pressed = False
        self.ground_bottom = y + PLAYER_SIZE

    def jump(self):
        if not self.is_jumping:
            self.velocity_y = -JUMP_STRENGTH
            self.is_jumping = True
            self.stop_duck()
    
    def start_duck(self):
        if not self.is_ducking and not self.is_jumping:
            self.is_ducking = True
            self.is_down_pressed = True
            self.height = PLAYER_DUCK_SIZE
            self.y += (PLAYER_SIZE - PLAYER_DUCK_SIZE)
    
    def stop_duck(self):
        if self.is_ducking:
            self.is_ducking = False
            self.is_down_pressed = False
            self.height = PLAYER_SIZE
            self.y -= (PLAYER_SIZE - PLAYER_DUCK_SIZE)
    
    def update(self):
        gravity = GRAVITY
        if self.is_down_pressed:
            gravity += GRAVITY_BOOST
        self.velocity_y += gravity
        self.y += self.velocity_y
        
        if self.y + self.height >= self.ground_bottom:
            self.y = self.ground_bottom - self.height
            self.velocity_y = 0
            self.is_jumping = False
            
    def draw(self, screen):
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(screen, BLUE if self.is_ducking else GREEN, rect)
        pygame.draw.rect(screen, BLACK, rect, 2)


class Enemy:
    def __init__(self, x, y, width=ENEMY_WIDTH, height=ENEMY_HEIGHT, color=RED, kind='cactus'):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.kind = kind
        
        # Calculate actual logical bird position based on its Y-coordinate relative to the player.
        # 0 = Low (jump over), 1 = Middle (duck), 2 = High (duck)
        enemy_bottom = self.y + self.height
        if 'bird' in self.kind:
            if enemy_bottom >= GROUND_LEVEL + 35:
                self.bird_position = 0
            elif enemy_bottom >= GROUND_LEVEL + 5:
                self.bird_position = 1
            else:
                self.bird_position = 2
        else:
            self.bird_position = -1 # Not a bird

    def update(self, current_game_speed):
        self.x -= current_game_speed

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def draw(self, screen):
        rect = self.get_rect()
        pygame.draw.rect(screen, self.color, rect)
        pygame.draw.rect(screen, BLACK, rect, 2)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Dino Game - Fuzzy AI")
        self.clock = pygame.time.Clock()
        self.running = True
        self.font = pygame.font.Font(None, 36)
        
        self.ai = FuzzyDinoAI()
        self.ai_debug = {}
        self.restart_game()

    def restart_game(self):
        self.player = Player(100, GROUND_LEVEL)
        self.enemies = []
        self.game_over = False
        self.score = 0
        self.current_speed = 5
        self.spawn_timer = random.randint(ENEMY_MIN_SPAWN_DELAY, ENEMY_MAX_SPAWN_DELAY)
        self.ai_debug = {}

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r and self.game_over:
                    self.restart_game()

    def process_ai(self):
        # Find the closest enemy in front of the player
        closest_enemy = None
        min_dist = float('inf')
        
        for enemy in self.enemies:
            # Distance from front of player to front of enemy
            dist = enemy.x - (self.player.x + self.player.width)
            if dist > -enemy.width and dist < min_dist:
                min_dist = dist
                closest_enemy = enemy

        if closest_enemy:
            should_jump, should_duck = self.ai.process(
                distance=min_dist,
                obstacle_width=closest_enemy.width,
                obstacle_height=closest_enemy.height,
                speed=self.current_speed,
                is_bird='bird' in closest_enemy.kind,
                bird_position=closest_enemy.bird_position
            )

            self.ai_debug = dict(self.ai.last_debug)
            self.ai_debug['enemy_kind'] = closest_enemy.kind
            self.ai_debug['enemy_width'] = closest_enemy.width
            self.ai_debug['enemy_height'] = closest_enemy.height

            # Apply AI Outputs
            if should_duck:
                self.player.start_duck()
            else:
                self.player.stop_duck()
                if should_jump:
                    self.player.jump()
        else:
            self.ai_debug = {
                'decision': 'none',
                'reason': 'No obstacle in range'
            }

    def update(self):
        if self.game_over:
            return

        # Difficulty Scaling
        speed_increase = self.score / 5000.0
        self.current_speed = min(20, self.current_speed + speed_increase)
        
        # Let AI evaluate the frame
        self.process_ai()
        self.player.update()

        # Enemy Spawning
        self.spawn_timer -= 1
        if self.spawn_timer <= 0:
            if self.can_spawn_enemy():
                self.spawn_enemy()
                self.spawn_timer = random.randint(ENEMY_MIN_SPAWN_DELAY, ENEMY_MAX_SPAWN_DELAY)
            else:
                self.spawn_timer = 10

        # Update Enemies & Score
        for enemy in self.enemies:
            enemy.update(self.current_speed)
        
        # Clean up off-screen enemies
        self.enemies = [e for e in self.enemies if e.x + e.width > 0]

        if self.clock.get_time() % 2 == 0:
            self.score += 1 
            
        self.check_collisions()

    def spawn_enemy(self):
        enemy_type = random.choice(['cactus', 'cactus_tall', 'cactus_big', 'bird', 'tall_bird'])

        if enemy_type == 'bird' and self.current_speed >= 8:
            width = 35 + random.randint(0, 80)
            height = 40
            y = GROUND_LEVEL + PLAYER_SIZE - height - random.choice([0, 5, 35, 110])
            color = GRAY
        elif enemy_type == 'tall_bird' and self.current_speed >= 8:
            width = 30 
            height = 75
            y = GROUND_LEVEL + PLAYER_SIZE - height - random.choice([0, 35, 110])
            color = GRAY
        elif enemy_type == 'cactus':
            width = ENEMY_WIDTH
            height = ENEMY_HEIGHT
            y = GROUND_LEVEL + PLAYER_SIZE - height
            color = RED
        elif enemy_type == 'cactus_tall':
            width = ENEMY_WIDTH
            height = ENEMY_HEIGHT + 55
            y = GROUND_LEVEL + PLAYER_SIZE - height
            color = RED
        else:
            width = ENEMY_WIDTH + 75
            height = ENEMY_HEIGHT
            y = GROUND_LEVEL + PLAYER_SIZE - height
            color = RED

        enemy = Enemy(SCREEN_WIDTH, y, width=width, height=height, color=color, kind=enemy_type)
        self.enemies.append(enemy)

    def can_spawn_enemy(self):
        if not self.enemies:
            return True
        last_enemy = self.enemies[-1]
        distance_from_spawn = SCREEN_WIDTH - (last_enemy.x + last_enemy.width)
        required_gap = max(ENEMY_MIN_GAP, int(self.current_speed * 35))
        return distance_from_spawn >= required_gap
    
    def check_collisions(self):
        player_rect = pygame.Rect(self.player.x, self.player.y, self.player.width, self.player.height)
        for enemy in self.enemies:
            if player_rect.colliderect(enemy.get_rect()):
                self.game_over = True
    
    def draw_ai_debug_panel(self):
        panel_x, panel_y, panel_w, panel_h = 470, 100, 300, 180
        pygame.draw.rect(self.screen, (245, 245, 245), (panel_x, panel_y, panel_w, panel_h))
        pygame.draw.rect(self.screen, BLACK, (panel_x, panel_y, panel_w, panel_h), 2)

        title = self.font.render("AI Thinking", True, BLACK)
        self.screen.blit(title, (panel_x + 10, panel_y + 8))

        info_font = pygame.font.Font(None, 24)
        decision = self.ai_debug.get('decision', 'none').upper()
        lines = [
            f"Decision: {decision}",
            f"TTC: {self.ai_debug.get('ttc', '-')}",
            f"Jump TTC: {self.ai_debug.get('target_jump_ttc', '-')}",
            f"Duck Limit: {self.ai_debug.get('duck_ttc_limit', '-')}",
            f"Bird Pos: {self.ai_debug.get('bird_position', '-')}",
            f"Enemy: {self.ai_debug.get('enemy_kind', 'none')}",
            f"Size: {self.ai_debug.get('enemy_width', '-')}/{self.ai_debug.get('enemy_height', '-')}",
        ]

        for i, line in enumerate(lines):
            text = info_font.render(line, True, BLACK)
            self.screen.blit(text, (panel_x + 12, panel_y + 42 + i * 20))

    def draw(self):
        self.screen.fill(WHITE)
        pygame.draw.line(self.screen, BLACK, (0, GROUND_LEVEL + PLAYER_SIZE), (SCREEN_WIDTH, GROUND_LEVEL + PLAYER_SIZE), 3)
        
        self.player.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        
        title = self.font.render("Dino Game - AI Controlled", True, BLACK)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 20))
        self.screen.blit(title, title_rect)
        
        info_font = pygame.font.Font(None, 20)
        info_text = info_font.render("AI is playing! | ESC: Exit", True, GRAY)
        self.screen.blit(info_text, (10, 50))
        
        score_text = info_font.render(f"Score: {self.score}", True, BLACK)
        self.screen.blit(score_text, (10, 75))

        self.draw_ai_debug_panel()
        
        fps_text = info_font.render(f"FPS: {int(self.clock.get_fps())}", True, BLACK)
        self.screen.blit(fps_text, (SCREEN_WIDTH - 100, 10))
        
        if self.game_over:
            game_over_text = self.font.render("GAME OVER! Press R to restart", True, RED)
            game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(game_over_text, game_over_rect)
        
        pygame.display.flip()
    
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()

if __name__ == '__main__':
    game = Game()
    game.run()