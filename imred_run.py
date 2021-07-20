#!/usr/bin/env python

"""
Image Reduction Pipeline
2019-04-23, nmosko@lowell.edu

Assumes:
-all images are from the same instrument
-SkyFlats preferred over DomeFlats
-non-mosaic ccd, no multi-extension fits file
-header contains information about trim section
-multiple filters handled in parsing of files

Dependencies:
numpy
astropy
scipy
astropy.photutils, astropy.table, astropy.io

Steps (instrument dependent):
trim all images
create master bias
bias correct flats and target frames
create master flat
flatten target frames

"""

import argparse
import os
import re
import sys

import imred_config
import imred_bias
import imred_flat

import numpy as np

from astropy.io import ascii, fits
from astropy.table import Table, unique, vstack

# possible instrument header keywords
instrument_keywords = ['LCAMMOD', 'INSTRUME']

# table for storing summary data
t = Table(names=('im','ut','airmass','imtype','target',
                 'filter','exptime','binning','image_size'),
          dtype=(object,object,float,object,object,object,float,object,object))

def imred_run(filenames):
    """ Wrapper function for running reduction pipeline
    """
    
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

    # read in header data and populate summary table
    for file in filenames:
        hdulist = fits.open(file)
        if len(hdulist) == 1:
            hdr = hdulist[0].header
            dat = hdulist[0].data
        elif len(hdulist) == 2:
            hdr = hdulist[0].header + hdulist[1].header
            dat = hdulist[1].data
        else:
            print(file+' contains more than two image extensions. Exiting!')
            sys.exit()

        imsize = dat.shape

        if type(params['binning'][0]) == int:
            bin_x = params['binning'][0]
            bin_y = params['binning'][1]
        elif '#' in params['binning'][0]:
            if '#blank' in params['binning'][0]:
                bin_x = str(hdr[params['binning'][0].split('#')[0]].split()[0])
                bin_y = str(hdr[params['binning'][1].split('#')[0]].split()[1])
        else:
            bin_x = str(hdr[params['binning'][0]])
            bin_y = str(hdr[params['binning'][1]])
        
        t.add_row([file,hdr[params['time']],hdr[params['airmass']],
                   hdr[params['frame_type']],hdr[params['object']],
                   hdr[params['filter']],hdr[params['exptime']],
                   str(bin_x)+'x'+str(bin_y),
                   str(imsize)])

    # output summary table
    if not os.path.isfile('./data_summary.txt'):
        ascii.write(t,'data_summary.txt',format='fixed_width_two_line')
    
    # check that binning is uniform across images
    if len(t.group_by('binning').groups) != 1:
        print('Not all images are same binning. See data_summary.txt. Exiting...')
        exit()

    # check that all images are same size
    if len(t.group_by('image_size').groups) != 1:
        print('Not all images are the same size. See data_summary.txt. Exiting...')
        exit()

    # image types in this data set
    image_types = unique(t,keys='imtype')['imtype']

    # create processed images directory
    if not os.path.exists('proc'):
        os.mkdir('proc')


    # trim images
    if params['trim']:
        print('Trimming images...')
        for file in t['im']:
            
            # open image and retrieve trim parameters
            hdulist = fits.open(file)
            if len(hdulist) == 1:
                hdr = hdulist[0].header
                data = hdulist[0].data
            elif len(hdulist) == 2:
                hdr = hdulist[0].header + hdulist[1].header
                data = hdulist[1].data

            trimsec = hdr[params['data_region']]
            xmin,xmax,ymin,ymax = [int(s) for s in re.findall(r'\d+',trimsec)]
            
            # write new trimmed image
            data = data[ymin:ymax,xmin:xmax]
            if len(hdulist) == 1:
                hdulist[0].data = data
            elif len(hdulist) == 2:
                hdulist[1].data = data
            a = file.split('.')
            out_file = '.'.join(a[:-1])+'_trim.'+a[-1]
            if not os.path.isfile('./proc/'+out_file):
                hdulist.writeto('./proc/'+out_file, overwrite = True)
            else:
                print('   '+out_file+' already exists.')
            hdulist.close()

            # rename files in Table that have been trimmed
            t['im'][np.where(t['im'] == file)] = './proc/'+file.replace('.fits','_trim.fits')

        print('Trimming done!')
        print('')


    # bias correct
    if params['bias_correct']:
        print('Bias correcting data...')
        
        # retrieve bias, flat and object image names
        if params['bias'] in image_types:
            bias_frames = t['im'][t['imtype']==params['bias']]
        else:
            print('No bias frames present. Exiting...')
            exit()

        if params['skyflat'] in image_types:
            flat_frames = t['im'][t['imtype']==params['skyflat']]
        elif params['domeflat']  in image_types:
            flat_frames = t['im'][t['imtype']==params['domeflat']]
        else:
            print('No flat frames present. Exiting...')
            exit()

        if params['object'] in image_types:
            obj_frames = t['im'][t['imtype']==params['object']]
        else:
            print('No object frames present. Exiting...')
            exit()

        # check whether master bias exists
        if not os.path.isfile('./proc/master_bias.fits'):
            print('   Creating master bias frame...')
            imred_bias.master_bias(bias_frames,params)

        # bias correct
        print('   Bias correcting flat fields...')
        imred_bias.bias_correct(flat_frames)
        print('   Bias correcting object frames...')
        imred_bias.bias_correct(obj_frames)

        # rename flat and object images as those now bias corrected
        if params['trim']:
            for file in flat_frames:
                t['im'][np.where(t['im'] == file)] = file.replace('.fits','_bias.fits')
            for file in obj_frames:
                t['im'][np.where(t['im'] == file)] = file.replace('.fits','_bias.fits')
        else:
            for file in flat_frames:
                t['im'][np.where(t['im'] == file)] = './proc/'+file.replace('.fits','_bias.fits')
            for file in obj_frames:
                t['im'][np.where(t['im'] == file)] = './proc/'+file.replace('.fits','_bias.fits')

        print('Bias correction done!')
        print('')

    # flat field
    if params['flat_correct']:
        print('Flat fielding data...')
        # need to go through each filter separately
        uniq_filt = unique(t,keys='filter')['filter']
        for filt in uniq_filt:
            
            # list of all flat fields in single filter
            if params['skyflat'] in image_types:
                flats = t['im'][(t['imtype']==params['skyflat']) & (t['filter']==filt)]
            elif params['domeflat']  in image_types:
                flats = t['im'][(t['imtype']==params['domeflat']) & (t['filter']==filt)]
            else:
                print('   No flat frames present. Exiting...')
                exit()

            # create master flat
            print('   Creating master normalized flat for filter '+filt)
            if len(flats) != 0:
                imred_flat.master_flat(flats,filt.replace(' ',''),params)
            else:
                print('   No '+filt+' band flat frames present.')
                continue

            # list of all object exposures in single filter
            objs = t['im'][(t['imtype']==params['object']) & (t['filter']==filt)]

            # flatten images
            print('   Flattening all '+filt+' band images.')
            imred_flat.flat_correct(objs,filt.replace(' ',''))
        
        print('Flat fielding done!')



if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Process imaging data.')
    parser.add_argument('images', help='images to process',
                        nargs='+')
    args = parser.parse_args()
    filenames = sorted(args.images)

    imred_run(filenames)
