import cupy as cp
import numpy as np
from PIL import Image
import cv2

# Load image with PIL
img=Image.open('output.png').convert('RGB')
img_np=np.array(img)

# Transfer image to GPU
img_gpu=cp.asarray(img_np)

# Transfer back to CPU for display (OpenCV can't display from GPU)
img_cpu=cp.asnumpy(img_gpu)

# Display fullscreen using OpenCV
cv2.namedWindow('Fullscreen', cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty('Fullscreen', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cv2.imshow('Fullscreen', img_cpu)
cv2.waitKey(0)
cv2.destroyAllWindows()