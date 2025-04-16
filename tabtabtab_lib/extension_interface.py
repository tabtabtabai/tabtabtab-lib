import abc
from typing import Any, Dict, Optional, Union, List
from dataclasses import dataclass
from .sse_interface import SSESenderInterface
from .llm_interface import LLMProcessorInterface
import logging
from enum import Enum

log = logging.getLogger(__name__)


class NotificationStatus(Enum):
    """
    Enum representing the status of an extension.
    """

    PENDING = "pending"  # Extension is running normally
    READY = "ready"  # Extension is disabled by user/system
    ERROR = "error"  # Extension encountered an error

@dataclass
class Notification:
    """
    Data class representing a push notification.
    """

    request_id: str
    title: str
    detail: str
    content: str
    status: NotificationStatus

    def to_dict(self) -> Dict[str, str]:
        """
        Serializes the Notification to a JSON-compatible dictionary.

        Returns:
            A dictionary containing the notification data.
        """
        return {
            "notification_request_id": self.request_id,
            "notification_title": self.title,
            "notification_detail": self.detail,
            "notification_content": self.content,
            "notification_status": self.status.value,
        }

@dataclass
class ImmediatePaste:
    """
    Data class representing an immediate paste.
    """

    content: str

    def to_dict(self) -> Dict[str, str]:
        """
        Serializes the ImmediatePaste to a JSON-compatible dictionary.
        """
        return {"immediate_paste_content": self.content}


@dataclass
class CopyResponse:
    """
    Response object returned by the on_copy method.

    Attributes:
        notification: Notification object to be sent to the user.
    """

    notification: Notification

    def to_dict(self) -> Dict[str, str]:
        """
        Serializes the CopyResponse to a JSON-compatible dictionary.
        """
        dict = {}
        if self.notification:
            dict["notification"] = self.notification.to_dict()

        return dict


@dataclass
class PasteResponse:
    """
    Response object returned by the on_paste method.
    """

    paste: Union[ImmediatePaste, Notification]

    def to_dict(self) -> Dict[str, str]:
        """
        Serializes the PasteResponse to a JSON-compatible dictionary.
        """
        dict = {}
        if isinstance(self.paste, Notification):
            dict["notification"] = self.paste.to_dict()
        elif isinstance(self.paste, ImmediatePaste):
            dict["immediate_paste"] = self.paste.to_dict()

        return dict


@dataclass
class OnContextResponse:
    """
    Response object returned by the on_context_request method.
    """

    @dataclass
    class ExtensionContext:
        """
        Object to describe the context provided by an extension.
        """

        description: str
        context: str

    contexts: List[ExtensionContext]


class ExtensionInterface(abc.ABC):
    """
    Abstract Base Class defining the interface for all TabTabTab extensions.

    Each extension module must contain a class that inherits from this
    interface and implements all its abstract methods.
    """

    def __init__(
        self,
        sse_sender: SSESenderInterface,
        llm_processor: LLMProcessorInterface,
        extension_id: str,
    ):
        """
        Initializes the SampleExtension.

        Args:
            sse_sender: An object conforming to the SSESenderInterface
                        for sending notifications back to the client.
            llm_processor: An object conforming to the LLMProcessorInterface
                           for interacting with language models.
        """
        self.api_key: Optional[str] = None
        self.llm_processor = llm_processor  # Store the injected LLM processor
        self.sse_sender = sse_sender  # Store the injected SSE sender
        self.extension_id = extension_id
        log.info(f"[{self.extension_id}] Initializing...")

    @abc.abstractmethod
    async def on_context_request(
        self, source_extension_id: str, context_query: Dict[str, Any]
    ) -> Optional[OnContextResponse]:
        """
        Asynchronously handles requests for additional context.
        Extensions can use the context_query to get information about the current state of the application.

        Args:
            source_extension_id: Currently hardcoded to "tabtabtab_framework"; you can ignore this.
            context_query: A dictionary representing the current state of the application.
                Common keys include:
                - 'request_id': str, Unique identifier for this specific request
                - 'window_info': Dict[str, Any], Dictionary containing information about the active window; contains the url if the active window is a browser
                - 'screenshot_provided': bool, Boolean indicating if a screenshot is available
                - 'screenshot_data': Optional[bytes], Raw image data when a screenshot is provided
                - 'session_contents': str, Contents of the current session
                - 'hint': str, Parsed hint information
                - 'sticky_hint': str, Persistent hint information

        Returns:
            OnContextResponse object containing a list of ExtensionContext objects.
            If the extension does not need to provide any context, it should return None.
        """
        pass

    @abc.abstractmethod
    async def on_copy(self, context: Dict[str, Any]) -> Optional[CopyResponse]:
        """
        Handles a 'copy' event triggered by the user.

        This method is called when the framework detects a copy action relevant
        to potentially triggering extensions (e.g., copying text in a specific
        application). The extension can use the provided context to perform
        background tasks, prepare data, or interact with external services.

        Args:
            context: A dictionary containing information about the copy event.
                     Common keys include:
                     - 'request_id': str, Unique identifier for this specific request
                     - 'timestamp': str (ISO format UTC), Timestamp of the copy event
                     - 'window_info': Dict[str, Any], Dictionary containing information about the active window; contains the url if the active window is a browser
                     - 'screenshot_provided': bool, Boolean indicating if a screenshot is available
                     - 'selected_text': Optional[str], Text that was selected by the user
                     - 'screenshot_data': Optional[bytes] (Raw image data if screenshot_provided is True)

        Returns:
            A CopyResponse object, potentially containing a message to notify
            the user and indicating if a background task was started.
            Return None suggests that the extension skips processing the copy event.
        """
        pass

    @abc.abstractmethod
    async def on_paste(self, context: Dict[str, Any]) -> Optional[PasteResponse]:
        """
        Handles a 'paste' event triggered by the user.

        This method is called when the framework detects a paste action relevant
        to potentially triggering extensions. The extension can analyze the context 
        and decide whether to provide custom content to be pasted.

        Args:
            context: A dictionary containing information about the paste event.
                     Common keys include:
                     - 'request_id': str, Unique identifier for this specific request
                     - 'window_info': Dict[str, Any], Dictionary containing information about the active window; contains the url if the active window is a browser
                     - 'screenshot_provided': bool, Boolean indicating if a screenshot is available
                     - 'screenshot_data': Optional[bytes], Raw image data when a screenshot is provided
                     - 'session_contents': str, Contents of the current session
                     - 'hint': str, Parsed hint information
                     - 'sticky_hint': str, Persistent hint information

        Returns:
            A PasteResponse object containing the optional content to paste
            and/or an optional message to notify the user.
            Return None suggests that the extension skips processing the paste event.
        """
        pass

    async def send_push_notification(
        self, device_id: str, notification: Notification
    ) -> None:
        """
        Sends a push notification to the user.
        """
        notification_dict = notification.to_dict()
        notification_dict["extension_id"] = self.extension_id
        await self.sse_sender.send_event(
            device_id, "extension_notification", notification_dict
        )
