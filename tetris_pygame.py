import pygame
import random
import sys
from enum import Enum

pygame.init()

# Constants
GRID_WIDTH = 10
GRID_HEIGHT = 20
CELL_SIZE = 30
BORDER_WIDTH = 2

# Window dimensions
GAME_WIDTH = GRID_WIDTH * CELL_SIZE
GAME_HEIGHT = GRID_HEIGHT * CELL_SIZE
SIDEBAR_WIDTH = 200
WINDOW_WIDTH = GAME_WIDTH + SIDEBAR_WIDTH + BORDER_WIDTH * 3
WINDOW_HEIGHT = GAME_HEIGHT + BORDER_WIDTH * 2

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (192, 192, 192)

# Tetromino colors
COLORS = {
    'I': (0, 255, 255),    # Cyan
    'O': (255, 255, 0),    # Yellow
    'T': (255, 0, 255),    # Magenta
    'S': (0, 255, 0),      # Green
    'Z': (255, 0, 0),      # Red
    'J': (0, 0, 255),      # Blue
    'L': (255, 165, 0),    # Orange
}

class Tetromino:
    def __init__(self, shape_type):
        self.type = shape_type
        self.color = COLORS[shape_type]
        self.x = GRID_WIDTH // 2 - 1
        self.y = 0
        self.rotation = 0
        
        # Define tetromino shapes
        self.shapes = {
            'I': [
                ['..#.',
                 '..#.',
                 '..#.',
                 '..#.'],
                ['....',
                 '####',
                 '....',
                 '....']
            ],
            'O': [
                ['....',
                 '.##.',
                 '.##.',
                 '....']
            ],
            'T': [
                ['....',
                 '.#..',
                 '###.',
                 '....'],
                ['....',
                 '.#..',
                 '.##.',
                 '.#..'],
                ['....',
                 '....',
                 '###.',
                 '.#..'],
                ['....',
                 '.#..',
                 '##..',
                 '.#..']
            ],
            'S': [
                ['....',
                 '.##.',
                 '##..',
                 '....'],
                ['....',
                 '.#..',
                 '.##.',
                 '..#.']
            ],
            'Z': [
                ['....',
                 '##..',
                 '.##.',
                 '....'],
                ['....',
                 '..#.',
                 '.##.',
                 '.#..']
            ],
            'J': [
                ['....',
                 '.#..',
                 '.#..',
                 '##..'],
                ['....',
                 '....',
                 '#...',
                 '###.'],
                ['....',
                 '.##.',
                 '.#..',
                 '.#..'],
                ['....',
                 '....',
                 '###.',
                 '..#.']
            ],
            'L': [
                ['....',
                 '..#.',
                 '..#.',
                 '.##.'],
                ['....',
                 '....',
                 '###.',
                 '#...'],
                ['....',
                 '##..',
                 '.#..',
                 '.#..'],
                ['....',
                 '....',
                 '..#.',
                 '###.']
            ]
        }
    
    def get_shape(self):
        return self.shapes[self.type][self.rotation % len(self.shapes[self.type])]
    
    def get_cells(self):
        shape = self.get_shape()
        cells = []
        for row_idx, row in enumerate(shape):
            for col_idx, cell in enumerate(row):
                if cell == '#':
                    cells.append((self.x + col_idx, self.y + row_idx))
        return cells

class TetrisGame:
    def __init__(self):
        self.grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = None
        self.next_piece = None
        self.hold_piece = None
        self.can_hold = True  # Prevents holding multiple times per piece
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.fall_timer = 0
        self.fall_speed = 500  # milliseconds
        self.game_over = False
        self.paused = False
        
        # Key press tracking
        self.keys_held = set()
        self.key_timers = {}
        self.repeat_delay = 150  # milliseconds
        
        # SRS Wall Kick Data
        self.wall_kick_data = {
            'JLSTZ': {
                (0, 1): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
                (1, 0): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
                (1, 2): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
                (2, 1): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
                (2, 3): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
                (3, 2): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
                (3, 0): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
                (0, 3): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
            },
            'I': {
                (0, 1): [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
                (1, 0): [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
                (1, 2): [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
                (2, 1): [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
                (2, 3): [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
                (3, 2): [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
                (3, 0): [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
                (0, 3): [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
            }
        }
        
        self.spawn_new_piece()
        
    def spawn_new_piece(self):
        if self.next_piece is None:
            self.next_piece = random.choice(list(COLORS.keys()))
        
        self.current_piece = Tetromino(self.next_piece)
        self.next_piece = random.choice(list(COLORS.keys()))
        
        if not self.is_valid_position(self.current_piece):
            self.game_over = True
    
    def is_valid_position(self, piece, dx=0, dy=0, rotation_offset=0):
        test_piece = Tetromino(piece.type)
        test_piece.x = piece.x + dx
        test_piece.y = piece.y + dy
        test_piece.rotation = (piece.rotation + rotation_offset) % len(piece.shapes[piece.type])
        
        for x, y in test_piece.get_cells():
            if x < 0 or x >= GRID_WIDTH or y >= GRID_HEIGHT:
                return False
            if y >= 0 and self.grid[y][x] is not None:
                return False
        return True
    
    def place_piece(self):
        for x, y in self.current_piece.get_cells():
            if y >= 0:
                self.grid[y][x] = self.current_piece.color
        
        self.clear_lines()
        self.spawn_new_piece()
        self.can_hold = True  # Reset hold ability for new piece
    
    def clear_lines(self):
        lines_to_clear = []
        for y in range(GRID_HEIGHT):
            if all(self.grid[y][x] is not None for x in range(GRID_WIDTH)):
                lines_to_clear.append(y)
        
        for y in sorted(lines_to_clear, reverse=True):
            del self.grid[y]
            self.grid.insert(0, [None for _ in range(GRID_WIDTH)])
        
        lines_cleared = len(lines_to_clear)
        if lines_cleared > 0:
            self.lines_cleared += lines_cleared
            points = [0, 100, 300, 500, 800][lines_cleared]
            self.score += points * self.level
            
            # Level up every 10 lines
            new_level = self.lines_cleared // 10 + 1
            if new_level > self.level:
                self.level = new_level
                self.fall_speed = max(50, 500 - (self.level - 1) * 50)
    
    def move_piece(self, dx, dy):
        if self.current_piece and self.is_valid_position(self.current_piece, dx, dy):
            self.current_piece.x += dx
            self.current_piece.y += dy
            return True
        return False
    
    def rotate_piece(self, clockwise=True):
        if not self.current_piece:
            return False
        
        old_rotation = self.current_piece.rotation
        new_rotation = (old_rotation + (1 if clockwise else -1)) % len(self.current_piece.shapes[self.current_piece.type])
        
        # Get wall kick data
        kick_table = 'I' if self.current_piece.type == 'I' else 'JLSTZ'
        if self.current_piece.type == 'O':
            # O piece doesn't need wall kicks
            if self.is_valid_position(self.current_piece, rotation_offset=(1 if clockwise else -1)):
                self.current_piece.rotation = new_rotation
                return True
            return False
        
        kick_tests = self.wall_kick_data[kick_table].get((old_rotation, new_rotation), [(0, 0)])
        
        # Try each wall kick offset
        for dx, dy in kick_tests:
            if self.is_valid_position(self.current_piece, dx, dy, (1 if clockwise else -1)):
                self.current_piece.x += dx
                self.current_piece.y += dy
                self.current_piece.rotation = new_rotation
                return True
        
        return False
    
    def get_ghost_position(self):
        if not self.current_piece:
            return None
        
        # Create a copy of the current piece
        ghost_y = self.current_piece.y
        
        # Find the lowest possible position
        while True:
            test_piece = Tetromino(self.current_piece.type)
            test_piece.x = self.current_piece.x
            test_piece.y = ghost_y + 1
            test_piece.rotation = self.current_piece.rotation
            
            if not self.is_valid_position(test_piece):
                break
            ghost_y += 1
        
        return ghost_y
    
    def hold_current_piece(self):
        if not self.current_piece or not self.can_hold:
            return False
        
        if self.hold_piece is None:
            # First time holding - store current piece and spawn new one
            self.hold_piece = self.current_piece.type
            self.spawn_new_piece()
        else:
            # Swap current piece with held piece
            old_hold = self.hold_piece
            self.hold_piece = self.current_piece.type
            
            # Create new piece from held piece
            self.current_piece = Tetromino(old_hold)
            self.current_piece.x = GRID_WIDTH // 2 - 1
            self.current_piece.y = 0
            
            # Check if the swapped piece can be placed
            if not self.is_valid_position(self.current_piece):
                self.game_over = True
                return False
        
        self.can_hold = False  # Can't hold again until next piece
        return True
    
    def hard_drop(self):
        if not self.current_piece:
            return
        
        drop_distance = 0
        while self.move_piece(0, 1):
            drop_distance += 1
        
        self.score += drop_distance * 2
        self.place_piece()
    
    def soft_drop(self):
        if self.move_piece(0, 1):
            self.score += 1
        else:
            self.place_piece()
    
    def update(self, dt):
        if self.game_over or self.paused or not self.current_piece:
            return
        
        self.fall_timer += dt
        if self.fall_timer >= self.fall_speed:
            if not self.move_piece(0, 1):
                self.place_piece()
            self.fall_timer = 0
    
    def handle_input(self, keys_pressed, dt):
        if self.game_over or self.paused:
            return
        
        current_time = pygame.time.get_ticks()
        
        # Handle left movement
        if keys_pressed[pygame.K_a] or keys_pressed[pygame.K_LEFT]:
            key = 'left'
            if key not in self.key_timers:
                self.move_piece(-1, 0)
                self.key_timers[key] = current_time
            elif current_time - self.key_timers[key] >= self.repeat_delay:
                self.move_piece(-1, 0)
                self.key_timers[key] = current_time
        else:
            if 'left' in self.key_timers:
                del self.key_timers['left']
        
        # Handle right movement
        if keys_pressed[pygame.K_d] or keys_pressed[pygame.K_RIGHT]:
            key = 'right'
            if key not in self.key_timers:
                self.move_piece(1, 0)
                self.key_timers[key] = current_time
            elif current_time - self.key_timers[key] >= self.repeat_delay:
                self.move_piece(1, 0)
                self.key_timers[key] = current_time
        else:
            if 'right' in self.key_timers:
                del self.key_timers['right']
        
        # Handle down movement
        if keys_pressed[pygame.K_s] or keys_pressed[pygame.K_DOWN]:
            key = 'down'
            if key not in self.key_timers:
                self.soft_drop()
                self.key_timers[key] = current_time
            elif current_time - self.key_timers[key] >= self.repeat_delay:
                self.soft_drop()
                self.key_timers[key] = current_time
        else:
            if 'down' in self.key_timers:
                del self.key_timers['down']
    
    def handle_key_down(self, key):
        if key == pygame.K_p:  # Pause toggle
            self.paused = not self.paused
            return
        
        if self.game_over:
            if key == pygame.K_r:
                self.__init__()  # Restart game
            return
        
        if self.paused:
            return
        
        if key == pygame.K_w or key == pygame.K_UP:
            self.rotate_piece(clockwise=True)
        elif key == pygame.K_z:  # Counter-clockwise rotation
            self.rotate_piece(clockwise=False)
        elif key == pygame.K_q or key == pygame.K_SPACE:
            self.hard_drop()
        elif key == pygame.K_c:  # Hold piece
            self.hold_current_piece()

def draw_grid(screen):
    # Draw game area border
    pygame.draw.rect(screen, WHITE, 
                     (BORDER_WIDTH - 1, BORDER_WIDTH - 1, 
                      GAME_WIDTH + 2, GAME_HEIGHT + 2), 2)
    
    # Draw grid lines
    for x in range(GRID_WIDTH + 1):
        pygame.draw.line(screen, DARK_GRAY,
                        (BORDER_WIDTH + x * CELL_SIZE, BORDER_WIDTH),
                        (BORDER_WIDTH + x * CELL_SIZE, BORDER_WIDTH + GAME_HEIGHT))
    
    for y in range(GRID_HEIGHT + 1):
        pygame.draw.line(screen, DARK_GRAY,
                        (BORDER_WIDTH, BORDER_WIDTH + y * CELL_SIZE),
                        (BORDER_WIDTH + GAME_WIDTH, BORDER_WIDTH + y * CELL_SIZE))

def draw_cell(screen, x, y, color, alpha=255):
    rect = pygame.Rect(BORDER_WIDTH + x * CELL_SIZE + 1, 
                      BORDER_WIDTH + y * CELL_SIZE + 1,
                      CELL_SIZE - 1, CELL_SIZE - 1)
    
    if alpha < 255:
        # Create a surface for transparent drawing
        cell_surface = pygame.Surface((CELL_SIZE - 1, CELL_SIZE - 1))
        cell_surface.set_alpha(alpha)
        cell_surface.fill(color)
        screen.blit(cell_surface, rect.topleft)
        
        # Draw border for ghost piece
        border_color = tuple(min(255, c + 60) for c in color)
        pygame.draw.rect(screen, border_color, rect, 2)
    else:
        pygame.draw.rect(screen, color, rect)
        
        # Add some shading for 3D effect
        highlight = tuple(min(255, c + 40) for c in color)
        shadow = tuple(max(0, c - 40) for c in color)
        
        # Highlight (top and left)
        pygame.draw.line(screen, highlight, rect.topleft, rect.topright, 2)
        pygame.draw.line(screen, highlight, rect.topleft, rect.bottomleft, 2)
        
        # Shadow (bottom and right)
        pygame.draw.line(screen, shadow, rect.bottomleft, rect.bottomright, 2)
        pygame.draw.line(screen, shadow, rect.topright, rect.bottomright, 2)

def draw_game(screen, game):
    screen.fill(BLACK)
    
    # Draw grid
    draw_grid(screen)
    
    # Draw placed pieces
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if game.grid[y][x] is not None:
                draw_cell(screen, x, y, game.grid[y][x])
    
    # Draw ghost piece (hard drop preview)
    if game.current_piece:
        ghost_y = game.get_ghost_position()
        if ghost_y is not None and ghost_y != game.current_piece.y:
            ghost_piece = Tetromino(game.current_piece.type)
            ghost_piece.x = game.current_piece.x
            ghost_piece.y = ghost_y
            ghost_piece.rotation = game.current_piece.rotation
            
            for x, y in ghost_piece.get_cells():
                if 0 <= x < GRID_WIDTH and y >= 0:
                    draw_cell(screen, x, y, game.current_piece.color, alpha=80)
    
    # Draw current piece
    if game.current_piece:
        for x, y in game.current_piece.get_cells():
            if 0 <= x < GRID_WIDTH and y >= 0:
                draw_cell(screen, x, y, game.current_piece.color)
    
    # Draw UI
    draw_ui(screen, game)

def draw_ui(screen, game):
    font_large = pygame.font.Font(None, 36)
    font_medium = pygame.font.Font(None, 24)
    font_small = pygame.font.Font(None, 18)
    
    ui_x = GAME_WIDTH + BORDER_WIDTH * 2 + 10
    
    # Title
    title = font_large.render("TETRIS", True, WHITE)
    screen.blit(title, (ui_x, 20))
    
    # Score
    score_text = font_medium.render(f"Score: {game.score}", True, WHITE)
    screen.blit(score_text, (ui_x, 70))
    
    # Level
    level_text = font_medium.render(f"Level: {game.level}", True, WHITE)
    screen.blit(level_text, (ui_x, 100))
    
    # Lines
    lines_text = font_medium.render(f"Lines: {game.lines_cleared}", True, WHITE)
    screen.blit(lines_text, (ui_x, 130))
    
    # Hold piece
    hold_text = font_medium.render("Hold:", True, WHITE)
    screen.blit(hold_text, (ui_x, 160))
    
    if game.hold_piece:
        hold_tetromino = Tetromino(game.hold_piece)
        hold_shape = hold_tetromino.get_shape()
        hold_color = hold_tetromino.color if game.can_hold else tuple(c // 2 for c in hold_tetromino.color)
        
        for row_idx, row in enumerate(hold_shape):
            for col_idx, cell in enumerate(row):
                if cell == '#':
                    x = ui_x + col_idx * 20
                    y = 190 + row_idx * 20
                    pygame.draw.rect(screen, hold_color, (x, y, 18, 18))
    
    # Next piece
    next_text = font_medium.render("Next:", True, WHITE)
    screen.blit(next_text, (ui_x, 260))
    
    if game.next_piece:
        next_tetromino = Tetromino(game.next_piece)
        next_shape = next_tetromino.get_shape()
        
        for row_idx, row in enumerate(next_shape):
            for col_idx, cell in enumerate(row):
                if cell == '#':
                    x = ui_x + col_idx * 20
                    y = 290 + row_idx * 20
                    pygame.draw.rect(screen, next_tetromino.color,
                                   (x, y, 18, 18))
    
    # Controls
    controls_y = 380
    controls = [
        "Controls:",
        "W/↑ - Rotate CW",
        "Z - Rotate CCW",
        "A/← - Left", 
        "D/→ - Right",
        "S/↓ - Soft Drop",
        "Q/Space - Hard Drop",
        "C - Hold",
        "P - Pause",
        "",
        "R - Restart (Game Over)"
    ]
    
    for i, text in enumerate(controls):
        color = WHITE if i == 0 else LIGHT_GRAY
        font = font_medium if i == 0 else font_small
        control_text = font.render(text, True, color)
        screen.blit(control_text, (ui_x, controls_y + i * 20))
    
    # Pause overlay
    if game.paused:
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        
        pause_text = font_large.render("PAUSED", True, WHITE)
        resume_text = font_medium.render("Press P to resume", True, WHITE)
        
        text_rect = pause_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20))
        resume_rect = resume_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20))
        
        screen.blit(pause_text, text_rect)
        screen.blit(resume_text, resume_rect)
    
    # Game over
    elif game.game_over:
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        
        game_over_text = font_large.render("GAME OVER", True, WHITE)
        restart_text = font_medium.render("Press R to restart", True, WHITE)
        
        text_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20))
        restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20))
        
        screen.blit(game_over_text, text_rect)
        screen.blit(restart_text, restart_rect)

def main():
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Tetris")
    clock = pygame.time.Clock()
    
    game = TetrisGame()
    
    running = True
    while running:
        dt = clock.tick(60)
        keys_pressed = pygame.key.get_pressed()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    game.handle_key_down(event.key)
        
        game.handle_input(keys_pressed, dt)
        game.update(dt)
        
        draw_game(screen, game)
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()