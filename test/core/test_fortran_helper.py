"""Testing enzy_hpt.core.fortran_helper.py

Author: Qianzhen (QZ) Shao <shaoqz@icloud.com>
Date: 2024-01-23
"""
import enzy_htp.core.fortran_helper as fh

def test_parse_single_format():
    """as name"""
    assert fh.parse_single_format("20A4") == (20, str, 4, 0)

    assert fh.parse_single_format("5E16.8") == (5, float, 16, 8)

    assert fh.parse_single_format("10I8") == (10, int, 8, 0)

    assert fh.parse_single_format("I8") == (1, int, 8, 0)

def test_parse_format():
    """Testing that the parse_format() method works correctly for uppercase inputs."""
    assert fh.parse_format('FORMAT(20A4)') == [(20, str, 4, 0)]

    assert fh.parse_format('FORMAT(5E16.8)') == [(5, float, 16, 8)]

    assert fh.parse_format('FORMAT(10I8)') == [(10, int, 8, 0)]

    assert fh.parse_format('FORMAT(20a4)') == [(20, str, 4, 0)]

    assert fh.parse_format('FORMAT(20A4, 5E16.8, 10I8)') == [
        (20, str, 4, 0),
        (5, float, 16, 8),
        (10, int, 8, 0)
    ]

def test_parse_format_bad_input():
    """Testing that the parse_format() method returns the correct (None,-1) for bad inputs."""

    assert fh.parse_format('') == (-1, None, -1, -1)

    assert fh.parse_format('20a4') == (-1, None, -1, -1)

    assert fh.parse_format('%FORMAT(20a4)') == (-1, None, -1, -1)

    assert fh.parse_format('FORMAT(20a4') == (-1, None, -1, -1)
