from enum import IntEnum
from .integer_field import Int16Field


class IntEnumField(Int16Field):
    __slots__ = ('enum',)

    def __init__(self, int_enum, default=Int16Field._DEFAULT, index=None):
        if not issubclass(int_enum, IntEnum):
            raise ValueError('Not IntEnum argument')

        self.enum = int_enum

        if default is self._DEFAULT:
            default = list(int_enum.__members__.items())[0][1]

        Int16Field.__init__(self, default=default, index=index)

    def from_python(self, value):
        return Int16Field.from_python(self, value.value)

    def to_python(self, value):
        num = super(IntEnumField, self).to_python(value)
        return self.enum(num)
