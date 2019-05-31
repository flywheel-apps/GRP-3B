import classification_from_label
import re
import ast


def is_standard_scan(description):
    regexes = [
        re.compile('\\bNAC', re.IGNORECASE),
        re.compile('NAC\\b', re.IGNORECASE),
        re.compile('_NAC', re.IGNORECASE),
        re.compile('NAC_', re.IGNORECASE)
    ]
    return classification_from_label.regex_search_label(regexes, description)


def is_attn_corr_scan(description):
    regexes = [
        re.compile('\\bAC', re.IGNORECASE),
        re.compile('AC\\b', re.IGNORECASE),
        re.compile('_AC', re.IGNORECASE),
        re.compile('^AC_', re.IGNORECASE)
    ]
    return classification_from_label.regex_search_label(regexes, description)


def is_axial(description):
    regexes = [
        re.compile('axial', re.IGNORECASE),
        re.compile('trans', re.IGNORECASE)
    ]
    return classification_from_label.regex_search_label(regexes, description)


def is_coronal(description):
    regexes = [
        re.compile('cor', re.IGNORECASE)
    ]
    return classification_from_label.regex_search_label(regexes, description)


def is_sagittal(description):
    regexes = [
        re.compile('sag', re.IGNORECASE)
    ]
    return classification_from_label.regex_search_label(regexes, description)


def is_chest(description):
    regexes = [
        re.compile('lung', re.IGNORECASE),
        re.compile('chest', re.IGNORECASE)
    ]
    return classification_from_label.regex_search_label(regexes, description)


def is_abdomen(description):
    regexes = [
        re.compile('abd', re.IGNORECASE)
    ]
    return classification_from_label.regex_search_label(regexes, description)


def is_head(scan_coverage):
    return scan_coverage is not None and scan_coverage < 250


def is_whole_body(scan_coverage):
    return scan_coverage is not None and scan_coverage > 1300


def is_cap(scan_coverage):
    return scan_coverage is not None and scan_coverage > 800 and scan_coverage < 1300

def is_abdomen(description):
    regexes = [
        re.compile('abd', re.IGNORECASE)
    ]
    return classification_from_label.regex_search_label(regexes)


def is_not_contrast(description):
    regexes = [
        re.compile('w\\^o', re.IGNORECASE)
    ]
    return classification_from_label.regex_search_label(regexes, description)


def is_contrast(description):
    regexes = [
        re.compile('w\\^IV', re.IGNORECASE)
    ]
    return classification_from_label.regex_search_label(regexes, description)


def is_arterial_phase(description):
    regexes = [
        re.compile('arterial', re.IGNORECASE)
    ]
    return classification_from_label.regex_search_label(regexes, description)


def is_portal_venous(description):
    regexes = [
        re.compile('venous', re.IGNORECASE)
    ]
    return classification_from_label.regex_search_label(regexes, description)


def is_delayed(description):
    regexes = [
        re.compile('delayed', re.IGNORECASE),
        re.compile('equil', re.IGNORECASE)
    ]
    return classification_from_label.regex_search_label(regexes, description)


def classify_CT(df, single_header_object, acquisition):
    """Classifies a CT dicom series

    Args:
        df (DataFrame): A pandas DataFrame where each row is a dicom image header information
    Returns:
        dict: The dictionary for the CT classification
    """
    series_description = single_header_object.get('SeriesDescription') or ''
    classifications = {}
    info_object = {}
    if classification_from_label.is_localizer(acquisition.label) or classification_from_label.is_localizer(series_description) or len(df) < 10:
        classifications['Scan Type'] = ['Localizer']
    else:
        # SCAN CONVERAGE
        # put this on the file
        scan_coverage = None
        if single_header_object['ImageType'][0] == 'ORIGINAL':
            df['ImagePositionPatient-Z'] = df.apply(lambda x: ast.literal_eval(x['ImagePositionPatient'])[2], axis=1)
            max = df['ImagePositionPatient-Z'].max()
            min = df['ImagePositionPatient-Z'].min()
            result = max - min
            scan_coverage = result if result > 0 else result * -1
        if scan_coverage:
            info_object['ScanCoverage'] = scan_coverage

        # Scan orientation from acquisition label
        scan_orientation = None
        if is_axial(acquisition.label):
            scan_orientation = 'axial'
        elif is_coronal(acquisition.label):
            scan_orientation = 'coronal'
        elif is_sagittal(acquisition.label):
            scan_orientation = 'sagittal'
        elif is_axial(series_description):
            scan_orientation = 'axial'
        elif is_coronal(series_description):
            scan_orientation = 'coronal'
        elif is_sagittal(series_description):
            scan_orientation = 'sagittal'
        if scan_orientation:
            info_object['ScanOrientation'] = scan_orientation


        # Anatomy
        if is_chest(acquisition.label):
            classifications['Anatomy'] = ['Chest']
        elif is_abdomen(acquisition.label):
            classifications['Anatomy'] = ['Abdomen']
        elif is_chest(series_description):
            classifications['Anatomy'] = ['Chest']
        elif is_abdomen(series_description):
            classifications['Anatomy'] = ['Abdomen']
        elif is_head(scan_coverage):
            classifications['Anatomy'] = ['Head']
        elif is_whole_body(scan_coverage):
            classifications['Anatomy'] = ['Whole Body']
        elif is_cap(scan_coverage):
            classifications['Anatomy'] = ['C/A/P']

        # Contrast
        if is_not_contrast(acquisition.label):
            classifications['Contrast'] = ['No Contrast']
        elif is_contrast(acquisition.label):
            if is_arterial_phase(acquisition.label):
                classifications['Contrast'] = ['Arterial Phase']
            elif is_delayed(acquisition.label):
                classifications['Contrast'] = ['Delayed Phase']
            elif is_portal_venous(acquisition.label):
                classifications['Contrast'] = ['Portal Venous Phase']
            else:
                classifications['Contrast'] = ['With Contrast']
        elif is_not_contrast(series_description):
            classifications['Contrast'] = ['No Contrast']
        elif is_contrast(series_description):
            if is_arterial_phase(series_description):
                classifications['Contrast'] = ['Arterial Phase']
            elif is_delayed(series_description):
                classifications['Contrast'] = ['Delayed Phase']
            elif is_portal_venous(series_description):
                classifications['Contrast'] = ['Portal Venous Phase']
            else:
                classifications['Contrast'] = ['With Contrast']

        if scan_coverage:
            slice_thickness = scan_coverage / len(df)
            info_object['SliceThickness'] = slice_thickness
    return classifications, info_object



