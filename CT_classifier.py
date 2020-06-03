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

        # Compute scan coverage
        scan_coverage, info_object = \
            common_utils.compute_scan_coverage_if_original(header_dicom, df,
                                                           info_object)
        
        # # Reconstruction window
        reconstruction_window = None
        reconstruction_window = common_utils.get_reconstruction_window(
            acquisition.label)
        if reconstruction_window:
            info_object['ReconstructionWindow'] = reconstruction_window
        
        # # Scan orientation 
        scan_orientation = None
        scan_orientation = common_utils.get_scan_orientation(acquisition.label)
        if scan_orientation:
            info_object['ScanOrientation'] = scan_orientation
        else:
            scan_orientation = common_utils.get_scan_orientation(
                series_description)
            if scan_orientation:
                info_object['ScanOrientation'] = scan_orientation

        # Classify Anatomy
        classification = common_utils.classify_anatomy(
            classification, acquisition, series_description, scan_coverage)

        # # Contrast
        classification['Contrast'] = common_utils.get_contrast_classification(
            acquisition.label)
        if not classification['Contrast']:
            classification['Contrast'] = \
                common_utils.get_contrast_classification(
                series_description)

        if scan_coverage:
            spacing_between_slices = scan_coverage / len(df)
            info_object['SpacingBetweenSlices'] = round(spacing_between_slices, 2)
        
        dcm_metadata['info'].update(info_object)

    dcm_metadata['classification'] = classification

    return dcm_metadata
