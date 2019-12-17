import os
import json
import sys
import logging
import flywheel
import re
import string
from fnmatch import fnmatch
import pydicom
import zipfile
import pandas as pd
import pprint
import ast


# Scan Coverage
def compute_scan_coverage(df):
    df['ImagePositionPatient-Z'] = df.apply(lambda x: ast.literal_eval(x['ImagePositionPatient'])[2], axis=1)
    max = df['ImagePositionPatient-Z'].max()
    min = df['ImagePositionPatient-Z'].min()
    result = max - min
    scan_coverage = result if result > 0 else result * -1
    return scan_coverage


# Utility:  Check a list of regexes for truthyness
def regex_search_label(regexes, label):
    if any(regex.search(label) for regex in regexes):
            return True
    else:
            return False

        
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
