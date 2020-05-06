import logging
import pandas as pd

import common_utils


logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

# Test dicom header ImageType
hd_0 = {'ImageType': ['ORIGINAL']}
hd_1 = {'ImageType': ['Not_Orig_Der']}
hd_2 = {'NoImageType': []}
hd_3 = {"ImageType": 'ORIGINAL'}
hd_4 = {"ImageType": 'string_and_not_orig_der'}

df = pd.DataFrame(pd.Series({0: [1, 2, 3.2], 1: [1, 2, 3.4]},
                            name='ImagePositionPatient'))
info_object = {}

dicom_headers = [hd_0, hd_1, hd_2, hd_3, hd_4]

for header_dicom in dicom_headers:
    scan_coverage, info_object = common_utils.compute_scan_coverage_if_original(
        header_dicom, df, info_object)


# Test 'ImagePositionPatient' format in df of slices
df_0 = pd.DataFrame(pd.Series({0: None, 1: [1, 2, 3]},
                              name='ImagePositionPatient'))
df_1 = pd.DataFrame(pd.Series({0: 'hi', 1: [1, 2, 3]},
                              name='ImagePositionPatient'))
df_2 = pd.DataFrame(pd.Series({0: [1, 2, 3], 1: [1, 2]},
                              name='ImagePositionPatient'))
df_3 = pd.DataFrame(pd.Series({0: [1, 2, 3.2], 1: [1, 2, '3.5']},
                              name='ImagePositionPatient'))
df_4 = {}

df_5 = pd.DataFrame(pd.Series({0: [1, 2, 3.2], 1: [1, 2, 3.4]},
                              name='ImagePositionPatient'))
dfs = [df_0, df_1, df_2, df_3, df_4, df_5]
header_dicom = hd_0 = {'ImageType': ['ORIGINAL']}
for df in dfs:
    scan_coverage, info_object = common_utils.compute_scan_coverage_if_original(
        header_dicom, df, info_object)

print('debug holder')
