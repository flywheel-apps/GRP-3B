#!/usr/bin/env python3

import os
import json
import sys
import logging
import flywheel
import pydicom
import pprint
import dicom_processor
import CT_classifier
import MR_classifier
import OPHTHA_classifier
import PT_classifier


logging.basicConfig()
log = logging.getLogger('grp-3B')

def log_errors(log_level_message):
    for each_level_message in log_level_message:
        log_level = each_level_message[0]
        log_message = each_level_message[1]
        if (log_level == 'debug'):
            log.debug(log_message)
        elif (log_level == 'info'):
            log.info(log_message)
        elif (log_level == 'warning'):
            log.warning(log_message)
        elif (log_level == 'error'):
            log.error(log_message)
        elif (log_level == 'exception'):
            log.exception(log_message)

            
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
    df, dcm, log_level_message = dicom_processor.process_dicom(dicom_filepath)
    log_errors(log_level_message)
    
    if modality == "MR":
        log.info("Determining MR Classification...")
        dicom_metadata, log_level_message = MR_classifier.classify_MR(df, dcm, dicom_metadata)
        log_errors(log_level_message)
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
        log.info("Determining CT Classification...")
        with flywheel.GearContext() as gear_context:
            acquisition = gear_context.client.get(gear_context.destination['id'])
        original_info_object = dicom_metadata['info']
        classification, info_object = CT_classifier.classify_CT(df, dicom_header, acquisition)
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
    elif modality == 'PT':
        log.info("Determining PT Classification...")
        with flywheel.GearContext() as gear_context:
            acquisition = gear_context.client.get(gear_context.destination['id'])
        original_info_object = dicom_metadata['info']
        classification, info_object = PT_classifier.classify_PT(df, dicom_header, acquisition)
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
    elif modality == 'OPT' or modality == 'OP':
        log.info("Determining OPHTHA Classification...")
        with flywheel.GearContext() as gear_context:
            acquisition = gear_context.client.get(gear_context.destination['id'])
        
        original_info_object = dicom_metadata['info']
        original_classification_object = dicom_metadata['classification']
        
        modality, classification = OPHTHA_classifier.classify_OPHTHA(df, dicom_header, acquisition)
        
        # original_classification_object.update(classification)

        output_metadata['acquisition'] = dict()

        output_metadata['acquisition']['files'] = [
            {
                "classification": classification,
                "modality": modality,
                "name": dicom_name
            }
        ]
        output_metadata['acquisition']['files'][0]['name'] = dicom_name
        # print(output_metadata)
        pprint.pprint(output_metadata)
        with open(metadata_output_filepath, 'w') as metafile:
            json.dump(output_metadata, metafile, separators=(', ', ': '), sort_keys=True, indent=4)



