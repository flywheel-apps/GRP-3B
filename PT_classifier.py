import re
import common_utils
from operator import add
from functools import reduce
from collections import defaultdict
import abc
import logging

from dotty_dict import Dotty

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

    # Compute scan coverage
    scan_coverage, info_object = \
        common_utils.compute_scan_coverage_if_original(header_dicom, df,
                                                       info_object)

    # Classify Anatomy
    classification = common_utils.classify_anatomy(
        classification, acquisition, series_description, scan_coverage)

    # Classify Isotope, Processing, Tracer
    pt_classifier = PTClassifier(header_dicom=header_dicom, acquisition=acquisition)
    classification, info_object = pt_classifier.classify(classification, info_object)

    dcm_metadata['info'].update(info_object)

    dcm_metadata['classification'] = classification

    return dcm_metadata
