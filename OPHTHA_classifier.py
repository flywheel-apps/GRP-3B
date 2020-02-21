import re
import common_utils


def is_left(description):
    regexes = [
        re.compile('(^|[^a-zA-Z])L([^a-zA-Z]|$)', re.IGNORECASE),  # match letter L not surrounded by any other letters
        re.compile('LEFT', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)


def is_right(description):
    regexes = [
        re.compile('(^|[^a-zA-Z])R([^a-zA-Z]|$)', re.IGNORECASE),  # match letter R not surrounded by any other letters
        re.compile('RIGHT', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)


def is_OCT(description):
    regexes = [
        re.compile('OCT', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)


def is_OCT_OP(description):
    regexes = [
        re.compile('SD.*OCT.*OP(?!T)', re.IGNORECASE)   # match ...OP, but not ...OPT
    ]
    return common_utils.regex_search_label(regexes, description)


def is_OCT_OPT(description):
    regexes = [
        re.compile('SD.*OCT.*OPT', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)


def classify_OPHTHA(df, single_header_object, acquisition):
    """
    Classifies a OCT dicom series
    Args:
        df (DataFrame): A pandas DataFrame where each row is a dicom image header information
        single_header_object - dicom data object
        acquisition_name - acquisition label
    Returns:
        str: Modality
        dict: The dictionary for the OCT classification
    """

    classifications = {}

    # Get Modality
    modality = None
    if single_header_object['AcquisitionDeviceTypeCodeSequence']['CodeValue'] == 'A-00FBE':
        modality = 'OCT'
    elif is_OCT(acquisition.label):
        modality = 'OCT'
    elif single_header_object['AcquisitionDeviceTypeCodeSequence']['CodeValue'] and single_header_object.get('StudyDescription') == 'CF':
        modality = 'CF'


    # get Laterality
    laterality = None
    if single_header_object.get('ImageLaterality') == 'R':
        laterality = 'Right Eye'
    elif single_header_object.get('ImageLaterality') == 'L':
        laterality = 'Left Eye'
    elif is_right(acquisition.label):
        laterality = 'Right Eye'
    elif is_left(acquisition.label):
        laterality = 'Left Eye'

    if laterality:  # set classification laterality
        classifications.update({"Laterality": [laterality]})


    # get OCT Type
    oct_type = None
    if single_header_object['AcquisitionDeviceTypeCodeSequence']['CodeValue'] == 'A-00FBE':
        oct_type = 'Standard'
        # print("Found match for Standard OCT from AcquisitionDeviceTypeCodeSequence match")
    elif single_header_object['AcquisitionDeviceTypeCodeSequence']['CodeValue'] == 'A-00E8A':
        oct_type = 'Fundus'
        # print("Found match for Fundus OCT from AcquisitionDeviceTypeCodeSequence match")
    elif is_OCT_OP(acquisition.label):
        oct_type = 'Fundus'
        # print("Found match for Fundus OCT from is_OCT_OP match")
    elif is_OCT_OPT(acquisition.label):
        oct_type = 'Standard'
        # print("Found match for Standard OCT from is_OCT_OPT match")

    if oct_type:
        classifications.update({"OCT Type": [oct_type]})


    return modality, classifications