import astropy
from astropy.visualization import (
    ImageNormalize, MinMaxInterval, ZScaleInterval, LinearStretch
)
from astropy.visualization import make_lupton_rgb  # Optional for color
import matplotlib.pyplot as plt
import numpy as np

# Open FITS file
hdul = astropy.io.fits.open('assets/h_m51_b_s05_drz_sci.fits')
image_data = hdul[0].data

# Convert to numpy array
np_img = np.array(image_data)
print("Max value in image:", np_img.max())

# Example cropping (replace with actual crop coordinates)
# cropped_np_img = np_img[y1:y2, x1:x2]

# Normalize and plot
norm = ImageNormalize(np_img, interval=ZScaleInterval(), stretch=LinearStretch())
plt.imshow(np_img, cmap='gray', origin='lower', norm=norm)
plt.colorbar()
plt.title('FITS Image (Z-Scale)')
plt.show()