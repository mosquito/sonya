import abc


class BaseField(object):
    __slots__ = 'index', 'default'

    TYPE = None
    DEFAULT = None
    _DEFAULT = object()

    def __init__(self, default=_DEFAULT, index=None):
        """ Base field for the sophia document definition

        :param name: field name
        :param index: if not None the
        :type name: str
        :type index: int
        """

        if index is not None and index < 0:
            raise ValueError('Index must be grater then zero')

        self.index = index

        if default is self._DEFAULT:
            default = self.DEFAULT

        self.default = default

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
