import msgpack
from .bytes_field import BytesField


class MessagePackField(BytesField):
    DEFAULT = None

    def from_python(self, value):
        return msgpack.packb(value, use_bin_type=True, encoding='utf-8')

    def to_python(self, value):
        return msgpack.unpackb(value, encoding='utf-8')
