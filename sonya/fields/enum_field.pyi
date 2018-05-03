from enum import IntEnum
from typing import Type

from .integer_field import Int16Field


class IntEnumField(Int16Field):
    def __init__(self, int_enum: Type[IntEnum], default=..., index=None):
        self.enum = ...     # type: Type[IntEnum]
    def from_python(self, value) -> int: ...
    def to_python(self, value) -> IntEnum: ...
