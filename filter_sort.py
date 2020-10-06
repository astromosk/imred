#!/usr/bin/env python

"""
Sort images into directories based on filter
2020-10-06, nmosko@lowell.edu
"""

import glob
import ntpath
import os

import imred_config

from astropy.io import fits

# possible instrument header keywords
instrument_keywords = ['LCAMMOD', 'INSTRUME']

# retrieve current fits file names
filenames = glob.glob('*.fits')

# telescope and instrument header keywords
hdulist = fits.open(filenames[0])
header = hdulist[0].header
telescope = header['TELESCOP']
for inst_key in instrument_keywords:
    if inst_key in header:
        instrument=header[inst_key]
        break
    else:
        instrument=''

# telescope and instrument configuration parameters
tel_inst = telescope+'_'+instrument
params = imred_config.parameters(tel_inst)

for file in filenames:

    # open file and extract filter name from header
    hdulist = fits.open(file)
    if len(hdulist) == 1:
        hdr = hdulist[0].header
    elif len(hdulist) == 2:
        hdr = hdulist[0].header + hdulist[1].header
    else:
        print(file+' contains more than two image extensions. Exiting!')
        sys.exit()
    
    filter = hdr[params['filter']]
     
    hdulist.close
    
    # create directory for filter if doesnt exist and move file
    if os.path.isdir(filter):
        os.rename(file,filter+'/'+file)
    else:
        os.mkdir(filter)
        os.rename(file,filter+'/'+file)

    
