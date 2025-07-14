#!/usr/bin/env python

"""
Prepare PJ1m_Moravian image headers for processing:
-Add UT time to header
-Remove underscores from OBJECT names
2025-06-09, nmosko@lowell.edu
"""

import glob
import ntpath
import os

from astropy.io import fits

# retrieve current fits file names
filenames = glob.glob('*.fits')

for file in filenames:

    hdu = fits.open(file,mode='update')
    hdr = hdu[0].header
 
    # retrieve date obs keyword
    date_obs = hdr['DATE-OBS']
     
    # extract time from date obs
    time = date_obs.split('T')[1]
    
    # add UT keyword to header
    hdr['UT'] = time
    
    # remove underscores from OBJECT keyword
    if 'OBJECT' in hdu[0].header:
        hdr['OBJECT'] = hdr['OBJECT'].replace('_',' ')
    else:
        hdr['OBJECT'] = hdr['FRAME']
     
    hdu.close()
    
