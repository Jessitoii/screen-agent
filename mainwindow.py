"""
Main entry point for the Windows OS Agent GUI.

This module defines the primary window and worker thread management
for the application, handling the visualization of the agent interaction.
"""
import sys
import threading
import time
from datetime import datetime
from typing import Dict, Any

from PyQt5.QtCore import Qt, pyqtSignal, QObject, QSize
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter, QListWidget, QListWidgetItem,
    QVBoxLayout, QLabel, QPushButton, QTextEdit, QHBoxLayout, QSizePolicy, QFrame, QScrollArea, QDesktopWidget
)
from PyQt5.QtGui import QColor, QFont
from PyQt5 import QtWidgets, QtGui, QtCore
from src.cursor.set_cursor import restore_cursor
from src.orchestrator import run_orchestrator


class UiMessage:
    """Data class for representing a message in the UI.

    Attributes:
        sender: The sender type ("user", "assistant", "thought", or "tool_result").
        content: The message text or data.
        timestamp: Epoch timestamp of the message.
        meta: Optional metadata dictionary.
    """
    def __init__(self, sender: str, content: str, timestamp: float = None, meta: Dict[str, Any] = None):
        """Initializes a UiMessage object."""
        self.sender = sender
        self.content = content
        self.timestamp = timestamp or time.time()
        self.meta = meta or {}


class OrchestratorWorker(QObject):
    """Worker class to run the orchestrator in a background thread.

    Communicates with the main UI thread via Qt signals.
    """
    step_signal = pyqtSignal(object)
    finished = pyqtSignal()

    def __init__(self, prompt: str):
        """Initializes the worker with a user prompt.

        Args:
            prompt: The user input to be processed.
        """
        super().__init__()
        self.prompt = prompt
        self._thread = None

    def start(self):
        """Starts the background thread for orchestration."""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        """Internal method that executes the orchestrator loop."""
        try:
            # Iterate through generator steps yielded by the orchestrator
            for step in run_orchestrator(self.prompt):
                # Emit step data to the main thread for UI update
                self.step_signal.emit(step)
                # Small delay to keep the UI responsive
                time.sleep(0.01)
        finally:
            self.finished.emit()


def make_bubble_widget(msg: UiMessage) -> QWidget:
    """Factory function to create a stylized chat bubble widget.

    Args:
        msg: The UiMessage object containing content and sender info.

    Returns:
        QWidget: A configured widget representing the message bubble.
    """
    w = QWidget()
    layout = QVBoxLayout(w)
    layout.setContentsMargins(6, 6, 6, 6)
    frame = QFrame()
    frame_layout = QVBoxLayout(frame)
    frame_layout.setContentsMargins(12, 8, 12, 8)

    label = QLabel(msg.content)
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextSelectableByMouse)
    label.setFont(QFont("Segoe UI", 10))

    # Apply specific styling based on message type
    if msg.sender == "user":
        frame.setStyleSheet("background:#2b79ff;color:white;border-radius:10px;")
        label.setStyleSheet("color:white;")
        frame_layout.addWidget(label)
        layout.addWidget(frame, 0, Qt.AlignRight)
    elif msg.sender == "assistant":
        frame.setStyleSheet("background:#ffffff;color:#111;border-radius:10px;")
        frame_layout.addWidget(label)
        layout.addWidget(frame, 0, Qt.AlignLeft)
    elif msg.sender == "thought":
        # Italicized gray bubble for internal reasoning
        label.setStyleSheet("color:#444;font-style:italic;")
        frame.setStyleSheet("background:#efefef;color:#444;border-radius:10px;")
        frame_layout.addWidget(label)
        layout.addWidget(frame, 0, Qt.AlignLeft)
    elif msg.sender == "tool_result":
        # Monospaced block for technical tool output
        label.setFont(QFont("Consolas", 9))
        frame.setStyleSheet("background:#111111;color:#f6f6f6;border-radius:6px;")
        frame_layout.addWidget(label)
        layout.addWidget(frame, 0, Qt.AlignLeft)
    else:
        frame_layout.addWidget(label)
        layout.addWidget(frame, 0, Qt.AlignLeft)

    return w


class MainWindow(QMainWindow):
    """Main Window class for the Windows OS Agent application.

    Manages the UI layout, input handling, and coordinates background workers.
    """
    def __init__(self):
        """Initializes the main window and sets up UI components."""
        super().__init__()
        self.setWindowTitle("Windows OS Agent - GUI")
        self.setWindowIcon(QtGui.QIcon("./public/icon.png"))
        self.resize(1100, 700)

        # Layout setup
        central = QWidget()
        self.setCentralWidget(central)

        splitter = QSplitter(Qt.Horizontal, self)
        splitter.setHandleWidth(6)

        # Sidebar component
        self.sidebar = QWidget()
        s_layout = QVBoxLayout(self.sidebar)
        header = QLabel("Windows OS Agent")
        header.setStyleSheet("font-weight:700;padding:8px;")
        new_chat_btn = QPushButton("New Chat")
        new_chat_btn.clicked.connect(self.on_new_chat)
        self.conv_list = QListWidget()
        self.conv_list.addItem("Conversation 1")
        self.conv_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        s_layout.addWidget(header)
        s_layout.addWidget(new_chat_btn)
        s_layout.addWidget(self.conv_list)

        # Chat area component
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        self.msg_list = QListWidget()
        self.msg_list.setSpacing(8)
        self.msg_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        chat_layout.addWidget(self.msg_list)

        # Input bar component
        input_bar = QWidget()
        ib_layout = QHBoxLayout(input_bar)
        ib_layout.setContentsMargins(8, 8, 8, 8)
        self.input_edit = QTextEdit()
        self.input_edit.setFixedHeight(90)
        send_btn = QPushButton("Send")
        send_btn.setFixedWidth(100)
        send_btn.clicked.connect(self.on_send_clicked)
        ib_layout.addWidget(self.input_edit)
        ib_layout.addWidget(send_btn)
        chat_layout.addWidget(input_bar)

        # Assemble main view
        splitter.addWidget(self.sidebar)
        splitter.addWidget(chat_container)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([280, 800])

        main_layout = QVBoxLayout()
        main_layout.addWidget(splitter)
        central.setLayout(main_layout)

        self._worker = None

    def on_new_chat(self):
        """Clears the chat display and starts a new conversation session."""
        self.conv_list.addItem(f"Conversation {self.conv_list.count() + 1}")
        self.msg_list.clear()
        self.input_edit.clear()

    def on_send_clicked(self):
        """Handles the user's prompt submission."""
        self.enterMiniMode()
        prompt = self.input_edit.toPlainText().strip()
        if not prompt:
            return
        
        # Display user message immediately
        user_msg = UiMessage(sender="user", content=prompt)
        self._append_message(user_msg)
        self.input_edit.clear()

        # Launch background orchestrator
        self._worker = OrchestratorWorker(prompt)
        self._worker.step_signal.connect(self.handle_orchestrator_step)
        self._worker.finished.connect(self.on_worker_finished)
        self._worker.start()
        self.exitMiniMode()

    def handle_orchestrator_step(self, step: Dict[str, Any]):
        """Updates the UI based on steps emitted by the background worker.

        Args:
            step: A dictionary containing step information (type, content).
        """
        stype = step.get("type")
        content = step.get("content")
        
        if stype == "user_prompt":
            note = UiMessage(sender="thought", content=f"Prompt submitted: {content}")
            self._append_message(note)
        elif stype == "thought":
            # Extract reasoning text from planner output
            if isinstance(content, dict):
                thought_text = content.get("thought") or str(content)
            else:
                thought_text = str(content)
            thought_msg = UiMessage(sender="thought", content=str(thought_text))
            self._append_message(thought_msg)
        elif stype == "tool_result":
            # Render tool output as indented JSON for readability
            import json
            try:
                text = json.dumps(content, ensure_ascii=False, indent=2)
            except Exception:
                text = str(content)
            tool_msg = UiMessage(sender="tool_result", content=text)
            self._append_message(tool_msg)
        elif stype == "assistant":
            assistant_msg = UiMessage(sender="assistant", content=str(content))
            self._append_message(assistant_msg)
        else:
            other_msg = UiMessage(sender="assistant", content=f"{stype}: {content}")
            self._append_message(other_msg)

    def _append_message(self, ui_msg: UiMessage):
        """Internal helper to add a message bubble to the list view.

        Args:
            ui_msg: The UiMessage object to render.
        """
        item = QListWidgetItem()
        widget = make_bubble_widget(ui_msg)
        item.setSizeHint(widget.sizeHint())
        self.msg_list.addItem(item)
        self.msg_list.setItemWidget(item, widget)
        self.msg_list.scrollToBottom()

    def on_worker_finished(self):
        """Cleanup handler for when the background worker finishes."""
        self.exitMiniMode()

    def enterMiniMode(self):
        """Transforms the window into a compact, frameless overlay mode."""
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.Tool
        )

        screen = QtWidgets.QApplication.primaryScreen()
        geo = screen.availableGeometry()

        self.resize(500, self.height())
        w = 500
        
        # Position window at the top-right of the screen
        x = geo.x() + geo.width() - w
        y = geo.y()
        self.move(x, y)

        self.show()

    def resizeEvent(self, event):
        """Responsive UI handler for sidebar visibility."""
        if self.width() < 800:
            self.sidebar.hide()
        else:
            self.sidebar.show()

    def exitMiniMode(self):
        """Restores the window to its standard desktop state."""
        self.setWindowFlags(QtCore.Qt.Widget)
        self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        # Load external stylesheet if present
        with open("./src/ui/styles.qss", "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except Exception as e:
        print(f"Failed to load stylesheet: {e}")
        
    win = MainWindow()
    win.show()
    # Ensure system cursors are reset on startup
    restore_cursor()
    sys.exit(app.exec_())