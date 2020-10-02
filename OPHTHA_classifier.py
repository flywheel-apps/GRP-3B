import re
import common_utils
import logging

log = logging.getLogger(__name__)

# Laterality, Left
def is_left(description):
    """
    # return false
    >>> is_left('some string')
    False
    
    # returns true
    >>> is_left('left')
    True

    >>> is_left('abc_le_123.jpg')
    True

    >>> is_left('abc_OS_123.jpg')
    True

    >>> is_left('abc_OD_123.jpg')
    False

    """

    regexes = [
        re.compile('(^|[^a-zA-Z])(L|LE)([^a-zA-Z]|$)', re.IGNORECASE),
        # L or LE not surrounded by any other letters
        re.compile('(^|[^a-zA-Z])(OS)([^a-zA-Z]|$)', re.IGNORECASE),
        # OS not surrounded by any other letters
        re.compile('LEFT', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)

# Laterality, Right
def is_right(description):
    """
    # return false
    >>> is_right('some string')
    False
    
    # returns true
    >>> is_right('right')
    True

    >>> is_right('abc_re_123.jpg')
    True

    >>> is_right('abc_OD_123.jpg')
    True

    >>> is_right('abc_OS_123.jpg')
    False

    """
    regexes = [
        re.compile('(^|[^a-zA-Z])(R|RE)([^a-zA-Z]|$)', re.IGNORECASE),
        # R or RE not surrounded by any other letters
        re.compile('(^|[^a-zA-Z])(OD)([^a-zA-Z]|$)', re.IGNORECASE),
        # OD not surrounded by any other letters
        re.compile('RIGHT', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)

# Modality, OCT
def is_OCT(description):
    regexes = [
        re.compile('OCT', re.IGNORECASE),
        #for Eyecor - Start with OP_ or OPT_ or OT_
        re.compile('^OP?T?_', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)

# Modality, OCT-OP
def is_OCT_OP(description):
    regexes = [
        # match ...OP, but not ...OPT
        re.compile('SD.*OCT.*OP(?!T)', re.IGNORECASE),
        #for Eyecor - Start with OP_
        re.compile('^OP_', re.IGNORECASE)       
    ]
    return common_utils.regex_search_label(regexes, description)

# Modality, OCT-OPT
def is_OCT_OPT(description):
    regexes = [
        re.compile('SD.*OCT.*OPT', re.IGNORECASE),
        #for Eyecor - Start with OPT_
        re.compile('^OPT_', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)

# # Modality, OCT-OT
# def is_OCT_OT(description):
#     regexes = [
#         #for Eyecor - Start with OT_
#         re.compile('^OT_', re.IGNORECASE)
#     ]
#     return common_utils.regex_search_label(regexes, description)

# For EyeKore
# Determine Procedure Name
def getProtocolName(single_header_object):
    protocolName = None
    if 'ProtocolName' in single_header_object.keys():
            protocolName = single_header_object['ProtocolName']
    return protocolName

# The commented blocks below are for Future development
# def is_FA(dicom_filepath):
#     regexes = [
#         #for Eyecor - has with /FA/ in the path
#         re.compile('\/FA\/', re.IGNORECASE)
#     ]
#     return common_utils.regex_search_label(regexes, description)

# def is_FAF(dicom_filepath):
#     regexes = [
#         #for Eyecor - has with /FAF/ in the path
#         re.compile('\/FAF\/', re.IGNORECASE)
#     ]
#     return common_utils.regex_search_label(regexes, description)

# def is_COLOR(dicom_filepath):
#     regexes = [
#         #for Eyecor - has with /COLOR/ in the path
#         re.compile('\/COLOR\/', re.IGNORECASE)
#     ]
#     return common_utils.regex_search_label(regexes, description)        

# def is_ICG(dicom_filepath):
#     regexes = [
#         # for Eyecor - has with /ICG/ in the path
#         re.compile('\/ICG\/', re.IGNORECASE)
#     ]
#     return common_utils.regex_search_label(regexes, description) 

# def is_SD_OCT(dicom_filepath):
#     regexes = [
#         #for Eyecor - has /SD-OCT/ in the path
#         re.compile('\/SD-OCT\/', re.IGNORECASE)
#     ]
#     return common_utils.regex_search_label(regexes, description)         

# def get_Modality(dicom_filepath):
#     if is_FA(dicom_filepath):
#         modality = ['FP']
#         modalityType = ['Fluorescein Angiography']
#     elif is_FAF(dicom_filepath):
#         modality = ['FP']
#         modalityType = ['Autofluorescence']
#     elif is_COLOR(dicom_filepath):
#         modality = ['FP']
#         modalityType = ['Color']
#     elif is_ICG:
#         modality = ['FP']
#         modalityType = ['Indocyanine Green']
#     return modality, modalityType    

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
    protocolName = None
    octType = None
    subType = None
    modality = None
    modalityType = None
    protocolNameMessage = None

    if 'Columns' in single_header_object.keys():
        updateFlag = True
    elif is_OCT(acquisition.label):
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
        
        # Get ProtocolName - used in EyeCore
        protocolName = getProtocolName(single_header_object)

        # Get Modality
        if protocolName:
            protocolNameMessage = "Got protocolName:" + protocolName
            log.debug(protocolNameMessage)
            if protocolName == 'FA':
                modality = 'FP'
                modalityType = 'Fluorescein Angiography'
                subType = 'Standard Field'
            elif protocolName == 'FA-4W Sweep':
                modality = 'FP'
                modalityType = 'Fluorescein Angiography'
                subType = 'Wide Field'
            elif protocolName == 'FA: UltraWidefield':
                modality = 'FP'
                modalityType = 'Fluorescein Angiography'
                subType = 'Ultra-wide Field' 
            elif protocolName == 'FA6':
                modality = 'FP'
                modalityType = 'Fluorescein Angiography'
            elif protocolName == 'FAF':
                modality = 'FP'
                modalityType = 'Autofluorescence'
            elif protocolName in ['FP','FP-2','FP-3M','FP-4W','FP-7M','FP-7Std','FP-9','FP-ROP']:
                log.debug("Inside logic for ColorFundus using IN [FP, FP-2, and so on]")
                modality = 'FP'
                modalityType = 'Color'
                if protocolName in ['FP-7Std']:
                    subType = 'Standard'  
                elif protocolName in ['FP-4W']: 
                    subType = 'Wide Field' 
            elif protocolName == 'ICG':
                modality = 'FP'
                modalityType = 'Indocyanine Green'
            elif protocolName == 'OCT Angiography':
                log.debug("Inside logic for OCT-A")
                modality = 'OCT'
                octType = ['Angiography']
            elif protocolName == 'SD-OCT':
                modality = 'OCT'
                octType = ['Standard']
            elif protocolName == 'UWF-AF':
                modality = 'FP'
                modalityType = 'Autofluorescence' 
                subType = 'Ultra-wide Field'  
            elif protocolName == 'UWF-C':
                modality = 'FP'
                modalityType = 'Color' 
                subType = 'Ultra-wide Field' 
            elif protocolName == 'UWF-ICG':
                modality = 'FP'
                modalityType = 'Indocyanine Green' 
                subType = 'Ultra-wide Field'
            elif protocolName == 'Widefield OCT':
                modality = 'OCT'
                octType = ['Standard'] 
                # octSubType = 'Wide Field'
        elif device_code_sequence and device_code_sequence == 'A-00FBE':
            modality = 'OCT'
        elif device_code_sequence and study_description and study_description == 'CF':
            modality = 'FP'
            modalityType = 'Color'
        elif is_OCT(acquisition.label):
            modality = 'OCT'
            # updateFlag = True

        if modality:
            log.debug('In Modality... Got:')
            log.debug(modality)
            updateFlag = True 
            if modalityType:
                classifications['Type']=[modalityType]
            if subType:
                classifications['Sub-Type'] = [subType]
  
        # Get Laterality
        laterality = None
        if single_header_object.get('ImageLaterality'):
            if single_header_object.get('ImageLaterality') in ('R','OD'):
                laterality = ['Right Eye']
            elif single_header_object.get('ImageLaterality') in ('L','OS'):
                laterality = ['Left Eye']
        elif is_right(acquisition.label):
            laterality = ['Right Eye']
        elif is_left(acquisition.label):
            laterality = ['Left Eye']
        
        if laterality:  # set classification laterality
            classifications['Laterality'] = laterality
            # classifications.update({"Laterality": laterality}) update later using Dictionary
        
        # Get OCT Type
        if octType is None:
            if device_code_sequence and device_code_sequence == 'A-00FBE':
                octType = ['Standard']
                log.debug("Found match for Standard OCT from AcquisitionDeviceTypeCodeSequence match")
            elif device_code_sequence and device_code_sequence == 'A-00E8A':
                octType = ['Fundus']
                log.debug("Found match for Fundus OCT from AcquisitionDeviceTypeCodeSequence match")
            elif is_OCT_OP(acquisition.label):
                octType = ['Fundus']
                log.debug("Found match for Fundus OCT from is_OCT_OP match")
            elif is_OCT_OPT(acquisition.label):
                octType = ['Standard']
                log.debug("Found match for Standard OCT from is_OCT_OPT match")
        
        if modality == 'OCT' and octType:
            classifications.update({"OCT Type": octType})

        if classifications:
            dcm_metadata['classification'] = classifications

        if modality:
            dcm_metadata['modality'] = modality
            dcm_metadata['type'] = modalityType
            if subType:
                dcm_metadata['Sub-Type'] = [subType]
            log.debug("In Modality last block -> have dcm_metadata:")
            log.debug(dcm_metadata)  
        else:
            log.debug("missing modality last block")      
    else:
        log.debug("Updtate Flag is false... Not processing this file")
        pass

    log.debug("Sending dcm_metadata to run module:")
    log.debug(dcm_metadata)    
    return dcm_metadata

## Perform test if run directly
if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)