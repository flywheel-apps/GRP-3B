import logging
import re
import ast

log = logging.getLogger(__name__)


# Scan Coverage
def compute_scan_coverage(df):
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

    return scan_coverage


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
    if type(image_type) is not list:
        # Throw error
        raise TypeError(
            f"Cannot determine if scan coverage should be computed. "
            f"Dicom header 'ImageType' is not a list, type is "
            f"{type(image_type)}). Try re-running latest GRP-3 "
            f"metadata import and validation gear.")

    # Check if not original or derived
    if (image_type[0] is not 'ORIGINAL') and (image_type is not 'DERIVED'):
        log.error(
            f"Cannot determine if scan coverage should be computed. "
            f"Dicom header 'ImageType[0]' ({image_type[0]}) is not "
            f"'ORIGINAL' or 'DERIVED'. See {dicom_std_link}"
        )
        return None, info_object

    # Check if it's 'DERIVED'
    if image_type[0] == 'DERIVED':
        log.info(f"Cannot computed scan coverage. 'ImageType' is "
                 f"{image_type[0]}")
        return None, info_object

    # Compute if all checks are passed
    scan_coverage = compute_scan_coverage(df)

    if scan_coverage:
        info_object['ScanCoverage'] = scan_coverage

    return scan_coverage, info_object
