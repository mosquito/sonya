try:
    import cPickle as pickle
except ImportError:
    import pickle

from .bytes_field import BytesField


class PickleField(BytesField):
    DEFAULT = pickle.dumps(None)

    def from_python(self, value):
        return pickle.dumps(value)

    def to_python(self, value):
        return pickle.loads(value)
