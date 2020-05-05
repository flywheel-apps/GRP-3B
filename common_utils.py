import logging
import re
import ast

log = logging.getLogger(__name__)

# Scan Coverage
def compute_scan_coverage(df):
    if 'ImagePositionPatient' in df.keys():
        df['ImagePositionPatient-Z'] = df.apply(lambda x: x['ImagePositionPatient'][2], axis=1)
        max = df['ImagePositionPatient-Z'].max()
        min = df['ImagePositionPatient-Z'].min()
        result = max - min
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
    if header_dicom.get('ImageType', [None])[0] == 'ORIGINAL':
        scan_coverage = compute_scan_coverage(df)
    if scan_coverage:
        info_object['ScanCoverage'] = scan_coverage

    return scan_coverage, info_object
