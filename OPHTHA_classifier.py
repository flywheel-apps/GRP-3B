import re
import common_utils
import logging

log = logging.getLogger(__name__)

# Laterality, Left


def is_left(description):
    regexes = [
        re.compile('(^|[^a-zA-Z])(L|LE)([^a-zA-Z]|$)', re.IGNORECASE),  # L or LE not surrounded by any other letters
        re.compile('LEFT', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)

# Laterality, Right


def is_right(description):
    regexes = [
        re.compile('(^|[^a-zA-Z])(R|RE)([^a-zA-Z]|$)', re.IGNORECASE),  # R or RE not surrounded by any other letters
        re.compile('RIGHT', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)

# Modality, OCT


def is_OCT(description):
    regexes = [
        re.compile('OCT', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)

# Modality, OCT-OP


def is_OCT_OP(description):
    regexes = [
        re.compile('SD.*OCT.*OP(?!T)', re.IGNORECASE)   # match ...OP, but not ...OPT
    ]
    return common_utils.regex_search_label(regexes, description)

# Modality, OCT-OPT


def is_OCT_OPT(description):
    regexes = [
        re.compile('SD.*OCT.*OPT', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)

######################################################################################
######################################################################################


def classify_OPHTHA(dcm_metadata, acquisition):
    """
    Classifies a OCT dicom series
    Args:
        dcm_metadata:  dicom data object
        acquisition:  acquisition object
    Returns:
        dcm_metadata: The dictionary for the OCT classification 
    """
    log.info("Determining OPHTHA Classification...")
    single_header_object = dcm_metadata['info']['header']['dicom']

    updateFlag = False

    if 'Columns' in single_header_object.keys():
        updateFlag = True
    elif  is_OCT(acquisition.label):
        updateFlag = True   
    
    if updateFlag:
        study_description = None
        if 'StudyDescription' in single_header_object.keys():
            study_description = single_header_object['StudyDescription']
        
        device_code_sequence = None
        if 'AcquisitionDeviceTypeCodeSequence' in single_header_object.keys():
            if 'CodeValue' in single_header_object['AcquisitionDeviceTypeCodeSequence']:
                device_code_sequence = single_header_object['AcquisitionDeviceTypeCodeSequence']['CodeValue']  
            elif 'CodeValue' in single_header_object['AcquisitionDeviceTypeCodeSequence'][0]:
                device_code_sequence = single_header_object['AcquisitionDeviceTypeCodeSequence'][0]['CodeValue']  

        classifications = {}

        # Get Modality
        modality = None
        if device_code_sequence and device_code_sequence == 'A-00FBE':
            modality = 'OCT'
        elif is_OCT(acquisition.label):
            modality = 'OCT'
            updateFlag = True
        elif device_code_sequence and study_description and study_description == 'CF':
            modality = 'CF'


        # Get Laterality
        laterality = None
        if single_header_object.get('ImageLaterality') == 'R':
            laterality = ['Right Eye']
        elif single_header_object.get('ImageLaterality') == 'L':
            laterality = ['Left Eye']
        elif is_right(acquisition.label):
            laterality = ['Right Eye']
        elif is_left(acquisition.label):
            laterality = ['Left Eye']
        if laterality:  # set classification laterality
            classifications.update({"Laterality": laterality})

        # Get OCT Type
        oct_type = None
        if device_code_sequence and device_code_sequence == 'A-00FBE':
            oct_type = ['Standard']
            # print("Found match for Standard OCT from AcquisitionDeviceTypeCodeSequence match")
        elif device_code_sequence and device_code_sequence == 'A-00E8A':
            oct_type = ['Fundus']
            # print("Found match for Fundus OCT from AcquisitionDeviceTypeCodeSequence match")
        elif is_OCT_OP(acquisition.label):
            oct_type = ['Fundus']
            # print("Found match for Fundus OCT from is_OCT_OP match")
        elif is_OCT_OPT(acquisition.label):
            oct_type = ['Standard']
            # print("Found match for Standard OCT from is_OCT_OPT match")

        if oct_type:
            classifications.update({"OCT Type": oct_type})
        if classifications:
            dcm_metadata['classification'] = classifications
        if modality:
            dcm_metadata['modality'] = modality
    else: 
        pass        

    return dcm_metadata
