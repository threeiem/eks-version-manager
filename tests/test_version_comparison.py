import pytest
from eks_versions import compare_versions

def test_version_comparison():
    """Test the version comparison function"""
    assert compare_versions("1.27", "1.26") > 0
    assert compare_versions("1.26", "1.27") < 0
    assert compare_versions("1.26", "1.26") == 0
    
def test_version_comparison_with_patch():
    """Test version comparison with patch numbers"""
    assert compare_versions("1.27.1", "1.27.0") > 0
    assert compare_versions("1.27.0", "1.27.1") < 0
    assert compare_versions("1.27.1", "1.27.1") == 0

def test_invalid_version():
    """Test handling of invalid version strings"""
    assert compare_versions("invalid", "1.27") == 0
    assert compare_versions("1.27", "invalid") == 0
    assert compare_versions("invalid1", "invalid2") == 0
