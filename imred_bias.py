#!/usr/bin/env python

"""
Image Reduction Pipeline Bias Correction
2019-04-23, nmosko@lowell.edu
"""

import os
import argparse

import numpy as np

from astropy.io import fits
from astropy.table import Table

def master_bias(bias_frames,params):
    """ Build master bias frame
    """

    # read bias frames into numpy arrays
    all_frames = []
    for file in bias_frames:
        hdulist = fits.open(file)
        if len(hdulist) == 1:
            data = hdulist[0].data
        elif len(hdulist) == 2:
            data = hdulist[1].data

        # exclude file if bias level is more that 20% away from expected
        min_counts = 0.8 * params['bias_counts']
        max_counts = 1.2 * params['bias_counts']
        if min_counts <= data.mean() <= max_counts:
            all_frames.append(data)
        else:
            print('   Image '+file+' excluded from master bias.')
            if data.mean() < min_counts:
                    print('      Counts too low')
            else:
                    print('      Counts too high')
            
    # take median across all bias frames
    master = np.median(all_frames,axis=0)

    # write master bias frame
    if len(hdulist) == 1:
        hdulist[0].data = master
    elif len(hdulist) == 2:
        hdulist[1].data = master
    hdulist.writeto('./proc/master_bias.fits', overwrite = True)
    hdulist.close()


def bias_correct(obj_frames):
    """ Bias correct input frames
    """

    hdu_bias = fits.open('./proc/master_bias.fits')
    if len(hdu_bias) == 1:
        bias = hdu_bias[0].data
    elif len(hdu_bias) == 2:
        bias = hdu_bias[1].data

    for file in obj_frames:

        print('      Image '+file,end='\r',flush=True)
        if file == obj_frames[-1]:
            print('      done'.ljust(50,' '),end='\n',flush=True)

        # open and bias correct frame
        hdulist = fits.open(file)
        if len(hdulist) == 1:
            data = hdulist[0].data
            data_bias_cor = data - bias
            hdulist[0].data = data_bias_cor
        elif len(hdulist) == 2:
            data = hdulist[1].data
            data_bias_cor = data - bias
            hdulist[1].data = data_bias_cor
        
        # write bias corrected image to new file
        a = file.split('.')
        if 'proc/' in file:
            out_file = '.'.join(a[:-1])+'_bias.'+a[-1]
        else:
            temp = '.'.join(a[:-1])+'_bias.'+a[-1]
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
#    args = parser.parse_args()
#    obj_frames = sorted(args.obj_frames)
    
#    if not os.path.isfile('./master_bias.fits'):
#        print('No master_bias.fits file in current directory. Exiting...')
#        exit()
#    else:
#        bias_correct(obj_frames)
