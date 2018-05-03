from sonya import sophia
from .base import BaseField


class BytesField(BaseField):
    TYPE = sophia.Types.string
    DEFAULT = b''

    def from_python(self, value):
        """
        :type value: bytes
        """
        if not isinstance(value, bytes):
            raise ValueError('Expected bytes got %r' % type(value))

        return value

    def to_python(self, value):
        return value


class StringField(BytesField):
    DEFAULT = ''

    def from_python(self, value):
        """
        :type value: str
        """
        if not isinstance(value, str):
            raise ValueError('Expected str got %r' % type(value))

        return value.encode()

    def to_python(self, value):
        return value.decode()
