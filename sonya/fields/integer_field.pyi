import struct
from .base import BaseField


class UInt64Field(BaseField):
    TYPE = ...
    DEFAULT = ...

    def from_python(self, value) -> int: ...
    def to_python(self, value) -> int: ...


class UInt64ReverseField(UInt64Field):
    TYPE = ...


class UInt8Field(UInt64Field):
    TYPE = ...


class UInt16Field(UInt64Field):
    TYPE = ...


class UInt32Field(UInt64Field):
    TYPE = ...


class UInt8ReverseField(UInt64Field):
    TYPE = ...


class UInt16ReverseField(UInt64Field):
    TYPE = ...


class UInt32ReverseField(UInt64Field):
    TYPE = ...


class Int64Field(UInt64ReverseField):
    DEFAULT = 0
    FORMAT = 'Q', 'q'

    def from_python(self, value):
        return struct.unpack(
            self.FORMAT[0],
            struct.pack(self.FORMAT[1], value)
        )[0]

    def to_python(self, value):
        return struct.unpack(
            self.FORMAT[1],
            struct.pack(self.FORMAT[0], value)
        )[0]


class Int32Field(UInt32ReverseField, Int64Field):
    FORMAT = 'L', 'l'


class Int16Field(UInt16ReverseField, Int64Field):
    FORMAT = 'H', 'h'


class Int8Field(UInt8ReverseField, Int64Field):
    FORMAT = 'B', 'b'
