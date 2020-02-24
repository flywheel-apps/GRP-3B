import os
import re
import string
import pydicom
import zipfile
import pandas as pd



log = logging.getLogger(__name__)

def format_string(in_string):
    formatted = re.sub(r'[^\x00-\x7f]',r'', str(in_string)) # Remove non-ascii characters
    formatted = ''.join(filter(lambda x: x in string.printable, formatted))
    if len(formatted) == 1 and formatted == '?':
        formatted = None
    return formatted#.encode('utf-8').strip()



def assign_type(s):
    '''
    Sets the type of a given input.
    '''
    if type(s) == pydicom.valuerep.PersonName or type(s) == pydicom.valuerep.PersonName3 or type(s) == pydicom.valuerep.PersonNameBase:
        return format_string(s)
    if type(s) == list or type(s) == pydicom.multival.MultiValue:
        try:
            return [ float(x) for x in s ]
        except ValueError:
            try:
                return [ int(x) for x in s ]
            except ValueError:
                return [ format_string(x) for x in s if len(x) > 0 ]
    elif type(s) == float or type(s) == int:
        return s
    else:
        s = str(s)
        try:
            return int(s)
        except ValueError:
            try:
                return float(s)
            except ValueError:
                return format_string(s)



def get_seq_data(sequence, ignore_keys):
    seq_dict = {}
    for seq in sequence:
        for s_key in seq.dir():
            s_val = getattr(seq, s_key, '')
            if type(s_val) is pydicom.UID.UID or s_key in ignore_keys:
                continue

            if type(s_val) == pydicom.sequence.Sequence:
                _seq = get_seq_data(s_val, ignore_keys)
                seq_dict[s_key] = _seq
                continue

            if type(s_val) == str:
                s_val = format_string(s_val)
            else:
                s_val = assign_type(s_val)

            if s_val:
                seq_dict[s_key] = s_val

    return seq_dict



def get_pydicom_header(dcm):
    '''
    Extract the header values
    '''
    header = {}
    exclude_tags = ['[Unknown]', 'PixelData', 'Pixel Data',  '[User defined data]', '[Protocol Data Block (compressed)]', '[Histogram tables]', '[Unique image iden]']
    tags = dcm.dir()
    for tag in tags:
        try:
            if (tag not in exclude_tags) and ( type(dcm.get(tag)) != pydicom.sequence.Sequence ):
                value = dcm.get(tag)
                if value or value == 0: # Some values are zero
                    # Put the value in the header
                    if type(value) == str and len(value) < 10240: # Max pydicom field length
                        header[tag] = format_string(value)
                    else:
                        header[tag] = assign_type(value)
                else:
                    log.debug('No value found for tag: ' + tag)

            if type(dcm.get(tag)) == pydicom.sequence.Sequence:
                seq_data = get_seq_data(dcm.get(tag), exclude_tags)
                # Check that the sequence is not empty
                if seq_data:
                    header[tag] = seq_data
        except:
            log.debug('Failed to get ' + tag)
            pass
    return header



def process_dicom(zip_file_path):
    '''
    Create Pandas Dataframe where each row is a dicom image header information
    '''
    if zipfile.is_zipfile(zip_file_path):
        dcm_list = []
        zip_obj = zipfile.ZipFile(zip_file_path)
        num_files = len(zip_obj.namelist())
        for n in range((num_files - 1), -1, -1):
            dcm_path = zip_obj.extract(zip_obj.namelist()[n], '/tmp')
            dcm_tmp = None
            if os.path.isfile(dcm_path):
                try:
                    log.info('reading %s' % dcm_path)
                    dcm_tmp = pydicom.read_file(dcm_path)
                    # Here we check for the Raw Data Storage SOP Class, if there
                    # are other pydicom files in the zip then we read the next one,
                    # if this is the only class of pydicom in the file, we accept
                    # our fate and move on.
                    if dcm_tmp.get('SOPClassUID') == 'Raw Data Storage' and n != range((num_files - 1), -1, -1)[-1]:
                        continue
                    else:
                        dcm_list.append(dcm_tmp)
                except:
                    pass
            else:
                log.warning('%s does not exist!' % dcm_path)
        # Select last image
        dcm = dcm_list[-1]
    else:
        log.info('Not a zip. Attempting to read %s directly' % os.path.basename(zip_file_path))
        dcm = pydicom.read_file(zip_file_path)
        dcm_list = [dcm]

    # Create pandas object for comparing headers
    df_list = []
    for header in dcm_list:
        tmp_dict = get_pydicom_header(header)
        for key in tmp_dict:
            if type(tmp_dict[key]) == list:
                tmp_dict[key] = str(tmp_dict[key])
            else:
                tmp_dict[key] = [tmp_dict[key]]
        df_tmp = pd.DataFrame.from_dict(tmp_dict)
        df_list.append(df_tmp)
    df = pd.concat(df_list, ignore_index=True, sort=True)

    return df, dcm

