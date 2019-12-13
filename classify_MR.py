import os
import json
import sys
import logging
import flywheel
import re
import string
from fnmatch import fnmatch
import pydicom
import zipfile
import pandas as pd
import pprint

import classify_dicom
import classify_CT
import classification_from_label

def classify_dicom(dcm, slice_number, unique_iop=''):
    """
    Generate a classification dict from DICOM header info.

    Classification logic is as follows:
     1. Check for custom (context) classification.
     2. Check for classification based on the acquisition label.
     3. Attempt to generate a classification based on the imaging params.

    When a classification is returned the logic cascade ends.
    """

    classification_dict = {}
    series_desc = classify_ALL.format_string(dcm.get('SeriesDescription', ''))

    # 1. Custom classification from context
    if series_desc:
        classification_dict = get_custom_classification(series_desc, '/flywheel/v0/config.json')
        if classification_dict:
            log.info('Custom classification from config: %s', classification_dict)

    # 2. Classification from SeriesDescription
    if not classification_dict and series_desc:
        classification_dict = classification_from_label.infer_classification(series_desc)
        if classification_dict:
            log.info('Inferred classification from label: %s', classification_dict)

    # 3. Classification from Imaging params
    if not classification_dict:
        classification_dict = get_param_classification(dcm, slice_number, unique_iop)

    return classification_dict


def get_param_classification(dcm, slice_number, unique_iop):
    """
    Get classification based on imaging parameters in DICOM header.
    """
    classification_dict = {}

    log.info('Attempting to deduce classification from imaging prameters...')
    tr = dcm.get('RepetitionTime')
    te = dcm.get('EchoTime')
    ti = dcm.get('InversionTime')
    sd = dcm.get('SeriesDescription')

    # Log empty parameters
    if not tr:
        log.warning('RepetitionTime unset')
    else:
        log.info('tr=%s' % str(tr))
    if not te:
        log.warning('EchoTime unset')
    else:
        log.info('te=%s' % str(te))
    if not ti:
        log.warning('InversionTime unset')
    else:
        log.info('ti=%s' % str(ti))
    if not sd:
        log.warning('SeriesDescription unset')
    else:
        log.info('sd=%s' % str(sd))
########## Changes to be made to tr range
    if (te and te < 30) and (tr and tr < 800):
        classification_dict['Measurement'] = ["T1"]
        log.info('(te and te < 30) and (tr and tr < 800) -- T1 Measurement')
    elif (te and te  > 50) and (tr and tr > 2000) and (not ti or ti == 0):
        classification_dict['Measurement'] = ["T2"]
        log.info('(te and te  > 50) and (tr and tr > 2000) and (not ti or ti == 0) -- T2 Measurement')
    elif (ti and (ti > 0)):
        classification_dict['Measurement'] = ["FLAIR"]
        log.info('(ti and (ti > 0)) -- FLAIR Measurement')
    elif (te and te  < 50) and (tr and tr > 1000):
        classification_dict['Measurement'] = ["PD"]
        log.info('(te and te  < 50) and (tr and tr > 1000) -- PD Measurement')

    if re.search('POST', sd, flags=re.IGNORECASE):
        classification_dict['Custom'] = ['Contrast']
        log.info('POST found in Series Description -- Adding Contrast to custom classification')

    if slice_number and slice_number < 10:
        classification_dict['Intent'] = ['Localizer']
        log.info('slice_number and slice_number < 10 -- Localizer Intent')

    if unique_iop:
        classification_dict['Intent'] = ['Localizer']
        log.info('unique_iop found -- Localizer')

    if not classification_dict:
        log.warning('Could not determine classification based on parameters!')
    else:
        log.info('Inferred classification from parameters: %s', classification_dict)

    return classification_dict

def get_classification_from_string(value):
    result = {}

    parts = re.split(r'\s*,\s*', value)
    last_key = None
    for part in parts:
        key_value = re.split(r'\s*:\s*', part)

        if len(key_value) == 2:
            last_key = key = key_value[0]
            value = key_value[1]
        else:
            if last_key:
                key = last_key
            else:
                log.warning('Unknown classification format: {0}'.format(part))
                key = 'Custom'
            value = part

        if key not in result:
            result[key] = []

        result[key].append(value)

    return result


def get_custom_classification(label, config_file):
    if config_file is None or not os.path.isfile(config_file):
        return None

    try:
        with open(config_file, 'r') as f:
            config = json.load(f)

        # Check custom classifiers
        classifications = config['inputs'].get('classifications', {}).get('value', {})
        if not classifications:
            log.debug('No custom classifications found in config...')
            return None

        if not isinstance(classifications, dict):
            log.warning('classifications must be an object!')
            return None

        for k in classifications.keys():
            val = classifications[k]

            if not isinstance(val, str):
                log.warning('Expected string value for classification key %s', k)
                continue

            if len(k) > 2 and k[0] == '/' and k[-1] == '/':
                # Regex
                try:
                    if re.search(k[1:-1], label, re.I):
                        log.debug('Matched custom classification for key: %s', k)
                        return get_classification_from_string(val)
                except re.error:
                    log.exception('Invalid regular expression: %s', k)
            elif fnmatch(label.lower(), k.lower()):
                log.debug('Matched custom classification for key: %s', k)
                return get_classification_from_string(val)

    except IOError:
        log.exception('Unable to load config file: %s', config_file)

    return None

def classify_MR(df, dcm, dcm_metadata):
    # Determine how many DICOM files are in directory
    slice_number = len(df)

    # Determine whether ImageOrientationPatient is constant
    if hasattr(df, 'ImageOrientationPatient'):
        uniqueiop = df.ImageOrientationPatient.is_unique
    else:
        uniqueiop = []
    # Classification (# Only set classification if the modality is MR)
    if dcm_metadata['modality'] == 'MR':
        log.info('MR series detected. Attempting classification...')
        classification = classify_dicom(dcm, slice_number, uniqueiop)
        
        #scan_coverage = classify_CT.scan_coverage(df)
        #label = acquisition.label
        #series_desc = format_string(dcm.get('SeriesDescription', ''))
        
         # Anatomy
        #if is_chest(acquisition.label):
        #    classifications['Anatomy'] = ['Chest']
        #elif is_abdomen(acquisition.label):
        #    classifications['Anatomy'] = ['Abdomen']
        ######## Pelvis check using acq label
        #elif is_pelvis(acquisition.label):
        #    classifications['Anatomy'] = ['Pelvis']
        #elif is_chest(series_description):
        #   classifications['Anatomy'] = ['Chest']
        #elif is_abdomen(series_description):
        #   classifications['Anatomy'] = ['Abdomen']
        ######## Pelvis check using series description
        #elif is_pelvis(series_description):
         #   classifications['Anatomy'] = ['Pelvis']
        #if classify_CT.is_head(scan_coverage):
         #   classification['Anatomy'] = ['Head']
        #elif classify_CT.is_whole_body(scan_coverage):
         #   classification['Anatomy'] = ['Whole Body']
        #elif classify_CT.is_cap(scan_coverage):
         #   classification['Anatomy'] = ['C/A/P']
        
        if classification:
            dcm_metadata['classification'] = classification

    return dcm_metadata