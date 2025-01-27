#!/usr/bin/env python

"""
Convert a 64 bit fits file to 32 bit
2025-01-24, nmosko@lowell.edu
"""

import glob
import ntpath
import os

from astropy.io import fits

# retrieve current fits file names
filenames = glob.glob('*.fits')

for file in filenames:

    with fits.open(file) as hdu:
    
        # Get the image data and header from the primary HDU
        data = hdu[0].data
        header = hdu[0].header

        # Convert the data to 32-bit float
        data = data.astype('float32')

        # Create a new HDU with the 32-bit data
        new_hdu = fits.PrimaryHDU(data,header=header)

        # Save the new FITS file
        new_name = file.replace('.fits','_32b.fits')
        new_hdu.writeto(new_name)

