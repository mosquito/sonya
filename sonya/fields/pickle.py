import pickle
from .bytes import BytesField


class PickleField(BytesField):
    DEFAULT = None

    def from_python(self, value):
        return pickle.dumps(value)

    def to_python(self, value):
        return pickle.loads(value)
