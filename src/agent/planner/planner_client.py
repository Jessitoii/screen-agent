"""
Planner Client module for communicating with Large Language Models.

This module provides the PlannerClient class, which manages the agent's
interaction history, handles system prompts (ReAct and Summarizer),
and interfaces with LLMs like Ollama or Gemini to determine the next steps.
"""
from typing import List, Dict, Optional, Any
from pathlib import Path
import json
import re
import pyautogui
import ollama  # Requires 'pip install ollama'

class PlannerClient:
    """Client for managing agent planning and LLM communication.

    Responsibilities include:
      - Loading system prompts (ReAct and Summarizer).
      - Maintaining a history of interaction entries.
      - Generating the next action step via an LLM.
      - Processing tool responses.
      - Summarizing history to manage context window size.
    """
    
    def __init__(self, react_prompt_path: str, summarizer_prompt_path: str) -> None:
        """Initializes the PlannerClient with prompt paths.

        Args:
            react_prompt_path: Path to the ReAct system prompt file.
            summarizer_prompt_path: Path to the Summarizer system prompt file.
        """
        self.react_prompt = self._load_prompt(react_prompt_path)
        self.summarizer_prompt = self._load_prompt(summarizer_prompt_path)
        self._history: List[Dict[str, Any]] = []  # list of dicts: {'role':..., 'content':...}
        self.model = "windows-agent:gemma"

    def _load_prompt(self, path: str) -> str:
        """Loads a prompt string from a file.

        Args:
            path: The file path to load from.

        Returns:
            str: The content of the file, or an empty string if it doesn't exist.
        """
        p = Path(path)
        return p.read_text(encoding="utf-8") if p.exists() else ""
    
    def screen_capture(self):
        """Captures a screenshot and saves it to 'screenshot.png'."""
        pyautogui.screenshot('screenshot.png')
        

    def _serialize_history_for_messages(self) -> List[Dict[str, str]]:
        """Converts internal history into LLM-compatible message formats.

        Returns:
            List[Dict[str, str]]: A list of messages with 'role' and 'content' keys.
        """
        msgs: List[Dict[str, str]] = []
        for e in self._history:
            role = e.get("role", "user")
            content = e.get("content", "")
            # Ensure content is a string; serialize dicts/lists to JSON
            if isinstance(content, (dict, list)):
                content = json.dumps(content, ensure_ascii=False)
            else:
                content = str(content)
            msgs.append({"role": role, "content": content})
        return msgs

    def _call_ollama(self, system_prompt: str, messages: List[Dict[str, str]], images = False) -> str:
        """Calls the Ollama chat endpoint.

        Args:
            system_prompt: The system instructions for the LLM.
            messages: The conversation history messages.
            images: Whether to include a screenshot in the request.

        Returns:
            str: The raw text response from the assistant.

        Raises:
            RuntimeError: If the API call fails or the response is malformed.
        """
        msgs = list(messages or [])
        # Ensure system prompt is present as the first message
        if not msgs or msgs[0].get("role") != "system":
            msgs = [{"role": "system", "content": system_prompt}] + msgs
        
        # Optionally attach a screenshot for multimodal analysis
        if images is True:
            msgs.append({
                "role": "user", 
                "content": "Here is the current screen image.", 
                "images": ["D:\\Software\\Python\\windows-os-agent\\screenshot.png"]
            })

        try:
            resp = ollama.chat(model=self.model, messages=msgs, format="json")  
        except Exception as e:
            raise RuntimeError("ollama.chat call failed", e) from e

        # Extract content from the response object
        assistant_text = resp.get("message", {}).get("content")

        print("assistant_text:", assistant_text)
        if assistant_text is None:
            raise RuntimeError(f"unable to extract assistant text from ollama response: {repr(resp)}")

        return str(assistant_text)

    def _extract_json_block(self, text: str) -> str:
        """Extracts the first valid JSON object or array from a string.

        Args:
            text: The potentially noisy string containing JSON.

        Returns:
            str: The extracted JSON substring.

        Raises:
            ValueError: If no valid JSON structure is found.
        """
        if not text:
            raise ValueError("empty assistant text")

        # 1. Look for markdown code blocks
        for m in re.finditer(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL):
            json_block = m.group(1)
            if re.match(r"^\s*(\{.*\}|\[.*\])\s*$", json_block, re.DOTALL):
                return json_block

        # 2. Manual brace counting for fallback extraction
        stack = []
        start_idx = -1
        for i, char in enumerate(text):
            if char in "{[":
                if not stack:
                    start_idx = i
                stack.append(char)
            elif char in "}]" and stack:
                stack.pop()
                if not stack:
                    return text[start_idx : i + 1]

        raise ValueError("no valid JSON block found in assistant text")

    def get_next_step(self, user_input: Optional[str] = None) -> Dict:
        """Generates the next action step from the LLM.

        Args:
            user_input: Optional new input from the user.

        Returns:
            Dict: The parsed JSON response containing either 'tool_call' or 'final_response'.

        Raises:
            ValueError: If the LLM response is invalid or missing required keys.
        """
        if user_input:
            self._history.append({"role": "user", "content": user_input})

        messages = self._serialize_history_for_messages()
        system_message = {"role": "system", "content": self.react_prompt}
        full_messages = [system_message] + messages

        self.screen_capture()
        assistant_text = self._call_ollama(self.react_prompt, full_messages, True)
        
        try:
            parsed = json.loads(self._extract_json_block(assistant_text))
        except Exception as exc:
            self._history.append({"role": "assistant", "content": {"status": "error", "error": f"invalid-json: {str(exc)}"}})
            raise

        # Validation of the expected response structure
        if not isinstance(parsed, dict) or ("tool_call" not in parsed and "final_response" not in parsed):
            self._history.append({"role": "assistant", "content": {"status": "error", "error": "invalid-response", "note": "missing tool_call and final_response"}})
            raise ValueError("LLM response contains neither tool_call nor final_response.")

        self._history.append({"role": "assistant", "content": parsed})
        return parsed

    def add_tool_response(self, result_json: Dict) -> None:
        """Adds a tool execution result to the interaction history.

        Args:
            result_json: The outcome of a tool execution.
        """
        self._history.append({"role": "tool", "content": result_json})

    def summarize_and_clear_history(self) -> None:
        """Summarizes the current history to compress the context.

        Replaces the current history with a single memory entry containing the summary.
        """
        messages = self._serialize_history_for_messages()
        system_message = {"role": "system", "content": self.summarizer_prompt}
        full_messages = [system_message] + messages

        summary_text = self._call_ollama(self.summarizer_prompt, full_messages, False)
        
        self._history.clear()
        self._history.append({"role": "memory", "content": summary_text})

    def _call_gemini(self, system_prompt: str, messages: List[Dict[str, str]]) -> str:
        """Calls the Google Gemini API as an alternative to Ollama.

        Args:
            system_prompt: System instructions for Gemini.
            messages: Conversation history.

        Returns:
            str: The response text from Gemini.

        Raises:
            RuntimeError: If the library is missing or the API call fails.
        """
        try:
            import google.generativeai as genai
            import os
            import json
        except ImportError:
            raise RuntimeError("Please install 'google.generativeai' library.")

        try:
            # Note: API key is hardcoded as per legacy logic; should ideally use environment variables.
            api_key = "AIzaSyDxXJfNUDzP_zDYAk2zpWLIkg2-VVr8VoU"
            genai.configure(api_key=api_key)
        except KeyError:
            raise RuntimeError("GOOGLE_API_KEY environment variable not set.")

        # Configure JSON mode for Gemini
        generation_config = genai.GenerationConfig(
            response_mime_type="application/json"
        )
        
        model = genai.GenerativeModel(
            'gemini-2.5-flash',
            system_instruction=system_prompt,
            generation_config=generation_config
        )

        # Convert messages to Gemini's specific 'role/parts' format
        gemini_history = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")

            if role == "assistant":
                role = "model"
            elif role == "tool":
                role = "user"
            elif role in ("system", "memory"):
                role = "user"  # Map system/memory to user role for Gemini processing

            # Ensure content is stringified
            content_str = json.dumps(content) if isinstance(content, dict) else str(content)
            gemini_history.append({'role': role, 'parts': [{'text': content_str}]})

        try:
            response = model.generate_content(gemini_history)
            print("Gemini response:", response.text)
            return response.text
        except Exception as e:
            raise RuntimeError(f"Gemini API call failed: {e}")