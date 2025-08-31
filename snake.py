import pygame
import random
import json
import os
from enum import Enum
import math

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
GRID_SIZE = 20
GRID_WIDTH = WINDOW_WIDTH // GRID_SIZE
GRID_HEIGHT = (WINDOW_HEIGHT - 100) // GRID_SIZE  # Leave space for UI

# Colors (Retro Theme)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 200, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (255, 0, 255)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
PINK = (255, 192, 203)
LIME = (50, 205, 50)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)

# Power-up types
class PowerUpType(Enum):
    SPEED_BOOST = 1
    SLOW_DOWN = 2
    DOUBLE_POINTS = 3
    INVINCIBILITY = 4
    SHRINK = 5
    EXTEND = 6

class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

class SnakeGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Retro Snake Game")
        self.clock = pygame.time.Clock()
        
        # Fonts for retro UI
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
        # Game state
        self.reset_game()
        self.high_score = self.load_high_score()
        self.paused = False
        
        # Power-up system
        self.power_ups = []
        self.active_power_ups = {}
        self.power_up_spawn_timer = 0
        
        # Particle effects
        self.particles = []
        
        # Sound effects (if available)
        try:
            pygame.mixer.init()
            self.sound_enabled = True
        except:
            self.sound_enabled = False
    
    def reset_game(self):
        """Reset game to initial state"""
        self.snake = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = Direction.RIGHT
        self.food = self.spawn_food()
        self.score = 0
        self.level = 1
        self.speed = 8
        self.base_speed = 8
        self.game_over = False
        self.power_ups = []
        self.active_power_ups = {}
        self.particles = []
        self.power_up_spawn_timer = 0
        
        # Smooth movement
        self.move_timer = 0
        self.move_delay = 1000 // self.speed  # milliseconds
        
    def load_high_score(self):
        """Load high score from file"""
        try:
            if os.path.exists('high_score.json'):
                with open('high_score.json', 'r') as f:
                    data = json.load(f)
                    return data.get('high_score', 0)
        except:
            pass
        return 0
    
    def save_high_score(self):
        """Save high score to file"""
        try:
            with open('high_score.json', 'w') as f:
                json.dump({'high_score': self.high_score}, f)
        except:
            pass
    
    def spawn_food(self):
        """Spawn food at random location not on snake"""
        while True:
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            if (x, y) not in self.snake:
                return (x, y)
    
    def spawn_power_up(self):
        """Spawn a random power-up"""
        while True:
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            if (x, y) not in self.snake and (x, y) != self.food:
                power_type = random.choice(list(PowerUpType))
                self.power_ups.append({
                    'pos': (x, y),
                    'type': power_type,
                    'timer': 300,  # frames before disappearing
                    'blink': 0
                })
                break
    
    def handle_input(self):
        """Handle keyboard input with smooth controls"""
        keys = pygame.key.get_pressed()
        
        # Prevent reverse direction
        if keys[pygame.K_UP] and self.direction != Direction.DOWN:
            self.direction = Direction.UP
        elif keys[pygame.K_DOWN] and self.direction != Direction.UP:
            self.direction = Direction.DOWN
        elif keys[pygame.K_LEFT] and self.direction != Direction.RIGHT:
            self.direction = Direction.LEFT
        elif keys[pygame.K_RIGHT] and self.direction != Direction.LEFT:
            self.direction = Direction.RIGHT
    
    def update_snake(self):
        """Update snake position with smooth movement"""
        current_time = pygame.time.get_ticks()
        
        if current_time - self.move_timer >= self.move_delay:
            self.move_timer = current_time
            
            # Calculate new head position
            head_x, head_y = self.snake[0]
            dx, dy = self.direction.value
            new_head = (head_x + dx, head_y + dy)
            
            # Check wall collision
            if (new_head[0] < 0 or new_head[0] >= GRID_WIDTH or 
                new_head[1] < 0 or new_head[1] >= GRID_HEIGHT):
                if 'invincibility' not in self.active_power_ups:
                    self.game_over = True
                    return
                else:
                    # Wrap around with invincibility
                    new_head = (new_head[0] % GRID_WIDTH, new_head[1] % GRID_HEIGHT)
            
            # Check self collision
            if new_head in self.snake and 'invincibility' not in self.active_power_ups:
                self.game_over = True
                return
            
            # Add new head
            self.snake.insert(0, new_head)
            
            # Check food collision
            if new_head == self.food:
                points = 10
                if 'double_points' in self.active_power_ups:
                    points *= 2
                self.score += points
                self.food = self.spawn_food()
                self.create_food_particles(new_head)
                
                # Increase difficulty
                if self.score % 50 == 0:
                    self.level += 1
                    self.speed = min(20, self.base_speed + self.level)
                    self.move_delay = 1000 // self.speed
            else:
                # Remove tail if no food eaten
                self.snake.pop()
            
            # Check power-up collision
            for power_up in self.power_ups[:]:
                if new_head == power_up['pos']:
                    self.activate_power_up(power_up['type'])
                    self.power_ups.remove(power_up)
                    self.create_power_up_particles(new_head)
    
    def activate_power_up(self, power_type):
        """Activate a power-up effect"""
        if power_type == PowerUpType.SPEED_BOOST:
            self.active_power_ups['speed_boost'] = 300
            self.move_delay = max(50, self.move_delay // 2)
        elif power_type == PowerUpType.SLOW_DOWN:
            self.active_power_ups['slow_down'] = 300
            self.move_delay = min(500, self.move_delay * 2)
        elif power_type == PowerUpType.DOUBLE_POINTS:
            self.active_power_ups['double_points'] = 300
        elif power_type == PowerUpType.INVINCIBILITY:
            self.active_power_ups['invincibility'] = 200
        elif power_type == PowerUpType.SHRINK:
            if len(self.snake) > 1:
                self.snake = self.snake[:max(1, len(self.snake) // 2)]
        elif power_type == PowerUpType.EXTEND:
            tail = self.snake[-1]
            for _ in range(3):
                self.snake.append(tail)
    
    def update_power_ups(self):
        """Update power-up timers and effects"""
        # Update active power-up timers
        for power_up in list(self.active_power_ups.keys()):
            self.active_power_ups[power_up] -= 1
            if self.active_power_ups[power_up] <= 0:
                del self.active_power_ups[power_up]
                # Reset speed when speed power-ups expire
                if power_up in ['speed_boost', 'slow_down']:
                    self.move_delay = 1000 // self.speed
        
        # Update power-up spawn timer
        self.power_up_spawn_timer += 1
        if self.power_up_spawn_timer >= 600:  # Spawn every 10 seconds at 60 FPS
            self.spawn_power_up()
            self.power_up_spawn_timer = 0
        
        # Update power-up blink and timer
        for power_up in self.power_ups[:]:
            power_up['timer'] -= 1
            power_up['blink'] += 1
            if power_up['timer'] <= 0:
                self.power_ups.remove(power_up)
    
    def create_food_particles(self, pos):
        """Create particle effect when eating food"""
        for _ in range(10):
            self.particles.append({
                'pos': [pos[0] * GRID_SIZE + GRID_SIZE // 2, pos[1] * GRID_SIZE + GRID_SIZE // 2],
                'vel': [random.uniform(-3, 3), random.uniform(-3, 3)],
                'life': 30,
                'color': YELLOW
            })
    
    def create_power_up_particles(self, pos):
        """Create particle effect when collecting power-up"""
        for _ in range(15):
            self.particles.append({
                'pos': [pos[0] * GRID_SIZE + GRID_SIZE // 2, pos[1] * GRID_SIZE + GRID_SIZE // 2],
                'vel': [random.uniform(-4, 4), random.uniform(-4, 4)],
                'life': 40,
                'color': PURPLE
            })
    
    def update_particles(self):
        """Update particle effects"""
        for particle in self.particles[:]:
            particle['pos'][0] += particle['vel'][0]
            particle['pos'][1] += particle['vel'][1]
            particle['life'] -= 1
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def draw_grid(self):
        """Draw retro grid background"""
        for x in range(0, WINDOW_WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, (20, 20, 20), (x, 0), (x, GRID_HEIGHT * GRID_SIZE))
        for y in range(0, GRID_HEIGHT * GRID_SIZE, GRID_SIZE):
            pygame.draw.line(self.screen, (20, 20, 20), (0, y), (WINDOW_WIDTH, y))
    
    def draw_snake(self):
        """Draw snake with retro styling"""
        for i, segment in enumerate(self.snake):
            x, y = segment[0] * GRID_SIZE, segment[1] * GRID_SIZE
            
            # Head is brighter
            if i == 0:
                color = LIME if 'invincibility' not in self.active_power_ups else GOLD
                # Add eyes
                pygame.draw.rect(self.screen, color, (x, y, GRID_SIZE, GRID_SIZE))
                pygame.draw.circle(self.screen, BLACK, (x + 5, y + 5), 2)
                pygame.draw.circle(self.screen, BLACK, (x + 15, y + 5), 2)
            else:
                color = GREEN if 'invincibility' not in self.active_power_ups else YELLOW
                pygame.draw.rect(self.screen, color, (x + 1, y + 1, GRID_SIZE - 2, GRID_SIZE - 2))
            
            # Add border
            pygame.draw.rect(self.screen, DARK_GREEN, (x, y, GRID_SIZE, GRID_SIZE), 2)
    
    def draw_food(self):
        """Draw food with pulsing effect"""
        x, y = self.food[0] * GRID_SIZE, self.food[1] * GRID_SIZE
        pulse = int(5 * math.sin(pygame.time.get_ticks() * 0.01))
        size = GRID_SIZE // 2 + pulse
        center_x = x + GRID_SIZE // 2
        center_y = y + GRID_SIZE // 2
        pygame.draw.circle(self.screen, RED, (center_x, center_y), size)
        pygame.draw.circle(self.screen, ORANGE, (center_x, center_y), size - 3)
    
    def draw_power_ups(self):
        """Draw power-ups with effects"""
        for power_up in self.power_ups:
            x, y = power_up['pos'][0] * GRID_SIZE, power_up['pos'][1] * GRID_SIZE
            
            # Blinking effect when about to disappear
            if power_up['timer'] < 60 and power_up['blink'] % 10 < 5:
                continue
            
            # Different shapes for different power-ups
            power_type = power_up['type']
            center_x = x + GRID_SIZE // 2
            center_y = y + GRID_SIZE // 2
            
            if power_type == PowerUpType.SPEED_BOOST:
                pygame.draw.polygon(self.screen, CYAN, [
                    (center_x, center_y - 8),
                    (center_x - 6, center_y + 8),
                    (center_x + 6, center_y + 8)
                ])
            elif power_type == PowerUpType.SLOW_DOWN:
                pygame.draw.circle(self.screen, BLUE, (center_x, center_y), 8)
            elif power_type == PowerUpType.DOUBLE_POINTS:
                pygame.draw.rect(self.screen, GOLD, (x + 2, y + 2, GRID_SIZE - 4, GRID_SIZE - 4))
            elif power_type == PowerUpType.INVINCIBILITY:
                pygame.draw.polygon(self.screen, PURPLE, [
                    (center_x, center_y - 8),
                    (center_x - 8, center_y),
                    (center_x, center_y + 8),
                    (center_x + 8, center_y)
                ])
            elif power_type == PowerUpType.SHRINK:
                pygame.draw.circle(self.screen, PINK, (center_x, center_y), 6)
            elif power_type == PowerUpType.EXTEND:
                pygame.draw.rect(self.screen, ORANGE, (x + 1, y + 1, GRID_SIZE - 2, GRID_SIZE - 2))
    
    def draw_particles(self):
        """Draw particle effects"""
        for particle in self.particles:
            alpha = int(255 * (particle['life'] / 40))
            color = (*particle['color'], min(255, alpha))
            size = max(1, particle['life'] // 10)
            pygame.draw.circle(self.screen, particle['color'], 
                             (int(particle['pos'][0]), int(particle['pos'][1])), size)
    
    def draw_ui(self):
        """Draw retro-style UI"""
        ui_y = GRID_HEIGHT * GRID_SIZE + 10
        
        # Background for UI
        pygame.draw.rect(self.screen, (40, 40, 40), (0, ui_y - 5, WINDOW_WIDTH, 100))
        
        # Score
        score_text = self.font_medium.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (20, ui_y))
        
        # High Score
        high_score_text = self.font_medium.render(f"High Score: {self.high_score}", True, YELLOW)
        self.screen.blit(high_score_text, (200, ui_y))
        
        # Level
        level_text = self.font_medium.render(f"Level: {self.level}", True, GREEN)
        self.screen.blit(level_text, (450, ui_y))
        
        # Speed
        speed_text = self.font_medium.render(f"Speed: {self.speed}", True, CYAN)
        self.screen.blit(speed_text, (600, ui_y))
        
        # Active power-ups
        power_up_y = ui_y + 30
        x_offset = 20
        for power_up, timer in self.active_power_ups.items():
            power_text = self.font_small.render(f"{power_up.replace('_', ' ').title()}: {timer//60 + 1}s", True, PURPLE)
            self.screen.blit(power_text, (x_offset, power_up_y))
            x_offset += power_text.get_width() + 20
        
        # Controls hint
        if not self.game_over:
            controls_text = self.font_small.render("Arrow Keys: Move | SPACE: Pause | ESC: Quit", True, (150, 150, 150))
            self.screen.blit(controls_text, (20, ui_y + 60))
    
    def draw_game_over(self):
        """Draw game over screen"""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Game Over text
        game_over_text = self.font_large.render("GAME OVER", True, RED)
        text_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 100))
        self.screen.blit(game_over_text, text_rect)
        
        # Final score
        score_text = self.font_medium.render(f"Final Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
        self.screen.blit(score_text, score_rect)
        
        # High score
        if self.score > self.high_score:
            new_high_text = self.font_medium.render("NEW HIGH SCORE!", True, GOLD)
            new_high_rect = new_high_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            self.screen.blit(new_high_text, new_high_rect)
        
        # Restart instructions
        restart_text = self.font_medium.render("Press SPACE to play again or ESC to quit", True, GREEN)
        restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
        self.screen.blit(restart_text, restart_rect)
    
    def draw_pause_screen(self):
        """Draw pause screen"""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        pause_text = self.font_large.render("PAUSED", True, YELLOW)
        text_rect = pause_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.screen.blit(pause_text, text_rect)
        
        resume_text = self.font_medium.render("Press SPACE to resume", True, WHITE)
        resume_rect = resume_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
        self.screen.blit(resume_text, resume_rect)
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        if self.game_over:
                            # Update high score if needed
                            if self.score > self.high_score:
                                self.high_score = self.score
                                self.save_high_score()
                            self.reset_game()
                        else:
                            self.paused = not self.paused
            
            if not self.game_over and not self.paused:
                self.handle_input()
                self.update_snake()
                self.update_power_ups()
                self.update_particles()
            
            # Draw everything
            self.screen.fill(BLACK)
            self.draw_grid()
            self.draw_snake()
            self.draw_food()
            self.draw_power_ups()
            self.draw_particles()
            self.draw_ui()
            
            if self.game_over:
                self.draw_game_over()
            elif self.paused:
                self.draw_pause_screen()
            
            pygame.display.flip()
            self.clock.tick(60)  # 60 FPS for smooth animation
        
        pygame.quit()

def main():
    """Main function to start the game"""
    game = SnakeGame()
    game.run()

if __name__ == "__main__":
    main()