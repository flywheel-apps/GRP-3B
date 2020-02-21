import re
import string
import common_utils
from operator import add
from functools import reduce

SEQUENCE_ANATOMY = ['Head', 'Neck', 'Chest', 'Abdomen', 'Pelvis', 'Lower Extremity', 'Upper Extremity', 'Whole Body']
######################################################################################
######################################################################################
# Check 'to' in labels for ranged anatomy
def is_to(description):
    regexes = [
        re.compile('(^|[^a-zA-Z])to([^a-zA-Z]|$)', re.IGNORECASE)
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
# Anatomy, Lower Extremity
def is_lower_extremity(description):
    regexes = [
        re.compile('(^|[^a-zA-Z])le([^a-zA-Z]|$)', re.IGNORECASE),
        re.compile('(lower.?extremity)', re.IGNORECASE),
        re.compile('(lower.?extremities)', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, description)
# Anatomy, Upper Extremity
def is_upper_extremity(description):
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

######################################################################################
######################################################################################

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
        new_anatomy.append(['Neck', 'Chest'])
    if is_neck_upper_label(label):
        new_anatomy.append(['Head', 'Neck'])
    
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
    if is_lower_extremity(label):
        new_anatomy.append(['Lower Extremity'])
    if is_upper_extremity(label):
        new_anatomy.append(['Upper Extremity'])    
    if is_whole_body(label):
        new_anatomy.append(['Whole Body'])
    
    if new_anatomy:
        new_anatomy = reduce(add, new_anatomy)
        new_anatomy = list(set(new_anatomy))
    return new_anatomy


def get_ranged_anatomy(label):
    new_anatomy = []
    label_lower = label.lower()
    split_label = re.split(r"[^a-zA-Z0-9\s]|\s+", label_lower)
    idx = split_label.index('to')
    
    first_anatomy = get_anatomy_classification(split_label[idx-1])
    first_anatomy = reduce(add, first_anatomy)
    first_anatomy_idx = SEQUENCE_ANATOMY.index(first_anatomy)
    
    last_anatomy = get_anatomy_classification(split_label[idx+1])
    last_anatomy = reduce(add, last_anatomy)
    last_anatomy_idx = SEQUENCE_ANATOMY.index(last_anatomy)
    
    new_anatomy = SEQUENCE_ANATOMY[first_anatomy_idx:last_anatomy_idx+1]
    
    return new_anatomy


def get_anatomy_from_label(label):
    new_anatomy = []
    label_lower = label.lower()
    if is_to(label_lower):
        new_anatomy = get_ranged_anatomy(label)
    else:
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

######################################################################################
######################################################################################

def classify_PT(df, single_header_object, acquisition):
    '''
    Classifies a PT dicom series

    Args:
        df (DataFrame): A pandas DataFrame where each row is a dicom image header information
    Returns:
        dict: The dictionary for the PT classification
    '''
    series_description = single_header_object.get('SeriesDescription') or ''
    classifications = {}
    info_object = {}

    if common_utils.is_localizer(acquisition.label) or common_utils.is_localizer(series_description) or len(df) < 10:
        classifications['Scan Type'] = ['Localizer']
    else:
        scan_coverage = None
        if single_header_object['ImageType'][0] == 'ORIGINAL':
            scan_coverage = common_utils.compute_scan_coverage(df)
        if scan_coverage:
            info_object['ScanCoverage'] = scan_coverage

        # # Anatomy
        classifications['Anatomy'] = get_anatomy_from_label(acquisition.label)
        if not classifications['Anatomy']:
            classifications['Anatomy'] = get_anatomy_from_label(series_description)
        if not classifications['Anatomy']:
            classifications['Anatomy'] = get_anatomy_from_scan_coverage(scan_coverage)

    return classifications, info_object









