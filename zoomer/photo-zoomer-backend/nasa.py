import os
from astropy.io import fits
from astropy.visualization import (ImageNormalize, MinMaxInterval, ZScaleInterval, LinearStretch)
from astropy.visualization import make_lupton_rgb
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt
# from google.colab.patches import cv2_imshow
import numpy as np
import cv2
import cupy as cp
from skimage.color import rgb2hsv

b_channel_hdul = fits.open('assets/h_m51_b_s05_drz_sci.fits')
h_channel_hdul = fits.open('assets/h_m51_h_s05_drz_sci.fits')
v_channel_hdul = fits.open('assets/h_m51_v_s05_drz_sci.fits')

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

def select_zone(np_image: np.array, x: int, y: int, zoom_level: int, w_resolution: int = 1920, h_resolution: int = 1080):
    h_img, w_img = np_image.shape[:2]

    section_height = int(h_img // zoom_level)
    section_width = int(w_img // zoom_level)

    if section_height <= 0 or section_width <= 0:
        return None

    y_end = min(y + section_height, h_img)
    x_end = min(x + section_width, w_img)

    if y_end > y and x_end > x:
        sectioned_array = np_image[y:y_end, x:x_end, :]
    else:
        return None

    return sectioned_array, w_resolution, h_resolution


def compress_zone(np_image_section: np.array, w_resolution: int, h_resolution: int, quality: int = 95):
    if np_image_section is None or np_image_section.size == 0:
        return b''

    if np.issubdtype(np_image_section.dtype, np.floating):
        np_image_section = np.clip(np_image_section, 0, 1) * 255.0
        np_image_section = np_image_section.astype(np.uint8)

    if np_image_section.shape[:2] == (1, 1):
        pass

    try:
        jpg_img = Image.fromarray(np_image_section)
        jpg_img = jpg_img.resize((w_resolution, h_resolution))
        buf = BytesIO()
        jpg_img.save(buf, format="JPEG", quality=quality)
        return buf.getvalue()
    except Exception as e:
        print(f"Compression failed: {e}")
        return b''

def get_zone_image(np_image: np.array, x: int, y: int, zoom_level: int, w_resolution: int = 1920, h_resolution: int = 1080):
  selected = select_zone(np_image=np_image,
                            x=x,
                            y=y,
                            zoom_level=zoom_level,
                            w_resolution=w_resolution,
                            h_resolution=h_resolution)
  if selected is None:
      return b''
  sectioned_array, wr, hr = selected
  return compress_zone(sectioned_array, wr, hr)

def save_compression_levels(np_image: np.array, filename: str, exit_w_dim: int = 1920, exit_h_dim: int = 1080):
    w_img = np_image.shape[1]
    h_img = np_image.shape[0]

    max_zoom = int(max(w_img / exit_w_dim, h_img / exit_h_dim)) + 1
    for zoom_level in range(1, max_zoom+1):
        x = 0
        x_c = 0
        step_x = max(1, w_img / zoom_level)
        step_y = max(1, h_img / zoom_level)

        while x < w_img:
            y = 0
            y_c = 0
            x = int(step_x * x_c)
            while y < h_img:
                y = int(step_y * y_c)
                zone_data = get_zone_image(np_image=np_image, x=x, y=y, w_resolution=exit_w_dim, h_resolution=exit_h_dim, zoom_level=zoom_level)
                if zone_data:
                  output_filename = f'{filename}_compression_level_{zoom_level}_x_{x}_y_{y}.jpg'
                  with open(output_filename, 'wb') as f:
                      f.write(get_zone_image(np_image=np_image, x=x, y=y, w_resolution=exit_w_dim, h_resolution=exit_h_dim, zoom_level = zoom_level))
                  print(f"Saved: {output_filename}, also y_step {step_y}, also x_step {step_x}")
                y_c += 1
            x_c += 1

np_rgb_image = rgb_image.get()
save_compression_levels(np_rgb_image, "test")