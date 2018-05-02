import json
from .bytes_field import StringField


class JSONField(StringField):
    DEFAULT = None

    def from_python(self, value):
        return json.dumps(value, ensure_ascii=False).encode()

    def to_python(self, value):
        return json.loads(super(JSONField, self).to_python(value))
