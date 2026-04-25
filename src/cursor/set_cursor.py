"""
Cursor management module for Windows.

This module provides low-level system calls to change the system cursor's
appearance, specifically tinting it to indicate the agent's active state.
"""
import ctypes
from ctypes import wintypes

# Windows API DLLs
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

# Argument and return type definitions for GDI functions
gdi32.GetBitmapBits.argtypes = [wintypes.HBITMAP, wintypes.LONG, ctypes.c_void_p]
gdi32.GetBitmapBits.restype = wintypes.LONG
gdi32.SetBitmapBits.argtypes = [wintypes.HBITMAP, wintypes.DWORD, ctypes.c_void_p]
gdi32.SetBitmapBits.restype = wintypes.LONG
gdi32.GetObjectW.argtypes = [wintypes.HGDIOBJ, ctypes.c_int, ctypes.c_void_p]
gdi32.GetObjectW.restype = ctypes.c_int

# Standard Windows OCR (Object Cursor Resource) IDs
cursor_ids = [
    32512,  # OCR_NORMAL
    32513,  # OCR_IBEAM
    32514,  # OCR_WAIT
    32515,  # OCR_CROSS
    32516,  # OCR_UP
    32642,  # OCR_SIZENWSE
    32643,  # OCR_SIZENESW
    32644,  # OCR_SIZEWE
    32645,  # OCR_SIZENS
    32646,  # OCR_SIZEALL
    32648,  # OCR_NO
    32649,  # OCR_HAND
    32650,  # OCR_APPSTARTING
]

class ICONINFO(ctypes.Structure):
    """Windows ICONINFO structure representing cursor/icon information."""
    _fields_ = [
        ("fIcon", wintypes.BOOL),
        ("xHotspot", wintypes.DWORD),
        ("yHotspot", wintypes.DWORD),
        ("hbmMask", wintypes.HBITMAP),
        ("hbmColor", wintypes.HBITMAP)
    ]

class BITMAP(ctypes.Structure):
    """Windows BITMAP structure representing image data metadata."""
    _fields_ = [
        ("bmType", wintypes.LONG),
        ("bmWidth", wintypes.LONG),
        ("bmHeight", wintypes.LONG),
        ("bmWidthBytes", wintypes.LONG),
        ("bmPlanes", wintypes.WORD),
        ("bmBitsPixel", wintypes.WORD),
        ("bmBits", ctypes.c_void_p)
    ]

def change_cursor_color(ocr: int):
    """Tints a specific system cursor by modifying its bitmap data.

    This function loads a system cursor, copies it, modifies the color bits
    to apply a tint, and then updates the system cursor for that specific OCR ID.

    Args:
        ocr: The Windows Object Cursor Resource ID to modify.
    """
    # Load existing system cursor
    hcur = user32.LoadCursorW(None, ctypes.c_int(ocr))
    if not hcur:
        return

    # Create a copy to work on
    hicon = user32.CopyIcon(hcur)

    iconinfo = ICONINFO()
    if not user32.GetIconInfo(hicon, ctypes.byref(iconinfo)):
        return

    # CRITICAL: Monochrome cursors (black and white) do not have a color bitmap root.
    if not iconinfo.hbmColor:
        # Cleanup to prevent GDI handle leaks
        gdi32.DeleteObject(iconinfo.hbmMask)
        user32.DestroyIcon(hicon)
        print(f"Cursor {ocr} has no color map (monochrome). Skipping.")
        return

    # Get bitmap metadata
    bmpinfo = BITMAP()
    gdi32.GetObjectW(iconinfo.hbmColor, ctypes.sizeof(bmpinfo), ctypes.byref(bmpinfo))

    width = bmpinfo.bmWidth
    height = bmpinfo.bmHeight

    # Calculate buffer size (assuming 32-bit ARGB)
    buf_size = width * height * 4
    pixels = (ctypes.c_uint8 * buf_size)()

    # Retrieve raw pixel bits from GDI
    gdi32.GetBitmapBits(iconinfo.hbmColor, buf_size, pixels)

    # Apply tint to non-transparent pixels
    for i in range(0, buf_size, 4):
        if pixels[i+3] != 0: # Alpha channel check
            pixels[i+2] = 20   # Red component
            pixels[i+1] = 40   # Green component
            pixels[i+0] = 40   # Blue component

    # Write modified bits back to the bitmap
    gdi32.SetBitmapBits(iconinfo.hbmColor, buf_size, pixels)

    # Create a new cursor from the modified info and apply it system-wide
    new_cursor = user32.CreateIconIndirect(ctypes.byref(iconinfo))
    user32.SetSystemCursor(new_cursor, ocr)

    # CLEANUP: Delete temporary GDI objects to avoid system exhaustion/crash
    gdi32.DeleteObject(iconinfo.hbmMask)
    gdi32.DeleteObject(iconinfo.hbmColor)
    user32.DestroyIcon(hicon)

def tint_cursor_color_correct():
    """Iterates through common system cursors and applies a color tint."""
    for cursor_id in cursor_ids:
        try:
            change_cursor_color(cursor_id)
        except Exception as e:
            print(f"Error on cursor {cursor_id}: {e}")

def restore_cursor():
    """Restores all system cursors to their original default states."""
    SPI_SETCURSORS = 0x57
    user32.SystemParametersInfoW(SPI_SETCURSORS, 0, None, 0)

# Default initialization to ensure cursors are in a known state
restore_cursor()

