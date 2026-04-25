"""
Security Policy module for path and executable validation.

This module provides utility functions to ensure that the agent only
operates within a secure base directory and only interacts with
whitelisted applications.
"""
import os
from typing import List

# --- SECURE BASE PATH ---
# The primary directory where the agent is allowed to perform operations.
# Defaults to the user's home directory to prevent access to system folders like C:\Windows.
ALLOWED_BASE_PATH = os.path.abspath(os.path.expanduser('~'))


def is_path_safe(path: str, base_path: str = ALLOWED_BASE_PATH) -> bool:
    """Checks if a given path is within the secure base directory.

    This function protects against Path Traversal attacks (e.g., using '../')
    by normalizing the path and verifying its common root with the base path.

    Args:
        path: The file or directory path to check.
        base_path: The root directory that the path must reside within.

    Returns:
        bool: True if the path is safe, False otherwise.
    """
    
    # 1. Normalize the path (resolving '~' and '..')
    try:
        if not path:
            return False
        normalized_path = os.path.abspath(os.path.expanduser(path))
    except Exception:
        # Invalid path (e.g., contains null bytes)
        return False

    # 2. Security Check (Path Traversal Protection)
    # Using os.path.commonpath to ensure the normalized path is actually under base_path.
    # A simple string startswith check is insufficient as it can be spoofed.
    try:
        common = os.path.commonpath([normalized_path, base_path])
    except ValueError:
        # Occurs if paths are on different drives (e.g., C: vs D:)
        return False
        
    return os.path.normpath(common) == os.path.normpath(base_path)


def is_executable_allowed(app_name: str, whitelist: List[str]) -> bool:
    """Verifies if an application is present in the static whitelist.

    The check is case-insensitive and only considers the base filename of the application.

    Args:
        app_name: The name or path of the application to check.
        whitelist: A list of allowed application names.

    Returns:
        bool: True if the application is whitelisted, False otherwise.
    """
    if not app_name:
        return False
        
    # Extract basename and convert to lowercase for comparison
    app_basename = os.path.basename(app_name).lower()
    
    for allowed_app in whitelist:
        if app_basename == allowed_app.lower():
            return True
            
    return False