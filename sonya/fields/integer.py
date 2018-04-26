from sonya import sophia
from .base import BaseField


class Int64Field(BaseField):
    TYPE = sophia.Types.u64
    DEFAULT = 0

    def from_python(self, value):
        return int(value)

    def to_python(self, value):
        return value


class Int64ReverseField(Int64Field):
    TYPE = sophia.Types.u64_rev


class Int8Field(Int64Field):
    TYPE = sophia.Types.u8


class Int16Field(Int64Field):
    TYPE = sophia.Types.u16


class Int32Field(Int64Field):
    TYPE = sophia.Types.u32


class Int8ReverseField(Int64Field):
    TYPE = sophia.Types.u8_rev


class Int16ReverseField(Int64Field):
    TYPE = sophia.Types.u16_rev


class Int32ReverseField(Int64Field):
    TYPE = sophia.Types.u32_rev
