import numpy as np
from PIL import Image
import cv2
import cupy as cp

def loader(path):
    print(Image)
    img=Image.open(path).convert('RGB')
    img_np=np.array(img)
    return img_np

'''
# --- GPU processing section start ---
# You can add your GPU (CuPy) processing code below.
# Example:
img_gpu = cp.asarray(img_np)
# ...your GPU processing here...
img_np = cp.asnumpy(img_gpu)  # Convert back to NumPy for display
# --- GPU processing section end ---
'''

def main():
    path='./output.png'
    img_np=loader(path)
    cv2.namedWindow('Fullscreen',cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty('Fullscreen',cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
    cv2.imshow('Fullscreen',img_np)
    while True:
        key=cv2.waitKey(1)
        if key==27:  # ESC key code
            break
    cv2.destroyAllWindows()

if __name__=="__main__":
    main()