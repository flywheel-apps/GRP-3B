#!/usr/bin/env python3

import os
import json
import sys
import logging
import flywheel
import pprint
import dicom_processor
import CT_classifier
import MR_classifier
import PT_classifier
import OPHTHA_classifier


logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)


def update_metadata(dcm_metadata, dicom_name):
    
    output_metadata = dict()
    output_metadata['acquisition'] = dict()

    if modality == 'MR':
        output_metadata['acquisition']['files'] = [
            {"classification": dcm_metadata['classification']}
        ]
    if modality == 'CT' or modality == 'PT':
        output_metadata['acquisition']['files'] = [
            {"classification": dcm_metadata['classification'],
             "name": dicom_name,
             "info": dcm_metadata['info']}
        ]
    if modality == 'OPT' or modality == 'OP':
        output_metadata['acquisition']['files'] = [
            {"classification": dcm_metadata['classification'],
             "modality": dcm_metadata['modality'],
             "name": dicom_name}
        ]
    output_metadata['acquisition']['files'][0]['name'] = dicom_name
    return output_metadata


            
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
    # Get the modality
    modality = config['inputs']['dicom']['object']['modality']
    # Get Acquisition
    with flywheel.GearContext() as gear_context:
            acquisition = gear_context.client.get(gear_context.destination['id'])
    df, dcm = dicom_processor.process_dicom(dicom_filepath)
    

    # Check that metadata import ran
    try:
        dicom_header = dicom_metadata['info']['header']['dicom']
    except KeyError:
        print('ERROR: No dicom header information found! Please run metadata import and validation.')
        sys.exit(1)
    
    
    original_info_object = dicom_metadata['info']
    

    if modality == "MR":
        dicom_metadata = MR_classifier.classify_MR(df, dcm, dicom_metadata) 
    elif modality == 'CT':
        dicom_metadata = CT_classifier.classify_CT(df, dicom_metadata, acquisition)
    elif modality == 'PT':
        dicom_metadata = PT_classifier.classify_PT(df, dicom_metadata, acquisition)
    elif modality == 'OPT' or modality == 'OP':
        dicom_metadata = OPHTHA_classifier.classify_OPHTHA(df, dicom_metadata, acquisition)

    output_metadata = update_metadata(dicom_metadata, dicom_name)
    meta_log_string = pprint.pformat(output_metadata)
    log.info(meta_log_string)
    with open(metadata_output_filepath, 'w') as metafile:
        json.dump(output_metadata, metafile, separators=(', ', ': '), sort_keys=True, indent=4)


