import numpy as np
import PIL as Image
import cv2
import cupy as cp
import glfw
from OpenGL.GL import *

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

def init():
    glfw.init()
    global window
    window=make_full_screen_window()
    glfw.make_context_current(window)
    global texture_id,img_w,img_h
    texture_id,img_w,img_h=load_image_to_next_frame('output.png')

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