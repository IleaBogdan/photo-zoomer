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
from pynput import mouse

running_event=threading.Event()
running_event.set()

scroll_counter=0
def on_scroll(x, y, dx, dy):
    global scroll_counter
    
    if dy > 0:
        # Scrolling up/forward
        scroll_counter += 0.5
    elif dy < 0:
        # Scrolling down/backward
        scroll_counter -= 0.5
    scroll_counter=max(0,scroll_counter)
    print(scroll_counter)


def make_window(width,height): # returning a window with screen size
    monitor=glfw.get_primary_monitor()
    video_mode=glfw.get_video_mode(monitor)
    window=glfw.create_window(
        width,
        height,
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

def remove_black_borders(image):
    """
    Remove black borders from image and return the content area
    """
    if isinstance(image, Image.Image):
        # Convert PIL Image to numpy array for processing
        img_array = np.array(image)
    else:
        img_array = image
    
    # Convert to grayscale to find non-black regions
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    # Find non-black pixels
    non_black = gray > 10  # Threshold to detect non-black pixels
    
    # Find bounding box of non-black region
    rows = np.any(non_black, axis=1)
    cols = np.any(non_black, axis=0)
    
    if not np.any(rows) or not np.any(cols):
        # Entire image is black, return original
        return Image.fromarray(img_array) if not isinstance(image, Image.Image) else image
    
    y_min, y_max = np.where(rows)[0][[0, -1]]
    x_min, x_max = np.where(cols)[0][[0, -1]]
    
    # Crop to content area
    content_crop = img_array[y_min:y_max+1, x_min:x_max+1]
    
    # Convert back to PIL
    content_pil = Image.fromarray(content_crop)
    
    return content_pil

def crop_and_resize_image(image, zoom_level, target_w, target_h):
    """
    Crop and resize with integer zoom levels
    """
    # First remove black borders
    image_no_borders = remove_black_borders(image)
    
    w, h = image_no_borders.size
    target_aspect = target_w / target_h
    
    # With integer zoom levels, we divide the content area by zoom_level
    # Higher zoom_level = smaller crop area = more zoomed in
    crop_w = w // zoom_level
    crop_h = h // zoom_level
    
    # Ensure minimum size
    crop_w = max(crop_w, 1)
    crop_h = max(crop_h, 1)
    
    # Adjust crop to maintain target aspect ratio
    if crop_w / crop_h > target_aspect:
        # Too wide - adjust height
        crop_h = int(crop_w / target_aspect)
    else:
        # Too tall - adjust width
        crop_w = int(crop_h * target_aspect)
    
    # Ensure we don't crop more than available
    crop_w = min(crop_w, w)
    crop_h = min(crop_h, h)
    
    # Center the crop
    left = (w - crop_w) // 2
    top = (h - crop_h) // 2
    right = left + crop_w
    bottom = top + crop_h
    
    # Crop and resize
    cropped = image_no_borders.crop((left, top, right, bottom))
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
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
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
    window=make_window(1300,800)
    glfw.make_context_current(window)
    glfw.set_mouse_button_callback(window, mouse_button_callback)
    # init loading the image
    zoom_level=1
    newImg=get_stitched_image(x=0, y=0, zoom_level=zoom_level, w_resolution=1920, h_resolution=1080, 
                              w_img=np_rgb_image.shape[1], h_img=np_rgb_image.shape[0])
    init_img(load_image_to_next_frame2,newImg)
    
    # # text_window 
    # global text_window
    # text_window=SimpleTextWindow(width=600, height=100, x=300, y=200)
    # clock for frame rate limit
    global clock
    clock=pygame.time.Clock()

    # mouse scroll
    listener = mouse.Listener(on_scroll=on_scroll)
    listener.start()

# def run_text_window(): # text_window loop
#     while running_event.is_set():
#         # pulling text and displaying the text
#         if not text_window.handle_events():
#             running_event.clear() # updating the inter thread variable to stop both threads
#         text_window.update_cursor()
#         text_window.draw()
#         pygame.display.flip()
#         clock.tick(60)

def loop():
    # # Start Pygame text window in a separate thread
    # text_thread=threading.Thread(target=run_text_window,daemon=True)
    # text_thread.start()

    # OpenGL window loop
    while (not glfw.window_should_close(window)) and glfw.get_key(window, glfw.KEY_ESCAPE)!=glfw.PRESS and running_event.is_set():
        # buffer clearing
        glClearColor(.2,.3,.8,1.0)
        glClear(GL_COLOR_BUFFER_BIT)

        zoom_level=int(scroll_counter)+1
        newImg=get_stitched_image(x=0, y=0, zoom_level=zoom_level, w_resolution=1920, h_resolution=1080, 
                              w_img=np_rgb_image.shape[1], h_img=np_rgb_image.shape[0])
        init_img(load_image_to_next_frame2,newImg)
        
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
    listener.stop()

def main(): # les mainos lupos
    init();loop();kill()
if __name__=="__main__":
    main()