import re
import string
import common_utils
from operator import add
from functools import reduce
import logging
import abc

from CT_classifier import is_lung_window

log = logging.getLogger(__name__)

SEQUENCE_ANATOMY = ['Head', 'Neck', 'Chest', 'Abdomen', 'Pelvis', 'Lower Extremities', 'Upper Extremities', 'Whole Body']

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


class Classifier(abc.ABC):
    """
    An abstract base class that's the component in the composite design
    pattern.

    All children will define the method 'classify', which returns
    classifications and info_object parameters. Any new classification
    method within children shall be added to the 'classify' method of each
    child, and each classification method shall update parameter
    'classification', 'info_object', or both.

    The composite class 'Classifiers' will be used to perform all
    classifications. To do so, all children of 'Classifer' (e.g.,
    components) shall be added to Classifiers.classify() method.
    """

    def __init__(self, single_header_object: dict, acquisition,
                 classifications: dict = {}, info_object: dict = {}):
        """
        single_header_object: this is just the GIP dicom header info similar
            to file.info['header']['dicom'].
        """
        self.single_header_object = single_header_object
        self.classifications = classifications
        self.info_object = info_object
        self.acquisition = acquisition
        self.label = acquisition.label

    @abc.abstractmethod
    def classify(self):
        # Always return self.classifications, self.info_object
        pass

    def get_dicom_tag(self, dicom_tag_key: str):
        """
        Gets a dicom tag from a dicom header.

        The header is a Flywheel dictionary object, so nested dicom
        properties are simply nested dictionaries.

        dicom_tag_key: str
            The format of this should be "['tag']['tag_nested'][
            'tag_nested_nested']"
        """

        try:
            dicom_tag = eval("self.single_header_object" + dicom_tag_key)
        except (AttributeError, IndexError, KeyError):
            dicom_tag = None

        # if it's an empty value (e.g., '' or []), then set as None
        if not dicom_tag:
            dicom_tag = None

        return dicom_tag

    def append_to_param(self, key, value, param):
        """
        Appends a new key value pair to either 'classifications' or
        'info_object' parameter.
        """
        if param == 'classifications':
            dict_out = self.classifications
        elif param == 'info_object':
            dict_out = self.info_object
        else:
            raise ValueError("param should be 'classifications' or "
                             "'info_object', not {}".format(param))

        if key in dict_out:
            dict_out[key].append(value)
        else:
            value = [value]
            dict_out[key] = value
        exec("self." + param + " = dict_out")


class IsotopeClassifier(Classifier):

    def __init__(self, single_header_object: dict, acquisition,
                 classifications: dict = {}, info_object: dict = {}):
        super().__init__(single_header_object=single_header_object,
                         classifications=classifications,
                         info_object=info_object,
                         acquisition=acquisition)
        # get CodeValue of Isotope
        log.info(self.single_header_object)
        dicom_tag_key = "['RadiopharmaceuticalInformationSequence'][0]" \
                        "['RadionuclideCodeSequence'][0]['CodeValue']"
        self.code_value = self.get_dicom_tag(dicom_tag_key=dicom_tag_key)

        # get CodeMeaning of Isotope. Convert to lowercase if str is found.
        dicom_tag_key = "['RadiopharmaceuticalInformationSequence'][0]" \
                        "['RadionuclideCodeSequence'][0]['CodeMeaning']"
        code_meaning = self.get_dicom_tag(dicom_tag_key=dicom_tag_key)
        if type(code_meaning) == str:
            code_meaning = code_meaning.lower()
        self.code_meaning = code_meaning

        # get CodeMeaning of Tracer. Sometimes F18 info is in this.
        dicom_tag_key = "['RadiopharmaceuticalInformationSequence'][0]" \
                        "['RadiopharmaceuticalCodeSequence'][0]['CodeMeaning']"
        code_meaning_tracer = self.get_dicom_tag(dicom_tag_key=dicom_tag_key)
        if type(code_meaning_tracer) == str:
            code_meaning_tracer = code_meaning_tracer.lower()
        self.code_meaning_tracer = code_meaning_tracer

    def classify(self):
        # Classify isotopes
        self.classify_f18()

        return self.classifications, self.info_object

    def classify_f18(self):
        isotope_f18 = None

        # classify based on code value first
        if self.code_value == 'C-111A1':
            isotope_f18 = 'F18'

        # classify based on code meaning if none is found
        if not isotope_f18:
            if self.code_meaning:
                code_meaning = self.code_meaning
                if ('18' in code_meaning) and ('f' in code_meaning):
                    isotope_f18 = 'F18'

        # classify based on Tracer code meaning
        if not isotope_f18:
            if self.code_meaning_tracer:
                code_meaning = self.code_meaning_tracer
                if 'f^18' in code_meaning:
                    isotope_f18 = 'F18'

        # append to classifications if classified
        if isotope_f18:
            self.append_to_param(key='Isotope', value=isotope_f18,
                                 param='classifications')


class ProcessingClassifier(Classifier):

    def __init__(self, single_header_object: dict, acquisition,
                 classifications: dict = {}, info_object: dict = {}):
        super().__init__(single_header_object=single_header_object,
                         classifications=classifications,
                         info_object=info_object,
                         acquisition=acquisition)
        # get AttenuationCorrectionMethod
        dicom_tag_key = "['AttenuationCorrectionMethod']"
        self.ac_method = self.get_dicom_tag(dicom_tag_key=dicom_tag_key)

        # get CorrectedImage
        dicom_tag_key = "['CorrectedImage']"
        self.corrected_image = self.get_dicom_tag(dicom_tag_key=dicom_tag_key)

    def classify(self):
        self.classify_attenuation_corrected()

        return self.classifications, self.info_object

    def classify_attenuation_corrected(self):
        processing_ac = None

        # classify based on dicom header 'AttenuationCorrectionMethod'
        # exists first
        if self.ac_method:
            processing_ac = 'Attenuation Corrected'

        # classify based on 'CorrectedImage' if haven't classified
        if not processing_ac:
            if self.corrected_image:
                if 'ATTN' in self.corrected_image:
                    processing_ac = 'Attenuation Corrected'

        # classify based on acquisition label if haven't classified
        if not processing_ac:
            if self.label:
                if "AC" in self.label:
                    processing_ac = 'Attenuation Corrected'

        # append to classifications if classified
        if processing_ac:
            self.append_to_param(key='Processing', value=processing_ac,
                                 param='classifications')


class TracerClassifier(Classifier):

    def __init__(self, single_header_object: dict, acquisition,
                 classifications: dict = {}, info_object: dict = {}):
        super().__init__(single_header_object=single_header_object,
                         classifications=classifications,
                         info_object=info_object,
                         acquisition=acquisition)

        # get CodeValue of Tracer.
        dicom_tag_key = "['RadiopharmaceuticalInformationSequence'][0]" \
                        "['RadiopharmaceuticalCodeSequence'][0]['CodeValue']"
        self.code_value_tracer = self.get_dicom_tag(
            dicom_tag_key=dicom_tag_key)

        # get CodeMeaning of Tracer.
        dicom_tag_key = "['RadiopharmaceuticalInformationSequence'][0]" \
                        "['RadiopharmaceuticalCodeSequence'][0]['CodeMeaning']"
        code_meaning_tracer = self.get_dicom_tag(dicom_tag_key=dicom_tag_key)
        if type(code_meaning_tracer) == str:
            code_meaning_tracer = code_meaning_tracer.lower()
        self.code_meaning_tracer = code_meaning_tracer

        # get 'Radiopharmaceutical' from 'RadionuclideCodeSequence'
        dicom_tag_key = "['RadiopharmaceuticalInformationSequence'][0]" \
                        "['RadionuclideCodeSequence'][0][" \
                        "'Radiopharmaceutical']"
        radiopharma = self.get_dicom_tag(dicom_tag_key=dicom_tag_key)
        if type(radiopharma) == str:
            radiopharma = radiopharma.lower()
        self.radiopharma = radiopharma

    def classify(self):
        self.classify_fdg()

        return self.classifications, self.info_object

    def classify_fdg(self):
        tracer_fdg = None

        # classify based on code value first
        if (self.code_value_tracer == 'C-B1031') or \
            (self.code_value_tracer == 'Y-X1743'):
            tracer_fdg = 'FDG'

        # classify based on code meaning if none is found
        if not tracer_fdg:
            if self.code_meaning_tracer:
                code_meaning = self.code_meaning_tracer
                if ('fluorodeoxyglucose' in code_meaning) or \
                        ('fdg' in code_meaning):
                    tracer_fdg = 'FDG'

        # classify based on 'Radiopharmaceutical' if none is found
        if not tracer_fdg:
            if self.radiopharma:
                if ('fluorodeoxyglucose' in self.radiopharma) or \
                        ('fdg' in self.radiopharma):
                    tracer_fdg = 'FDG'

        # append to classifications if classified
        if tracer_fdg:
            self.append_to_param(key='Tracer', value=tracer_fdg,
                                 param='classifications')


class AnatomyClassifier(Classifier):
    """
    Classifies PET anatomy.

    Since some classification for anatomy is already done externally,
    this classifier accounts for this. At this time, this Classifier object
    is not currently implemented in Classifiers, since current
    classification requirements are already fulfilled.

    Notes
    -----
    FUTURE - move all external anatomy classifications to this Classifier
    object.
    """

    def __init__(self, single_header_object: dict, acquisition,
                 classifications: dict = {}, info_object: dict = {}):
        super().__init__(single_header_object=single_header_object,
                         classifications=classifications,
                         info_object=info_object,
                         acquisition=acquisition)

    def classify(self):

        classifications_anatomy = self.classifications.get('Anatomy')

        # classify what's not been classified if classifications_anatomy is
        # not empty, else classify everything.
        if classifications_anatomy is not None:
            if 'Whole Body' not in classifications_anatomy:
                self.classify_whole_body()

            # check and call all remaining methods

        else:
            # call all of the classify methods
            pass

    def classify_abdomen(self):
        pass

    def classify_chest(self):
        pass

    def classify_head(self):
        pass

    def classify_lower_extremities(self):
        pass

    def classify_neck(self):
        pass

    def classify_pelvis(self):
        pass

    def classify_upper_extremities(self):
        pass

    def classify_whole_body(self):
        pass


class Classifiers(Classifier):
    """
    This is the composite class in the composite design pattern.

    It's really a pseudo-composite class; children cannot be added externally.
    Add new Classifier children to 'classify' method here.

    Notes
    -----
    FUTURE - To make this a truly composite class, we can make a class
    variable 'classifiers' and add the ability to add/remove external children
    to this variable by creating these methods for Classifiers.
    """

    def __init__(self, single_header_object: dict, acquisition,
                 classifications: dict = {}, info_object: dict = {}):
        super().__init__(single_header_object=single_header_object,
                         classifications=classifications,
                         info_object=info_object,
                         acquisition=acquisition)

    def classify(self):
        """
        Instantiates all Classifier children and calls each child's
        classify() method.

        The parameters 'classifications' and 'info_object' are passed to the
        next child that's instantiated. In this manner, one need only
        instantiate a Classifiers object and call its classify() method to
        perform all classifications.
        """
        classifiers = [IsotopeClassifier, ProcessingClassifier,
                       TracerClassifier]

        # assign
        single_header_object = self.single_header_object
        classifications = self.classifications
        info_object = self.info_object
        acquisition = self.acquisition
        for classifier in classifiers:
            my_classifier = classifier(
                single_header_object=single_header_object,
                acquisition=acquisition,
                classifications=classifications,
                info_object=info_object)
            classifications, info_object = my_classifier.classify()

        return classifications, info_object

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
    single_header_object = dcm_metadata['info']['header']['dicom']
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

        # Classify Isotope, Processing, Tracer
        my_classifiers = Classifiers(
            single_header_object=single_header_object,
            acquisition=acquisition,
            classifications=classifications,
            info_object=info_object)
        classifications, info_object = my_classifiers.classify()

        dcm_metadata['info'].update(info_object)

    dcm_metadata['classification'] = classifications

    return dcm_metadata
