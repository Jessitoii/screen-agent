"""
Views module for the Windows OS Agent.

This module defines the graphical user interface using PyQt5, including
custom delegates for chat bubbles and the main application window.
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QListView, QVBoxLayout, QLabel,
    QPushButton, QTextEdit, QHBoxLayout, QSizePolicy, QFrame, QStackedWidget, QScrollArea
)
from PyQt5.QtCore import Qt, QRect, QPropertyAnimation
from PyQt5.QtGui import QPainter, QColor, QFont, QPalette
from .ui.viewmodels import MainViewModel, MessageListModel
from .ui.models import Message
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QStyledItemDelegate
from .orchestrator import run_orchestrator

class BubbleDelegate(QStyledItemDelegate):
    """Custom delegate for rendering chat messages as speech bubbles.

    Handles the drawing of user and assistant messages with different colors,
    alignments, and shadows.
    """
    PADDING = 12
    MAX_WIDTH = 520
    RADIUS = 10

    def paint(self, painter: QPainter, option, index):
        """Paints the message bubble and text.

        Args:
            painter: The QPainter object used for drawing.
            option: Style options for the item.
            index: The model index of the item being painted.
        """
        sender = index.model().data(index, MessageListModel.SenderRole)
        text = index.model().data(index, MessageListModel.TextRole)
        rect = option.rect
        painter.save()

        # choose bubble color and alignment based on sender
        if sender == "user":
            color = QColor("#DCF8C6")  # Light green for user
            align_right = True
            x = rect.right() - min(self.MAX_WIDTH, rect.width()) - 10
        else:
            color = QColor("#FFFFFF")  # White for assistant
            align_right = False
            x = rect.left() + 10

        # prepare text wrapping and font settings
        font = painter.font()
        font.setPointSize(10)
        painter.setFont(font)
        fm = painter.fontMetrics()
        
        # compute size using boundingRect for accurate bubble dimensions
        text_rect = fm.boundingRect(0, 0, self.MAX_WIDTH, 1000, Qt.TextWordWrap, text)
        bubble_w = text_rect.width() + self.PADDING * 2
        bubble_h = text_rect.height() + self.PADDING * 2

        bubble_rect = QRect(x, rect.top() + 6, bubble_w, bubble_h)
        
        # draw subtle shadow for the bubble
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 10))
        painter.drawRoundedRect(bubble_rect.adjusted(1, 2, 1, 2), self.RADIUS, self.RADIUS)
        
        # draw main bubble body
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(bubble_rect, self.RADIUS, self.RADIUS)

        # draw message text inside the bubble
        painter.setPen(QColor("#222"))
        painter.drawText(bubble_rect.adjusted(self.PADDING, self.PADDING, -self.PADDING, -self.PADDING),
                         Qt.TextWordWrap, text)

        painter.restore()

    def sizeHint(self, option, index):
        """Returns the size hint for the message item based on text content.

        Args:
            option: Style options for the item.
            index: The model index of the item.

        Returns:
            QSize: The recommended size for the item.
        """
        text = index.model().data(index, MessageListModel.TextRole)
        fm = option.fontMetrics
        text_rect = fm.boundingRect(0, 0, self.MAX_WIDTH, 1000, Qt.TextWordWrap, text)
        return QSize(text_rect.width() + self.PADDING * 4, text_rect.height() + self.PADDING * 3)

class EnterTextEdit(QTextEdit):
    """Custom QTextEdit that triggers send action on Enter key press.

    Supports Shift+Enter for new lines while treating Enter as the send command.
    """
    send_requested = lambda self, text: None

    def keyPressEvent(self, event):
        """Handles key press events to detect Enter/Return keys.

        Args:
            event: The QKeyEvent object.
        """
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
            # emit send request if text is not empty
            text = self.toPlainText().strip()
            if text:
                # Trigger the parent's on_send_clicked handler
                if hasattr(self.parent(), 'on_send_clicked'):
                    self.parent().on_send_clicked()
            self.clear()
            return
        super().keyPressEvent(event)

class MainWindow(QMainWindow):
    """Main application window for the Windows OS Agent.

    Sets up the UI layout including sidebar, chat area, and input controls.
    Manages communication between the UI and the agent orchestrator.
    """
    def __init__(self):
        """Initializes the main window and sets up the user interface."""
        super().__init__()
        self.setWindowTitle("Windows OS Agent")
        self.resize(1100, 700)

        self.vm = MainViewModel()
        central = QWidget()
        self.setCentralWidget(central)

        # Splitter to allow resizing sidebar and chat area
        splitter = QSplitter(Qt.Horizontal, self)
        splitter.setHandleWidth(6)

        # Sidebar setup (Conversation history placeholder)
        sidebar = QWidget()
        s_layout = QVBoxLayout(sidebar)
        header = QLabel("Windows OS Agent")
        header.setObjectName("appHeader")
        new_chat_btn = QPushButton("New Chat")
        new_chat_btn.clicked.connect(self.on_new_chat)
        conv_list = QListView()
        conv_list.setModel(self.vm.sidebar)
        conv_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        s_layout.addWidget(header)
        s_layout.addWidget(new_chat_btn)
        s_layout.addWidget(conv_list)

        # Main chat area setup
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        self.list_view = QListView()
        self.list_view.setModel(self.vm.chat.model)
        self.list_view.setItemDelegate(BubbleDelegate())
        self.list_view.setSpacing(8)
        self.list_view.setUniformItemSizes(False)
        self.list_view.setEditTriggers(QListView.NoEditTriggers)

        # Connect signals for auto-scrolling and animations
        self.vm.chat.model.rowsInserted.connect(self.on_rows_inserted)
        self.vm.chat.message_added.connect(self.animate_new_message)

        chat_layout.addWidget(self.list_view)

        # Input bar setup
        input_bar = QWidget()
        ib_layout = QHBoxLayout(input_bar)
        ib_layout.setContentsMargins(8, 8, 8, 8)
        self.input_edit = EnterTextEdit()
        self.input_edit.setFixedHeight(90)
        send_btn = QPushButton("Send")
        send_btn.setFixedWidth(100)
        send_btn.clicked.connect(self.on_send_clicked)
        ib_layout.addWidget(self.input_edit)
        ib_layout.addWidget(send_btn)
        chat_layout.addWidget(input_bar)

        # Add components to splitter
        splitter.addWidget(sidebar)
        splitter.addWidget(chat_container)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([280, 800])

        layout = QVBoxLayout()
        layout.addWidget(splitter)
        central.setLayout(layout)

        self._apply_default_focus()

    def _apply_default_focus(self):
        """Sets the initial focus to the input field."""
        self.input_edit.setFocus()

    def on_new_chat(self):
        """Handles the 'New Chat' button click event."""
        title = f"Chat {self.vm.sidebar.rowCount() + 1}"
        self.vm.sidebar.add(title)
        self.vm.chat.model.clear()
        self.input_edit.clear()

    def on_send_clicked(self):
        """Handles the 'Send' button click or Enter key press event."""
        text = self.input_edit.toPlainText().strip()
        if not text:
            return
        
        # Add user message to the UI
        self.vm.chat.send_user(text)
        
        # Immediate visual feedback
        self.vm.chat.send_assistant("Processing: " + (text[:200] + ("..." if len(text) > 200 else "")))
        self.input_edit.clear()
        
        # Start orchestrator and process steps
        for step in run_orchestrator(text):
            self.handle_orchestrator_step(step)

    def handle_orchestrator_step(self, step):
        """Processes a single step from the orchestrator and updates the UI.

        Args:
            step: A dictionary containing step information (thought, tool_result, etc.).
        """
        if step.get("thought") is not None:
            self.vm.chat.message_added("thought : ", step["thought"])
        elif step.get("result") is not None:
            self.vm.chat.message_added("result : ", step["result"])

    def on_rows_inserted(self, parent, first, last):
        """Scrolls the chat view to the bottom when new messages are added.

        Args:
            parent: The parent model index.
            first: The index of the first row inserted.
            last: The index of the last row inserted.
        """
        self.list_view.scrollToBottom()

    def animate_new_message(self, index):
        """Applies a simple fade-in animation to the chat view when a message arrives.

        Args:
            index: The model index of the new message.
        """
        anim = QPropertyAnimation(self.list_view, b"windowOpacity", self)
        anim.setDuration(220)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.start()