#!/usr/bin/env python

"""
Rename NOAO archive images based on original file name
2019-10-10, nmosko@lowell.edu
"""

import glob
import ntpath
import os

from astropy.io import fits

# retrieve current fits file names
filenames = glob.glob('*.fits')

for file in filenames:

    hdu = fits.open(file)
 
    original_name = ntpath.basename(hdu[0].header['DTACQNAM'])
     
    hdu.close
    
    os.rename(file,original_name)

    
