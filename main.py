import numpy as np
import cv2
import cupy as cp
import glfw
from OpenGL.GL import *
from PIL import Image
from io import * 
import pygame
import sys
from textbox import SimpleTextWindow
import threading

running_event=threading.Event()
running_event.set()

def make_full_screen_window(): # returning a window with screen size
    monitor=glfw.get_primary_monitor()
    video_mode=glfw.get_video_mode(monitor)
    window=glfw.create_window(
        video_mode.size.width,
        video_mode.size.height,
        "Fullscreen Window",
        None,
        None
    )
    glfw.set_window_attrib(window,glfw.DECORATED,False)
    glfw.set_window_pos(window,0,0)
    return window

def load_image_to_next_frame(image_path):
    # Load image to GPU
    pil_image=Image.open(image_path).convert('RGB')
    pil_image=pil_image.transpose(Image.FLIP_TOP_BOTTOM)
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
    global texture_id,img_w,img_h
    texture_id,img_w,img_h=load_image_to_next_frame('./output.png') # loading the image to gpu

def mouse_button_callback(window, button, action, mods):
    if button==glfw.MOUSE_BUTTON_LEFT and action==glfw.PRESS:
        x,y=glfw.get_cursor_pos(window)
        print(f"Mouse clicked at: x={x}, y={y}")

def init():
    pygame.init()
    glfw.init()
    # opengl window (with glfw)
    global window
    window=make_full_screen_window()
    glfw.make_context_current(window)
    glfw.set_mouse_button_callback(window, mouse_button_callback)
    # init loading the image
    init_img()
    # text_window 
    global text_window
    text_window=SimpleTextWindow(width=600, height=100, x=300, y=200)
    # clock for frame rate limit
    global clock
    clock=pygame.time.Clock()

def run_text_window(): # text_window loop
    while running_event.is_set():
        # pulling text and displaying the text
        if not text_window.handle_events():
            running_event.clear() # updating the inter thread variable to stop both threads
        text_window.update_cursor()
        text_window.draw()
        pygame.display.flip()
        clock.tick(60)

def loop():
    # Start Pygame text window in a separate thread
    text_thread=threading.Thread(target=run_text_window,daemon=True)
    text_thread.start()

    # OpenGL window loop
    while (not glfw.window_should_close(window)) and glfw.get_key(window, glfw.KEY_ESCAPE)!=glfw.PRESS and running_event.is_set():
        # buffer clearing
        glClearColor(.2,.3,.8,1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        
        # printing the image on the screen
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
        # buffer swapping
        glfw.swap_buffers(window)

def kill(): # destructor 
    glfw.terminate()
    cv2.destroyAllWindows()
    pygame.quit()
    sys.exit()

def main(): # les mainos lupos
    init();loop();kill()
if __name__=="__main__":
    main()