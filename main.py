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
from loader import *

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

def crop_and_resize_image(image, zoom_level, target_w, target_h):
    w, h = image.size
    target_aspect = target_w / target_h

    # Calculate crop size based on zoom_level and aspect ratio
    crop_w = int(w / zoom_level)
    crop_h = int(h / zoom_level)

    # Adjust crop_w and crop_h to maintain aspect ratio
    if crop_w / crop_h > target_aspect:
        crop_w = int(crop_h * target_aspect)
    else:
        crop_h = int(crop_w / target_aspect)

    left = (w - crop_w) // 2
    top = (h - crop_h) // 2
    right = left + crop_w
    bottom = top + crop_h

    cropped = image.crop((left, top, right, bottom))
    resized = cropped.resize((target_w, target_h), Image.LANCZOS)
    return resized

zoom_level=1
def load_image_to_next_frame2(image, target_w=1920, target_h=1080):
    pil_image = crop_and_resize_image(image, zoom_level, target_w, target_h)
    pil_image = pil_image.transpose(Image.FLIP_TOP_BOTTOM)
    cpu_array = np.array(pil_image)
    gpu_image = cp.asarray(cpu_array)
    cpu_for_texture = cp.asnumpy(gpu_image)
    h, w = cpu_array.shape[:2]
    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, w, h, 0, GL_RGB, GL_UNSIGNED_BYTE, cpu_for_texture)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    return texture_id, w, h

def init_img(funct,param):
    global texture_id,img_w,img_h
    texture_id,img_w,img_h=funct(param) # loading the image to gpu

def mouse_button_callback(window, button, action, mods):
    if button==glfw.MOUSE_BUTTON_LEFT and action==glfw.PRESS:
        x,y=glfw.get_cursor_pos(window)
        print(f"Mouse clicked at: x={x}, y={y}")

def init():
    pygame.init()
    glfw.init()
    global np_rgb_image
    np_rgb_image=init_loader()
    # opengl window (with glfw)
    global window
    window=make_full_screen_window()
    glfw.make_context_current(window)
    glfw.set_mouse_button_callback(window, mouse_button_callback)
    # init loading the image
    zoom_level=3
    newImg=get_stitched_image(x=0, y=0, zoom_level=zoom_level, w_resolution=1920, h_resolution=1080, 
                              w_img=np_rgb_image.shape[1], h_img=np_rgb_image.shape[0])
    init_img(load_image_to_next_frame2,newImg)
    # init_img(load_image_to_next_frame,"./output.png")
    
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

    # newImg=get_stitched_image(x=400, y=50, zoom_level=3, w_resolution=1920, h_resolution=1080, 
    #                           w_img=np_rgb_image.shape[1], h_img=np_rgb_image.shape[0])
    # OpenGL window loop
    while (not glfw.window_should_close(window)) and glfw.get_key(window, glfw.KEY_ESCAPE)!=glfw.PRESS and running_event.is_set():
        # buffer clearing
        glClearColor(.2,.3,.8,1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        
        # init_img(load_image_to_next_frame2,newImg)
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