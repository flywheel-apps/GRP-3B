import logging
import re
from pprint import pformat
from functools import reduce
from operator import add

log = logging.getLogger(__name__)


SEQUENCE_ANATOMY = ['Head', 'Neck', 'Chest', 'Abdomen', 'Pelvis', 'Lower Extremities', 'Upper Extremities', 'Whole Body']


# Scan Coverage
def compute_scan_coverage(df):
    """
    Returns the scan coverage--the z-direction/axial direction range--of a
    set of images that are part of a scan.
    Scan coverage is typically computed for CT and PET GIP/Flywheel metadata.
    Params
    ------
    df: DataFrame
    A pandas DataFrame where each row is a dicom image header information.
    Examples/Tests
    --------------
    # Returns scan coverage computation by using dicom header info of slices
    >>> import pandas as pd
    >>> df = pd.DataFrame(pd.Series({0: [1, 2, 3.2], 1: [1, 2, 3.4]}, name='ImagePositionPatient'))
    >>> compute_scan_coverage(df)
    (0.19999999999999973, 3.4, 3.2)

    # Returns 'None' and warns "Some or all 'ImagePositionPatient' values of
    dicom slices are not length 3"
    >>> df = pd.DataFrame(pd.Series({0: [1, 2, 3], 1: [1, 2]}, name='ImagePositionPatient'))
    >>> compute_scan_coverage(df)
    
    # Returns 'None' and warns "Some or all 'ImagePositionPatient' values
    # of dicom slices are missing."
    >>> df = pd.DataFrame(pd.Series({0: None, 1: [1, 2, 3]}, name='ImagePositionPatient'))
    >>> compute_scan_coverage(df)
    
    # Returns 'None' and warns "Some or all 'ImagePositionPatient' values
    are not type 'list'"
    >>> df = pd.DataFrame(pd.Series({0: 'hi', 1: [1, 2, 3]}, name='ImagePositionPatient'))
    >>> compute_scan_coverage(df)
    
    # Returns 'None' and warns "Some or all 'ImagePositionPatient' z-axis
    values of dicom slices are not type 'float'."
    >>> df = pd.DataFrame(pd.Series({0: [1, 2, 3.2], 1: [1, 2, '3.5']}, name='ImagePositionPatient'))
    >>> compute_scan_coverage(df)
    
    # Returns 'None' and warns "'ImagePositionPatient' not in dataframe
    (dicom headers)."
    >>> df = {}
    >>> compute_scan_coverage(df)
    """
    
    log.info(
        f"Attempting to compute scan coverage..."
    )
    dicom_std_link = \
        "https://dicom.innolitics.com/ciods/pet-image/image-plane/00200032"
    if 'ImagePositionPatient' not in df.keys():
        log.error(
            f"Cannot compute scan coverage. 'ImagePositionPatient' not in "
            f"dataframe (dicom headers). This is required. See "
            f"{dicom_std_link}")
        return None

    image_positions = df['ImagePositionPatient']

    # Check if all image positions are not None. Log error.
    if not all(image_positions.isnull().apply(lambda x: not x)):
        log.error(
            f"Cannot compute scan coverage.. Some or all "
            f"'ImagePositionPatient' values of dicom slices "
            f"are missing. This is required. See {dicom_std_link}")
        return None
    # Check if all values are type list. Log type error if not.
    if not all(image_positions.apply(lambda x: type(x) == list)):
        log.error(
            f"Cannot compute scan coverage. Some or all "
            f"'ImagePositionPatient' values are not type 'list'.")
        return None
    # Check if all lists are at least length 3. Log missing
    # values error if not.
    if not all(image_positions.apply(lambda x: len(x) == 3)):
        log.error(
            f"Cannot compute scan coverage. Some or all "
            f"'ImagePositionPatient' values of dicom slices "
            f"are not length 3. This is required. See"
            f" {dicom_std_link}")
        return None
    # Check that all values in the z axis are type float
    if not all(image_positions.apply(lambda x:
                                 type(x[2]) == float)):
        log.error(
            f"Cannot compute scan coverage. Some or all "
            f"'ImagePositionPatient' z-axis values of dicom "
            f"slices are not type 'float'.")
        return None

    # Compute scan coverage if all conditions are met
    z_position = image_positions.apply(lambda x: x[2])
    result = z_position.max() - z_position.min()
    scan_coverage = result if result > 0 else result * -1
    log.info(
        f"Computed scan coverage ({scan_coverage})")

    return (scan_coverage, z_position.max(), z_position.min())


# Utility:  Check a list of regexes for truthyness
def regex_search_label(regexes, label):
    found = False
    if type(label) == str:
        if any(regex.search(label) for regex in regexes):
            found = True
    elif isinstance(label, list):
        if any(regex_search_label(regexes, item) for item in label):
            found = True
    return found


# Localizer
def is_localizer(label):
    regexes = [
        re.compile('localizer', re.IGNORECASE),
        re.compile('localiser', re.IGNORECASE),
        re.compile('survey', re.IGNORECASE),
        re.compile('loc\.', re.IGNORECASE),
        re.compile(r'\bscout\b', re.IGNORECASE),
        re.compile('(?=.*plane)(?=.*loc)', re.IGNORECASE),
        re.compile('(?=.*plane)(?=.*survey)', re.IGNORECASE),
        re.compile('3-plane', re.IGNORECASE),
        re.compile('^loc*', re.IGNORECASE),
        re.compile('Scout', re.IGNORECASE),
        re.compile('AdjGre', re.IGNORECASE),
        re.compile('topogram', re.IGNORECASE)
        ]
    return regex_search_label(regexes, label)


def compute_scan_coverage_if_original(header_dicom, df, info_object):

    """
    Computes the scan coverage of a scan (e.g., PET or CT) only if the image
    type is 'ORIGINAL', otherwise returns 'None' and the value of the passed
    parameter 'info_object'.
    Parameters
    ----------
    header_dicom: dict
        The dicom header of a dicom image, usually retrieved from dicom
        metadata 'dcm_metadata' (e.g., dcm_metadata['info']['header'][
        'dicom']).
    df: DataFrame
        A pandas DataFrame where each row is a dicom image header information.
    info_object: dict
        The custom information dictionary (i.e., 'info') of a Flywheel/GIP
        object. This dictionary is stored in the dicom metadata dictionary (
        e.g., 'dcm_metadata'), along with the 'classification' dictionary.
    Examples/Tests
    --------------
    # Returns computed 'scan_coverage' and updated 'info_object'
    >>> import pandas as pd
    >>> info_object = {}
    >>> df = pd.DataFrame(pd.Series({0: [1, 2, 3.2], 1: [1, 2, 3.4]},
    ...     name='ImagePositionPatient'))
    >>> header_dicom = {'ImageType': ['ORIGINAL']}
    >>> compute_scan_coverage_if_original(header_dicom, df, info_object)
    (0.19999999999999973, {'ScanCoverage': 0.19999999999999973, 'MaxSliceLocation': 3.4, 'MinSliceLocation': 3.2})
    
    # Returns 'None' for 'scan_coverage' and the value of the passed
    'info_object', and it throws "Dicom header not 'ORIGINAL' or 'DERIVED'"
    warning
    >>> header_dicom = {'ImageType': ['Not_Orig_Der']}
    >>> compute_scan_coverage_if_original(header_dicom, df, info_object)
    (None, {'ScanCoverage': 0.19999999999999973, 'MaxSliceLocation': 3.4, 'MinSliceLocation': 3.2})
    
    # Returns 'None' for 'scan_coverage' and the value of the passed
    'info_object', and it throws "Could not find 'ImageType' in dicom header"
    warning
    >>> header_dicom = {'NoImageType': []}
    >>> compute_scan_coverage_if_original(header_dicom, df, info_object)
    (None, {'ScanCoverage': 0.19999999999999973, 'MaxSliceLocation': 3.4, 'MinSliceLocation': 3.2})
    
    # Raises 'TypeError', since 'ImageType' value in header_dicom should be
    # a list.
    >>> header_dicom = {"ImageType": 'ORIGINAL'}
    >>> compute_scan_coverage_if_original(header_dicom, df, info_object)
    Traceback (most recent call last):
        ...
    TypeError: Cannot determine if scan coverage should be computed. Dicom header 'ImageType' is not a list, type is <class 'str'>). Try re-running latest GRP-3 metadata import and validation gear.
    
    # Returns 'None' for 'scan_coverage' and the value of the passed
    'info_object', and it logs the info "Cannot compute scan coverage.
    'ImageType' is 'DERIVED'".
    >>> header_dicom = {"ImageType": ['DERIVED']}
    >>> compute_scan_coverage_if_original(header_dicom, df, info_object)
    (None, {'ScanCoverage': 0.19999999999999973, 'MaxSliceLocation': 3.4, 'MinSliceLocation': 3.2})
    
    """

    log.info(
        f"Checking if header 'ImageType' == 'ORIGINAL' to determine if scan "
        f"coverage should be computed..."
    )

    # Check for ImageType, which is always at the 0'd index and either
    # 'ORIGINAL' or 'DERIVED'
    dicom_std_link = \
        "https://dicom.innolitics.com/ciods/cr-image/general-image/00080008"
    image_type = header_dicom.get('ImageType')

    # Check if empty
    if not image_type:
        log.warning(
            f"Cannot determine if scan coverage should be computed. Could "
            f"not find 'ImageType' in dicom header {header_dicom}"
        )
        return None, info_object

    # Check type is list
    if (type(image_type) is not list):
        # Throw error
        raise TypeError(
            f"Cannot determine if scan coverage should be computed. "
            f"Dicom header 'ImageType' is not a list, type is "
            f"{type(image_type)}). Try re-running latest GRP-3 "
            f"metadata import and validation gear.")

    # Check if it's 'DERIVED'
    if (image_type[0] == 'DERIVED'):
        log.info(f"Cannot compute scan coverage. 'ImageType' is "
                 f"{image_type[0]}")
        return None, info_object

    # Check if it's anything other than original, since we already checked
    # 'DERIVED' 'ORIGINAL'
    if (image_type[0] != 'ORIGINAL'):   # Not sure why it requires the
                                        # parentheses on Flywheel...but doesn't
                                        # work if removed...seems like
                                        # Python version used in Docker may
                                        # be different
        log.error(
            f"Cannot determine if scan coverage should be computed. "
            f"Dicom header 'ImageType[0]' ({image_type[0]}) is not "
            f"'ORIGINAL' or 'DERIVED'. See {dicom_std_link}"
        )
        return None, info_object

    # Compute if all checks are passed
    (scan_coverage, max_slice_location, min_slice_location) = compute_scan_coverage(df)

    if scan_coverage:
        info_object['ScanCoverage'] = scan_coverage
    if max_slice_location:
        info_object['MaxSliceLocation'] = max_slice_location
    if min_slice_location:
        info_object['MinSliceLocation'] = min_slice_location


    return scan_coverage, info_object


# -----------------------------------------------------------------------------
# sub methods for get_scan_type_classification()
# -----------------------------------------------------------------------------
# Standard Scan
def is_standard_scan(description):
    regexes = [
        re.compile('\\bNAC', re.IGNORECASE),
        re.compile('NAC\\b', re.IGNORECASE),
        re.compile('_NAC', re.IGNORECASE),
        re.compile('NAC_', re.IGNORECASE)
    ]
    return regex_search_label(regexes, description)


# Attenuation Corrected Scan
def is_attn_corr_scan(description):
    regexes = [
        re.compile('\\bAC', re.IGNORECASE),
        re.compile('AC\\b', re.IGNORECASE),
        re.compile('_AC', re.IGNORECASE),
        re.compile('^AC_', re.IGNORECASE)
    ]
    return regex_search_label(regexes, description)


# -----------------------------------------------------------------------------
# sub methods for get_scan_orientation()
# -----------------------------------------------------------------------------
# Scan Orientation, Axial
def is_axial(description):
    regexes = [
        re.compile('axial', re.IGNORECASE),
        re.compile('trans', re.IGNORECASE)
    ]
    return regex_search_label(regexes, description)


# Scan Orientation, Coronal
def is_coronal(description):
    regexes = [
        re.compile('cor', re.IGNORECASE)
    ]
    return regex_search_label(regexes, description)


# Scan Orientation, Sagittal
def is_sagittal(description):
    regexes = [
        re.compile('sag', re.IGNORECASE)
    ]
    return regex_search_label(regexes, description)


# -----------------------------------------------------------------------------
# Check aggregate anatomy
# -----------------------------------------------------------------------------

# Aggregate Anatomy
def is_cap_label(description):
    regexes = [
        re.compile('(c.?a.?p)', re.IGNORECASE)
    ]
    return regex_search_label(regexes, description)


def is_ncap_label(description):
    regexes = [
        re.compile('(n.?c.?a.?p)', re.IGNORECASE)
    ]
    return regex_search_label(regexes, description)


def is_hcap_label(description):
    regexes = [
        re.compile('(h.?c.?a.?p)', re.IGNORECASE)
    ]
    return regex_search_label(regexes, description)


def is_hn_label(description):
    regexes = [
        re.compile('(^|[^a-zA-Z])hn([^a-zA-Z]|$)', re.IGNORECASE)
    ]
    return regex_search_label(regexes, description)


def is_neck_lower_label(description):
    regexes = [
        re.compile('Neck w\^IV lower', re.IGNORECASE),
        re.compile('Neck lower', re.IGNORECASE),
        re.compile('(neck.?lower)', re.IGNORECASE)
    ]
    return regex_search_label(regexes, description)


def is_neck_upper_label(description):
    regexes = [
        re.compile('Neck w\^IV upper', re.IGNORECASE),
        re.compile('Neck upper', re.IGNORECASE),
        re.compile('(neck.?upper)', re.IGNORECASE)
    ]
    return regex_search_label(regexes, description)


# -----------------------------------------------------------------------------
# Scan Coverage ranges
# -----------------------------------------------------------------------------
# Anatomy, Head (Scan Coverage)
def is_head(scan_coverage):
    return scan_coverage is not None and scan_coverage < 250


# Anatomy, Whole Body (Scan Coverage)
def is_whole_body(scan_coverage):
    return scan_coverage is not None and scan_coverage > 1300


# Anatomy, C/A/P (Scan Coverage)
def is_cap(scan_coverage):
    return scan_coverage is not None and scan_coverage > 800 and scan_coverage < 1300


# -----------------------------------------------------------------------------
# Check anatomy labels
# -----------------------------------------------------------------------------
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
    return regex_search_label(regexes, description)


# Anatomy, Head
def is_head_label(description):
    regexes = [
        re.compile('head', re.IGNORECASE),
        re.compile('brain', re.IGNORECASE)
    ]
    return regex_search_label(regexes, description)


# Anatomy, Neck
def is_neck_label(description):
    regexes = [
        re.compile('neck', re.IGNORECASE),
        re.compile('cervical', re.IGNORECASE),
        re.compile('hals', re.IGNORECASE)
    ]
    return regex_search_label(regexes, description)


# Anatomy, Chest
def is_chest_label(description):
    regexes = [
        re.compile('chest', re.IGNORECASE),
        re.compile('lung', re.IGNORECASE),
        re.compile('thorax', re.IGNORECASE),
        re.compile('thoracic', re.IGNORECASE),
        re.compile('thoracicspine', re.IGNORECASE)
    ]
    return regex_search_label(regexes, description)


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
    return regex_search_label(regexes, description)


# Anatomy, Pelvis
def is_pelvis_label(description):
    regexes = [
        re.compile('pel', re.IGNORECASE),
        re.compile('(^|[^a-zA-Z])pv([^a-zA-Z]|$)', re.IGNORECASE)
    ]
    return regex_search_label(regexes, description)


# Anatomy, Lower Extremities
def is_lower_extremities(description):
    regexes = [
        re.compile('(^|[^a-zA-Z])le([^a-zA-Z]|$)', re.IGNORECASE),
        re.compile('(lower.?extremity)', re.IGNORECASE),
        re.compile('(lower.?extremities)', re.IGNORECASE)
    ]
    return regex_search_label(regexes, description)


# Anatomy, Upper Extremities
def is_upper_extremities(description):
    regexes = [
        re.compile('(^|[^a-zA-Z])ue([^a-zA-Z]|$)', re.IGNORECASE),
        re.compile('(upper.?extremity)', re.IGNORECASE),
        re.compile('(upper.?extremities)', re.IGNORECASE)
    ]
    return regex_search_label(regexes, description)


# Anatomy, Whole Body
def is_whole_body_label(description):
    regexes = [
        re.compile('whole', re.IGNORECASE),
        re.compile('(^|[^a-zA-Z])wb([^a-zA-Z]|$)', re.IGNORECASE),
        re.compile('body', re.IGNORECASE),
        re.compile('eyes.?to.?thighs', re.IGNORECASE),
        re.compile('eye.?to.?thigh', re.IGNORECASE)
    ]
    return regex_search_label(regexes, description)


# -----------------------------------------------------------------------------
# Check Reconstruction Window
# -----------------------------------------------------------------------------
# Reconstruction Window, Bone
def is_bone_window(description):
    regexes = [
        re.compile('(bone.?window)', re.IGNORECASE)
    ]
    return regex_search_label(regexes, description)


# Reconstruction Window, Lung
def is_lung_window(description):
    regexes = [
        re.compile('(lung.?window)', re.IGNORECASE)
    ]
    return regex_search_label(regexes, description)


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
    return regex_search_label(regexes, description)


# -----------------------------------------------------------------------------
# Check Contrast
# -----------------------------------------------------------------------------
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
    return regex_search_label(regexes, description)


# Contrast, Arterial Phase
def is_arterial(description):
    regexes = [
        re.compile('arterial', re.IGNORECASE),
    ]
    return regex_search_label(regexes, description)


# Contrast, Portal Venous Phase
def is_portal_venous(description):
    regexes = [
        re.compile('portal', re.IGNORECASE),
        re.compile('venous', re.IGNORECASE)
    ]
    return regex_search_label(regexes, description)


# Contrast, Delayed Phase
def is_delayed_equil(description):
    regexes = [
        re.compile('delayed', re.IGNORECASE),
        re.compile('equil', re.IGNORECASE)
    ]
    return regex_search_label(regexes, description)


# -----------------------------------------------------------------------------
# Higher order anatomy classification functions
# FUTURE: put these in AnatomyClassifier class
# -----------------------------------------------------------------------------
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
    if is_neck_label(label) and not is_neck_lower_label(
        label) and not is_neck_upper_label(label):
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
    if is_whole_body_label(label):
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
        log.warning(
            f"Could not create first anatomy from label "
            f"'{split_label[idx - 1]}'. Got '{first_anatomy}'")
        return None
    first_anatomy = reduce(add, first_anatomy)
    if first_anatomy not in SEQUENCE_ANATOMY:
        log.warning(
            f"Could not find first anatomy '{first_anatomy}' in ranged "
            f"anatomy search. Anatomy must be one of the following:\n"
            f"{pformat(SEQUENCE_ANATOMY)}")
        return None

    first_anatomy_idx = SEQUENCE_ANATOMY.index(first_anatomy)

    # classify the second ranged anatomy (right of 'to')
    last_anatomy = get_anatomy_classification(split_label[idx + 1])
    if not last_anatomy:
        log.warning(
            f"Could not create second anatomy from label "
            f"'{split_label[idx + 1]}'. Got '{last_anatomy}'")
        return None
    last_anatomy = reduce(add, last_anatomy)
    if last_anatomy not in SEQUENCE_ANATOMY:
        log.warning(
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


def classify_anatomy(classification, acquisition, series_description,
                     scan_coverage):

    log.info("Attempting to get anatomy classification from acquisition "
             "label...")
    anatomy_classification = get_anatomy_from_label(acquisition.label)

    if not anatomy_classification:
        log.info("Could not classify. Attempting to classify from series "
                 "description...")
        anatomy_classification = get_anatomy_from_label(series_description)

    if not anatomy_classification:
        log.info("Could not classify. Attempting to classify from scan "
                 "coverage...")
        anatomy_classification = get_anatomy_from_scan_coverage(scan_coverage)

    if anatomy_classification:
        log.info(f"Classified as {anatomy_classification}")
    else:
        anatomy_classification = []
        log.info(f"Could not classify. Set anatomy classification to "
                 f"'{anatomy_classification}'")

    classification['Anatomy'] = anatomy_classification
    return classification


# -----------------------------------------------------------------------------
# Higher order CT scan classification functions
# FUTURE: put these in a class
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# Higher order contrast classification function for CT
# FUTURE: put this in a class
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# Custom info reconstruction window function for CT classification
# FUTURE: put this in a class
# -----------------------------------------------------------------------------
def get_reconstruction_window(label):
    reconstruction_window = None
    if is_bone_window(label):
        reconstruction_window = 'Bone'
    elif is_lung_window(label):
        reconstruction_window = 'Lung'

    if reconstruction_window:
        return reconstruction_window


if __name__ == "__main__":
    import doctest
    doctest.testmod()
