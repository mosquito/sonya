from uuid import UUID
from .bytes_field import BytesField


class UUIDField(BytesField):
    DEFAULT = UUID('00000000-0000-0000-0000-000000000000')

    def from_python(self, value):
        """
        :type value: UUID
        """
        if not isinstance(value, UUID):
            raise ValueError('Expected UUID got %r' % type(value))

        return value.bytes

    def to_python(self, value):
        """
        :return: UUID
        """
        return UUID(bytes=value)
