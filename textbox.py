import os
import pygame
import ctypes

class SimpleTextWindow:
    def __init__(self, width=600, height=100, x=300, y=200):
        os.environ['SDL_VIDEO_WINDOW_POS'] = f"{x},{y}"
        self.screen = pygame.display.set_mode((width, height), pygame.NOFRAME)
        self.width=width
        self.height=height
        pygame.display.set_caption("Text Overlay")
        self.set_always_on_top()

    def set_always_on_top(self):
        hwnd = pygame.display.get_wm_info()['window']
        # HWND_TOPMOST = -1, SWP_NOMOVE = 0x0002, SWP_NOSIZE = 0x0001
        ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002)
        
        # Colors
        self.BG_COLOR = (240, 240, 240)
        self.TEXT_COLOR = (0, 0, 0)
        self.CURSOR_COLOR = (0, 0, 0)
        
        # Text properties
        self.font = pygame.font.Font(None, 32)
        self.text = ""
        self.cursor_visible = True
        self.cursor_timer = 0
        self.cursor_blink_speed = 500  # milliseconds
        
        # Text box rectangle
        self.text_rect = pygame.Rect(10, 10, self.width - 20, self.height - 20)
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    # Print current text when Enter is pressed
                    print(f"Text entered: {self.text}")
                    self.text = ""  # Clear after displaying
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    # Add character to text (filter out non-printable characters)
                    if event.unicode.isprintable():
                        self.text += event.unicode
                        
        return True
    
    def update_cursor(self):
        # Blink cursor
        self.cursor_timer += 1
        if self.cursor_timer >= self.cursor_blink_speed // 16:  # Assuming 60 FPS
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0
    
    def draw(self):
        self.screen.fill(self.BG_COLOR)
        
        # Draw text box background
        pygame.draw.rect(self.screen, (255, 255, 255), self.text_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), self.text_rect, 2)
        
        # Render text
        text_surface = self.font.render(self.text, True, self.TEXT_COLOR)
        
        # Calculate text position (centered vertically)
        text_y = self.text_rect.centery - text_surface.get_height() // 2
        
        # Draw text with clipping to stay within the box
        text_pos = (self.text_rect.left + 5, text_y)
        self.screen.blit(text_surface, text_pos, 
                        area=pygame.Rect(0, 0, 
                                       min(text_surface.get_width(), self.text_rect.width - 10),
                                       text_surface.get_height()))
        
        # Draw blinking cursor
        if self.cursor_visible:
            cursor_x = self.text_rect.left + 5 + text_surface.get_width()
            cursor_y = text_y
            cursor_height = text_surface.get_height()
            pygame.draw.line(self.screen, self.CURSOR_COLOR,
                           (cursor_x, cursor_y),
                           (cursor_x, cursor_y + cursor_height), 2)

# Usage
if __name__ == "__main__":
    window = SimpleTextWindow()
    clock = pygame.time.Clock()
    running=True
    while running:
        running = window.handle_events()
        window.update_cursor()
        window.draw()
        
        pygame.display.flip()
        clock.tick(60)
        
        # Display text in console as you type (optional)
        # if window.text:  # Only print if there's text
        #     print(f"Current text: {window.text}", end='\r')
    pygame.quit()