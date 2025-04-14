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
        is_processing_task: Boolean indicating if the extension has started a
                       longer-running background task related to this copy event.
                       Defaults to False.
    """

    notification: Notification
    is_processing_task: bool = False

    def to_dict(self) -> Dict[str, str]:
        """
        Serializes the CopyResponse to a JSON-compatible dictionary.
        """
        dict = {}
        if self.notification:
            dict["notification"] = self.notification.to_dict()

        dict["is_processing_task"] = self.is_processing_task
        return dict


@dataclass
class PasteResponse:
    """
    Response object returned by the on_paste method.
    """

    paste: Union[ImmediatePaste, Notification]
    is_processing_task: bool = False

    def is_accepted(self) -> bool:
        """
        Returns True if the paste request is accepted by the extension.
        """
        return self.paste is not None or self.is_processing_task

    def to_dict(self) -> Dict[str, str]:
        """
        Serializes the PasteResponse to a JSON-compatible dictionary.
        """
        dict = {}
        if isinstance(self.paste, Notification):
            dict["notification"] = self.paste.to_dict()
        elif isinstance(self.paste, ImmediatePaste):
            dict["immediate_paste"] = self.paste.to_dict()

        dict["is_processing_task"] = self.is_processing_task

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
    ) -> OnContextResponse:
        """
        Asynchronously handles requests for additional context.
        Extensions can inspect the context_query and return relevant data.

        Args:
            source_extension_id: The ID of the extension or module requesting context.
            context_query: A dictionary representing the initial context or query.

        Returns:
            OnContextResponse object containing a list of ExtensionContext objects.
        """
        pass

    @abc.abstractmethod
    async def on_copy(self, context: Dict[str, Any]) -> CopyResponse:
        """
        Handles a 'copy' event triggered by the user.

        This method is called when the framework detects a copy action relevant
        to potentially triggering extensions (e.g., copying text in a specific
        application). The extension can use the provided context to perform
        background tasks, prepare data, or interact with external services.

        Args:
            context: A dictionary containing information about the copy event.
                     Common keys include:
                     - 'device_id': str
                     - 'session_id': str
                     - 'request_id': str
                     - 'timestamp': str (ISO format UTC)
                     - 'window_info': Dict[str, Any] (parsed window info)
                     - 'screenshot_provided': bool
                     - 'selected_text': Optional[str]
                     - 'screenshot_data': Optional[bytes] (Raw image data if screenshot_provided is True)

        Returns:
            A CopyResponse object, potentially containing a message to notify
            the user and indicating if a background task was started.
        """
        pass

    @abc.abstractmethod
    async def on_paste(self, context: Dict[str, Any]) -> PasteResponse:
        """
        Handles a 'paste' event triggered by the user, potentially modifying
        or providing the content to be pasted.

        This method is called when the framework routes a paste action to this
        specific extension. The extension can analyze the context and decide
        whether to provide custom content to be pasted.

        Args:
            context: A dictionary containing information about the paste event,
                     such as the target application, active URL, current
                     clipboard content (if available), etc.

        Returns:
            A PasteResponse object containing the optional content to paste
            and/or an optional message to notify the user.
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
