import logging
import re
import ast

log = logging.getLogger(__name__)

# Scan Coverage
def compute_scan_coverage(df):
    if 'ImagePositionPatient' in df.keys():
        df['ImagePositionPatient-Z'] = df.apply(lambda x: x['ImagePositionPatient'][2], axis=1)
        position_max = df['ImagePositionPatient-Z'].max()
        position_min = df['ImagePositionPatient-Z'].min()
        result = position_max - position_min
        scan_coverage = result if result > 0 else result * -1
    else:
        scan_coverage = None
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
    scan_coverage = None

    # Check for ImageType, which is always at the 0'd index and either
    # 'ORIGINAL' or 'DERIVED'
    #
    dicom_std_link = \
        "https://dicom.innolitics.com/ciods/cr-image/general-image/00080008"
    image_type = header_dicom.get('ImageType')
    if image_type:
        is_original = False
        if type(image_type) is list:
            if image_type[0] == 'ORIGINAL':
                is_original = True
            elif image_type[0] == 'DERIVED':
                # do nothing
                pass
            else:
                log.warning(
                    f"Dicom header 'ImageType[0]' ({image_type[0]}) is not "
                    f"'ORIGINAL' or 'DERIVED'. See {dicom_std_link}"
                )
        elif type(image_type) is str:
            log.warning(
                f"'ImageType' in dicom header is not a list but a string "
                f"({image_type}). This does not follow the dicom standard. "
                f"See {dicom_std_link}"
            )
            if image_type == 'ORIGINAL':
                is_original = True
            elif image_type == 'DERIVED':
                # do nothing
                pass
            else:
                log.warning(
                    f"Dicom header 'ImageType' ({image_type}) is not "
                    f"'ORIGINAL' or 'DERIVED'. See {dicom_std_link}"
                )
        else:
            # Throw error
            log.warning(
                f"Dicom header 'ImageType' is not a list or string, type is "
                f"{type(image_type)})")

        if is_original:
            scan_coverage = compute_scan_coverage(df)
    else:
        log.warning(
            f"Could not find 'ImageType' in dicom header {header_dicom}"
        )

    if scan_coverage:
        info_object['ScanCoverage'] = scan_coverage

    return scan_coverage, info_object




