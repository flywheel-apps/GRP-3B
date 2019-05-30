#!/usr/bin/env python3

import os
import json
import sys
import logging
import classification_from_label
import flywheel
import re
import string
from fnmatch import fnmatch
import pydicom
import zipfile
import pandas as pd
import pprint

import classify_CT

logging.basicConfig()
log = logging.getLogger('grp-3B')


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
    series_desc = format_string(dcm.get('SeriesDescription', ''))

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

    if (te and te < 30) and (tr and tr < 8000):
        classification_dict['Measurement'] = ["T1"]
        log.info('(te and te < 30) and (tr and tr < 8000) -- T1 Measurement')
    elif (te and te  > 50) and (tr and tr > 2000) and (ti and ti == 0):
        classification_dict['Measurement'] = ["T2"]
        log.info('(te and te  > 50) and (tr and tr > 2000) and (ti and ti == 0) -- T2 Measurement')
    elif (te and te  > 50) and (tr and tr > 8000) and (ti and (3000 > ti > 1500)):
        classification_dict['Measurement'] = ["FLAIR"]
        log.info('(te and te  > 50) and (tr and tr > 8000) and (ti and (3000 > ti > 1500)) -- FLAIR Measurement')
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


def assign_type(s):
    """
    Sets the type of a given input.
    """
    if type(s) == pydicom.valuerep.PersonName or type(s) == pydicom.valuerep.PersonName3 or type(s) == pydicom.valuerep.PersonNameBase:
        return format_string(s)
    if type(s) == list or type(s) == pydicom.multival.MultiValue:
        try:
            return [ float(x) for x in s ]
        except ValueError:
            try:
                return [ int(x) for x in s ]
            except ValueError:
                return [ format_string(x) for x in s if len(x) > 0 ]
    elif type(s) == float or type(s) == int:
        return s
    else:
        s = str(s)
        try:
            return int(s)
        except ValueError:
            try:
                return float(s)
            except ValueError:
                return format_string(s)


def format_string(in_string):
    formatted = re.sub(r'[^\x00-\x7f]',r'', str(in_string)) # Remove non-ascii characters
    formatted = ''.join(filter(lambda x: x in string.printable, formatted))
    if len(formatted) == 1 and formatted == '?':
        formatted = None
    return formatted#.encode('utf-8').strip()


def get_seq_data(sequence, ignore_keys):
    seq_dict = {}
    for seq in sequence:
        for s_key in seq.dir():
            s_val = getattr(seq, s_key, '')
            if type(s_val) is pydicom.UID.UID or s_key in ignore_keys:
                continue

            if type(s_val) == pydicom.sequence.Sequence:
                _seq = get_seq_data(s_val, ignore_keys)
                seq_dict[s_key] = _seq
                continue

            if type(s_val) == str:
                s_val = format_string(s_val)
            else:
                s_val = assign_type(s_val)

            if s_val:
                seq_dict[s_key] = s_val

    return seq_dict


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


def process_dicom(zip_file_path):
    if zipfile.is_zipfile(zip_file_path):
        dcm_list = []
        zip_obj = zipfile.ZipFile(zip_file_path)
        num_files = len(zip_obj.namelist())
        for n in range((num_files - 1), -1, -1):
            dcm_path = zip_obj.extract(zip_obj.namelist()[n], '/tmp')
            dcm_tmp = None
            if os.path.isfile(dcm_path):
                try:
                    log.info('reading %s' % dcm_path)
                    dcm_tmp = pydicom.read_file(dcm_path)
                    # Here we check for the Raw Data Storage SOP Class, if there
                    # are other pydicom files in the zip then we read the next one,
                    # if this is the only class of pydicom in the file, we accept
                    # our fate and move on.
                    if dcm_tmp.get('SOPClassUID') == 'Raw Data Storage' and n != range((num_files - 1), -1, -1)[-1]:
                        continue
                    else:
                        dcm_list.append(dcm_tmp)
                except:
                    pass
            else:
                log.warning('%s does not exist!' % dcm_path)
        # Select last image
        dcm = dcm_list[-1]
    else:
        log.info('Not a zip. Attempting to read %s directly' % os.path.basename(zip_file_path))
        dcm = pydicom.read_file(zip_file_path)
        dcm_list = [dcm]

    # Create pandas object for comparing headers
    df_list = []
    for header in dcm_list:
        tmp_dict = get_pydicom_header(header)
        for key in tmp_dict:
            if type(tmp_dict[key]) == list:
                tmp_dict[key] = str(tmp_dict[key])
            else:
                tmp_dict[key] = [tmp_dict[key]]
        df_tmp = pd.DataFrame.from_dict(tmp_dict)
        df_list.append(df_tmp)
    df = pd.concat(df_list, ignore_index=True, sort=True)

    # Determine how many DICOM files are in directory
    slice_number = len(df)
    return df


def classify_MR(df, dcm_metadata):

    # Determine whether ImageOrientationPatient is constant
    if hasattr(df, 'ImageOrientationPatient'):
        uniqueiop = df.ImageOrientationPatient.is_unique
    else:
        uniqueiop = []
    # Classification (# Only set classification if the modality is MR)
    if dcm_metadata['modality'] == 'MR':
        log.info('MR series detected. Attempting classification...')
        classification = classify_dicom(dcm, slice_number, uniqueiop)
        if classification:
            dcm_metadata['classification'] = classification

    return dcm_metadata


def get_pydicom_header(dcm):
    # Extract the header values
    header = {}
    exclude_tags = ['[Unknown]', 'PixelData', 'Pixel Data',  '[User defined data]', '[Protocol Data Block (compressed)]', '[Histogram tables]', '[Unique image iden]']
    tags = dcm.dir()
    for tag in tags:
        try:
            if (tag not in exclude_tags) and ( type(dcm.get(tag)) != pydicom.sequence.Sequence ):
                value = dcm.get(tag)
                if value or value == 0: # Some values are zero
                    # Put the value in the header
                    if type(value) == str and len(value) < 10240: # Max pydicom field length
                        header[tag] = format_string(value)
                    else:
                        header[tag] = assign_type(value)
                else:
                    log.debug('No value found for tag: ' + tag)

            if type(dcm.get(tag)) == pydicom.sequence.Sequence:
                seq_data = get_seq_data(dcm.get(tag), exclude_tags)
                # Check that the sequence is not empty
                if seq_data:
                    header[tag] = seq_data
        except:
            log.debug('Failed to get ' + tag)
            pass
    return header


if __name__ == '__main__':
    # Set paths
    input_folder = '/flywheel/v0/input/file/'
    output_folder = '/flywheel/v0/output/'
    config_file_path = '/flywheel/v0/config.json'
    metadata_output_filepath = os.path.join(output_folder, '.metadata.json')

    # Load config file
    with open(config_file_path) as config_data:
        config = json.load(config_data)

    # Set dicom path and name from config file
    dicom_filepath = config['inputs']['dicom']['location']['path']
    dicom_name = config['inputs']['dicom']['location']['name']
    # Get the current dicom metadata
    dicom_metadata = config['inputs']['dicom']['object']

    # Check that metadata import ran
    try:
        dicom_header = dicom_metadata['info']['header']['dicom']
    except KeyError:
        print('ERROR: No dicom header information found! Please run metadata import and validation.')
        sys.exit(1)

    # Get the modality
    modality = config['inputs']['dicom']['object']['modality']

    output_metadata = dict()
    df = process_dicom(dicom_filepath)
    if modality == "MR":
        log.info("Determining MR Classification...")
        dicom_metadata = classify_MR(df, dicom_metadata)
        print(dicom_metadata)
        output_metadata['acquisition'] = dict()

        output_metadata['acquisition']['files'] = [
            {"classification": dicom_metadata['classification']}
        ]
        output_metadata['acquisition']['files'][0]['name'] = dicom_name
        pprint.pprint(output_metadata)
        with open(metadata_output_filepath, 'w') as metafile:
            json.dump(output_metadata, metafile, separators=(', ', ': '), sort_keys=True, indent=4)
    elif modality == 'CT':
        with flywheel.GearContext() as gear_context:
            acquisition = gear_context.client.get(gear_context.destination['id'])
        original_info_object = dicom_metadata['info']
        classification, info_object = classify_CT.classify_CT(df, dicom_header, acquisition)
        original_info_object.update(info_object)
        output_metadata['acquisition'] = dict()

        output_metadata['acquisition']['files'] = [
            {
                "classification": classification,
                "name": dicom_name,
                "info": original_info_object
            }
        ]
        output_metadata['acquisition']['files'][0]['name'] = dicom_name
        print(output_metadata)
        pprint.pprint(output_metadata)
        with open(metadata_output_filepath, 'w') as metafile:
            json.dump(output_metadata, metafile, separators=(', ', ': '), sort_keys=True, indent=4)



