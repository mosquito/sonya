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

    def define_db(self, db_name, *args, **kwargs):
        yield "db", db_name

        key_base = ".".join(("db", db_name, 'scheme'))

        for field_name, field_type in self:
            yield key_base, field_name
            yield ".".join((key_base, field_name)), field_type.value()

        for key, value in args:
            yield '.'.join(('db', db_name, key)), value

        for key, value in kwargs.items():
            yield '.'.join(('db', db_name, key)), value


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


def with_metaclass(meta, *bases):
    class metaclass(type):

        def __new__(cls, name, this_bases, d):
            return meta(name, bases, d)

        @classmethod
        def __prepare__(cls, name, this_bases):
            return meta.__prepare__(name, bases)

    return type.__new__(metaclass, 'temporary_class', (), {})


Schema = with_metaclass(SchemaMeta, SchemaBase)


__all__ = ('Schema',)
