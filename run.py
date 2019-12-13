#!/usr/bin/env python3

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
import classify_MR
import classification_from_label

logging.basicConfig()
log = logging.getLogger('grp-3B')


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
    df, dcm = classify_ALL.process_dicom(dicom_filepath)
    if modality == "MR":
        log.info("Determining MR Classification...")
        dicom_metadata = classify_MR.classify_MR(df, dcm, dicom_metadata)
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
