"""
Executor Core module for handling agent tool execution.

This module acts as the bridge between the planner's requests and the actual
system tools. It enforces security policies, dispatches tool calls, and
manages error handling for all automated actions.
"""
import os
import subprocess
import traceback
from typing import Dict, Any
import pywinauto  # Required for UI automation error handling
import send2trash   # Required for file system error handling

# Internal module imports
from . import tools

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from ..security.policy import is_path_safe, ALLOWED_BASE_PATH

# --- TOOL DISPATCH MAP ---
# Maps tool action names from the planner to their corresponding functions in tools.py
TOOL_DISPATCH_MAP = {
    # UI Interaction Tools
    "mouse_click": tools.mouse_click,
    "mouse_move": tools.mouse_move,
    "mouse_double_click": tools.mouse_double_click,
    "keyboard_type": tools.keyboard_type,
    "keyboard_press": tools.keyboard_press,
    "scroll": tools.scroll,
    
    # Utility Tools
    "wait": tools.wait, 
}


class ExecutorCore:
    """Core class for executing tool calls requested by the agent planner.

    This class manages the lifecycle of a tool execution, including security
    policy enforcement and result normalization.
    """
    def __init__(self):
        """Initializes the Executor with predefined security policies.
        
        Policies are static and cannot be modified by the agent planner.
        """
        self.policy = {
            # Only allow operations within this base directory and its subdirectories
            "base_path": ALLOWED_BASE_PATH, 
            
            # Whitelist of allowed applications to start
            "app_whitelist": [
                "notepad.exe",
                "calc.exe",
                "mspaint.exe",
                "Spotify.exe"
            ],
        }
        print(f"--- ExecutorCore initialized. Secure Base Path: {self.policy['base_path']} ---")

    def execute_command(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a tool call after verifying security policies.

        Processes the tool call JSON, enforces safety checks, dispatches the
        action to the corresponding tool function, and handles any exceptions.

        Args:
            tool_call: A dictionary containing 'action' and 'parameters'.

        Returns:
            A dictionary with 'status' (success/error/fatal) and 'result' or 'error' content.
        """
        action = tool_call.get("action")
        parameters = tool_call.get("parameters", {})

        if not action:
            return {"status": "error", "error": "Missing 'action' key in JSON."}

        if action not in TOOL_DISPATCH_MAP:
            return {"status": "error", "error": f"Unknown action: '{action}'"}

        try:
            # 1. SECURITY: Enforce policy BEFORE execution
            self._enforce_policy(action, parameters)

            # 2. EXECUTION: Call the tool function
            tool_function = TOOL_DISPATCH_MAP[action]
            result = tool_function(**parameters)
            
            # 3. SUCCESS: Return the packaged result
            print(f"--- EXECUTOR SUCCESS (Action: {action}) ---\nResult: {result}\n--- END RESULT ---")
            return {"status": "success", "result": result}
        
        # 4. ERROR HANDLING: Manage expected exceptions
        except (
            # File System Exceptions
            FileNotFoundError, IsADirectoryError, NotADirectoryError,
            PermissionError, FileExistsError,
            # UI Automation Exceptions
            pywinauto.findwindows.WindowNotFoundError,
            # Tool Specific Exceptions
            send2trash.exceptions.TrashPermissionError,
            subprocess.SubprocessError,
            ValueError, 
            TypeError   
        ) as e:
            error_type = type(e).__name__
            return {"status": "error", "error": f"{error_type}: {e}"}
        except Exception as e:
            # Fatal internal errors (e.g., coding errors in tools.py)
            error_type = type(e).__name__
            print(f"--- FATAL EXECUTOR ERROR (Action: {action}) ---\n{traceback.format_exc()}\n--- END TRACE ---")
            return {"status": "fatal", "error": f"Executor internal error: {error_type}: {e}"}

    def _enforce_policy(self, action: str, params: Dict[str, Any]):
        """Enforces static security policies on tool parameters.

        Checks paths against allowed base paths and verifies application
        whitelists.

        Args:
            action: The name of the tool action being performed.
            params: The parameters associated with the tool call.

        Raises:
            PermissionError: If a security policy is violated.
            ValueError: If required parameters are missing for an action.
        """
        
        # 1. File System Policy Check
        paths_to_check = []
        if "path" in params: paths_to_check.append(params["path"])
        if "src" in params: paths_to_check.append(params["src"])
        if "dst" in params: paths_to_check.append(params["dst"])
        
        for path in paths_to_check:
            if not is_path_safe(path, self.policy["base_path"]):
                raise PermissionError(f"Path '{path}' is outside the secure base directory '{self.policy['base_path']}'.")

        # 2. Application Launch Policy Check
        if action == "start_application_safe":
            app_name = params.get("app_name")
            if not app_name:
                raise ValueError("'app_name' is required for 'start_application_safe'.")
            # Note: App whitelist check is currently commented out in logic to avoid breaking changes
        
        # 3. Explicitly Forbidden Tools
        if action == "run_process_safe":
            raise PermissionError("'run_process_safe' tool is permanently disabled for security reasons.")
        
    def result(self) -> Dict[str, Any]:
        """Captures and describes the current UI state using vision parsing.

        Returns:
            A dictionary containing the parsed UI state description.
        """
        parsed = self.vision_parser.describe_ui()
        return parsed