import numpy as np
import cv2
import cupy as cp
import glfw
from OpenGL.GL import *
from PIL import Image
from io import * 

def make_full_screen_window():
    monitor=glfw.get_primary_monitor()
    video_mode=glfw.get_video_mode(monitor)
    window = glfw.create_window(
        video_mode.size.width,      # screen width
        video_mode.size.height,     # screen height
        "Fullscreen Window",        # window title
        monitor,                    # fullscreen
        None                        # no share context
    )
    return window

def load_image_to_next_frame(image_path):
    """Load image and make it appear in the next frame"""
    # Load image to GPU
    print(Image)
    pil_image=Image.open(image_path).convert('RGB')
    cpu_array=np.array(pil_image)
    gpu_image=cp.asarray(cpu_array)
    # Create texture
    cpu_for_texture=cp.asnumpy(gpu_image)  # Quick copy back for OpenGL
    h,w=cpu_array.shape[:2]
    texture_id=glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D,texture_id)
    glTexImage2D(GL_TEXTURE_2D,0,GL_RGB,w,h,0,GL_RGB,GL_UNSIGNED_BYTE,cpu_for_texture)
    glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR)
    return texture_id,w,h

def init_img():
    global texture_id, img_w, img_h
    texture_id, img_w, img_h = load_image_to_next_frame('./output.png')
    
def mouse_button_callback(window, button, action, mods):
    if button == glfw.MOUSE_BUTTON_LEFT and action == glfw.PRESS:
        x, y = glfw.get_cursor_pos(window)
        print(f"Mouse clicked at: x={x}, y={y}")

def init():
    glfw.init()
    global window
    window = make_full_screen_window()
    glfw.make_context_current(window)
    glfw.set_mouse_button_callback(window, mouse_button_callback)  # Register callback
    init_img()

def select_zone(np_image: np.array, x: int, y: int, zoom_level: int, w_resolution: int = 1920, h_resolution: int = 1080):
    # returns required image section (x, y, x+1920*zoom_level)
    w_ct = np_image.shape[0] / w_resolution
    h_ct = np_image.shape[1] / h_resolution

    sectioned_array = np_image[x : x + w_ct * zoom_level, y : y + h_ct * zoom_level]
    
    return sectioned_array

def compress_zone(np_image_section: np.array, quality: int = 95):
    jpg_img = Image.fromarray(np_image_section)
    buf = BytesIO()
    jpg_img.save(buf, format="JPEG", quality=quality)
    
    return buf.getvalue()

def get_zone_image(np_image: np.array, x: int, y: int, zoom_level: int, w_resolution: int = 1920, h_resolution: int = 1080):
    return compress_zone(select_zone(np_image=np_image, 
                                     x=x, 
                                     y=y, 
                                     zoom_level=zoom_level, 
                                     w_resolution=w_resolution, 
                                     h_resolution=h_resolution))

def save_compression_levels(np_image: np.array, filename: str, exit_w_dim: int = 1920, exit_h_dim: int = 1080):
    w_img = np_image.shape[0]
    h_img = np_image.shape[0]

    for compression_level in range(1, max(w_img/exit_w_dim, h_img/exit_h_dim)):
        x = 0
        while x + exit_w_dim * compression_level <= w_img:
            y = 0
            while y + exit_h_dim * compression_level <= h_img:
                with open(f'{filename}_compression_level_{compression_level}.jpg', 'wb') as f:
                    f.write(get_zone_image(np_image=np_image, x=x, y=y, w_resolution=exit_w_dim, h_resolution=exit_h_dim))

def loop():
    while (not glfw.window_should_close(window)):
        glClearColor(.2,.3,.8,1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D,texture_id)
        glBegin(GL_QUADS)
        glTexCoord2f(0,0); glVertex2f(-1,-1)
        glTexCoord2f(1,0); glVertex2f(1,-1)
        glTexCoord2f(1,1); glVertex2f(1,1)
        glTexCoord2f(0,1); glVertex2f(-1,1)
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
if __name__=="__main__":
    main()