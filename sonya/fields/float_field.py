import struct
from .integer_field import UInt64Field


class FloatField(UInt64Field):
    DEFAULT = 0.0

    def from_python(self, value):
        return struct.unpack('>q', struct.pack('>d', value))[0]

    def to_python(self, value):
        return struct.unpack('>d', struct.pack('>q', value))[0]
