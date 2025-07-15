import pygame
import random
import sys
import time
import math
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
GOLD = (255, 215, 0)
BRIGHT_GOLD = (255, 255, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
RED = (255, 0, 0)

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

class Particle:
    def __init__(self, x, y, color, velocity_x=0, velocity_y=0, size=3, lifetime=1000):
        self.x = x
        self.y = y
        self.color = color
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.gravity = 0.2
        self.bounce_factor = 0.7
        
    def update(self, dt):
        self.lifetime -= dt
        
        # Apply gravity
        self.velocity_y += self.gravity
        
        # Update position
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # Bounce off bottom
        if self.y > GAME_HEIGHT - self.size:
            self.y = GAME_HEIGHT - self.size
            self.velocity_y *= -self.bounce_factor
            self.velocity_x *= 0.9  # Friction
        
        # Bounce off sides
        if self.x < 0 or self.x > GAME_WIDTH - self.size:
            self.velocity_x *= -self.bounce_factor
            self.x = max(0, min(GAME_WIDTH - self.size, self.x))
        
        return self.lifetime > 0
    
    def draw(self, screen):
        # Fade out over time
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        if alpha > 0:
            # Create a surface for alpha blending
            particle_surface = pygame.Surface((self.size * 2, self.size * 2))
            particle_surface.set_alpha(alpha)
            
            # Draw particle with gradient effect
            center_color = self.color
            edge_color = tuple(max(0, c - 50) for c in self.color)
            
            pygame.draw.circle(particle_surface, center_color, (self.size, self.size), self.size)
            pygame.draw.circle(particle_surface, edge_color, (self.size, self.size), self.size, 1)
            
            screen.blit(particle_surface, (BORDER_WIDTH + self.x - self.size, BORDER_WIDTH + self.y - self.size))

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
        self.in_settings = False
        
        # Key press tracking
        self.keys_held = set()
        self.key_timers = {}
        self.repeat_delay = 150  # milliseconds
        
        # Golden cube system
        self.golden_cubes = set()  # Set of (x, y) positions with golden cubes
        self.golden_spawn_chance = 0.1  # 10% chance per line clear
        self.golden_cubes_in_line = 0  # Track golden cubes in current clearing lines
        
        # Combo system
        self.combo_active = False
        self.combo_lines = []  # Lines to clear sequentially
        self.combo_timer = 0
        self.combo_delay = 500  # milliseconds between each line clear
        
        # Buff system
        self.active_buffs = {}
        self.buff_types = {
            'speed_boost': {'name': 'Speed Boost', 'duration': 15000, 'color': (0, 255, 255)},
            'score_multiplier': {'name': 'Score x2', 'duration': 20000, 'color': (255, 165, 0)},
            'ghost_mode': {'name': 'Ghost Mode', 'duration': 10000, 'color': (128, 0, 128)},
            'line_clear_bonus': {'name': 'Line Bonus', 'duration': 25000, 'color': (0, 255, 0)},
            'hold_reset': {'name': 'Hold Reset', 'duration': 12000, 'color': (255, 192, 203)},
            'slow_fall': {'name': 'Slow Fall', 'duration': 18000, 'color': (255, 255, 0)}
        }
        
        # Particle system
        self.particles = []
        
        # Settings system
        self.settings = {
            'particle_density': 1.0,  # 0.0 to 2.0
            'particle_lifetime': 1.0,  # 0.5 to 2.0
            'particle_effects': True,
            'show_particles': True
        }
        self.settings_selected = 0
        self.settings_options = ['particle_density', 'particle_lifetime', 'particle_effects', 'show_particles']
        self.settings_names = {
            'particle_density': 'Particle Density',
            'particle_lifetime': 'Particle Lifetime',
            'particle_effects': 'Particle Effects',
            'show_particles': 'Show Particles'
        }
        
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
        if not self.current_piece:
            return
            
        # Create landing particles
        self.create_landing_particles()
        
        # Place the piece on the grid
        for x, y in self.current_piece.get_cells():
            if y >= 0:
                self.grid[y][x] = self.current_piece.color
        
        # Clear current piece reference so it doesn't get drawn during combo
        self.current_piece = None
        
        # Only clear lines if not in combo mode
        if not self.combo_active:
            self.clear_lines()
    
    def create_landing_particles(self):
        """Create particles when a piece lands"""
        if not self.current_piece or not self.settings['show_particles'] or not self.settings['particle_effects']:
            return
        
        piece_cells = self.current_piece.get_cells()
        piece_color = self.current_piece.color
        
        # Create particles for each cell of the landed piece
        for cell_x, cell_y in piece_cells:
            if cell_y >= 0:
                # Convert grid coordinates to screen coordinates
                screen_x = cell_x * CELL_SIZE + CELL_SIZE // 2
                screen_y = cell_y * CELL_SIZE + CELL_SIZE // 2
                
                # Create multiple particles per cell
                particle_count = int(random.randint(3, 6) * self.settings['particle_density'])
                for _ in range(max(1, particle_count)):
                    # Random velocity in different directions
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(1, 4)
                    vel_x = math.cos(angle) * speed
                    vel_y = math.sin(angle) * speed - random.uniform(1, 3)  # Slight upward bias
                    
                    # Vary particle properties
                    size = random.randint(2, 4)
                    lifetime = random.randint(800, 1500)
                    
                    # Create color variations
                    color_variation = random.randint(-30, 30)
                    particle_color = tuple(max(0, min(255, c + color_variation)) for c in piece_color)
                    
                    particle = Particle(
                        screen_x + random.uniform(-CELL_SIZE//4, CELL_SIZE//4),
                        screen_y + random.uniform(-CELL_SIZE//4, CELL_SIZE//4),
                        particle_color,
                        vel_x,
                        vel_y,
                        size,
                        int(lifetime * self.settings['particle_lifetime'])
                    )
                    self.particles.append(particle)
    
    def create_line_clear_particles(self, cleared_lines):
        """Create special particles when lines are cleared"""
        if not self.settings['show_particles'] or not self.settings['particle_effects']:
            return
        
        for line_y in cleared_lines:
            for x in range(GRID_WIDTH):
                screen_x = x * CELL_SIZE + CELL_SIZE // 2
                screen_y = line_y * CELL_SIZE + CELL_SIZE // 2
                
                # Create more intense particles for line clears
                particle_count = int(random.randint(5, 8) * self.settings['particle_density'])
                for _ in range(max(1, particle_count)):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(2, 6)
                    vel_x = math.cos(angle) * speed
                    vel_y = math.sin(angle) * speed - random.uniform(2, 4)
                    
                    size = random.randint(3, 6)
                    lifetime = random.randint(1000, 2000)
                    
                    # Golden particles for golden cube lines
                    if (x, line_y) in self.golden_cubes:
                        particle_color = random.choice([GOLD, BRIGHT_GOLD, YELLOW])
                    else:
                        particle_color = random.choice([WHITE, YELLOW, ORANGE])
                    
                    particle = Particle(
                        screen_x + random.uniform(-CELL_SIZE//2, CELL_SIZE//2),
                        screen_y + random.uniform(-CELL_SIZE//2, CELL_SIZE//2),
                        particle_color,
                        vel_x,
                        vel_y,
                        size,
                        int(lifetime * self.settings['particle_lifetime'])
                    )
                    self.particles.append(particle)
    
    def update_particles(self, dt):
        """Update all particles and remove dead ones"""
        self.particles = [p for p in self.particles if p.update(dt)]
    
    def spawn_golden_cube(self, x, y):
        """Add a golden cube at the specified position"""
        self.golden_cubes.add((x, y))
    
    def activate_random_buff(self):
        """Activate a random buff when golden cubes are cleared"""
        buff_type = random.choice(list(self.buff_types.keys()))
        current_time = pygame.time.get_ticks()
        
        self.active_buffs[buff_type] = {
            'start_time': current_time,
            'duration': self.buff_types[buff_type]['duration']
        }
        
        # Apply immediate buff effects
        if buff_type == 'speed_boost':
            self.fall_speed = max(25, self.fall_speed // 2)
        elif buff_type == 'slow_fall':
            self.fall_speed = min(1000, self.fall_speed * 2)
        elif buff_type == 'hold_reset':
            self.can_hold = True
    
    def update_buffs(self):
        """Update active buffs and remove expired ones"""
        current_time = pygame.time.get_ticks()
        expired_buffs = []
        
        for buff_type, buff_data in self.active_buffs.items():
            if current_time - buff_data['start_time'] >= buff_data['duration']:
                expired_buffs.append(buff_type)
        
        # Remove expired buffs and reset their effects
        for buff_type in expired_buffs:
            del self.active_buffs[buff_type]
            if buff_type == 'speed_boost' or buff_type == 'slow_fall':
                self.fall_speed = max(50, 500 - (self.level - 1) * 50)
    
    def get_score_multiplier(self):
        """Get current score multiplier based on active buffs"""
        if 'score_multiplier' in self.active_buffs:
            return 2
        return 1
    
    def is_ghost_mode_active(self):
        """Check if ghost mode is active (pieces can pass through some blocks)"""
        return 'ghost_mode' in self.active_buffs
    
    def get_line_clear_bonus(self):
        """Get bonus multiplier for line clears"""
        if 'line_clear_bonus' in self.active_buffs:
            return 1.5
        return 1.0
    
    def clear_lines(self):
        lines_to_clear = []
        for y in range(GRID_HEIGHT):
            if all(self.grid[y][x] is not None for x in range(GRID_WIDTH)):
                lines_to_clear.append(y)
        
        if lines_to_clear:
            if len(lines_to_clear) > 1:
                # Multiple lines - start combo mode with delay
                self.combo_active = True
                self.combo_lines = sorted(lines_to_clear, reverse=True)  # Start from bottom
                self.combo_timer = 0
                # Don't clear the first line immediately - wait for timer
            else:
                # Single line - clear immediately
                self.clear_single_line(lines_to_clear[0])
                self.finish_line_clear()
        else:
            # No lines to clear - spawn new piece and reset hold
            self.spawn_new_piece()
            self.can_hold = True
    
    def clear_single_line(self, line_y):
        """Clear a single line and handle particles/golden cubes"""
        # Create line clear particles before clearing
        self.create_line_clear_particles([line_y])
        
        # Check for golden cubes in this line
        golden_cubes_cleared = 0
        for x in range(GRID_WIDTH):
            if (x, line_y) in self.golden_cubes:
                golden_cubes_cleared += 1
                self.golden_cubes.remove((x, line_y))
        
        # Clear the line and move everything above it down
        del self.grid[line_y]
        self.grid.insert(0, [None for _ in range(GRID_WIDTH)])
        
        # Update golden cube positions (move down by 1 only for cubes above the cleared line)
        golden_cubes_to_update = []
        for x, y in list(self.golden_cubes):
            if y < line_y:  # Only cubes above the cleared line need to move down
                golden_cubes_to_update.append((x, y))
        
        for x, y in golden_cubes_to_update:
            self.golden_cubes.remove((x, y))
            self.golden_cubes.add((x, y + 1))
        
        # Update score and stats
        self.lines_cleared += 1
        points = 100  # Base points per line in combo
        
        # Apply score multiplier and line clear bonus
        multiplier = self.get_score_multiplier() * self.get_line_clear_bonus()
        self.score += int(points * self.level * multiplier)
        
        # Activate buff if golden cubes were cleared
        if golden_cubes_cleared > 0:
            self.activate_random_buff()
        
        # Remove the line we just cleared first
        if line_y in self.combo_lines:
            self.combo_lines.remove(line_y)
        
        # Update remaining combo lines positions (since we removed a line above them)
        # Only lines above the cleared line need to move down
        self.combo_lines = [y + 1 if y < line_y else y for y in self.combo_lines]
    
    def finish_line_clear(self):
        """Finish line clearing process"""
        # Spawn new golden cubes randomly
        if random.random() < self.golden_spawn_chance:
            self.spawn_random_golden_cube()
        
        # Level up every 10 lines
        new_level = self.lines_cleared // 10 + 1
        if new_level > self.level:
            self.level = new_level
            # Don't update fall speed if speed buff is active
            if 'speed_boost' not in self.active_buffs and 'slow_fall' not in self.active_buffs:
                self.fall_speed = max(50, 500 - (self.level - 1) * 50)
        
        # Reset combo state and spawn new piece
        self.combo_active = False
        self.combo_lines = []
        self.combo_timer = 0
        self.spawn_new_piece()
        self.can_hold = True
    
    def spawn_random_golden_cube(self):
        """Spawn a golden cube at a random position in the grid"""
        # Find empty positions
        empty_positions = []
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.grid[y][x] is not None and (x, y) not in self.golden_cubes:
                    empty_positions.append((x, y))
        
        if empty_positions:
            x, y = random.choice(empty_positions)
            self.spawn_golden_cube(x, y)
    
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
        
        self.score += drop_distance * 2 * self.get_score_multiplier()
        self.place_piece()
    
    def soft_drop(self):
        if self.move_piece(0, 1):
            self.score += 1 * self.get_score_multiplier()
        else:
            self.place_piece()
    
    def update(self, dt):
        if self.game_over or self.paused:
            # Update particles even when paused/game over
            self.update_particles(dt)
            return
        
        # Update buffs
        self.update_buffs()
        
        # Update particles
        self.update_particles(dt)
        
        # Handle combo system
        if self.combo_active:
            self.combo_timer += dt
            if self.combo_timer >= self.combo_delay:
                if self.combo_lines:
                    # Clear next line in combo
                    self.clear_single_line(self.combo_lines[0])
                    self.combo_timer = 0
                else:
                    # Combo finished
                    self.finish_line_clear()
            return  # Don't update piece during combo
        
        if not self.current_piece:
            return
        
        self.fall_timer += dt
        if self.fall_timer >= self.fall_speed:
            if not self.move_piece(0, 1):
                self.place_piece()
            self.fall_timer = 0
    
    def handle_input(self, keys_pressed, dt):
        if self.game_over or self.paused or self.in_settings or self.combo_active:
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
            if self.in_settings:
                self.in_settings = False
            else:
                self.paused = not self.paused
            return
        
        if self.game_over:
            if key == pygame.K_r:
                self.__init__()  # Restart game
            return
        
        if self.in_settings:
            self.handle_settings_input(key)
            return
        
        if self.paused:
            if key == pygame.K_c:  # Open settings
                self.in_settings = True
            return
        
        # Don't accept input during combo
        if self.combo_active:
            return
        
        if key == pygame.K_w or key == pygame.K_UP:
            self.rotate_piece(clockwise=True)
        elif key == pygame.K_z:  # Counter-clockwise rotation
            self.rotate_piece(clockwise=False)
        elif key == pygame.K_q or key == pygame.K_SPACE:
            self.hard_drop()
        elif key == pygame.K_c:  # Hold piece
            self.hold_current_piece()
    
    def handle_settings_input(self, key):
        """Handle input in settings menu"""
        if key == pygame.K_UP or key == pygame.K_w:
            self.settings_selected = (self.settings_selected - 1) % len(self.settings_options)
        elif key == pygame.K_DOWN or key == pygame.K_s:
            self.settings_selected = (self.settings_selected + 1) % len(self.settings_options)
        elif key == pygame.K_LEFT or key == pygame.K_a:
            self.adjust_setting(-1)
        elif key == pygame.K_RIGHT or key == pygame.K_d:
            self.adjust_setting(1)
        elif key == pygame.K_ESCAPE:
            self.in_settings = False
    
    def adjust_setting(self, direction):
        """Adjust the currently selected setting"""
        current_option = self.settings_options[self.settings_selected]
        
        if current_option == 'particle_density':
            self.settings['particle_density'] = max(0.0, min(2.0, 
                self.settings['particle_density'] + direction * 0.1))
        elif current_option == 'particle_lifetime':
            self.settings['particle_lifetime'] = max(0.5, min(2.0, 
                self.settings['particle_lifetime'] + direction * 0.1))
        elif current_option == 'particle_effects':
            self.settings['particle_effects'] = not self.settings['particle_effects']
        elif current_option == 'show_particles':
            self.settings['show_particles'] = not self.settings['show_particles']

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

def draw_cell(screen, x, y, color, alpha=255, is_golden=False):
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
        
        # Draw golden cube effect
        if is_golden:
            # Animated golden sparkle effect
            current_time = pygame.time.get_ticks()
            sparkle_alpha = int(abs(255 * (0.5 + 0.5 * (current_time % 1000) / 1000 - 0.5)))
            
            # Create golden overlay
            gold_surface = pygame.Surface((CELL_SIZE - 1, CELL_SIZE - 1))
            gold_surface.set_alpha(sparkle_alpha)
            gold_surface.fill(BRIGHT_GOLD)
            screen.blit(gold_surface, rect.topleft)
            
            # Draw golden border
            pygame.draw.rect(screen, GOLD, rect, 3)

def draw_game(screen, game):
    screen.fill(BLACK)
    
    # Draw grid
    draw_grid(screen)
    
    # Draw placed pieces
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if game.grid[y][x] is not None:
                is_golden = (x, y) in game.golden_cubes
                draw_cell(screen, x, y, game.grid[y][x], is_golden=is_golden)
    
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
    
    # Draw particles
    if game.settings['show_particles']:
        for particle in game.particles:
            particle.draw(screen)
    
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
    
    # Active buffs
    buff_y = 160
    if game.active_buffs:
        buff_title = font_medium.render("Active Buffs:", True, GOLD)
        screen.blit(buff_title, (ui_x, buff_y))
        buff_y += 25
        
        current_time = pygame.time.get_ticks()
        for buff_type, buff_data in game.active_buffs.items():
            buff_info = game.buff_types[buff_type]
            remaining_time = (buff_data['duration'] - (current_time - buff_data['start_time'])) / 1000
            
            if remaining_time > 0:
                buff_text = font_small.render(f"{buff_info['name']}: {remaining_time:.1f}s", True, buff_info['color'])
                screen.blit(buff_text, (ui_x, buff_y))
                buff_y += 18
    
    # Golden cubes count
    if game.golden_cubes:
        golden_text = font_small.render(f"Golden Cubes: {len(game.golden_cubes)}", True, GOLD)
        screen.blit(golden_text, (ui_x, buff_y))
        buff_y += 25
    
    # Adjust other UI elements position
    hold_y = buff_y + 10
    
    # Hold piece
    hold_text = font_medium.render("Hold:", True, WHITE)
    screen.blit(hold_text, (ui_x, hold_y))
    
    if game.hold_piece:
        hold_tetromino = Tetromino(game.hold_piece)
        hold_shape = hold_tetromino.get_shape()
        hold_color = hold_tetromino.color if game.can_hold else tuple(c // 2 for c in hold_tetromino.color)
        
        for row_idx, row in enumerate(hold_shape):
            for col_idx, cell in enumerate(row):
                if cell == '#':
                    x = ui_x + col_idx * 20
                    y = hold_y + 30 + row_idx * 20
                    pygame.draw.rect(screen, hold_color, (x, y, 18, 18))
    
    # Next piece
    next_y = hold_y + 100
    next_text = font_medium.render("Next:", True, WHITE)
    screen.blit(next_text, (ui_x, next_y))
    
    if game.next_piece:
        next_tetromino = Tetromino(game.next_piece)
        next_shape = next_tetromino.get_shape()
        
        for row_idx, row in enumerate(next_shape):
            for col_idx, cell in enumerate(row):
                if cell == '#':
                    x = ui_x + col_idx * 20
                    y = next_y + 30 + row_idx * 20
                    pygame.draw.rect(screen, next_tetromino.color,
                                   (x, y, 18, 18))
    
    # Controls
    controls_y = next_y + 120
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
        "Pause Menu:",
        "C - Settings",
        "",
        "Golden Cubes:",
        "Clear lines with golden",
        "cubes for random buffs!",
        "",
        "R - Restart (Game Over)"
    ]
    
    for i, text in enumerate(controls):
        color = WHITE if i == 0 else LIGHT_GRAY
        font = font_medium if i == 0 else font_small
        control_text = font.render(text, True, color)
        screen.blit(control_text, (ui_x, controls_y + i * 20))
    
    # Pause overlay
    if game.paused and not game.in_settings:
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        
        pause_text = font_large.render("PAUSED", True, WHITE)
        resume_text = font_medium.render("Press P to resume", True, WHITE)
        settings_text = font_medium.render("Press C for settings", True, WHITE)
        
        text_rect = pause_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 40))
        resume_rect = resume_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        settings_rect = settings_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 40))
        
        screen.blit(pause_text, text_rect)
        screen.blit(resume_text, resume_rect)
        screen.blit(settings_text, settings_rect)
    
    # Settings overlay
    elif game.in_settings:
        draw_settings_menu(screen, game)
    
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

def draw_settings_menu(screen, game):
    """Draw the settings menu overlay"""
    font_large = pygame.font.Font(None, 36)
    font_medium = pygame.font.Font(None, 24)
    font_small = pygame.font.Font(None, 18)
    
    # Dark overlay
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    overlay.set_alpha(200)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))
    
    # Settings window
    settings_width = 400
    settings_height = 300
    settings_x = (WINDOW_WIDTH - settings_width) // 2
    settings_y = (WINDOW_HEIGHT - settings_height) // 2
    
    # Draw settings background
    pygame.draw.rect(screen, DARK_GRAY, (settings_x, settings_y, settings_width, settings_height))
    pygame.draw.rect(screen, WHITE, (settings_x, settings_y, settings_width, settings_height), 2)
    
    # Title
    title_text = font_large.render("SETTINGS", True, WHITE)
    title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, settings_y + 30))
    screen.blit(title_text, title_rect)
    
    # Settings options
    option_y = settings_y + 70
    for i, option in enumerate(game.settings_options):
        option_name = game.settings_names[option]
        setting_value = game.settings[option]
        
        # Highlight selected option
        if i == game.settings_selected:
            highlight_rect = pygame.Rect(settings_x + 10, option_y + i * 40 - 5, settings_width - 20, 30)
            pygame.draw.rect(screen, (50, 50, 50), highlight_rect)
            pygame.draw.rect(screen, WHITE, highlight_rect, 1)
        
        # Option name
        option_text = font_medium.render(option_name, True, WHITE)
        screen.blit(option_text, (settings_x + 20, option_y + i * 40))
        
        # Option value
        if isinstance(setting_value, bool):
            value_text = "ON" if setting_value else "OFF"
            value_color = (0, 255, 0) if setting_value else (255, 0, 0)
        else:
            value_text = f"{setting_value:.1f}"
            value_color = WHITE
        
        value_surface = font_medium.render(value_text, True, value_color)
        value_rect = value_surface.get_rect(right=settings_x + settings_width - 20, top=option_y + i * 40)
        screen.blit(value_surface, value_rect)
    
    # Controls help
    help_y = settings_y + settings_height - 80
    help_texts = [
        "Use W/S or ↑/↓ to navigate",
        "Use A/D or ←/→ to adjust values",
        "Press P or ESC to close"
    ]
    
    for i, help_text in enumerate(help_texts):
        help_surface = font_small.render(help_text, True, LIGHT_GRAY)
        help_rect = help_surface.get_rect(center=(WINDOW_WIDTH // 2, help_y + i * 20))
        screen.blit(help_surface, help_rect)

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