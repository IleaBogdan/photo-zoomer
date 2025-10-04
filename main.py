# %%
import astropy
from astropy.visualization import (ImageNormalize, MinMaxInterval, ZScaleInterval, LinearStretch)
from astropy.visualization import make_lupton_rgb  # Optional for color
import matplotlib.pyplot as plt
import numpy as np
hdul = astropy.io.fits.open('assets/h_m51_b_s05_drz_sci.fits')

# %%
image_data = hdul[0].data
image_data

# %%
np_img = np.array(image_data)
np_img.max()

# %%
cropped_np_img = 

# %%
norm = ImageNormalize(np_img, interval=ZScaleInterval(), stretch=LinearStretch())
plt.imshow(np_img, cmap='gray', origin='lower', norm=norm)
plt.colorbar()
plt.title('FITS Image (Z-Scale)')
plt.show()

# %%



