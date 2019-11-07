#!/usr/bin/env python

"""
Image Reduction Pipeline Configuation Script
2019-04-23, nmosko@lowell.edu
"""

import sys

# telescope/instrument configurations
implemented_instruments = ['hall_nasa42','DCT_lmi','SOAR 4.1m_Goodman Spectro','2.1m Otto Struve_','31-in_NASAcam']


# Lowell 31", NASAcam
lowell31in_nasacam = {
    
    # instrument-specific FITS header keywords
    'time': 'UT',  # UT time at start of exposure
    'airmass': 'AIRMASS',   # airmass of observation
    'binning': ('CDELT1', 'CDELT2'),    # x and y bin factors
    'target_name': 'OBJECT',  # target name keyword
    'filter': 'FILTER2',  # filter keyword
    'exptime': 'EXPTIME',  # exposure time keyword (s)
    'data_region': 'TRIMSEC',   # trim region keyword
    
    'frame_type': 'IMAGETYP',   # keyword for type of image
    'bias': 'bias',  # bias frame_type
    'skyflat': 'flat',  # twilight flat frame_type
    'domeflat': 'flat',  # dome flat frame_type
    'object': 'object',  # object frame_type
    
    # instrument specific properties
    'bias_counts': 1540.,    # typical bias frame counts
    'max_counts': 40000.,   # max counts before non-linear
    
    # instrument specific processing steps
    'bias_correct' : True,
    'flat_correct' : True,
    'trim' : False
}


# McDonald 2.1m, CQUEAN
mcdonald2m_cquean = {
    
    # instrument-specific FITS header keywords
    'time': 'TIME-OBS',  # UT time at start of exposure
    'airmass': 'AIRMASS',   # airmass of observation
    'binning': (1, 1),    # x and y bin factors
    'target_name': 'OBJECT',  # target name keyword
    'filter': 'FILTER',  # filter keyword
    'exptime': 'EXPTIME',  # exposure time keyword (s)
    'data_region': 'TRIMSEC',   # trim region keyword
    
    'frame_type': 'OBSTYPE',   # keyword for type of image
    'bias': 'BIAS',  # bias frame_type
    'skyflat': 'SKYFLAT',  # twilight flat frame_type
    'domeflat': 'DOMEFLAT',  # dome flat frame_type
    'object': 'OBJECT',  # object frame_type
    
    # instrument specific properties
    'bias_counts': 4400,    # typical bias frame counts
    'max_counts': 40000.,   # max counts before non-linear
    
    # instrument specific processing steps
    'bias_correct' : True,
    'flat_correct' : True,
    'trim' : False
}

# 42", NASA42
hall_nasa42 = {

    # instrument-specific FITS header keywords
    'time': 'UTC-OBS',  # UT time at start of exposure
    'airmass': 'AIRMASS',   # airmass of observation
    'binning': ('ADELX_01', 'ADELY_01'),    # x and y bin factors
    'target_name': 'OBJECT',  # target name keyword
    'filter': 'FILTNAME',  # filter keyword
    'exptime': 'EXPTIME',  # exposure time keyword (s)
    'data_region': 'TRIMSEC',   # trim region keyword

    'frame_type': 'IMAGETYP',   # keyword for type of image
    'bias': 'BIAS',  # bias frame_type
    'skyflat': 'SKYFLAT',  # twilight flat frame_type
    'domeflat': 'DOMEFLAT',  # dome flat frame_type
    'object': 'OBJECT',  # object frame_type

    # instrument specific properties
    'bias_counts': 1625.,    # typical bias frame counts
    'max_counts': 40000.,   # max counts before non-linear

    # instrument specific processing steps
    'bias_correct' : True,
    'flat_correct' : True,
    'trim' : True
}

# DCT, LMI
dct_lmi = {
    
    # instrument-specific FITS header keywords
    'time': 'UT',  # UT time at start of exposure
    'airmass': 'AIRMASS',   # airmass of observation
    'binning': ('CCDSUM#blank0', 'CCDSUM#blank1'),    # x and y bin factors
    'target_name': 'OBJECT',  # target name keyword
    'filter': 'FILTER1',  # filter keyword
    'exptime': 'EXPTIME',  # exposure time keyword (s)
    'data_region': 'TRIM01',   # trim region keyword
    
    'frame_type': 'IMAGETYP',   # keyword for type of image
    'bias': 'BIAS',  # bias frame_type
    'skyflat': 'SKY FLAT',  # twilight flat frame_type
    'domeflat': 'DOME FLAT',  # dome flat frame_type
    'object': 'OBJECT',  # object frame_type
    
    # instrument specific properties
    'bias_counts': 1010,    # typical bias frame counts
    'max_counts': 40000.,   # max counts before non-linear
    
    # instrument specific processing steps
    'bias_correct' : True,
    'flat_correct' : True,
    'trim' : True
}

# SOAR, Goodman
soar_goodman = {
    
    # instrument-specific FITS header keywords
    'time': 'UT',  # UT time at start of exposure
    'airmass': 'AIRMASS',   # airmass of observation
    'binning': ('CCDSUM#blank0', 'CCDSUM#blank1'),    # x and y bin factors
    'target_name': 'OBJECT',  # target name keyword
    'filter': 'FILTER',  # filter keyword
    'exptime': 'EXPTIME',  # exposure time keyword (s)
    'data_region': 'TRIMSEC',   # trim region keyword
    
    'frame_type': 'OBSTYPE',   # keyword for type of image
    'bias': 'BIAS',  # bias frame_type
    'skyflat': 'FLAT',  # twilight flat frame_type
    'domeflat': 'FLAT',  # dome flat frame_type
    'object': 'OBJECT',  # object frame_type
    
    # instrument specific properties
    'bias_counts': 550.,    # typical bias frame counts
    'max_counts': 52000.,   # max counts before non-linear
    
    # instrument specific processing steps
    'bias_correct' : True,
    'flat_correct' : True,
    'trim' : False
}


# translate telescope+instrument keywords into parameter set defined here
params = {
    'hall_nasa42':                  hall_nasa42,
    'DCT_lmi':                      dct_lmi,
    '2.1m Otto Struve_':            mcdonald2m_cquean,
    'SOAR 4.1m_Goodman Spectro':    soar_goodman,
    '31-in_NASAcam':                lowell31in_nasacam
}

def parameters(tel_inst):
    """ Retrieve telescope specific parameter set
    """

    if tel_inst not in implemented_instruments:
        print(tel_inst+' not implemented. Exiting...')
        exit()
    
    tel_param = params[tel_inst]
    
    return tel_param

if __name__ == '__main__':
    
    tel_name = sys.argv[1]
    inst_name = sys.argv[2]

    tel_inst = tel_name+'_'+inst_name

    parameters(tel_inst)
