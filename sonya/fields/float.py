import struct
from .integer import Int64Field


class FloatField(Int64Field):
    DEFAULT = 0.0

    def from_python(self, value):
        return struct.unpack('>q', struct.pack('>d', value))[0]

    def to_python(self, value):
        return struct.unpack('>d', struct.pack('>q', value))[0]
