# coding=utf-8
#!/usr/bin/env python

# -------------------------------------------------------------------------------
# Name:        international_support.py
# Purpose:     Pragmatic way to detect encoding.
#
# Author:      Nuno Brum (nuno.brum@gmail.com) with special thanks to Fugio Yokohama (yokohama.fujio@gmail.com)
#
# Created:     14-05-2022
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------
"""
International Support functions
Not using other known unicode detection libraries because we don't need something so complicated. LTSpice only supports
for the time being a reduced set of encodings.
"""
from pathlib import Path
from typing import Union


def detect_encoding(file_path, expected_str: Union[str, Path] = '') -> str:
    """
    Simple strategy to detect file encoding.  If an expected_str is given the function will scan through the possible
    encodings and return a match.
    If an expected string is not given, it will use the second character is null, high chances are that this file has an
    'utf_16_le' encoding, otherwise it is assuming that it is 'utf-8'.
    :param file_path: path to the filename
    :type file_path: str
    :param expected_str: text which the file should start with
    :type expected_str: str
    :return: detected encoding
    :rtype: str
    """
    for encoding in ('utf-8', 'utf_16_le', 'ansi', 'cp1252', 'cp1250', 'shift-jis'):
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                lines = f.readlines()
                f.seek(0)
        except UnicodeDecodeError:
            # This encoding didn't work, let's try again
            continue
        else:
            if expected_str:
                if not lines[0].startswith(expected_str):
                    # File did not start with expected string
                    # Try again with a different encoding (This is unlikely to resolve the issue)
                    continue
            if encoding == 'utf-8' and lines[0][1] == '\x00':
                continue
            return encoding
    else:
        raise UnicodeError(f"Unable to detect log file encoding, or expected string ""{expected_str}"" not found")
