import os
from astropy.io import fits
from astropy.visualization import (ImageNormalize, MinMaxInterval, ZScaleInterval, LinearStretch)
from astropy.visualization import make_lupton_rgb
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt
import numpy as np
import cv2
import cupy as cp

def init_loader():
    b_channel_hdul = fits.open('ass-at/h_m51_b_s05_drz_sci.fits')
    h_channel_hdul = fits.open('ass-at/h_m51_h_s05_drz_sci.fits')
    v_channel_hdul = fits.open('ass-at/h_m51_v_s05_drz_sci.fits')

    b_channel = b_channel_hdul[0].data
    h_channel = h_channel_hdul[0].data
    v_channel = v_channel_hdul[0].data

    b_channel = np.array(b_channel)
    h_channel = np.array(h_channel)
    v_channel = np.array(v_channel)
    b_channel.max()

    b_ch_normalised = ImageNormalize(b_channel, interval=ZScaleInterval(), stretch=LinearStretch())
    h_ch_normalised = ImageNormalize(h_channel, interval=ZScaleInterval(), stretch=LinearStretch())
    v_ch_normalised = ImageNormalize(v_channel, interval=ZScaleInterval(), stretch=LinearStretch())

    b_norm_gpu = cp.array(b_ch_normalised(b_channel))
    h_norm_gpu = cp.array(h_ch_normalised(h_channel))
    v_norm_gpu = cp.array(v_ch_normalised(v_channel))

    rgb_image = cp.stack([b_norm_gpu, h_norm_gpu, v_norm_gpu], axis=-1)
    intensity_image = cp.average(rgb_image, axis=-1)
    rgb_image = np.transpose(rgb_image, axes=(1, 0, 2))
    np_rgb_image = rgb_image.get()
    return np_rgb_image

def get_preprocessed_image(x: int, y: int, zoom: int):
    img = Image.open(f'save/test_compression_level_{zoom}_x_{int(x)}_y_{int(y)}.jpg')
    # print(img)
    return img

def get_stitched_image(x: int, y: int, zoom_level: float, w_resolution: int, h_resolution: int, w_img: int, h_img: int):
    print(w_resolution,h_resolution,w_img,h_img)
    print(f"--- {x} {y} ---")
    float_zoom_level = zoom_level
    zoom_level=int(zoom_level)
    zoom_level=zoom_level if zoom_level>=1 else 1
    if zoom_level==1:
        img=get_preprocessed_image(0, 0, zoom_level)
        img=img.resize((w_resolution, h_resolution))
        return img
    
    # ok so this is a shit code.
    # how we can fix it:
    # we do a simple rule of three
    # we consider 1920 (w_resolution) to be 12200 (w_img)
    # and also    1080 (h_resolution) to be 8600  (h_img)
    # and we comput the x and y coords just like that
    
    # percent of x and y
    px=100*x/w_resolution
    py=100*y/h_resolution

    # the actual x and y coords on the image
    img_x=int(w_img*px)//100
    img_y=int(h_img*py)//100
    # all we need now is to just find the 4 sections of the image that are the closer to the img_x nad img_y
    # for simplicity (this is not the best solution, but it will work better then befor),
    # we will chose the cadran that has the point A(img_x,img_y) in it (we fid the upper corner) 
    # and then we will find the edge corners and they will be the other 3 sections

    w_unit = (w_img / zoom_level)
    h_unit = (h_img / zoom_level)

    x_tl = (img_x // w_unit) * w_unit # upper cornder
    y_tl = (img_y // h_unit) * h_unit # upper cornder

    x_tr = x_tl + w_unit
    y_tr = y_tl

    x_bl = x_tl
    y_bl = y_tl + h_unit

    x_br = x_tl + w_unit
    y_br = y_tl + h_unit
    
    if x_br>=w_img:
        x_tl-=w_unit
        x_tr-=w_unit
        x_bl-=w_unit
        x_br-=w_unit
    if y_br>=h_img:
        y_tl-=h_unit
        y_tr-=h_unit
        y_bl-=h_unit
        y_br-=h_unit
    print("---",x_tl,y_tl,"---")
    print("---",x_tr,y_tr,"---")
    print("---",x_bl,y_bl,"---")
    print("---",x_br,y_br,"---")
    img_tl = get_preprocessed_image(x_tl, y_tl, zoom_level)
    img_tr = get_preprocessed_image(x_tr, y_tr, zoom_level)
    img_bl = get_preprocessed_image(x_bl, y_bl, zoom_level)
    img_br = get_preprocessed_image(x_br, y_br, zoom_level)

    stitched_img = Image.new("RGB", (int(w_unit) * 2, int(h_unit) * 2))

    stitched_img.paste(img_tl, (0, 0))
    stitched_img.paste(img_tr, (w_resolution, 0))
    stitched_img.paste(img_bl, (0, h_resolution))
    stitched_img.paste(img_br, (w_resolution, h_resolution))

    x_offset = x-x_tl
    y_offset = y-y_tl

    cropped_img = stitched_img.crop((x_offset, y_offset, x_offset + int(w_img / float_zoom_level), y_offset + int(h_img / float_zoom_level)))
    cropped_img = cropped_img.resize((w_resolution, h_resolution))

    return cropped_img

import matplotlib.pyplot as plt
import numpy as np

def test_stitched_image():
    image=init_loader()
    # Define test parameters
    x = 500  # x coordinate
    y = 300  # y coordinate
    zoom_level = 2.0  # zoom level
    w_resolution = 1920  # width resolution
    h_resolution = 1080  # height resolution
    w_img = 12200  # image width
    h_img = 8600   # image height
    
    print(f"Testing get_stitched_image with:")
    print(f"x: {x}, y: {y}, zoom: {zoom_level}")
    print(f"w_res: {w_resolution}, h_res: {h_resolution}")
    print(f"w_img: {w_img}, h_img: {h_img}")
    
    # Get the stitched image
    stitched_img = get_stitched_image(x, y, zoom_level, w_resolution, h_resolution, w_img, h_img)
    
    # Convert PIL Image to numpy array for display
    img_array = np.array(stitched_img)
    
    # Display the image
    plt.figure(figsize=(12, 8))
    plt.imshow(img_array)
    plt.axis('off')
    plt.title(f'Stitched Image (x={x}, y={y}, zoom={zoom_level})')
    plt.show()
    
    return stitched_img

if __name__=="__main__":
    test_stitched_image()