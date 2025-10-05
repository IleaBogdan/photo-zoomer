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
import math

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

def get_preprocessed_image(chunk_x: int, chunk_y: int, zoom: int):
    path = f'save/test_compression_level_{zoom}_x_{int(chunk_x)}_y_{int(chunk_y)}.jpg'
    return Image.open(path)

def get_stitched_image(x: int, y: int, zoom_level: int, w_img: int, h_img: int):
    # Output image size
    w_resolution, h_resolution = 1920, 1080

    # Number of splits per axis at this zoom level
    splits = zoom_level if zoom_level > 1 else 1
    chunk_w = w_img // splits
    chunk_h = h_img // splits

    # Find which chunks are needed to cover the requested area
    x_start = max(0, x - w_resolution // 2)
    y_start = max(0, y - h_resolution // 2)
    x_end = min(w_img, x_start + w_resolution)
    y_end = min(h_img, y_start + h_resolution)

    # Which chunk indices do we need?
    chunk_x_start = x_start // chunk_w
    chunk_y_start = y_start // chunk_h
    chunk_x_end = math.ceil(x_end / chunk_w)
    chunk_y_end = math.ceil(y_end / chunk_h)

    # Create a blank canvas to stitch chunks
    stitched_w = (chunk_x_end - chunk_x_start) * chunk_w
    stitched_h = (chunk_y_end - chunk_y_start) * chunk_h
    stitched_img = Image.new("RGB", (stitched_w, stitched_h))

    # Paste each chunk in the correct position
    for cx in range(chunk_x_start, chunk_x_end):
        for cy in range(chunk_y_start, chunk_y_end):
            try:
                chunk_img = get_preprocessed_image(cx * chunk_w, cy * chunk_h, splits)
                stitched_img.paste(chunk_img, ((cx - chunk_x_start) * chunk_w, (cy - chunk_y_start) * chunk_h))
            except FileNotFoundError:
                # If chunk is missing, fill with black
                blank = Image.new("RGB", (chunk_w, chunk_h), (0, 0, 0))
                stitched_img.paste(blank, ((cx - chunk_x_start) * chunk_w, (cy - chunk_y_start) * chunk_h))

    # Crop to the requested area
    crop_x = x_start - chunk_x_start * chunk_w
    crop_y = y_start - chunk_y_start * chunk_h
    cropped_img = stitched_img.crop((crop_x, crop_y, crop_x + w_resolution, crop_y + h_resolution))

    # Resize to 1920x1080 if needed
    if cropped_img.size != (w_resolution, h_resolution):
        cropped_img = cropped_img.resize((w_resolution, h_resolution))

    return cropped_img