import abc


class BaseField:
    __slots__ = 'index',

    TYPE = None
    DEFAULT = None

    def __init__(self, index=None):
        """ Base field for the sophia document definition

        :param name: field name
        :param index: if not None the
        :type name: str
        :type index: int
        """
        if index is not None and index < 0:
            raise ValueError('Index must be grater then zero')

        self.index = index

    def value(self):
        result = self.TYPE.value

        if self.index is not None:
            result += b",key(" + str(self.index).encode() + b")"

        return result

    @abc.abstractmethod
    def from_python(self, value):
        raise NotImplementedError

    @abc.abstractmethod
    def to_python(self, value):
        raise NotImplementedError

    @classmethod
    def check_type(cls, other):
        typ = bytes if cls.TYPE.is_bytes else int
        return isinstance(other, typ)
