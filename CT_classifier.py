import re
import string
import common_utils
from functools import reduce
import logging

import common_utils

log = logging.getLogger(__name__)


def classify_CT(df, dcm_metadata, acquisition):
    '''
    Classifies a CT dicom series

    Args:
        df (DataFrame): A pandas DataFrame where each row is a dicom image header information
    Returns:
        dict: The dictionary for the CT classification
    '''
    log.info("Determining CT Classification...")
    header_dicom = dcm_metadata['info']['header']['dicom']
    series_description = header_dicom.get('SeriesDescription') or ''
    classification_source = {}
    classification = {}
    info_object = {}
    
    if common_utils.is_localizer(acquisition.label) or common_utils.is_localizer(series_description) or len(df) < 10:
        classification['Scan Type'] = ['Localizer']
    else:
        classification['Scan Type'] = \
            common_utils.get_scan_type_classification(
            acquisition.label, header_dicom)
        if not classification['Scan Type']:
            classification['Scan Type'] = \
                common_utils.get_scan_type_classification(
                series_description, header_dicom)

        # # Compute scan coverage
        scan_coverage, info_object = \
            common_utils.compute_scan_coverage_if_original(header_dicom, df,
                                                           info_object)
        
        # # Reconstruction window
        reconstruction_window = None
        reconstruction_window = common_utils.get_reconstruction_window(
            acquisition.label)
        if reconstruction_window:
            info_object['ReconstructionWindow'] = reconstruction_window
        
        # # Classify Scan orientation 
        classification['Scan Orientation'] = common_utils.get_scan_orientation(acquisition.label)
        if not classification['Scan Orientation']:
            classification['Scan Orientation'] = common_utils.get_scan_orientation(
                series_description)
            
            
        # # Classify Anatomy
        classification = common_utils.classify_anatomy(
            classification, acquisition, series_description, scan_coverage)

        # # Classify Contrast
        classification['Contrast'] = common_utils.get_contrast_classification(
            acquisition.label)
        if not classification['Contrast']:
            classification['Contrast'] = \
                common_utils.get_contrast_classification(
                series_description)



        # # Set Custom classification to 'Unknown' if any of the CT classification keys is absent or empty:
        if 'Scan Orientation' not in classification.keys():
            classification['Custom'] = ['Unknown']
        elif not classification['Scan Orientation']:
            classification['Custom'] = ['Unknown']
        else:
            # If classification exists  then create a tag in classification_source dict 
            # to indicate the source of Scan Orientation classification
            # This classification_source dict is then added to info object
            classification_source['ScanOrientationSource'] = 'Original'

        if 'Contrast' not in classification.keys():
            classification['Custom'] = ['Unknown']
        elif not classification['Contrast']:
            classification['Custom'] = ['Unknown']
        else:
            # If classification exists  then create a tag in classification_source dict 
            # to indicate the source of Contrast classification
            # This classification_source dict is then added to info object
            classification_source['ContrastSource'] = 'Original'

        if 'Anatomy' not in classification.keys():
            classification['Custom'] = ['Unknown']
        elif not classification['Anatomy']:
            classification['Custom'] = ['Unknown']
        else:
            # If classification exists  then create a tag in classification_source dict 
            # to indicate the source of Anatomy classification
            # This classification_source dict is then added to info object
            classification_source['AnatomySource'] = 'Original'


        # # Scan Coverage
        if scan_coverage:
            spacing_between_slices = scan_coverage / len(df)
            info_object['SpacingBetweenSlices'] = round(spacing_between_slices, 2)
        
        info_object['ClassificationSource'] = classification_source
        dcm_metadata['info'].update(info_object)

    dcm_metadata['classification'] = classification

    return dcm_metadata
