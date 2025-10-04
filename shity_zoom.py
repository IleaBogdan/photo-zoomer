import numpy as np
import cv2
import cupy as cp
import glfw
from OpenGL.GL import *
from PIL import Image

zoom_factor = 2.0  # How much to zoom in
zoom_center = None  # (x, y) in normalized coordinates

def make_full_screen_window():
    monitor = glfw.get_primary_monitor()
    video_mode = glfw.get_video_mode(monitor)
    window = glfw.create_window(
        video_mode.size.width,
        video_mode.size.height,
        "Fullscreen Window",
        monitor,
        None
    )
    return window

def load_image_to_next_frame(image_path):
    print(Image)
    pil_image = Image.open(image_path).convert('RGB')
    cpu_array = np.array(pil_image)
    gpu_image = cp.asarray(cpu_array)
    cpu_for_texture = cp.asnumpy(gpu_image)
    h, w = cpu_array.shape[:2]
    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, w, h, 0, GL_RGB, GL_UNSIGNED_BYTE, cpu_for_texture)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    return texture_id, w, h

def zoom_in(x, y):
    """
    Set the zoom center and factor.
    x, y: mouse coordinates in window space
    """
    global zoom_center
    # Convert to normalized coordinates (-1 to 1)
    norm_x = (x / img_w) * 2 - 1
    norm_y = 1 - (y / img_h) * 2
    zoom_center = (norm_x, norm_y)

def mouse_button_callback(window, button, action, mods):
    if button == glfw.MOUSE_BUTTON_LEFT and action == glfw.PRESS:
        xpos, ypos = glfw.get_cursor_pos(window)
        zoom_in(xpos, ypos)

def init():
    glfw.init()
    global window
    window = make_full_screen_window()
    glfw.make_context_current(window)
    global texture_id, img_w, img_h
    texture_id, img_w, img_h = load_image_to_next_frame('./output.png')
    glfw.set_mouse_button_callback(window, mouse_button_callback)

def clamp(val, minval, maxval):
    return max(minval, min(val, maxval))

def get_zoomed_quad(zx, zy, zoom_factor):
    half_width = 1.0 / (zoom_factor*2)
    half_height = 1.0 / (zoom_factor*2)

    # Clamp so the zoom window stays inside [-1, 1]
    left = zx - half_width
    right = zx + half_width
    bottom = zy - half_height
    top = zy + half_height

    # Shift if out of bounds
    if left < -1:
        right += (-1 - left)
        left = -1
    if right > 1:
        left -= (right - 1)
        right = 1
    if bottom < -1:
        top += (-1 - bottom)
        bottom = -1
    if top > 1:
        bottom -= (top - 1)
        top = 1

    # Final clamp (in case image is smaller than zoom window)
    left = max(left, -1)
    right = min(right, 1)
    bottom = max(bottom, -1)
    top = min(top, 1)
    return left, right, bottom, top

def loop():
    while not glfw.window_should_close(window):
        glClearColor(.2,.3,.8,1.0)
        glClear(GL_COLOR_BUFFER_BIT)

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D,texture_id)
        glBegin(GL_QUADS)

        if zoom_center:
            zx, zy = zoom_center
            left, right, bottom, top = get_zoomed_quad(zx, zy, zoom_factor)
        else:
            left, right, bottom, top = -1, 1, -1, 1

        glTexCoord2f(0, 0); glVertex2f(left, bottom)
        glTexCoord2f(1, 0); glVertex2f(right, bottom)
        glTexCoord2f(1, 1); glVertex2f(right, top)
        glTexCoord2f(0, 1); glVertex2f(left, top)
        glEnd()
        glDisable(GL_TEXTURE_2D)
        
        glfw.poll_events()
        glfw.swap_buffers(window)

def kill():
    glfw.terminate()
    cv2.destroyAllWindows()

def main():
    init()
    loop()
    kill()

if __name__ == "__main__":
    main()