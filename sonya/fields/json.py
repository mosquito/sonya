import json
from .bytes import BytesField


class JSONField(BytesField):
    DEFAULT = None

    def from_python(self, value):
        return json.dumps(value, ensure_ascii=False).encode()

    def to_python(self, value):
        return json.loads(value)
