from typing import Union
from .bytes_field import BytesField


MSGPACK_TYPE = Union[dict, str, type(None), float, bool, int, list]


class MessagePackField(BytesField):
    DEFAULT = None

    def from_python(self, value: MSGPACK_TYPE) -> bytes: ...
    def to_python(self, value: bytes) -> MSGPACK_TYPE: ...
