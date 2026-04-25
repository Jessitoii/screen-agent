"""
ViewModels module for the Windows OS Agent UI.

This module contains the PyQt5 models and viewmodels that manage the data
and state for the chat interface and sidebar.
"""
from PyQt5.QtCore import (
    Qt, QModelIndex, QAbstractListModel, QVariant, pyqtSignal, QObject
)
from typing import List
from .models import Message
from datetime import datetime

class MessageListModel(QAbstractListModel):
    """Qt model for managing a list of chat messages.

    Provides roles for sender, text, and timestamp to be used by UI delegates.
    """
    SenderRole = Qt.UserRole + 1
    TextRole = Qt.UserRole + 2
    TimeRole = Qt.UserRole + 3

    def __init__(self, messages: List[Message] = None):
        """Initializes the message list model.

        Args:
            messages: Optional initial list of messages.
        """
        super().__init__()
        self._messages = messages or []

    def rowCount(self, parent=QModelIndex()):
        """Returns the number of messages in the model.

        Args:
            parent: The parent model index.

        Returns:
            int: The row count.
        """
        return len(self._messages)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        """Returns the data for a given index and role.

        Args:
            index: The model index to retrieve data for.
            role: The role being requested.

        Returns:
            QVariant: The data for the requested role.
        """
        if not index.isValid():
            return QVariant()
        msg = self._messages[index.row()]
        if role == self.SenderRole:
            return msg.sender
        if role == self.TextRole or role == Qt.DisplayRole:
            return msg.text
        if role == self.TimeRole:
            return msg.timestamp.isoformat()
        return QVariant()

    def roleNames(self):
        """Maps role integers to byte string names for QML/Delegate access.

        Returns:
            dict: Mapping of role IDs to names.
        """
        return {
            self.SenderRole: b"sender",
            self.TextRole: b"text",
            self.TimeRole: b"time",
        }

    def add_message(self, message: Message):
        """Appends a new message to the model.

        Args:
            message: The Message object to add.
        """
        self.beginInsertRows(QModelIndex(), len(self._messages), len(self._messages))
        self._messages.append(message)
        self.endInsertRows()

    def clear(self):
        """Clears all messages from the model."""
        self.beginResetModel()
        self._messages.clear()
        self.endResetModel()

class ChatViewModel(QObject):
    """ViewModel for managing chat interactions and state.

    Emits signals when messages are added to the underlying model.
    """
    message_added = pyqtSignal(int)  # index added

    def __init__(self):
        """Initializes the chat viewmodel."""
        super().__init__()
        self.model = MessageListModel()

    def send_user(self, text: str):
        """Creates and adds a user message to the chat.

        Args:
            text: The text content of the message.
        """
        msg = Message(sender="user", text=text, timestamp=datetime.utcnow())
        self.model.add_message(msg)
        self.message_added.emit(self.model.rowCount() - 1)

    def send_assistant(self, text: str):
        """Creates and adds an assistant message to the chat.

        Args:
            text: The text content of the message.
        """
        msg = Message(sender="assistant", text=text, timestamp=datetime.utcnow())
        self.model.add_message(msg)
        self.message_added.emit(self.model.rowCount() - 1)

class SidebarListModel(QAbstractListModel):
    """Qt model for managing the list of chat titles in the sidebar."""
    TitleRole = Qt.UserRole + 1

    def __init__(self, items: List[str] = None):
        """Initializes the sidebar list model.

        Args:
            items: Optional initial list of chat titles.
        """
        super().__init__()
        self._items = items or []

    def rowCount(self, parent=QModelIndex()):
        """Returns the number of items in the sidebar.

        Args:
            parent: The parent model index.

        Returns:
            int: The row count.
        """
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        """Returns the data for a given index and role.

        Args:
            index: The model index to retrieve data for.
            role: The role being requested.

        Returns:
            QVariant: The data for the requested role.
        """
        if not index.isValid():
            return QVariant()
        if role == Qt.DisplayRole or role == self.TitleRole:
            return self._items[index.row()]
        return QVariant()

    def add(self, title: str):
        """Appends a new chat title to the sidebar.

        Args:
            title: The title string to add.
        """
        self.beginInsertRows(QModelIndex(), len(self._items), len(self._items))
        self._items.append(title)
        self.endInsertRows()

    def clear(self):
        """Clears all items from the sidebar."""
        self.beginResetModel()
        self._items.clear()
        self.endResetModel()

class MainViewModel(QObject):
    """Main ViewModel that aggregates chat and sidebar viewmodels.

    Acts as the single source of truth for the application state.
    """
    def __init__(self):
        """Initializes the main viewmodel with sub-viewmodels."""
        super().__init__()
        self.chat = ChatViewModel()
        self.sidebar = SidebarListModel(["Welcome"])