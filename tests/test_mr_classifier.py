import tempfile
import pandas as pd
from pydicom.data import get_testdata_files
import pydicom

from MR_classifier import classify_MR, _find_matches, intent_check, \
    measurement_check, feature_check


def test_classify_on_a_sample_MR():
    dcm = pydicom.read_file(get_testdata_files()[0])
    dcm.SeriesDescription = 'T2W_FLAIR'
    with tempfile.TemporaryFile(suffix='.dcm') as fp:
        dcm.save_as(fp)
        dcm_metadata = {
            'modality': 'MR',
            'info': {'header': {'dicom':  {
                        "header": {
                            "dicom": {
                                "SeriesDescription": "T2W_FLAIR",
                                "Modality": "MR"
                            }
                        }
                    }
            }}}
        ipp = [[0, 0, a] for a in range(100)]
        iop = [[0, 0, 0] for a in range(100)]
        df = pd.DataFrame({'ImagePositionPatient': ipp, 'ImageOrientationPatient': iop})
        res = classify_MR(df, dcm, dcm_metadata)
        assert res['classification']['Intent'] == ['Structural']
        assert res['classification']['Measurement'] == ['T2']
        assert res['classification']['Features'] == ['FLAIR']


def test_find_matches():
    label = 'Localizer'
    set = ['Local.+', '.+izer']
    matches = _find_matches(label, set)
    assert len(matches) == 2

    label = 'no-match'
    matches = _find_matches(label, set)
    assert len(matches) == 0


def test_intent_check():
    assert len(intent_check('NotAnIntent')) == 0
    assert intent_check('Localizer') == ['Localizer']
    assert intent_check('Localizer Shim') == ['Localizer', 'Shim']


def test_measurement_check():
    assert len(measurement_check('NotAMeasure')) == 0
    assert measurement_check('MRA') == ['MRA']
    assert measurement_check('MRA CEST') == ['MRA', 'CEST']
    assert measurement_check('T2*') == ['T2*']
    assert measurement_check('t2star') == ['T2*']
    assert measurement_check('T2') == ['T2']
    assert measurement_check('T2/T2*') == ['T2', 'T2*']


def test_feature_check():
    assert len(feature_check('NotAFeature')) == 0
    assert feature_check('2D') == ['2D']
    assert feature_check('2D-AAscout') == ['2D', 'AAscout']