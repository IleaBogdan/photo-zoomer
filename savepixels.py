import glfw
from OpenGL.GL import *
import cupy as cp
import numpy as np
from PIL import Image

# Setup
glfw.init()
window = glfw.create_window(800, 600, "Pixel Grabber", None, None)
glfw.make_context_current(window)

frame_count = 0

while not glfw.window_should_close(window):
    # Render something
    glClearColor(0.2, 0.3, 0.8, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    
    # Grab pixels
    width, height = 800, 600
    pixels = glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE)
    
    # Convert to arrays
    cpu_array = np.frombuffer(pixels, dtype=np.uint8).reshape((height, width, 3))
    gpu_array = cp.asarray(cpu_array)
    
    # OPTION 1: Print ALL pixels (warning: huge output!)
    print("=== ALL PIXELS RGB VALUES ===")
    print(cpu_array)
    print(f"Array shape: {cpu_array.shape}")  # (600, 800, 3)
    print(f"Total pixels: {height * width}")
    
    # # OPTION 2: Print just a sample of pixels (more practical)
    # print("\n=== SAMPLE OF PIXELS (first 10x10 corner) ===")
    # print(cpu_array[:10, :10, :])  # First 10 rows, 10 columns
    
    # # OPTION 3: Print specific pixel coordinates
    # print("\n=== SPECIFIC PIXELS ===")
    # print(f"Top-left (0,0): {cpu_array[0, 0, :]}")      # RGB at top-left
    # print(f"Center (300,400): {cpu_array[300, 400, :]}") # RGB at center
    # print(f"Bottom-right (599,799): {cpu_array[599, 799, :]}") # RGB at bottom-right
    
    # OPTION 4: Print unique colors found
    print("\n=== UNIQUE COLORS (first 10) ===")
    # Reshape to list of RGB tuples
    unique_colors = np.unique(cpu_array.reshape(-1, 3), axis=0)
    print(unique_colors[:10])  # Print first 10 unique colors
    
    # OPTION 5: Print pixel at mouse position (if you have mouse input)
    # x, y = glfw.get_cursor_pos(window)
    # y = height - int(y) - 1  # Flip Y coordinate
    # if 0 <= x < width and 0 <= y < height:
    #     print(f"Mouse pixel at ({int(x)},{int(y)}): {cpu_array[y, int(x), :]}")
    
    # Do GPU processing (example: invert colors)
    processed = 255 - gpu_array
    
    # Save every 10 frames to avoid spam
    if frame_count % 10 == 0:
        result = cp.asnumpy(processed)
        Image.fromarray(result, 'RGB').save(f'current_frame_{frame_count}.png')
        print(f"Saved frame {frame_count}")
    
    frame_count += 1
    
    glfw.swap_buffers(window)
    glfw.poll_events()

glfw.terminate()