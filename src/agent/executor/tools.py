"""
Tools module for system interactions.

This module provides low-level functions for mouse and keyboard control,
as well as utility functions like waiting. These tools are dispatched
by the ExecutorCore.
"""
import time
import pyautogui
from pywinauto import keyboard

# Mapping of common key names to pywinauto's send_keys syntax
SPECIAL_KEYS = {
    "CTRL": "^",
    "ALT": "%",
    "SHIFT": "+",
    "ENTER": "{ENTER}",
    "TAB": "{TAB}",
    "ESC": "{ESC}",
    "SPACE": " ",
    "BACKSPACE": "{BACKSPACE}",
    "DELETE": "{DELETE}",
    "UP": "{UP}",
    "DOWN": "{DOWN}",
    "LEFT": "{LEFT}",
    "RIGHT": "{RIGHT}",
}


def wait(seconds: float) -> float:
    """Pauses execution for a specified number of seconds.

    Args:
        seconds: The number of seconds to wait.

    Returns:
        float: The number of seconds actually waited.

    Raises:
        ValueError: If the provided seconds value is not a valid number.
    """
    # Attempt to convert to float; potential ValueError is caught by ExecutorCore
    s = float(seconds)
    time.sleep(s)
    return s


def mouse_click(x: int, y: int, button: str = "left") -> str:
    """Performs a mouse click at the specified screen coordinates.

    Args:
        x: The horizontal screen coordinate.
        y: The vertical screen coordinate.
        button: The mouse button to click ("left", "right", or "middle").

    Returns:
        str: A confirmation message indicating the click location and button.
    """
    # Use pyautogui for robust cross-application clicking with a slight duration for realism
    pyautogui.click(x=int(x), y=int(y), button=button, duration=0.8)
    return f"clicked:{int(x)},{int(y)}:{button}"


def keyboard_type(text: str) -> str:
    """Simulates typing a string of text on the keyboard.

    Args:
        text: The string to be typed.

    Returns:
        str: A confirmation message indicating the text that was typed.
    """
    # pywinauto's send_keys handles text input effectively
    keyboard.send_keys(text, with_spaces=True)
    return f"typed-text:{text}"


def mouse_move(x: int, y: int) -> str:
    """Moves the mouse cursor to the specified screen coordinates.

    Args:
        x: The horizontal screen coordinate.
        y: The vertical screen coordinate.

    Returns:
        str: A confirmation message indicating the move coordinates.
    """
    pyautogui.moveTo(int(x), int(y), duration=0.8)
    return f"moved-mouse:{int(x)},{int(y)}"


def mouse_double_click(x: int, y: int, button: str = "left") -> str:
    """Performs a mouse double-click at the specified screen coordinates.

    Args:
        x: The horizontal screen coordinate.
        y: The vertical screen coordinate.
        button: The mouse button to double-click ("left", "right", or "middle").

    Returns:
        str: A confirmation message indicating the double-click location and button.
    """
    pyautogui.doubleClick(x=int(x), y=int(y), button=button, duration=0.8)
    return f"double-clicked:{int(x)},{int(y)}:{button}"


def keyboard_press(text: str = "ENTER") -> str:
    """Simulates complex keyboard key presses and combinations.

    Args:
        text: The key or key combination to press (e.g., "ENTER", "CTRL+S").

    Returns:
        str: A confirmation message indicating the keys pressed.
    """
    parts = text.split("+")
    sequence = ""

    # Parse key combinations into pywinauto-compatible sequences
    for p in parts:
        p_upper = p.upper()

        if p_upper in SPECIAL_KEYS:
            sequence += SPECIAL_KEYS[p_upper]
        elif len(p) == 1:
            # Single character keys like "A" or "1"
            sequence += p
        else:
            # Multi-character keys like F1 or HOME
            sequence += f"{{{p_upper}}}"

    keyboard.send_keys(sequence)
    return f"pressed-keys:{text}"


def scroll(amount: int) -> str:
    """Scrolls the mouse wheel by a specified amount.

    Args:
        amount: The number of scroll units (positive for up, negative for down).

    Returns:
        str: A confirmation message indicating the scroll amount.
    """
    pyautogui.scroll(amount)
    return f"scrolled-mouse:{amount}"


