import re
import string
import common_utils
from operator import add
from functools import reduce
import logging
from pprint import pformat

from common_utils import SEQUENCE_ANATOMY

log = logging.getLogger(__name__)


######################################################################################
######################################################################################

# Check multiple occurrence of anatomy
def is_multiple_occurrence(label, string):
    test_string = string.lower()
    label_lower = label.lower()
    label_split = re.split(r"[^a-zA-Z0-9\s]|\s+", label_lower)
    idx = label_split.count(test_string)
    if idx > 1:
        return True
    else:
        return False
# Check 'to' in labels for ranged anatomy
def is_to(description):
    regexes = [
        re.compile('(^|[^a-zA-Z])to([^a-zA-Z]|$)', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)

# Standard Scan
def is_standard_scan(description):
    regexes = [
        re.compile('\\bNAC', re.IGNORECASE),
        re.compile('NAC\\b', re.IGNORECASE),
        re.compile('_NAC', re.IGNORECASE),
        re.compile('NAC_', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)
# Attenuation Corrected Scan
def is_attn_corr_scan(description):
    regexes = [
        re.compile('\\bAC', re.IGNORECASE),
        re.compile('AC\\b', re.IGNORECASE),
        re.compile('_AC', re.IGNORECASE),
        re.compile('^AC_', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)


# Scan Orientation, Axial
def is_axial(description):
    regexes = [
        re.compile('axial', re.IGNORECASE),
        re.compile('trans', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)
# Scan Orientation, Coronal
def is_coronal(description):
    regexes = [
        re.compile('cor', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)
# Scan Orientation, Sagittal
def is_sagittal(description):
    regexes = [
        re.compile('sag', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)


# Aggregate Anatomy
def is_cap_label(description):
    regexes = [
        re.compile('(c.?a.?p)', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)
def is_ncap_label(description):
    regexes = [
        re.compile('(n.?c.?a.?p)', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)
def is_hcap_label(description):
    regexes = [
        re.compile('(h.?c.?a.?p)', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)
def is_hn_label(description):
    regexes = [
        re.compile('(^|[^a-zA-Z])hn([^a-zA-Z]|$)', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)
def is_neck_lower_label(description):
    regexes = [
        re.compile('Neck w\^IV lower', re.IGNORECASE),
        re.compile('Neck lower', re.IGNORECASE),
        re.compile('(neck.?lower)', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)
def is_neck_upper_label(description):
    regexes = [
        re.compile('Neck w\^IV upper', re.IGNORECASE),
        re.compile('Neck upper', re.IGNORECASE),
        re.compile('(neck.?upper)', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)

# Anatomy, Head (Scan Coverage)
def is_head(scan_coverage):
    return scan_coverage is not None and scan_coverage < 250
# Anatomy, Whole Body (Scan Coverage)
def is_whole_body(scan_coverage):
    return scan_coverage is not None and scan_coverage > 1300
# Anatomy, C/A/P (Scan Coverage)
def is_cap(scan_coverage):
    return scan_coverage is not None and scan_coverage > 800 and scan_coverage < 1300

# Anatomy, Head
def is_head_label(description):
    regexes = [
        re.compile('head', re.IGNORECASE),
        re.compile('brain', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)
# Anatomy, Neck
def is_neck_label(description):
    regexes = [
        re.compile('neck', re.IGNORECASE),
        re.compile('cervical', re.IGNORECASE),
        re.compile('hals', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)
# Anatomy, Chest
def is_chest_label(description):
    regexes = [
        re.compile('chest', re.IGNORECASE),
        re.compile('lung', re.IGNORECASE),
        re.compile('thorax', re.IGNORECASE),
        re.compile('thoracic', re.IGNORECASE),
        re.compile('thoracicspine', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)
# Anatomy, Abdomen
def is_abdomen_label(description):
    regexes = [
        re.compile('abdomen', re.IGNORECASE),
        re.compile('abdomenl', re.IGNORECASE),
        re.compile('bdomen', re.IGNORECASE),
        re.compile('abd', re.IGNORECASE),
        re.compile('abdo', re.IGNORECASE),
        re.compile('lumbarspine', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)
# Anatomy, Pelvis
def is_pelvis_label(description):
    regexes = [
        re.compile('pel', re.IGNORECASE),
        re.compile('(^|[^a-zA-Z])pv([^a-zA-Z]|$)', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)
# Anatomy, Lower Extremities
def is_lower_extremities(description):
    regexes = [
        re.compile('(^|[^a-zA-Z])le([^a-zA-Z]|$)', re.IGNORECASE),
        re.compile('(lower.?extremity)', re.IGNORECASE),
        re.compile('(lower.?extremities)', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)
# Anatomy, Upper Extremities
def is_upper_extremities(description):
    regexes = [
        re.compile('(^|[^a-zA-Z])ue([^a-zA-Z]|$)', re.IGNORECASE),
        re.compile('(upper.?extremity)', re.IGNORECASE),
        re.compile('(upper.?extremities)', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)
# Anatomy, Whole Body
def is_whole_body(description):
    regexes = [
        re.compile('whole', re.IGNORECASE),
        re.compile('(^|[^a-zA-Z])wb([^a-zA-Z]|$)', re.IGNORECASE),
        re.compile('body', re.IGNORECASE),
        re.compile('eyes.?to.?thighs', re.IGNORECASE),
        re.compile('eye.?to.?thigh', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)


# Reconstruction Window, Bone
def is_bone_window(description):
    regexes = [
        re.compile('(bone.?window)', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)
# Reconstruction Window, Lung
def is_lung_window(description):
    regexes = [
        re.compile('(lung.?window)', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)


# No contrast
def is_unenhanced(description):
    regexes = [
        re.compile('(un.?enhanced)', re.IGNORECASE),
        re.compile('w\^.?o', re.IGNORECASE),
        re.compile('w\/.?o', re.IGNORECASE),
        re.compile('(^|[^a-zA-Z])wo([^a-zA-Z]|$)', re.IGNORECASE),
        re.compile('(^|[^a-zA-Z])no([^a-zA-Z]|$)', re.IGNORECASE),
        re.compile('(no.?IV)', re.IGNORECASE),
        re.compile('(sans.?IV)', re.IGNORECASE),
        re.compile('(non.?contrast)', re.IGNORECASE)   
    ]
    return common_utils.regex_search_label(regexes, description)
# Contrast
def is_enhanced(description):
    regexes = [
        re.compile('enhanced', re.IGNORECASE),
        re.compile('(w\^.?IV)', re.IGNORECASE),
        re.compile('(w\/.?IV)', re.IGNORECASE),
        re.compile('contrast', re.IGNORECASE),
        re.compile('contraste', re.IGNORECASE),
        re.compile('(with.?contrast)', re.IGNORECASE),
        re.compile('(w\/)', re.IGNORECASE),
        re.compile('(w.?contrast)', re.IGNORECASE),
        re.compile('(IV.?contrast)', re.IGNORECASE)    
    ]
    return common_utils.regex_search_label(regexes, description)
# Contrast, Arterial Phase
def is_arterial(description):
    regexes = [
        re.compile('arterial', re.IGNORECASE),
    ]
    return common_utils.regex_search_label(regexes, description)
# Contrast, Portal Venous Phase
def is_portal_venous(description):
    regexes = [
        re.compile('portal', re.IGNORECASE),
        re.compile('venous', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)
# Contrast, Delayed Phase
def is_delayed_equil(description):
    regexes = [
        re.compile('delayed', re.IGNORECASE),
        re.compile('equil', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)

######################################################################################
######################################################################################


def get_scan_type_classification(label, single_header_object):
    new_scan_type = []
    
    ## Scan Type
    if single_header_object.get('ImageType', [None])[0] == 'ORIGINAL':
        new_scan_type = ['Original']
    elif single_header_object.get('ImageType', [None])[0] == 'DERIVED':
        new_scan_type = ['Derived']
    elif is_standard_scan(label):
        new_scan_type = ['Standard']
    elif is_attn_corr_scan(label):
        new_scan_type = ['AC']   
    
    return new_scan_type
    
        
def get_anatomy_classification(label):
    new_anatomy = []
    
    ## Aggregate Anatomy
    if is_hcap_label(label):
        new_anatomy.append(['Head', 'Neck', 'Chest', 'Abdomen', 'Pelvis'])
    elif is_ncap_label(label):
        new_anatomy.append(['Neck', 'Chest', 'Abdomen', 'Pelvis'])    
    elif is_cap_label(label):
        new_anatomy.append(['Chest', 'Abdomen', 'Pelvis'])
    
    ## Combination Anatomy
    if is_hn_label(label):
        new_anatomy.append(['Head', 'Neck'])
    if is_neck_lower_label(label):
        new_anatomy.append(['Chest'])
    if is_neck_upper_label(label):
        new_anatomy.append(['Head'])
    
    ## Multiple Anatomy occurrences
    if is_multiple_occurrence(label, 'neck'):
        if is_neck_lower_label(label) and is_neck_upper_label(label):
            new_anatomy.append(['Head', 'Chest'])
        if is_neck_lower_label(label) and not is_neck_upper_label(label):
            new_anatomy.append(['Neck', 'Chest'])
        if not is_neck_lower_label(label) and is_neck_upper_label(label):
            new_anatomy.append(['Head', 'Neck'])
    if is_multiple_occurrence(label, 'lung'):
        new_anatomy.append(['Chest'])

    ## Anatomy
    if is_head_label(label):
        new_anatomy.append(['Head'])
    if is_neck_label(label) and not is_neck_lower_label(label) and not is_neck_upper_label(label):
        new_anatomy.append(['Neck'])
    if is_chest_label(label) and not is_lung_window(label):
        new_anatomy.append(['Chest'])
    if is_abdomen_label(label):
        new_anatomy.append(['Abdomen'])
    if is_pelvis_label(label):
        new_anatomy.append(['Pelvis'])  
    if is_lower_extremities(label):
        new_anatomy.append(['Lower Extremities'])
    if is_upper_extremities(label):
        new_anatomy.append(['Upper Extremities'])    
    if is_whole_body(label):
        new_anatomy.append(['Whole Body'])
    
    if new_anatomy:
        new_anatomy = reduce(add, new_anatomy)
        new_anatomy = list(set(new_anatomy))
    return new_anatomy


def get_ranged_anatomy(label: str):
    """
    Returns a ranged anatomy.

    The ranged anatomy must conform to order of the list SEQUENCE_ANATOMY.

    Parameters
    ----------
    label (string): must contain 'to' to classify a ranged anatomy.

    Examples/Tests
    --------------
    # Returns None if missing 'to' from label
    >>> get_ranged_anatomy("missing word")
    Traceback (most recent call last):
        ...
    ValueError: Argument label ('missing word') must contain 'to'.

    # Returns None if first anatomy could not be classified
    >>> get_ranged_anatomy("incorrect to pelvis")


    # Returns None if first anatomy not in SEQUENCE_ANATOMY
    >>> get_ranged_anatomy("NCAP to pelvis")


    # Returns None if last anatomy could not be classified
    >>> get_ranged_anatomy("head to incorrect")


    # Returns None if last anatomy not in SEQUENCE_ANATOMY
    >>> get_ranged_anatomy("head to ncap")


    # Returns the first anatomy if first and last are the same
    >>> get_ranged_anatomy("head to head")
    'Head'

    # Returns erorr if first anatomy index idex is greater than last anatomy index
    >>> get_ranged_anatomy("pelvis to head")
    Traceback (most recent call last):
        ...
    ValueError: Ranged anatomy does not conform to sequence. First anatomy index ('4') is greater than last anatomy index ('0'). First anatomy ('Pelvis') should come before last anatomy ('Head') to conform to SEQUENCE_ANATOMY:['Head', 'Neck', 'Chest', 'Abdomen', 'Pelvis', 'Lower Extremities', 'Upper Extremities', 'Whole Body']
    """
    label_lower = label.lower()
    split_label = re.split(r"[^a-zA-Z0-9\s]|\s+", label_lower)

    # Check 'to' is in passed label
    if 'to' not in split_label:
        raise ValueError(
            f"Argument label ('{label}') must contain 'to'."
        )
    idx = split_label.index('to')

    # classify the first ranged anatomy (left of 'to')
    first_anatomy = get_anatomy_classification(split_label[idx - 1])
    if not first_anatomy:
        log.error(
            f"Could not create first anatomy from label "
            f"'{split_label[idx - 1]}'. Got '{first_anatomy}'")
        return None
    first_anatomy = reduce(add, first_anatomy)
    if first_anatomy not in SEQUENCE_ANATOMY:
        log.error(
            f"Could not find first anatomy '{first_anatomy}' in ranged "
            f"anatomy search. Anatomy must be one of the following:\n"
            f"{pformat(SEQUENCE_ANATOMY)}")
        return None

    first_anatomy_idx = SEQUENCE_ANATOMY.index(first_anatomy)

    # classify the second ranged anatomy (right of 'to')
    last_anatomy = get_anatomy_classification(split_label[idx + 1])
    if not last_anatomy:
        log.error(
            f"Could not create second anatomy from label "
            f"'{split_label[idx + 1]}'. Got '{last_anatomy}'")
        return None
    last_anatomy = reduce(add, last_anatomy)
    if last_anatomy not in SEQUENCE_ANATOMY:
        log.error(
            f"Could not find last anatomy '{last_anatomy}' in ranged "
            f"anatomy search. Anatomy must be one of the following:\n"
            f"{pformat(SEQUENCE_ANATOMY)}")
        return None
    last_anatomy_idx = SEQUENCE_ANATOMY.index(last_anatomy)

    # Check that the first and last anatomies aren't the same. Return first
    # one if so.
    if first_anatomy_idx == last_anatomy_idx:
        new_anatomy = SEQUENCE_ANATOMY[first_anatomy_idx]
        log.warning(f"This is not a ranged anatomy in the form '["
                    f"first_anatomy] to [last_anatomy]'. The first and last "
                    f"anatomies are the same. \n "
                    f"Using only the first one "
                    f"('{new_anatomy}')")
        return new_anatomy

    # Ensure that it's actually a ranged anatomy by verifying that the first
    # anatomy index is before the last anatomy index
    if first_anatomy_idx > last_anatomy_idx:
        first_anatomy = SEQUENCE_ANATOMY[first_anatomy_idx]
        last_anatomy = SEQUENCE_ANATOMY[last_anatomy_idx]
        raise ValueError(
            f"Ranged anatomy does not conform to sequence. First anatomy "
            f"index ('{first_anatomy_idx}') is greater than last anatomy "
            f"index ('{last_anatomy_idx}'). "
            f"First anatomy ('{first_anatomy}') should come before last "
            f"anatomy ('{last_anatomy}') to conform to SEQUENCE_ANATOMY:"
            f"{SEQUENCE_ANATOMY}"
        )

    # Get the sequence anatomy if it passes all tests
    new_anatomy = SEQUENCE_ANATOMY[first_anatomy_idx:last_anatomy_idx + 1]

    return new_anatomy


def get_anatomy_from_label(label: str):
    """
    Returns a list of anatomy classifications.

    Tries to get a ranged anatomy if 'to' is found in the label. If no
    ranged anatomy is found, it re-attempts to classify using the entire label.

    Parameters
    ----------
    label (str): a label that might contain anatomy information.

    Examples/Tests
    --------------
    # Return ncap, even if 'to' is found in label. FUTURE: this is
    # non-deterministic. ncap is returned, but returned list is never sorted
    # correctly. Fix in future.
    get_anatomy_from_label("NCAP to some_other_thing")
    ['Chest', 'Neck', 'Abdomen', 'Pelvis']

    # Return head
    >>> get_anatomy_from_label("Head is here")
    ['Head']
    """
    new_anatomy = []
    label_lower = label.lower()
    if is_to(label_lower):
        new_anatomy = get_ranged_anatomy(label)

    if not new_anatomy:
        new_anatomy = get_anatomy_classification(label)

    return new_anatomy


def get_anatomy_from_scan_coverage(scan_coverage):
    new_anatomy = []
    if is_head(scan_coverage):
        new_anatomy.append(['Head'])
    if is_whole_body(scan_coverage):
        new_anatomy.append(['Whole Body'])
    if is_cap(scan_coverage):
        new_anatomy.append(['Chest', 'Abdomen', 'Pelvis'])

    if new_anatomy:
        new_anatomy = reduce(add, new_anatomy)
        new_anatomy = list(set(new_anatomy))
    return new_anatomy


def get_contrast_classification(label):
    new_contrast = []

    ## Contrast
    if is_arterial(label):
        new_contrast.append(['Arterial Phase'])
    if is_portal_venous(label):
        new_contrast.append(['Portal Venous Phase'])
    if is_delayed_equil(label):
        new_contrast.append(['Delayed/Equilibrium Phase'])
    if is_unenhanced(label):
        new_contrast.append(['No Contrast'])
    elif is_enhanced(label):
        new_contrast.append(['Contrast'])
    
    if new_contrast:
        new_contrast = reduce(add, new_contrast)
        new_contrast = list(set(new_contrast)) 
    return new_contrast


def get_scan_orientation(label):
    scan_orientation = None
    if is_axial(label):
        scan_orientation = 'axial'
    elif is_coronal(label):
        scan_orientation = 'coronal'
    elif is_sagittal(label):
        scan_orientation = 'sagittal'

    if scan_orientation:
        return scan_orientation

    
def get_reconstruction_window(label):
    reconstruction_window = None
    if is_bone_window(label):
        reconstruction_window = 'Bone'
    elif is_lung_window(label):
        reconstruction_window = 'Lung'

    if reconstruction_window:
        return reconstruction_window

######################################################################################
######################################################################################

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
    classifications = {}
    info_object = {}
    
    if common_utils.is_localizer(acquisition.label) or common_utils.is_localizer(series_description) or len(df) < 10:
        classifications['Scan Type'] = ['Localizer']
    else:
        classifications['Scan Type'] = get_scan_type_classification(acquisition.label, header_dicom)
        if not classifications['Scan Type']:
            classifications['Scan Type'] = get_scan_type_classification(series_description, header_dicom)

        scan_coverage, info_object = \
            common_utils.compute_scan_coverage_if_original(header_dicom, df,
                                                           info_object)
        
        # # Reconstruction window
        reconstruction_window = None
        reconstruction_window = get_reconstruction_window(acquisition.label)
        if reconstruction_window:
            info_object['ReconstructionWindow'] = reconstruction_window
        
        # # Scan orientation 
        scan_orientation = None
        scan_orientation = get_scan_orientation(acquisition.label)
        if scan_orientation:
            info_object['ScanOrientation'] = scan_orientation
        else:
            scan_orientation = get_scan_orientation(series_description)
            if scan_orientation:
                info_object['ScanOrientation'] = scan_orientation

        # # Anatomy
        classifications['Anatomy'] = get_anatomy_from_label(acquisition.label)
        if not classifications['Anatomy']:
            classifications['Anatomy'] = get_anatomy_from_label(series_description)
        if not classifications['Anatomy']:
            classifications['Anatomy'] = get_anatomy_from_scan_coverage(scan_coverage)

        # # Contrast
        classifications['Contrast'] = get_contrast_classification(acquisition.label)
        if not classifications['Contrast']:
            classifications['Contrast'] = get_contrast_classification(series_description)

        if scan_coverage:
            spacing_between_slices = scan_coverage / len(df)
            info_object['SpacingBetweenSlices'] = round(spacing_between_slices, 2)
        
        dcm_metadata['info'].update(info_object)

    dcm_metadata['classification'] = classifications

    return dcm_metadata


if __name__ == "__main__":
    import doctest
    doctest.testmod()
