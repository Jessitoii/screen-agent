"""
Unit tests for the Security Policy module.

This module contains tests to verify path safety and application whitelist
enforcement.
"""
import unittest
import os
from src.agent.security.policy import is_path_safe, is_executable_allowed

class TestSecurity(unittest.TestCase):
    """Test suite for the security policy rules."""

    def test_is_path_safe(self):
        """Verifies that only paths within the base directory are considered safe."""
        base = os.path.abspath(os.path.expanduser('~'))
        safe_path = os.path.join(base, "documents")
        unsafe_path = "C:\\Windows\\System32"
        
        self.assertTrue(is_path_safe(safe_path, base))
        self.assertFalse(is_path_safe(unsafe_path, base))

    def test_is_executable_allowed(self):
        """Checks if only whitelisted applications are allowed for execution."""
        whitelist = ["notepad.exe", "calc.exe"]
        self.assertTrue(is_executable_allowed("notepad.exe", whitelist))
        self.assertTrue(is_executable_allowed("C:\\Windows\\System32\\calc.exe", whitelist))
        self.assertFalse(is_executable_allowed("cmd.exe", whitelist))

if __name__ == '__main__':
    unittest.main()