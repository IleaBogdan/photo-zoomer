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
    zoom_level=int(zoom_level)
    if zoom_level==1:
        img=get_preprocessed_image(x, y, zoom_level)
        img=img.resize((w_resolution, h_resolution))
        return img

    zoom_level=zoom_level if zoom_level!=0 else 1
    w_unit = (w_img / zoom_level)
    h_unit = (h_img / zoom_level)

    x_tl = (x // w_unit) * w_unit # multiplu de w_resolution, divizor de w_img, divided by zoom_level
    y_tl = (y // h_unit) * h_unit # multiplu de w_resolution, divizor de w_img, divided by zoom_level

    x_tr = x_tl + w_unit
    y_tr = y_tl

    x_bl = x_tl
    y_bl = y_tl + h_unit

    x_br = x_tl + w_unit
    y_br = y_tl + h_unit

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

    cropped_img = stitched_img.crop((x_offset, y_offset, x_offset + w_unit, y_offset + h_unit))
    cropped_img = cropped_img.resize((w_resolution, h_resolution))

    return cropped_img