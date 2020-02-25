import os
import json
import re
from fnmatch import fnmatch
import dicom_processor
import common_utils

log = logging.getLogger(__name__)
#!/usr/bin/env python
'''
Infer acquisition classification by parsing the acquisition label.
'''

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



def infer_classification(label):
    '''
    Get classification based on acquisition label
    '''
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

    return classification



def get_param_classification(dcm, slice_number, unique_iop):
    '''
    Get classification based on imaging parameters in DICOM header.
    '''
    classification_dict = {}
    log.info('Attempting to deduce classification from imaging prameters...')
    
    tr = dcm.get('RepetitionTime')
    te = dcm.get('EchoTime')
    ti = dcm.get('InversionTime')
    sd = dcm.get('SeriesDescription')

    # Log empty parameters
    if not tr:
        log.warning('RepetitionTime unset')
        
    else:
        log.info('tr=%s' % str(tr))
        
    if not te:
        log.warning('EchoTime unset')
        
    else:
        log.info('te=%s' % str(te))
        
    if not ti:
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


    if re.search('POST', sd, flags=re.IGNORECASE):
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
    '''
    Get custom (context) based classification.
    '''
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



def classify_dicom(dcm, slice_number, unique_iop=''):
    '''
    Generate a classification dict from DICOM header info.

    Classification logic is as follows:
     1. Check for custom (context) classification.
     2. Check for classification based on the acquisition label.
     3. Attempt to generate a classification based on the imaging params.

    When a classification is returned the logic cascade ends.
    '''

    classification_dict = {}
    series_desc = dicom_processor.format_string(dcm.get('SeriesDescription', ''))

    # 1. Custom classification from context
    if series_desc:
        classification_dict = get_custom_classification(series_desc, '/flywheel/v0/config.json')
        if classification_dict:
            log.info('Custom classification from config: %s', classification_dict)

    # 2. Classification from SeriesDescription
    if not classification_dict and series_desc:
        classification_dict = infer_classification(series_desc)
        if classification_dict:
            log.info('Inferred classification from label: %s', classification_dict)

    # 3. Classification from Imaging params
    if not classification_dict:
        classification_dict = get_param_classification(dcm, slice_number, unique_iop)

    return classification_dict



def classify_MR(df, dcm, dcm_metadata):
    '''
    Classifies a MR dicom series
    '''
    
    # Determine how many DICOM files are in directory
    slice_number = len(df)

    # Determine whether ImageOrientationPatient is constant
    if hasattr(df, 'ImageOrientationPatient'):
        uniqueiop = df.ImageOrientationPatient.is_unique
    else:
        uniqueiop = []
    # Classification (# Only set classification if the modality is MR)
    if dcm_metadata['modality'] == 'MR':
        log.info("Determining MR Classification...")
        classification = classify_dicom(dcm, slice_number, uniqueiop)
        
        if classification:
            dcm_metadata['classification'] = classification

    return dcm_metadata



