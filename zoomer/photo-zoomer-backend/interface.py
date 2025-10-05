from PIL import Image 
from astropy.io import fits
import numpy as np

def get_preprocessed_image(x: int, y: int, zoom: int):
  img = Image.open(f'assets/test_compression_level_{zoom}_x_{int(x)}_y_{int(y)}.jpg')
  return img


def get_stitched_image(x: int, y: int, zoom_level: float, w_resolution: int, h_resolution: int, w_img: int, h_img: int):
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

  img_tl = get_preprocessed_image(x_tl, y_tl, int(zoom_level))
  img_tr = get_preprocessed_image(x_tr, y_tr, int(zoom_level))
  img_bl = get_preprocessed_image(x_bl, y_bl, int(zoom_level))
  img_br = get_preprocessed_image(x_br, y_br, int(zoom_level))

  # Stitch using tile pixel dimensions (each tile is w_resolution x h_resolution)
  stitched_img = Image.new("RGB", (int(w_resolution) * 2, int(h_resolution) * 2))

  stitched_img.paste(img_tl, (0, 0))
  stitched_img.paste(img_tr, (w_resolution, 0))
  stitched_img.paste(img_bl, (0, h_resolution))
  stitched_img.paste(img_br, (w_resolution, h_resolution))

  # Compute offsets in tile pixel space
  scale_x = w_resolution / w_unit
  scale_y = h_resolution / h_unit
  offset_px_x = int((x - x_tl) * scale_x)
  offset_px_y = int((y - y_tl) * scale_y)

  # Crop exactly one tile-sized viewport
  cropped_img = stitched_img.crop((offset_px_x, offset_px_y, offset_px_x + w_resolution, offset_px_y + h_resolution))

  return cropped_img

# Removed import-time test invocation to avoid side effects


