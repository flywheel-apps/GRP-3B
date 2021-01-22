"""MR classification"""
import os
import json
import re
from fnmatch import fnmatch
import dicom_processor
import common_utils
import logging

log = logging.getLogger(__name__)


def feature_check(label):
    """Check the label for a list of features.

    Args:
        label (str): String to regexp match with element of feature_list

    Returns:
        list: List of feature_list elements that regex matched with label
    """

    feature_list = ['2D', 'AAscout', 'Spin-Echo', 'Gradient-Echo',
                   'EPI', 'WASSR', 'FAIR', 'FAIREST', 'PASL', 'EPISTAR',
                   'PICORE', 'pCASL', 'MPRAGE', 'MP2RAGE', 'FLAIR',
                   'SWI', 'QSM', 'RMS', 'DTI', 'DSI', 'DKI', 'HARDI',
                   'NODDI', 'Water-Reference', 'Transmit-Reference',
                   'SBRef', 'Uniform', 'Singlerep', 'QC', 'TRACE',
                   'FA', 'MIP', 'Navigator', 'Contrast-Agent',
                   'Phase-Contrast', 'TOF', 'VASO', 'iVASO', 'DSC',
                   'DCE', 'Task', 'Resting-State', 'PRESS', 'STEAM',
                   'M0', 'Phase-Reversed', 'Spiral', 'SPGR',
                   'Quantitative', 'Multi-Shell', 'Multi-Echo', 'Multi-Flip',
                   'Multi-Band', 'Steady-State', '3D', 'Compressed-Sensing',
                   'Eddy-Current-Corrected', 'Fieldmap-Corrected',
                   'Gradient-Unwarped', 'Motion-Corrected', 'Physio-Corrected',
                   'Derived', 'In-Plane', 'Phase', 'Magnitude']

    return _find_matches(label, feature_list)


def measurement_check(label):
    """Check the label for a list of measurements.

    Args:
        label (str): String to regexp match with element of measurement_list

    Returns:
        list: List of measurement_list elements that regex matched with label
    """

    measurement_list = ['MRA', 'CEST', 'T1rho', 'SVS', 'CSI', 'EPSI', 'BOLD',
                        'Phoenix','B0', 'B1', 'T1', 'T2', 'T2*', 'PD', 'MT',
                        'Perfusion','Diffusion', 'Susceptibility', 'Fingerprinting']

    return _find_matches(label, measurement_list)


def intent_check(label):
    """Check the label for a list of intents.

    Args:
        label (str): String to regexp match with element of intent_list

    Returns:
        list: List of intent_list elements that regex matched with label
    """

    intent_list = [ 'Localizer',
                    'Shim',
                    'Calibration',
                    'Fieldmap',
                    'Structural',
                    'Functional',
                    'Screenshot',
                    'Non-Image',
                    'Spectroscopy' ]

    return _find_matches(label, intent_list)


def _find_matches(label, in_list):
    """For a given list find those entries that match a given label."""

    matches = []

    for l in in_list:
        regex = _compile_regex(l)
        if regex.findall(label):
            matches.append(l)

    return matches


def _compile_regex(string):
    """Generate the regex for label checking"""
    # Escape * for T2*
    if string == 'T2*':
        string = 'T2\*'
        regex = re.compile(r"(\b%s\b)|(_%s_)|(_%s)|(%s_)|(%s)|(t2star)" % (string, string,string,string,string), re.IGNORECASE)
    # Prevent T2 from capturing T2*
    elif string == 'T2':
        string = '(?!T2\*)T2'
        regex = re.compile(r"(\b%s\b)|(_%s_)|(_%s)|(%s_)" % (string,string,string,string), re.IGNORECASE)
    else:
        regex = re.compile(r"(\b%s\b)|(_%s_)|(_%s)|(%s_)" % (string,string,string,string), re.IGNORECASE)
    return regex


# Anatomy, T1
def is_anatomy_t1(label):
    regexes = [
        re.compile('t1', re.IGNORECASE),
        re.compile('t1w', re.IGNORECASE),
        re.compile('(?=.*3d anat)(?![inplane])', re.IGNORECASE),
        re.compile('(?=.*3d)(?=.*bravo)(?![inplane])', re.IGNORECASE),
        re.compile('spgr', re.IGNORECASE),
        re.compile('tfl', re.IGNORECASE),
        re.compile('mprage', re.IGNORECASE),
        re.compile('(?=.*mm)(?=.*iso)', re.IGNORECASE),
        re.compile('(?=.*mp)(?=.*rage)', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, label)

# Anatomy, T2
def is_anatomy_t2(label):
    regexes = [
        re.compile('t2', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, label)

# Aanatomy, Inplane
def is_anatomy_inplane(label):
    regexes = [
        re.compile('inplane', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, label)

# Anatomy, other
def is_anatomy(label):
    regexes = [
        re.compile('(?=.*IR)(?=.*EPI)', re.IGNORECASE),
        re.compile('flair', re.IGNORECASE)
    ]
    return common_utils.regex_search_label(regexes, label)

# Diffusion
def is_diffusion(label):
    regexes = [
        re.compile('dti', re.IGNORECASE),
        re.compile('dwi', re.IGNORECASE),
        re.compile('diff_', re.IGNORECASE),
        re.compile('diffusion', re.IGNORECASE),
        re.compile('(?=.*diff)(?=.*dir)', re.IGNORECASE),
        re.compile('hardi', re.IGNORECASE)
        ]
    return common_utils.regex_search_label(regexes, label)

# Diffusion - Derived
def is_diffusion_derived(label):
    regexes = [
        re.compile('_ADC$', re.IGNORECASE),
        re.compile('_TRACEW$', re.IGNORECASE),
        re.compile('_ColFA$', re.IGNORECASE),
        re.compile('_FA$', re.IGNORECASE),
        re.compile('_EXP$', re.IGNORECASE)
        ]
    return common_utils.regex_search_label(regexes, label)

# Functional
def is_functional(label):
    regexes = [
        re.compile('functional', re.IGNORECASE),
        re.compile('fmri', re.IGNORECASE),
        re.compile('func', re.IGNORECASE),
        re.compile('bold', re.IGNORECASE),
        re.compile('resting', re.IGNORECASE),
        re.compile('(?=.*rest)(?=.*state)', re.IGNORECASE),
        # NON-STANDARD
        re.compile('(?=.*ret)(?=.*bars)', re.IGNORECASE),
        re.compile('(?=.*ret)(?=.*wedges)', re.IGNORECASE),
        re.compile('(?=.*ret)(?=.*rings)', re.IGNORECASE),
        re.compile('(?=.*ret)(?=.*check)', re.IGNORECASE),
        re.compile('go-no-go', re.IGNORECASE),
        re.compile('words', re.IGNORECASE),
        re.compile('checkers', re.IGNORECASE),
        re.compile('retinotopy', re.IGNORECASE),
        re.compile('faces', re.IGNORECASE),
        re.compile('rings', re.IGNORECASE),
        re.compile('wedges', re.IGNORECASE),
        re.compile('emoreg', re.IGNORECASE),
        re.compile('conscious', re.IGNORECASE),
        re.compile('^REST$'),
        re.compile('ep2d', re.IGNORECASE),
        re.compile('task', re.IGNORECASE),
        re.compile('rest', re.IGNORECASE),
        re.compile('fBIRN', re.IGNORECASE),
        re.compile('^Curiosity', re.IGNORECASE),
        re.compile('^DD_', re.IGNORECASE),
        re.compile('^Poke', re.IGNORECASE),
        re.compile('^Effort', re.IGNORECASE),
        re.compile('emotion|conflict', re.IGNORECASE)
        ]
    return common_utils.regex_search_label(regexes, label)

# Functional, Derived
def is_functional_derived(label):
    regexes = [
        re.compile('mocoseries', re.IGNORECASE),
        re.compile('GLM$', re.IGNORECASE),
        re.compile('t-map', re.IGNORECASE),
        re.compile('design', re.IGNORECASE),
        re.compile('StartFMRI', re.IGNORECASE)
        ]
    return common_utils.regex_search_label(regexes, label)

# Shim
def is_shim(label):
    regexes = [
        re.compile('(?=.*HO)(?=.*shim)', re.IGNORECASE), # Contians 'ho' and 'shim'
        re.compile(r'\bHOS\b', re.IGNORECASE),
        re.compile('_HOS_', re.IGNORECASE),
        re.compile('.*shim', re.IGNORECASE)
        ]
    return common_utils.regex_search_label(regexes, label)

# Fieldmap
def is_fieldmap(label):
    regexes = [
        re.compile('(?=.*field)(?=.*map)', re.IGNORECASE),
        re.compile('(?=.*bias)(?=.*ch)', re.IGNORECASE),
        re.compile('field', re.IGNORECASE),
        re.compile('fmap', re.IGNORECASE),
        re.compile('topup', re.IGNORECASE),
        re.compile('DISTORTION', re.IGNORECASE),
        re.compile('se[-_][aprl]{2}$', re.IGNORECASE)
        ]
    return common_utils.regex_search_label(regexes, label)

# Calibration
def is_calibration(label):
    regexes = [
        re.compile('(?=.*asset)(?=.*cal)', re.IGNORECASE),
        re.compile('^asset$', re.IGNORECASE),
        re.compile('calibration', re.IGNORECASE)
        ]
    return common_utils.regex_search_label(regexes, label)

# Coil Survey
def is_coil_survey(label):
    regexes = [
        re.compile('(?=.*coil)(?=.*survey)', re.IGNORECASE)
        ]
    return common_utils.regex_search_label(regexes, label)

# Perfusion: Arterial Spin Labeling
def is_perfusion(label):
    regexes = [
        re.compile('asl', re.IGNORECASE),
        re.compile('(?=.*blood)(?=.*flow)', re.IGNORECASE),
        re.compile('(?=.*art)(?=.*spin)', re.IGNORECASE),
        re.compile('tof', re.IGNORECASE),
        re.compile('perfusion', re.IGNORECASE),
        re.compile('angio', re.IGNORECASE),
        ]
    return common_utils.regex_search_label(regexes, label)

# Proton Density
def is_proton_density(label):
    regexes = [
        re.compile('^PD$'),
        re.compile('(?=.*proton)(?=.*density)', re.IGNORECASE),
        re.compile('pd_'),
        re.compile('_pd')
        ]
    return common_utils.regex_search_label(regexes, label)

# Phase Map
def is_phase_map(label):
    regexes = [
        re.compile('(?=.*phase)(?=.*map)', re.IGNORECASE),
        re.compile('^phase$', re.IGNORECASE)
        ]
    return common_utils.regex_search_label(regexes, label)

# Screen Save / Screenshot
def is_screenshot(label):
    regexes = [
        re.compile('(?=.*screen)(?=.*save)', re.IGNORECASE),
        re.compile('.*screenshot', re.IGNORECASE),
        re.compile('.*screensave', re.IGNORECASE)
        ]
    return common_utils.regex_search_label(regexes, label)

# Spectroscopy
def is_spectroscopy(label):
    regexes = [
        re.compile('mip', re.IGNORECASE),
        re.compile('mrs', re.IGNORECASE),
        re.compile('svs', re.IGNORECASE),
        re.compile('gaba', re.IGNORECASE),
        re.compile('csi', re.IGNORECASE),
        re.compile('nfl', re.IGNORECASE),
        re.compile('mega', re.IGNORECASE),
        re.compile('press', re.IGNORECASE),
        re.compile('spect', re.IGNORECASE)
        ]
    return common_utils.regex_search_label(regexes, label)

# Post in Series Description
def is_post(label):
    found = False
    if type(label) == str:
        if re.search('POST', label, flags=re.IGNORECASE):
            found = True
    elif isinstance(label, list):
        if any(is_post(item) for item in label):
            found = True
    return found

# Susceptibility Weighted
def is_swi(label):
    regexes = [
        re.compile('swi', re.IGNORECASE),
        re.compile('susceptibility', re.IGNORECASE),
        ]
    return common_utils.regex_search_label(regexes, label)


def infer_classification(label):
    """
    Get classification based on acquisition label
    """
    if not label:
        return {}
    else:
        classification = {}
        if is_anatomy_inplane(label):
            classification['Intent'] = ['Structural']
            classification['Measurement'] = ['T1']
            classification['Features'] = ['In-Plane']
        elif is_fieldmap(label):
            classification['Intent'] = ['Fieldmap']
            classification['Measurement'] = ['B0']
        elif is_diffusion_derived(label):
            classification['Intent'] = ['Structural']
            classification['Measurement'] = ['Diffusion']
            classification['Features'] = ['Derived']
        elif is_diffusion(label):
            classification['Intent'] = ['Structural']
            classification['Measurement'] = ['Diffusion']
        elif is_functional_derived(label):
            classification['Intent'] = ['Functional']
            classification['Features'] = ['Derived']
        elif is_functional(label):
            classification['Intent'] = ['Functional']
            classification['Measurement'] = ['T2*']
        elif is_anatomy_t1(label):
            classification['Intent'] = ['Structural']
            classification['Measurement'] = ['T1']
        elif is_anatomy_t2(label):
            classification['Intent'] = ['Structural']
            classification['Measurement'] = ['T2']
        elif is_anatomy(label):
            classification['Intent'] = ['Structural']
        elif is_swi(label):
            classification['Intent'] = ['Structural']
            classification['Measurement'] = ['Susceptibility']
        elif common_utils.is_localizer(label):
            classification['Intent'] = ['Localizer']
            classification['Measurement'] = ['T2']
        elif is_shim(label):
            classification['Intent'] = ['Shim']
        elif is_calibration(label):
            classification['Intent'] = ['Calibration']
        elif is_coil_survey(label):
            classification['Intent'] = ['Calibration']
            classification['Measurement'] = ['B1']
        elif is_proton_density(label):
            classification['Intent'] = ['Structural']
            classification['Measurement'] = ['PD']
        elif is_perfusion(label):
            classification['Measurement'] = ['Perfusion']
        elif is_spectroscopy(label):
            classification['Intent'] = ['Spectroscopy']
        elif is_phase_map(label):
            classification['Custom'] = ['Phase Map']
        elif is_screenshot(label):
            classification['Intent'] = ['Screenshot']
        else:
            print(label.strip('\n') + ' --->>>> unknown')

        # Add features to classification
        features = feature_check(label)
        if features:
            class_features = classification.get('Features', [])
            [class_features.append(x) for x in features if x not in class_features]
            classification['Features'] = class_features

        # Add measurements to classification
        measurements = measurement_check(label)
        if measurements:
            class_measurement = classification.get('Measurement', [])
            [class_measurement.append(x) for x in measurements if x not in class_measurement]
            classification['Measurement'] = class_measurement

        # Add intents to classification
        intents = intent_check(label)
        if intents:
            class_intent = classification.get('Intent', [])
            [class_intent.append(x) for x in intents if x not in class_intent]
            classification['Intent'] = class_intent

    return classification



def get_param_classification(dcm, slice_number, unique_iop):
    """
    Get classification based on imaging parameters in DICOM header.
    """
    classification_dict = {}
    log.info('Attempting to deduce classification from imaging prameters...')
    
    tr = dcm.get('RepetitionTime')
    te = dcm.get('EchoTime')
    ti = dcm.get('InversionTime')
    sd = dcm.get('SeriesDescription')

    # Log empty parameters
    if not isinstance(tr, (int, float)):
        tr = None
        log.warning('RepetitionTime unset')
    else:
        log.info('tr=%s' % str(tr))
        
    if not isinstance(te, (int, float)):
        te = None
        log.warning('EchoTime unset')
    else:
        log.info('te=%s' % str(te))
        
    if not isinstance(ti, (int, float)):
        ti = None
        log.warning('InversionTime unset')
    else:
        log.info('ti=%s' % str(ti))
        
    if not sd:
        log.warning('SeriesDescription unset')
    else:
        log.info('sd=%s' % str(sd))

    if (te and te < 30) and (tr and tr < 800):
        classification_dict['Measurement'] = ["T1"]
        log.info('(te and te < 30) and (tr and tr < 800) -- T1 Measurement')
        
    elif (te and te  > 50) and (tr and tr > 2000) and (not ti or ti == 0):
        classification_dict['Measurement'] = ["T2"]
        log.info('(te and te  > 50) and (tr and tr > 2000) and (not ti or ti == 0) -- T2 Measurement')
        
    elif (ti and (ti > 0)):
        classification_dict['Features'] = ["FLAIR"]
        log.info('(ti and (ti > 0)) -- FLAIR Features')
        
    elif (te and te  < 50) and (tr and tr > 1000):
        classification_dict['Measurement'] = ["PD"]
        log.info('(te and te  < 50) and (tr and tr > 1000) -- PD Measurement')


    if is_post(sd):
        classification_dict['Custom'] = ['Contrast']
        log.info('POST found in Series Description -- Adding Contrast to custom classification')
        

    if slice_number and slice_number < 10:
        classification_dict['Intent'] = ['Localizer']
        log.info('slice_number and slice_number < 10 -- Localizer Intent')
        

    if unique_iop:
        classification_dict['Intent'] = ['Localizer']
        log.info('unique_iop found -- Localizer')
        

    if not classification_dict:
        log.warning('Could not determine classification based on parameters!')
        
    else:
        log.info('Inferred classification from parameters: %s', classification_dict)
        

    return classification_dict



def get_classification_from_string(value):
    result = {}

    parts = re.split(r'\s*,\s*', value)
    last_key = None
    for part in parts:
        key_value = re.split(r'\s*:\s*', part)

        if len(key_value) == 2:
            last_key = key = key_value[0]
            value = key_value[1]
        else:
            if last_key:
                key = last_key
            else:
                log.warning('Unknown classification format: {0}'.format(part))
                key = 'Custom'
            value = part

        if key not in result:
            result[key] = []

        result[key].append(value)

    return result



def get_custom_classification(label, config_file):
    """
    Get custom (context) based classification.
    """
    if config_file is None or not os.path.isfile(config_file):
        return None

    try:
        with open(config_file, 'r') as f:
            config = json.load(f)

        # Check custom classifiers
        classifications = config['inputs'].get('classifications', {}).get('value', {})
        if not classifications:
            log.debug('No custom classifications found in config...')
            
            return None

        if not isinstance(classifications, dict):
            log.warning('classifications must be an object!')
            
            return None

        for k in classifications.keys():
            val = classifications[k]

            if not isinstance(val, str):
                log.warning('Expected string value for classification key %s', k)
                
                continue

            if len(k) > 2 and k[0] == '/' and k[-1] == '/':
                # Regex
                try:
                    if re.search(k[1:-1], label, re.I):
                        log.debug('Matched custom classification for key: %s', k)
                        
                        return get_classification_from_string(val)
                except re.error:
                    log.exception('Invalid regular expression: %s', k)
                    
            elif fnmatch(label.lower(), k.lower()):
                log.debug('Matched custom classification for key: %s', k)

                return get_classification_from_string(val)

    except IOError:
        log.exception('Unable to load config file: %s', config_file)

    return None


def classify_dicom(dcm, slice_number, acquisition_label, unique_iop=None):
    """
    Generate a classification dict from DICOM header info.

    Classification logic is as follows:
     1. Check for custom (context) classification.
     2. Check for classification based on the acquisition label.
     3. Attempt to generate a classification based on the imaging params.

    When a classification is returned the logic cascade ends.
    """

    classification_dict = {}
    series_desc = dicom_processor.format_string(dcm.get('SeriesDescription', ''))

    if acquisition_label or series_desc:
        # 1. Custom classification from context
        classification_dict = get_custom_classification(acquisition_label, '/flywheel/v0/config.json')
        if not classification_dict and series_desc:    # acquisition_label gets precedence
            classification_dict = get_custom_classification(series_desc, '/flywheel/v0/config.json')
        if classification_dict:
            log.info('Custom classification from config: %s', classification_dict)

        # 2. Classification from SeriesDescription or acquisition_label
        if not classification_dict:
            if acquisition_label:
                classification_dict = infer_classification(acquisition_label)
            if not classification_dict and series_desc:    # acquisition_label gets precedence
                classification_dict = infer_classification(series_desc)
            if classification_dict:
                log.info('Inferred classification from label: %s', classification_dict)

    # 3. Classification from Imaging params
    if not classification_dict:
        classification_dict = get_param_classification(dcm, slice_number, unique_iop)

    return classification_dict


def convert_list_val_to_tuple(val):
    """Convert lists to tuples, otherwise return val"""
    return_val = val
    if isinstance(val, list):
        return_val = tuple([convert_list_val_to_tuple(x) for x in val])
    return return_val


def iop_is_unique(iop_series):
    """Determines whether valid ImageOrientationPatient values within the Series are unique"""
    is_unique = False
    # remove non-array values (ImageOrientationPatient should be 6 decimal strings)
    list_value_list = [x for x in iop_series.values if isinstance(x, list)]
    # convert values to tuples for hashing
    tuple_value_list = [convert_list_val_to_tuple(x) for x in list_value_list]
    # make sure we're not considering a single list to be a localizer
    if len(tuple_value_list) > 1:
        if len(tuple_value_list) == len(set(tuple_value_list)):
            is_unique = True
    return is_unique


def classify_MR(df, dcm, dcm_metadata, acquisition):
    """
    Classifies a MR dicom series
    """
    
    # Determine how many DICOM files are in directory
    slice_number = len(df)

    # Determine whether ImageOrientationPatient is unique for each image represented in the df
    if hasattr(df, 'ImageOrientationPatient') and len(df) > 1:
        uniqueiop = iop_is_unique(df.ImageOrientationPatient)
    else:
        uniqueiop = False
    # Classification (# Only set classification if the modality is MR)
    if dcm_metadata['modality'] == 'MR':
        log.info("Determining MR Classification...")
        classification = classify_dicom(dcm, slice_number, acquisition.get('label'), unique_iop=uniqueiop)
        
        if classification:
            dcm_metadata['classification'] = classification

    return dcm_metadata



