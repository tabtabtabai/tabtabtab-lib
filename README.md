# TabTabTab Library

This documentation is auto-generated based on code analysis.

## Overview

TabTabTab is a framework for building extensions that enhance text copy/paste operations with AI capabilities. The library enables developers to create extensions that can intelligently process content when users copy or paste text, providing contextual assistance and transformations.

## Core Components

### Extension System

Extensions follow a plugin-based architecture where each extension implements a standard interface and can be loaded and managed by the framework.

#### `ExtensionInterface` [(source)](src/extension/interface.py)

The abstract base class that all extensions must implement:

```python
class ExtensionInterface(abc.ABC):
    # Core methods that must be implemented:
    async def on_context_request(self, source_extension_id: str, context_query: Dict[str, Any]) -> Optional[OnContextResponse]:
        # Provides context for other extensions or framework components
        pass
    
    async def on_copy(self, context: Dict[str, Any]) -> Optional[CopyResponse]:
        # Handles copy events from the user
        pass
    
    async def on_paste(self, context: Dict[str, Any]) -> Optional[PasteResponse]:
        # Handles paste events and can modify content
        pass
```

#### Extension Registration [(source)](src/extension/registry.py)

Extensions are described and registered using the `ExtensionDescriptor` class:

```python
@dataclass
class ExtensionDescriptor:
    extension_id: BaseExtensionID
    description: str
    dependencies: List[BaseExtensionDependencies]
    extension_class: Type[ExtensionInterface]
```

To register your extension, contribute to the [TabTabTab OSS repository](https://github.com/tabtabtab/tabtabtab-oss).

### LLM Integration [(source)](src/llm/processor.py)

The library provides a standardized interface for interacting with Language Models:

```python
class LLMProcessorInterface(abc.ABC):
    @abc.abstractmethod
    async def process(
        self,
        system_prompt: Optional[str],
        message: str,
        contexts: List[LLMContext],
        model: LLMModel,
        stream: bool = False,
        # ... other parameters
    ) -> Union[str, AsyncGenerator[str, None]]:
        pass
```

#### Supported Models [(source)](src/llm/models.py)

The framework supports various LLM models through the `LLMModel` enum:

```python
class LLMModel(str, Enum):
    # Top Shelf Models
    ANTHROPIC_SONNET = "claude-3-5-sonnet-latest"
    ANTHROPIC_CLAUDE_SONNET_3_7 = "claude-3-7-sonnet-latest"
    GEMINI_FLASH2 = "gemini-2.0-flash"
    
    # Additional models from Anthropic, OpenAI, and Google
    # ...
```

### Communication System

The library includes a notification system for communicating with users. Extensions should use the `send_push_notification` method provided in the `ExtensionInterface` rather than directly accessing the SSE interface:

```python
async def send_push_notification(self, device_id: str, notification: Notification) -> None:
    """
    Sends a push notification to the user.
    """
    # Implementation details...
```

## User Notifications

Extensions can send notifications to users with various statuses:

```python
class NotificationStatus(Enum):
    PENDING = "pending"  # Extension is running normally
    READY = "ready"      # Extension is disabled by user/system
    ERROR = "error"      # Extension encountered an error

@dataclass
class Notification:
    request_id: str
    title: str
    detail: str
    content: str
    status: NotificationStatus
```

## Extension Response Types

Extensions can return different response types for copy and paste events:

```python
@dataclass
class CopyResponse:
    notification: Notification
    
@dataclass
class PasteResponse:
    paste: Union[ImmediatePaste, Notification]
    
@dataclass
class ImmediatePaste:
    content: str
```

## Context System

Extensions can request and provide context to enrich the user experience:

```python
@dataclass
class OnContextResponse:
    @dataclass
    class ExtensionContext:
        description: str
        context: str
    
    contexts: List[ExtensionContext]
```

## Getting Started

To create a new extension:

1. Create a class that inherits from `ExtensionInterface`
2. Implement the required abstract methods
3. Register your extension by contributing to the [TabTabTab OSS repository](https://github.com/tabtabtab/tabtabtab-oss)

---

*This documentation was automatically generated from the TabTabTab library source code.*
