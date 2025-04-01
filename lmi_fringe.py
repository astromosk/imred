#!/usr/bin/env python

"""
Image Reduction Pipeline Fringe Correction for LMI binning 3x3
2019-10-19, nmosko@lowell.edu
"""

import os
import argparse

import numpy as np

from astropy.io import fits
from astropy.table import Table
from scipy import stats
from photutils.background import ModeEstimatorBackground

def imred_fringe(filenames):

    fringe_frame = '/Users/nmosko/code/imred/fringe_med_cr_norm.fits'

    for file in filenames:
        hdu1 = fits.open(file,'update')
        hdu_fringe = fits.open(fringe_frame)
    
        scale = np.median(hdu1[0].data[3:2052,14:2049])

        hdu_fringe[0].data = hdu_fringe[0].data * scale

        hdu1[0].data = hdu1[0].data - hdu_fringe[0].data + scale

        hdu1[0].header.set('fringcor','True','Fringe frame correction applied (boolean)')
        
        hdu_fringe.close()
        hdu1.close()

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Process imaging data.')
    parser.add_argument('images', help='images to process',
                        nargs='+')
    args = parser.parse_args()
    filenames = sorted(args.images)
                        
    imred_fringe(filenames)
