import re
import common_utils


def test_regex_search_label():
    test_regex_list = [re.compile('^[A-Za-z0-9]+$')]

    # Test non-string
    input_label = None
    matches = common_utils.regex_search_label(test_regex_list, input_label)
    assert matches is False

    # Test match
    input_label = 'R2D2'
    matches = common_utils.regex_search_label(test_regex_list, input_label)
    assert matches is True

    # Test no match
    input_label = 'C-3PO'
    matches = common_utils.regex_search_label(test_regex_list, input_label)
    assert matches is False


def test_is_localizer():
    input_label = 'LOCALIZER'
    assert common_utils.is_localizer(input_label)
    input_label = 2
    assert not common_utils.is_localizer(input_label)