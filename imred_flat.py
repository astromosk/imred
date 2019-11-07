#!/usr/bin/env python

"""
Image Reduction Pipeline Flat Field Correction
2019-04-23, nmosko@lowell.edu
"""

import os
import argparse

import numpy as np

from astropy.io import fits
from astropy.table import Table
from scipy import stats
from photutils import ModeEstimatorBackground

# initialize background class
bkg=ModeEstimatorBackground()

def master_flat(flat_frames,filter,params):
    """ Build master flat field
    """

    # read flat frames into numpy arrays
    all_frames = []
    for file in flat_frames:
        hdulist = fits.open(file)
        if len(hdulist) == 1:
            data = hdulist[0].data
        elif len(hdulist) == 2:
            data = hdulist[1].data

        # exclude file if counts are more that instrument threshold
        if data.mean() < params['max_counts']:
            # scale image by median (faster than mode)
            #all_frames.append(data/np.median(data))
            all_frames.append(data/bkg(data))
        else:
            print('   Image '+file+' excluded from master flat.')
            print('      Mean counts of'+str(data.mean())+'in non-linear regime.')
            
    # take median across all flat frames and normalize
    master = np.median(all_frames,axis=0)
    master_norm = master / np.median(master)
    
    # write master bias frame
    if len(hdulist) == 1:
        hdulist[0].data = master_norm
    elif len(hdulist) == 2:
        hdulist[1].data = master_norm
    hdulist.writeto('./proc/master_flat_'+filter+'.fits', overwrite = True)
    hdulist.close()


def flat_correct(obj_frames,filter):
    """ Flat field correct images
    """

    hdu_flat = fits.open('./proc/master_flat_'+filter+'.fits')
    if len(hdu_flat) == 1:
        flat = hdu_flat[0].data
    elif len(hdu_flat) == 2:
        flat = hdu_flat[1].data
    flat[flat == 0] = 0.01
    
    for file in obj_frames:
        # open and flat correct frames
        hdulist = fits.open(file)
        if len(hdulist) == 1:
            data = hdulist[0].data
            data_flat_cor = data / flat
            hdulist[0].data = data_flat_cor
        elif len(hdulist) == 2:
            data = hdulist[1].data
            data_flat_cor = data / flat
            hdulist[1].data = data_flat_cor
        
        # write flat corrected image to new file
        a = file.split('.')
        if 'proc/' in file:
            out_file = '.'.join(a[:-1])+'_flat.'+a[-1]
        else:
            temp = '.'.join(a[:-1])+'_flat.'+a[-1]
            out_file = './proc/'+temp
        if not os.path.isfile(out_file):
            hdulist.writeto(out_file, overwrite = True)
        else:
            print('   '+out_file+' already exists.')
        hdulist.close()

#if __name__ == '__main__':
    
#    parser = argparse.ArgumentParser(description='Process imaging data.')
#    parser.add_argument('obj_frames', help='images to bias correct',
#                        nargs='+')
#    parser.add_argument('bias_frames', help='bias frames', nargs='+')
#    args = parser.parse_args()
#    obj_frames = sorted(args.obj_frames)
#    bias_frames = sorted(args.bias_frames)
    
#   if not os.path.isfile('./master_flat.fits'):
#     print('No master flat file in current directory. Exiting...')
#    exit()
#    else:
#        flat_correct(obj_frames
