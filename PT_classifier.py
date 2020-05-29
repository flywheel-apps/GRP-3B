import re
import common_utils
from operator import add
from functools import reduce
from collections import defaultdict
import abc
import logging

from dotty_dict import Dotty

from CT_classifier import is_lung_window
from common_utils import SEQUENCE_ANATOMY

log = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Apply patch to Dotty.get() method
# -----------------------------------------------------------------------------

def patch_get(self, key, default=None):
    """Get value from deep key or default if key does not exist.
​
            This method match 1:1 with dict .get method except that it
            accepts deeply nested key with dot notation.
​
            :param str key: Single key or chain of keys
            :param Any default: Default value if deep key does not exist
            :return: Any or default value
            """
    try:
        return self.__getitem__(key)
    except (KeyError, IndexError):
        return default


Dotty.get = patch_get


# -----------------------------------------------------------------------------
# Define module dictionaries
# -----------------------------------------------------------------------------

# http://dicom.nema.org/medical/dicom/2015c/output/chtml/part16/sect_CID_4021.html
TRACER_CODES = {
    'C-B1031': 'FDG',  #Fluorodeoxyglucose
    '126501': 'FBB',  #Florbetaben
    'C-E0269': 'FBP',  #Florbetapir = AV45
    'C-E0267': 'FMM',  #Flutemetamol
    'C1831937': 'FES',  #Fluoroestradiol
    '126500': 'PiB'   #Pittsburgh compound B
}

TRACER_MEANINGS = {
    # first the allowed values of CodeMeaning for tracer, i.e., (0008,0104)
    'Fluorodeoxyglucose F^18^': 'FDG',
    'Florbetaben F^18^': 'FBB',
    'Florbetapir F^18^': 'FBP',
    'Flutemetamol F^18^': 'FMM',
    'Fluoroestradiol (FES) F^18^': 'FES',
    'Pittsburgh compound B C^11^': 'PiB',
    # then values found for Radiopharmaceutical
    #not sure if this can work, Radiopharmaceutical may be free-form text ?
    'FDG -- fluorodeoxyglucose': 'FDG'
}

TRACER_TO_ISOTOPE = { # For some tracers, the tracer dictates the isotope
    'FDG': 'F18',
    'FBB': 'F18',
    'FBP': 'F18',
    'FMM': 'F18',
    'FES': 'F18',
    'PiB': 'C11'
}

#http://dicom.nema.org/medical/dicom/2015c/output/chtml/part16/sect_CID_4020.html
ISOTOPE_CODES = {
    'C-111A1': 'F18',
    'C-105A1': 'C11',
    'C-168A4': 'Zr89'
}
ISOTOPE_MEANINGS = {
    '^18^Fluorine': 'F18'
}


# -----------------------------------------------------------------------------
# Module methods
# FUTURE: most, if not all of these, are repeats of methods defined in other
# modules. Create a class or package instead of copy/pasting these in modules.
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


class PTSubClassifier(abc.ABC):
    """
    An abstract base class that's the sub-component in the composite design
    pattern. Currently, this sub-component is used to define only leaves.
    The composite of its leaves is defined as a concrete implementation of
    the parent (abstract) component.

    All leaves will define the method 'classify', which returns
    classifications and info_object parameters.
    """

    def __init__(self, header_dicom: dict, acquisition):
        """
        Args:
            header_dicom (dict): This is just the dicom header info similar to file.info['header']['dicom'].
            acquisition (flywheel.Acquisition): A flywheel acquisition container object
        """
        self.header_dicom = Dotty(header_dicom)
        self.acquisition = acquisition
        self.label = acquisition.label

    @abc.abstractmethod
    def classify(self, classifications, info_object):
        """Returns updated classifications and info_object

        Args:
            classifications (dict): A dictionary matching flywheel modality specific classification. Note the
                classification for a modality can be fetched with `fw.get_modality('PT')['classification']`
                for a PT modality for instance.
            info_object (dict): Info dictionary attribute of a file object.
        """
        raise NotImplemented

    def get_dicom_tag(self, dotty_key: str):
        """Returns the value of single_header_object at dotty_key location.

        Args:
            dotty_key (str): A string to reference the location of the targeted value
                (e.g. 'RadiopharmaceuticalInformationSequence.0.RadionuclideCodeSequence.0.CodeValue')
        """
        return self.header_dicom.get(dotty_key)

    @staticmethod
    def warn_if_isotope_different_from_previously_found(
            isotope, classification):
        if classification['Isotope']:
            if isotope not in classification['Isotope'] and (isotope is not None):
                log.warning(f'Isotope from CodeMeaning ({isotope}) is different from the one previously found '
                            f'({classification["Isotope"]})')


class IsotopePTSubClassifier(PTSubClassifier):

    def classify(self, classifications, info_object):
        """Returns updated classifications and info_object

        Args:
            classifications (dict): A dictionary matching flywheel modality specific classification. Note the
                classification for a modality can be fetched with `fw.get_modality('PT')['classification']`
                for a PT modality for instance.
            info_object (dict): Info dictionary attribute of a file object.
        """
        # Classify isotopes
        classifications, info_object = self.classify_based_on_isotope_code(classifications, info_object)
        classifications, info_object = self.classify_based_on_isotope_meaning(classifications, info_object)

        return classifications, info_object

    def classify_based_on_isotope_code(self, classification, info_object):
        """Returns updated classifications and info_object with Isotope Code info."""
        isotope = None
        code_value_isotope = self.get_dicom_tag(
            'RadiopharmaceuticalInformationSequence.0.RadionuclideCodeSequence.0.CodeValue')

        if code_value_isotope in ISOTOPE_CODES:
            isotope = ISOTOPE_CODES[code_value_isotope]

        self.warn_if_isotope_different_from_previously_found(
            isotope=isotope, classification=classification)

        if isotope and not classification['Isotope']:
            classification['Isotope'].append(isotope)

        return classification, info_object

    def classify_based_on_isotope_meaning(self, classification, info_object):
        """Returns updated classifications and info_object with Isotope Meaning info."""
        isotope = None

        lc_kw = {k.lower(): v for k, v in ISOTOPE_MEANINGS.items()}

        code_meaning_isotope = self.get_dicom_tag(
            'RadiopharmaceuticalInformationSequence.0.RadionuclideCodeSequence.0.CodeMeaning')

        if code_meaning_isotope and code_meaning_isotope.lower() in lc_kw:
            isotope = lc_kw[code_meaning_isotope.lower()]

        self.warn_if_isotope_different_from_previously_found(
            isotope=isotope, classification=classification)

        if isotope and not classification['Isotope']:
            classification['Isotope'].append(isotope)

        return classification, info_object


class ProcessingPTSubClassifier(PTSubClassifier):

    def classify(self, classification, info_object):
        """Returns updated classification and info_object

        Args:
            classification (dict): A dictionary matching flywheel modality specific classification. Note the
                classification for a modality can be fetched with `fw.get_modality('PT')['classification']`
                for a PT modality for instance.
            info_object (dict): Info dictionary attribute of a file object.
        """
        classification, info_object = self.classify_attenuation_corrected(classification, info_object)
        return classification, info_object

    def classify_attenuation_corrected(self, classification, info_object):
        """Returns updated classification and info_object with Processing info"""
        processing_ac = None

        ac_method = self.get_dicom_tag('AttenuationCorrectionMethod')
        if ac_method:
            processing_ac = 'Attenuation Corrected'

        # classify based on 'CorrectedImage' if haven't classified
        # get CorrectedImage
        corrected_image = self.get_dicom_tag('CorrectedImage')
        if not processing_ac:
            if corrected_image:
                if 'ATTN' in corrected_image:
                    processing_ac = 'Attenuation Corrected'

        # classify based on acquisition label if haven't classified
        if not processing_ac:
            if self.label:
                if "AC" in self.label:
                    processing_ac = 'Attenuation Corrected'

        # append to classification if classified
        if processing_ac:
            classification['Processing'].append(processing_ac)

        return classification, info_object


class TracerPTSubClassifier(PTSubClassifier):

    def classify(self, classification, info_object):
        """Returns updated classification and info_object.

        Args:
            classification (dict): A dictionary matching flywheel modality specific classification. Note the
                classification for a modality can be fetched with `fw.get_modality('PT')['classification']`
                for a PT modality for instance.
            info_object (dict): Info dictionary attribute of a file object.
        """
        classification, info_object = self.classify_based_on_tracer_code(classification, info_object)
        classification, info_object = \
            self.classify_based_on_tracer_meaning_or_radiopharmaceutical(classification, info_object)

        return classification, info_object

    def classify_based_on_tracer_code(self, classification, info_object):
        """Returns updated classification and info_object with Tracer code info."""
        tracer, isotope = None, None
        code_value_tracer = self.get_dicom_tag(
            'RadiopharmaceuticalInformationSequence.0.RadiopharmaceuticalCodeSequence.0.CodeValue')

        if code_value_tracer in TRACER_CODES:
            tracer = TRACER_CODES[code_value_tracer]
            isotope = TRACER_TO_ISOTOPE[tracer]

        self.warn_if_isotope_different_from_previously_found(
            isotope=isotope, classification=classification)

        if tracer and not classification['Tracer']:
            classification['Tracer'].append(tracer)
        if isotope and not classification['Isotope']:
            classification['Isotope'].append(isotope)

        return classification, info_object

    def classify_based_on_tracer_meaning_or_radiopharmaceutical(self, classification, info_object):
        """Returns updated classification and info_object with Tracer Code Meaning info."""
        tracer, isotope = None, None
        lc_kw = {k.lower(): v for k, v in TRACER_MEANINGS.items()}

        code_meaning_tracer = self.get_dicom_tag(
            'RadiopharmaceuticalInformationSequence.0.RadiopharmaceuticalCodeSequence.0.CodeMeaning')

        if code_meaning_tracer and code_meaning_tracer.lower() in lc_kw:
            tracer = lc_kw[code_meaning_tracer.lower()]
            isotope = TRACER_TO_ISOTOPE[tracer]

        self.warn_if_isotope_different_from_previously_found(
            isotope=isotope, classification=classification)

        if tracer and not classification['Tracer']:
            classification['Tracer'].append(tracer)
        if isotope and not classification['Isotope']:
            classification['Isotope'].append(isotope)

        radiopharma = self.get_dicom_tag(
            'RadiopharmaceuticalInformationSequence.0.RadionuclideCodeSequence.0.Radiopharmaceutical')

        if radiopharma and radiopharma.lower() in lc_kw:
            tracer = lc_kw[code_meaning_tracer.lower()]
            isotope = TRACER_TO_ISOTOPE[tracer]

        self.warn_if_isotope_different_from_previously_found(
            isotope=isotope, classification=classification)

        if tracer and not classification['Tracer']:
            classification['Tracer'].append(tracer)
        if isotope and not classification['Isotope']:
            classification['Isotope'].append(isotope)

        return classification, info_object


class BaseModalityClassifier(abc.ABC):
    """Modality Classifier abstract class.

    This is the main component in the composite design pattern. Concrete
    implementations of this adds leaves of a sub-composite class (e.g.,
    PTSubClassifier) to create a composite of those leaves (e.g.,
    PTClassifier). In this way, all composites and leaves can be treated
    the same way (i.e., use the same arguments and methods). Further
    explanation is below.

    There are two abstract base classes involved (component and
    sub-component): one for the modality and the other--a sub-classifier--for
    the classifications of a modality. The base modality class simply
    defines which concrete sub-classifiers (or leaves of a sub-component
    class) a modality will use, essentially creating a composite of those
    leaves (a sub-composite in the overall scheme).

    Concrete sub-classifier classes (leaves) are added to the modality's
    class variable list, sub_classifiers, to create a sub-composite. When a
    concrete modality class is instantiated, all concrete sub-classifiers are
    appended to the modality's instance variable, self.classifiers. Calling
    the instantiated modality class' self.classify() method will invoke all
    sub-classifier's classify() method, which is defined
    individually for each concrete sub-classifier class (since the
    sub-classifier's abstract base class has an abstract self.classify()
    method).  The passed arguments, classification and info_object,
    are updated as it passes through all sub-classifiers (i.e., updated as
    they pass through all leaves of the sub-composite).


    Args:
        header_dicom (dict): This is just the dicom header info similar to file.info['header']['dicom'].
        acquisition (flywheel.Acquisition): A flywheel acquisition container object

    Attributes:
        sub_classifiers (list): List of SubClassifier class that will be applied.
    """

    sub_classifiers = None

    def __init__(self, header_dicom, acquisition):
        self.header_dicom = header_dicom
        self.acquisition = acquisition
        self.classifiers = []
        for subclass in self.sub_classifiers:
            self.classifiers.append(subclass(self.header_dicom, self.acquisition))

    def classify(self, classification, info_object):
        """Returns updated classification and info_object

        Args:
            classification (dict): A dictionary matching flywheel modality specific classification. Note the
                classification for a modality can be fetched with `fw.get_modality('PT')['classification']`
                for a PT modality for instance.
            info_object (dict): Info dictionary attribute of a file object.
        """
        # make classification a defaultdict with default=list
        classification = defaultdict(list, classification)

        for classifier in self.classifiers:
            classification, info_object = classifier.classify(classification, info_object)

        return classification, info_object


class PTClassifier(BaseModalityClassifier):
    """The PT Classifier class"""
    sub_classifiers = [
        IsotopePTSubClassifier,
        TracerPTSubClassifier,
        ProcessingPTSubClassifier
    ]


######################################################################################
######################################################################################

def classify_PT(df, dcm_metadata, acquisition):
    '''
    Classifies a PT dicom series

    Args:
        df (DataFrame): A pandas DataFrame where each row is a dicom image header information
    Returns:
        dict: The dictionary for the PT classification
    '''
    log.info("Determining PT Classification...")
    header_dicom = dcm_metadata['info']['header']['dicom']
    series_description = header_dicom.get('SeriesDescription') or ''
    classification = {}
    info_object = {}

    scan_coverage, info_object = \
        common_utils.compute_scan_coverage_if_original(header_dicom, df,
                                                       info_object)

    # # Anatomy
    classification['Anatomy'] = get_anatomy_from_label(acquisition.label)
    if not classification['Anatomy']:
        classification['Anatomy'] = get_anatomy_from_label(series_description)
    if not classification['Anatomy']:
        classification['Anatomy'] = get_anatomy_from_scan_coverage(scan_coverage)

    # Classify Isotope, Processing, Tracer
    pt_classifier = PTClassifier(header_dicom=header_dicom, acquisition=acquisition)
    classification, info_object = pt_classifier.classify(classification, info_object)

    dcm_metadata['info'].update(info_object)

    dcm_metadata['classification'] = classification

    return dcm_metadata
