
# Ensure pygame is installed and import it
import importlib
import subprocess
import sys

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
GROUND_LEVEL = 450

# Physics constants
GRAVITY = 0.8
GRAVITY_BOOST = 0.5  # Additional gravity when down key is pressed
JUMP_STRENGTH = 15
PLAYER_SIZE = 40
PLAYER_DUCK_SIZE = 25

# Enemy constants
ENEMY_SPEED = 7
ENEMY_WIDTH = 30
ENEMY_HEIGHT = 50
ENEMY_MIN_GAP = 220  # Minimum horizontal gap between enemies
ENEMY_MIN_SPAWN_DELAY = 25  # Minimum frames between spawn attempts
ENEMY_MAX_SPAWN_DELAY = 100  # Maximum frames between spawn attempts

import random

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
		self.y += (PLAYER_SIZE - PLAYER_DUCK_SIZE)  # Adjust position to duck down
	
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
		pygame.draw.rect(screen, GREEN, rect)
		# Draw border
		pygame.draw.rect(screen, BLACK, rect, 2)

class Enemy:
	def __init__(self, x, y, width=ENEMY_WIDTH, height=ENEMY_HEIGHT, speed=ENEMY_SPEED, color=RED):
		self.x = x
		self.y = y
		self.width = width
		self.height = height
		self._base_speed = speed # Store the initial base speed (though it will be overridden by game speed)
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
		pygame.draw.rect(screen, BLACK, rect, 2)
	
	def get_rect(self):
		return pygame.Rect(self.x, self.y, self.width, self.height)

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
		self.current_speed = 5 # Initial speed of the game (pixels per frame/update cycle)
		self.spawn_timer = random.randint(ENEMY_MIN_SPAWN_DELAY, ENEMY_MAX_SPAWN_DELAY) - self.current_speed

		
	def handle_events(self):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				self.running = False
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					self.running = False
				elif event.key == pygame.K_UP or event.key == pygame.K_SPACE and not self.game_over:
					self.player.jump()
				elif event.key == pygame.K_DOWN and not self.game_over:
					self.player.start_duck()
				elif event.key == pygame.K_r and self.game_over:
					self.restart_game()
			elif event.type == pygame.KEYUP:
				if event.key == pygame.K_DOWN and not self.game_over:
					self.player.stop_duck()
	
	def restart_game(self):
		self.player = Player(100, GROUND_LEVEL)
		self.enemies = []
		self.game_over = False
		self.score = 0
		self.current_speed = 5 # Reset speed on restart

	def update(self):
		if self.game_over:
			return

		# --- DIFFICULTY SCALING (Speed Increase) ---
		# Gradually increase the speed based on elapsed time/score
		speed_increase = self.score / 5000.0 # Slow, continuous increase
		self.current_speed = min(20, self.current_speed + speed_increase)
		
		# --- FUZZY LOGIC AI CONTROL ---
		if not self.game_over:
			# 1. Reset ducking state by default so the dino stands back up
			if self.player.is_ducking:
				self.player.stop_duck()

			# 2. Check for active enemies
			if self.enemies:
				# Find the nearest enemy that is actually in front of the player
				nearest_enemy = None
				for enemy in self.enemies:
					if enemy.x + enemy.width > self.player.x:
						nearest_enemy = enemy
						break
				
				if nearest_enemy:
					# --- STEP A: CRISP INPUTS ---
					# Distance from front of player to front of enemy
					distance = nearest_enemy.x - (self.player.x + self.player.width)
					enemy_bottom = nearest_enemy.y + nearest_enemy.height
					
					# --- STEP B: FUZZIFICATION ---
					# Dynamic distance scaling: As speed increases, our "danger zone" must expand
					danger_threshold = self.current_speed * 16 
					
					# Fuzzy membership for distance (How "close" is it? 0.0 to 1.0)
					if distance <= 0:
						is_close = 1.0
					elif distance < danger_threshold * 2:
						# Linear drop-off for membership
						is_close = max(0.0, 1.0 - (distance / danger_threshold))
					else:
						is_close = 0.0

					# Fuzzy membership for obstacle height
					# Player ducking top is at y=465. If enemy bottom is above this, it's purely aerial.
					if enemy_bottom <= 465:
						is_aerial = 1.0
						is_ground = 0.0
					else:
						is_aerial = 0.0
						is_ground = 1.0

					# --- STEP C: FUZZY INFERENCE (Rules) ---
					# Rule 1: IF enemy is CLOSE AND enemy is GROUND -> JUMP
					weight_jump = min(is_close, is_ground)
					
					# Rule 2: IF enemy is CLOSE AND enemy is AERIAL -> DUCK
					weight_duck = min(is_close, is_aerial)

					# --- STEP D: DEFUZZIFICATION (Action Execution) ---
					# We use a threshold to convert fuzzy weights back to crisp actions
					ACTION_THRESHOLD = 0.35 
					
					if weight_jump > ACTION_THRESHOLD:
						# Only jump if we are touching the ground
						if self.player.y + self.player.height >= self.player.ground_bottom: 
							self.player.jump()
					elif weight_duck > ACTION_THRESHOLD:
						self.player.start_duck()
					
		self.player.update()

		# Spawn enemies with a minimum interval and spacing so the game remains fair.
		self.spawn_timer -= 1
		if self.spawn_timer <= 0:
			if self.can_spawn_enemy():
				self.spawn_enemy()
				self.spawn_timer = random.randint(ENEMY_MIN_SPAWN_DELAY, ENEMY_MAX_SPAWN_DELAY)
			else:
				self.spawn_timer = 10

		# Update all enemies using the global speed
		for enemy in self.enemies:
			enemy.update(self.current_speed)

		# Update score
		if self.clock.get_time() % 2 == 0:
			self.score += 1 
            
		# Check collision with enemies
		self.check_collisions()

	def spawn_enemy(self):
		# Use obstacle spacing and a little variety for a more Chrome-style feel.
		enemy_type = random.choice(['cactus', 'cactus_tall', 'cactus_big', 'bird', 'tall_bird'])

		if enemy_type == 'bird' and self.current_speed >= 8:
			width = 35 + random.randint(0, 80)
			height = 40
			y = GROUND_LEVEL + PLAYER_SIZE - height - random.choice([5 ,35, 110])
			color = GRAY
		elif enemy_type == 'tall_bird' and self.current_speed >= 8:
			width = 30 
			height = 75
			y = GROUND_LEVEL + PLAYER_SIZE - height - random.choice([35, 110])
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
		player_rect = pygame.Rect(self.player.x, self.player.y, self.player.width, self.player.height)
		for enemy in self.enemies:
			if player_rect.colliderect(enemy.get_rect()):
				self.game_over = True
	
	def draw(self):
		self.screen.fill(WHITE)
		
		# Draw ground
		pygame.draw.line(self.screen, BLACK, (0, GROUND_LEVEL + PLAYER_SIZE), (SCREEN_WIDTH, GROUND_LEVEL + PLAYER_SIZE), 3)
		
		# Draw player
		self.player.draw(self.screen)
		
		# Draw enemies
		for enemy in self.enemies:
			enemy.draw(self.screen)
		
		# Draw title
		title = self.font.render("Dino Game - Test Window", True, BLACK)
		title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 20))
		self.screen.blit(title, title_rect)
		
		# Draw info text
		info_font = pygame.font.Font(None, 20)
		info_text = info_font.render("UP / SPACE: Jump | DOWN: Duck | ESC: Exit", True, GRAY)
		info_rect = info_text.get_rect(topleft=(10, 50))
		self.screen.blit(info_text, info_rect)
		
		# Draw score
		score_text = info_font.render(f"Score: {self.score}", True, BLACK)
		self.screen.blit(score_text, (10, 75))
		
		# Draw FPS
		fps_text = info_font.render(f"FPS: {int(self.clock.get_fps())}", True, BLACK)
		self.screen.blit(fps_text, (SCREEN_WIDTH - 100, 10))
		
		# Draw game over message
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

# minimal usage check
if __name__ == '__main__':
	print('pygame version:', pygame.version.ver)
	game = Game()
	game.run()
