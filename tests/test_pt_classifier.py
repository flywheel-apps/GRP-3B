import pandas as pd
from PT_classifier import classify_PT
import flywheel


def test_classify_PT():
    dcm_metadata = {
        'info': {'header': {'dicom': {
                    'SeriesDescription': '[WB_CTAC] Body',
                    'ImageType': ['ORIGINAL', 'PRIMARY'],
                    'CorrectedImage': ['DECY', 'RADL', 'ATTN', 'SCAT', 'DTIM', 'RAN', 'NORM'],
                    'RadiopharmaceuticalInformationSequence': [{
                        'RadionuclideCodeSequence': [{'CodeValue': 'C-111A1'}],
                        'RadiopharmaceuticalCodeSequence': [{'CodeValue': 'C-B1031'}]
                    }]
        }}}}
    ipp = [[0, 0, float(a)] for a in range(100)]
    df = pd.DataFrame({'ImagePositionPatient': ipp})
    acquisition = flywheel.Acquisition(label='Neck')
    res = classify_PT(df, dcm_metadata, acquisition)
    assert res['classification']['Isotope'] == ['F18']
    assert res['classification']['Processing'] == ['Attenuation Corrected']
    assert res['classification']['Tracer'] == ['FDG']
