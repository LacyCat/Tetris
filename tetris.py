import os
import sys
import random
import time
import threading
from collections import deque

class Tetris:
    def __init__(self):
        self.width = 10
        self.height = 20
        self.board = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.fall_time = 0.8
        self.last_fall = time.time()
        self.game_over = False
        self.paused = False
        
        self.current_piece = None
        self.next_piece = None
        self.piece_x = 0
        self.piece_y = 0
        
        self.tetrominoes = {
            'I': [
                ['.....',
                 '..#..',
                 '..#..',
                 '..#..',
                 '..#..'],
                ['.....',
                 '.....',
                 '####.',
                 '.....',
                 '.....']
            ],
            'O': [
                ['.....',
                 '.....',
                 '.##..',
                 '.##..',
                 '.....']
            ],
            'T': [
                ['.....',
                 '.....',
                 '.#...',
                 '###..',
                 '.....'],
                ['.....',
                 '.....',
                 '.#...',
                 '.##..',
                 '.#...'],
                ['.....',
                 '.....',
                 '.....',
                 '###..',
                 '.#...'],
                ['.....',
                 '.....',
                 '.#...',
                 '##...',
                 '.#...']
            ],
            'S': [
                ['.....',
                 '.....',
                 '.##..',
                 '##...',
                 '.....'],
                ['.....',
                 '.#...',
                 '.##..',
                 '..#..',
                 '.....']
            ],
            'Z': [
                ['.....',
                 '.....',
                 '##...',
                 '.##..',
                 '.....'],
                ['.....',
                 '..#..',
                 '.##..',
                 '.#...',
                 '.....']
            ],
            'J': [
                ['.....',
                 '.#...',
                 '.#...',
                 '##...',
                 '.....'],
                ['.....',
                 '.....',
                 '#....',
                 '###..',
                 '.....'],
                ['.....',
                 '.##..',
                 '.#...',
                 '.#...',
                 '.....'],
                ['.....',
                 '.....',
                 '###..',
                 '..#..',
                 '.....']
            ],
            'L': [
                ['.....',
                 '..#..',
                 '..#..',
                 '.##..',
                 '.....'],
                ['.....',
                 '.....',
                 '###..',
                 '#....',
                 '.....'],
                ['.....',
                 '##...',
                 '.#...',
                 '.#...',
                 '.....'],
                ['.....',
                 '.....',
                 '..#..',
                 '###..',
                 '.....']
            ]
        }
        
        self.colors = {
            'I': '36',  # cyan
            'O': '33',  # yellow
            'T': '35',  # magenta
            'S': '32',  # green
            'Z': '31',  # red
            'J': '34',  # blue
            'L': '91'   # light red
        }
        
        self.spawn_new_piece()
        
    def spawn_new_piece(self):
        if self.next_piece is None:
            self.next_piece = random.choice(list(self.tetrominoes.keys()))
        
        self.current_piece = self.next_piece
        self.next_piece = random.choice(list(self.tetrominoes.keys()))
        self.piece_rotation = 0
        self.piece_x = self.width // 2 - 2
        self.piece_y = 0
        
        if not self.is_valid_position(self.piece_x, self.piece_y, self.piece_rotation):
            self.game_over = True
    
    def get_piece_shape(self, piece_type, rotation):
        return self.tetrominoes[piece_type][rotation % len(self.tetrominoes[piece_type])]
    
    def is_valid_position(self, x, y, rotation):
        shape = self.get_piece_shape(self.current_piece, rotation)
        
        for py, row in enumerate(shape):
            for px, cell in enumerate(row):
                if cell == '#':
                    nx, ny = x + px, y + py
                    if (nx < 0 or nx >= self.width or 
                        ny >= self.height or 
                        (ny >= 0 and self.board[ny][nx] != 0)):
                        return False
        return True
    
    def place_piece(self):
        shape = self.get_piece_shape(self.current_piece, self.piece_rotation)
        
        for py, row in enumerate(shape):
            for px, cell in enumerate(row):
                if cell == '#':
                    nx, ny = self.piece_x + px, self.piece_y + py
                    if 0 <= ny < self.height and 0 <= nx < self.width:
                        self.board[ny][nx] = self.current_piece
        
        self.clear_lines()
        self.spawn_new_piece()
    
    def clear_lines(self):
        lines_to_clear = []
        for y in range(self.height):
            if all(self.board[y][x] != 0 for x in range(self.width)):
                lines_to_clear.append(y)
        
        for y in sorted(lines_to_clear, reverse=True):
            del self.board[y]
            self.board.insert(0, [0 for _ in range(self.width)])
        
        lines_cleared = len(lines_to_clear)
        if lines_cleared > 0:
            self.lines_cleared += lines_cleared
            self.score += lines_cleared * 100 * self.level
            if lines_cleared == 4:  # Tetris bonus
                self.score += 300 * self.level
            
            # Level up every 10 lines
            self.level = self.lines_cleared // 10 + 1
            self.fall_time = max(0.1, 0.8 - (self.level - 1) * 0.05)
    
    def move_piece(self, dx, dy):
        if self.is_valid_position(self.piece_x + dx, self.piece_y + dy, self.piece_rotation):
            self.piece_x += dx
            self.piece_y += dy
            return True
        return False
    
    def rotate_piece(self):
        new_rotation = (self.piece_rotation + 1) % len(self.tetrominoes[self.current_piece])
        if self.is_valid_position(self.piece_x, self.piece_y, new_rotation):
            self.piece_rotation = new_rotation
    
    def hard_drop(self):
        while self.move_piece(0, 1):
            self.score += 2  # Bonus points for hard drop
        self.place_piece()
    
    def soft_drop(self):
        if self.move_piece(0, 1):
            self.score += 1  # Bonus point for soft drop
        else:
            self.place_piece()
    
    def update(self):
        current_time = time.time()
        if current_time - self.last_fall >= self.fall_time:
            if not self.move_piece(0, 1):
                self.place_piece()
            self.last_fall = current_time
    
    def render(self):
        os.system('clear' if os.name == 'posix' else 'cls')
        
        # Create display board
        display_board = [row[:] for row in self.board]
        
        # Add current piece to display
        if self.current_piece:
            shape = self.get_piece_shape(self.current_piece, self.piece_rotation)
            for py, row in enumerate(shape):
                for px, cell in enumerate(row):
                    if cell == '#':
                        nx, ny = self.piece_x + px, self.piece_y + py
                        if 0 <= ny < self.height and 0 <= nx < self.width:
                            display_board[ny][nx] = self.current_piece
        
        # Print game info
        print(f"\033[1;37m╔════════════════════════╦═══════════╗")
        print(f"║ \033[1;33mTETRIS\033[1;37m               ║ \033[1;36mNEXT\033[1;37m      ║")
        print(f"╠════════════════════════╬═══════════╣")
        
        # Print board with next piece
        for i in range(max(self.height, 6)):
            if i < self.height:
                line = "║ "
                for cell in display_board[i]:
                    if cell == 0:
                        line += "\033[1;30m▒▒\033[0m"
                    else:
                        color = self.colors.get(cell, '37')
                        line += f"\033[1;{color}m██\033[0m"
                line += " ║"
            else:
                line = "║                        ║"
            
            # Add next piece display
            if i < 5 and self.next_piece:
                next_shape = self.get_piece_shape(self.next_piece, 0)
                next_line = " "
                if i < len(next_shape):
                    for cell in next_shape[i][:4]:  # Only show first 4 chars
                        if cell == '#':
                            color = self.colors.get(self.next_piece, '37')
                            next_line += f"\033[1;{color}m██\033[0m"
                        else:
                            next_line += "  "
                else:
                    next_line += "        "
                line += next_line + " ║"
            else:
                line += "           ║"
            
            print(line)
        
        print(f"\033[1;37m╠════════════════════════╬═══════════╣")
        print(f"║ \033[1;33mScore: {self.score:8d}\033[1;37m     ║ \033[1;32mLevel: {self.level:2d}\033[1;37m  ║")
        print(f"║ \033[1;35mLines: {self.lines_cleared:8d}\033[1;37m     ║           ║")
        print(f"╚════════════════════════╩═══════════╝")
        print(f"\033[1;37mControls: \033[1;33mW\033[0m-Rotate \033[1;33mA\033[0m-Left \033[1;33mD\033[0m-Right \033[1;33mS\033[0m-Down \033[1;33mQ\033[0m-Hard Drop \033[1;31mESC\033[0m-Quit")
        
        if self.game_over:
            print(f"\n\033[1;31m╔═══════════════╗")
            print(f"║   GAME OVER   ║")
            print(f"║ Press R to    ║")
            print(f"║ restart or    ║")
            print(f"║ ESC to quit   ║")
            print(f"╚═══════════════╝\033[0m")

def get_key_input():
    if os.name == 'nt':  # Windows
        import msvcrt
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b'\xe0':  # Special key prefix on Windows
                key = msvcrt.getch()
            return key.decode('utf-8', errors='ignore').lower()
    else:  # Unix/Linux/Mac
        import termios, tty
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            key = sys.stdin.read(1)
            if key == '\x1b':  # ESC sequence
                key += sys.stdin.read(2)
            return key.lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return None

def main():
    game = Tetris()
    
    # Key press tracking for smooth movement
    keys_pressed = set()
    key_timers = {}
    repeat_delay = 0.15
    
    print("\033[?25l")  # Hide cursor
    
    try:
        while True:
            # Handle input
            key = None
            try:
                # Non-blocking input check
                if os.name == 'nt':
                    import msvcrt
                    if msvcrt.kbhit():
                        key = msvcrt.getch().decode('utf-8', errors='ignore').lower()
                else:
                    try:
                        import select
                        if select.select([sys.stdin], [], [], 0.01)[0]:
                            key = sys.stdin.read(1).lower()
                            if key == '\x1b':  # ESC
                                break
                    except:
                        # Fallback: simple input without select
                        import sys
                        key = input("Enter command (w/a/s/d/q/esc): ").lower()
                        if key == 'esc':
                            break
            except:
                pass
            
            current_time = time.time()
            
            if key:
                if key == '\x1b' or key == '\x03':  # ESC or Ctrl+C
                    break
                elif key == 'r' and game.game_over:
                    game = Tetris()
                    keys_pressed.clear()
                    key_timers.clear()
                elif not game.game_over:
                    if key in 'wasdq':
                        keys_pressed.add(key)
                        key_timers[key] = current_time
            
            # Handle continuous key presses
            if not game.game_over:
                for pressed_key in list(keys_pressed):
                    if pressed_key in key_timers and current_time - key_timers[pressed_key] >= repeat_delay:
                        if pressed_key == 'w':
                            game.rotate_piece()
                            keys_pressed.discard('w')  # Rotation shouldn't repeat
                        elif pressed_key == 'a':
                            game.move_piece(-1, 0)
                            key_timers[pressed_key] = current_time
                        elif pressed_key == 'd':
                            game.move_piece(1, 0)
                            key_timers[pressed_key] = current_time
                        elif pressed_key == 's':
                            game.soft_drop()
                            key_timers[pressed_key] = current_time
                        elif pressed_key == 'q':
                            game.hard_drop()
                            keys_pressed.discard('q')  # Hard drop shouldn't repeat
                
                # Initial key press handling
                if key and key in 'wasdq' and not game.game_over:
                    if key == 'w':
                        game.rotate_piece()
                    elif key == 'a':
                        game.move_piece(-1, 0)
                    elif key == 'd':
                        game.move_piece(1, 0)
                    elif key == 's':
                        game.soft_drop()
                    elif key == 'q':
                        game.hard_drop()
            
            # Update game
            if not game.game_over:
                game.update()
            
            # Render
            game.render()
            
            # Small delay to prevent excessive CPU usage
            time.sleep(0.05)
    
    except KeyboardInterrupt:
        pass
    finally:
        print("\033[?25h")  # Show cursor
        print("\033[0m")    # Reset colors

if __name__ == "__main__":
    # Setup terminal for better input handling on Unix systems
    if os.name != 'nt':
        try:
            import termios, tty, atexit
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            
            def restore_terminal():
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            
            atexit.register(restore_terminal)
            tty.setcbreak(sys.stdin.fileno())
        except:
            pass  # Fallback for environments where terminal control is not available
    
    main()