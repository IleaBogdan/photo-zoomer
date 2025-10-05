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
from old_loader import *
from pynput import mouse
import datetime

running_event=threading.Event()
running_event.set()

scroll_counter=1
mouse_x,mouse_y=0,0
max_b,max_h,max_v=0,0,0
def on_scroll(x, y, dx, dy):
    global scroll_counter
    global mouse_x,mouse_y

    if dy > 0:
        # Scrolling up/forward
        scroll_counter += 0.5
    elif dy < 0:
        # Scrolling down/backward
        scroll_counter -= 0.5
    scroll_counter=max(0,scroll_counter)
    mouse_x,mouse_y=x,y


def make_window(width, height):  # returning a window with screen size
    window = glfw.create_window(
        width,
        height,
        "Photo Zoomer",  # Set your window title here
        None,
        None
    )
    glfw.set_window_attrib(window, glfw.DECORATED, True)  # Show title bar
    # glfw.set_window_pos(window, 0, 0)
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

drawing = False
rect_start = None
rect_end = None
pixel_array = None  # Add this at the top, after your other globals
chuck_number=1

def mouse_button_callback(window, button, action, mods):
    global drawing, rect_start, rect_end, pixel_array, chuck_number
    if button == glfw.MOUSE_BUTTON_LEFT:
        if action == glfw.PRESS:
            x, y = glfw.get_cursor_pos(window)
            drawing = True
            rect_start = (int(x), int(y))
            rect_end = (int(x), int(y))
        elif action == glfw.RELEASE:
            drawing = False
            x, y = glfw.get_cursor_pos(window)
            rect_end = (int(x), int(y))
            # Capture pixels in marked area
            width, height = glfw.get_window_size(window)
            x0, y0 = rect_start
            x1, y1 = rect_end
            left = min(x0, x1)
            right = max(x0, x1)
            top = min(y0, y1)
            bottom = max(y0, y1)
            top_flipped = height - top
            bottom_flipped = height - bottom
            w = right - left
            h = abs(top_flipped - bottom_flipped)
            if w > 0 and h > 0:
                glPixelStorei(GL_PACK_ALIGNMENT, 1)
                pixel_data = glReadPixels(left, bottom_flipped, w, h, GL_RGB, GL_UNSIGNED_BYTE)
                arr = np.frombuffer(pixel_data, dtype=np.uint8).reshape((h, w, 3))
                pixel_array = arr.flatten().tolist()  # Flat list of all RGB values
                print("Marked area pixel array (flat RGB values):")
                # print(pixel_array)
                elements=[]
                elements.append([121.6,102.6,97.3,656.3,486.1,434,410.2])
                elements.append([58.4,53.7,51.3,1083,587.6,447.1,501.6,492.2])
                elements.append([323.3,670.8,610.4])
                elements.append([234.9,313.1,313,455.4,527])
                elements.append([69.4,88.3,108.2,136.2,162.3,206.6])
                elements.append([777.4,844.6,630,557.7,436.8])
                elements.append([95,74.2])
                elements.append([585.2,640.2,703.2,724.5,743.9])
                elements.append([589,589.6])
                elements.append([285.2,279.6])
                elements.append([396.2,394.4,669.6])
                elements.append([251.6,288.1,390.5])
                elements.append([177.5,178.7])
                elements.append([180.7,181.2,190])
                elements.append([134.7,135.7])
                elements.append([696.5,763.5,811.5,842.5,912.3])
                symbol=['H','He','Li','Be','B','C','N','O','F','Ne','Na','Mg','Al','Si','P','S','Cl','Ar']
                counter=dict({})
                with open("log.txt","a") as file:
                    file.write(f'Chunk {chuck_number}\n')
                    chuck_number+=1
                    for i in range(0,len(pixel_array)):
                        r,g,b=0,0,0
                        if i+2<len(pixel_array):
                            r=(800*pixel_array[i]/255+700)
                            g=(300*pixel_array[i+1]/255+400)
                            b=(400*pixel_array[i+2]/255)
                        i+=2
                        strg=''
                        for j in range(0,len(elements)):
                            for value in elements[j]:
                                if (value+3>r and value-3<r) or (value+3>g and value-3<g) or (value+3>b and value-3<b):
                                    if not symbol[j] in counter:
                                        counter.update({symbol[j]:0})
                                    counter[symbol[j]]+=1
                                    break
                        # if strg=="": continue
                        # if not strg in counter:
                        #     counter.update({strg:0})
                        # counter[strg]+=1
                    for key,value in counter.items():
                        file.write(key)
                        file.write(': ')
                        file.write(str(value))
                        file.write('\n')
                    file.write('\n')
            else:
                pixel_array = None

def cursor_pos_callback(window, xpos, ypos):
    global drawing, rect_end
    if drawing:
        rect_end = (int(xpos), int(ypos))

def draw_rectangle_overlay():
    if rect_start and rect_end and drawing:
        width, height = glfw.get_window_size(window)
        x0, y0 = rect_start
        x1, y1 = rect_end
        # Convert to normalized device coordinates [-1, 1]
        def norm(x, y):
            return (2 * x / width - 1, 1 - 2 * y / height)
        nx0, ny0 = norm(x0, y0)
        nx1, ny1 = norm(x1, y1)
        glColor3f(1, 0, 0)  # Red rectangle
        glLineWidth(2)
        glBegin(GL_LINE_LOOP)
        glVertex2f(nx0, ny0)
        glVertex2f(nx1, ny0)
        glVertex2f(nx1, ny1)
        glVertex2f(nx0, ny1)
        glEnd()
        glColor3f(1, 1, 1)  # Reset color

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
    glfw.set_cursor_pos_callback(window, cursor_pos_callback)
    # init loading the image
    zoom_level=1
    width,height=glfw.get_window_size(window)
    width,height=1920,1080
    newImg=get_stitched_image(x=0, y=0, zoom_level=zoom_level, w_resolution=width, h_resolution=height, 
                              w_img=np_rgb_image.shape[1], h_img=np_rgb_image.shape[0])
    init_img(load_image_to_next_frame2,newImg)

    global max_b,max_h,max_v
    with open("maximus.txt","r") as file:
        lines=file.readlines()
        max_b=float(lines[0])
        max_h=float(lines[1])
        max_v=float(lines[2])
    
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
    zoom_level=int(scroll_counter)+1
    prev_zoom=zoom_level
    while (not glfw.window_should_close(window)) and glfw.get_key(window, glfw.KEY_ESCAPE)!=glfw.PRESS and running_event.is_set():
        
        
        # buffer clearing
        glClearColor(.2,.3,.8,1.0)
        glClear(GL_COLOR_BUFFER_BIT)

        zoom_level=int(scroll_counter)+1    
        if zoom_level!=prev_zoom:
            prev_zoom=zoom_level
            width,height=glfw.get_window_size(window)
            width,height=1920,1080
            print(mouse_x,mouse_y,scroll_counter)
            newImg=get_stitched_image(x=mouse_x, y=mouse_y, zoom_level=zoom_level, w_resolution=width, h_resolution=height, 
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

        # Draw overlay rectangle if drawing
        draw_rectangle_overlay()

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