import struct

from sonya import sophia
from .base import BaseField


class UInt64Field(BaseField):
    TYPE = sophia.Types.u64
    DEFAULT = 0

    def from_python(self, value):
        return int(value)

    def to_python(self, value):
        return value


class UInt64ReverseField(UInt64Field):
    TYPE = sophia.Types.u64_rev


class UInt8Field(UInt64Field):
    TYPE = sophia.Types.u8


class UInt16Field(UInt64Field):
    TYPE = sophia.Types.u16


class UInt32Field(UInt64Field):
    TYPE = sophia.Types.u32


class UInt8ReverseField(UInt64Field):
    TYPE = sophia.Types.u8_rev


class UInt16ReverseField(UInt64Field):
    TYPE = sophia.Types.u16_rev


class UInt32ReverseField(UInt64Field):
    TYPE = sophia.Types.u32_rev


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
