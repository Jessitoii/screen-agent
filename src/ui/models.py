"""
Models module for UI data structures.

This module defines the data classes used for representing chat messages
and other UI-related data.
"""
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Message:
    """Represents a single message in a chat conversation.

    Attributes:
        sender: The sender of the message ("user" or "assistant").
        text: The content of the message.
        timestamp: The time the message was created.
    """
    sender: str
    text: str
    timestamp: datetime = field(default_factory=datetime.utcnow)