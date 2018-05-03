from contextlib import contextmanager

from .base import BaseField
from .integer_field import (
    Int8Field,
    Int16Field,
    Int32Field,
    Int64Field,
    UInt16Field,
    UInt16ReverseField,
    UInt32Field,
    UInt32ReverseField,
    UInt64Field,
    UInt64ReverseField,
    UInt8Field,
    UInt8ReverseField,
)
from .bytes_field import BytesField, StringField
from .float_field import FloatField
from .pickle_field import PickleField
from .uuid_field import UUIDField
from .ip_field import IPv6Field, IPv4Field
from .json_field import JSONField
from .enum_field import IntEnumField


__all__ = (
    "BaseField",
    "BytesField",
    "FloatField",
    "Int8Field",
    "Int16Field",
    "Int32Field",
    "Int64Field",
    "UInt16Field",
    "UInt16ReverseField",
    "UInt32Field",
    "UInt32ReverseField",
    "UInt64Field",
    "UInt64ReverseField",
    "UInt8Field",
    "UInt8ReverseField",
    "IntEnumField",
    "IPv4Field",
    "IPv6Field",
    "JSONField",
    "PickleField",
    "StringField",
    "UUIDField",
)


@contextmanager
def _suppress(exc_type):
    try:
        yield
    except exc_type:
        pass


with _suppress(ImportError):
    from .msgpack_field import MessagePackField
    __all__ += ('MessagePackField',)

