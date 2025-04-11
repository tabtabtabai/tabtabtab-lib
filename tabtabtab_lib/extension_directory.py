from dataclasses import dataclass
from typing import List, Type
from enum import Enum, auto

from .extension_interface import ExtensionInterface


class BaseExtensionID(Enum):
    """
    Enum containing all possible extension IDs.
    """

    pass


class BaseExtensionDependencies(Enum):
    """
    Enum containing all possible extension dependencies.
    """

    pass


@dataclass
class ExtensionDescriptor:
    extension_id: BaseExtensionID
    description: str
    dependencies: List[BaseExtensionDependencies]
    extension_class: Type[ExtensionInterface]
