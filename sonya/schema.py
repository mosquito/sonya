from six import with_metaclass
from sonya.fields import BaseField


class SchemaBase(object):
    def __init__(self, *args, **kwargs):
        self.__keys = None

    def __iter__(self):
        for field_name, field in self._fields.items():
            yield field_name, field

    @property
    def keys(self):
        if self.__keys is None:
            self.__keys = frozenset(
                {k for k, v in self.fields.items() if v.index is not None}
            )

        return self.__keys

    @property
    def fields(self):
        return dict(self._fields)


class SchemaMeta(type):
    def __new__(meta, name, bases, dct):
        keys = dict()
        fields = dict()

        for key, value in tuple(dct.items()):
            if not isinstance(value, BaseField):
                continue
            field = dct.pop(key)
            fields[key] = field

            if field.index is not None:
                keys[field.index] = field

        if keys:
            for idx in range(max(keys.keys()) + 1):
                if idx not in keys:
                    raise KeyError('Key fields must be numbered continuously')

        dct['_fields'] = fields
        dct['_keys'] = keys

        return super(SchemaMeta, meta).__new__(meta, name, bases, dct)

    def __init__(cls, name, bases, dct):
        super(SchemaMeta, cls).__init__(name, bases, dct)


Schema = with_metaclass(SchemaMeta, SchemaBase)


__all__ = ('Schema',)
