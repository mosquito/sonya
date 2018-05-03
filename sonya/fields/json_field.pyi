from typing import Union
from .bytes_field import StringField


JSON_TYPE = Union[dict, str, type(None), float, bool, int, list]


class JSONField(StringField):
    DEFAULT = ...

    def from_python(self, value: JSON_TYPE) -> bytes: ...
    def to_python(self, value) -> JSON_TYPE: ...
