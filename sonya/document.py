class Document:
    __slots__ = 'value', '__schema', '__types', '__readonly'

    def __init__(self, doc, schema, readonly=False):
        self.value = doc
        self.__schema = schema
        self.__types = {}
        self.__readonly = readonly

        for field_name, field_type in self.__schema:
            self.__types[field_name] = field_type

            if not self.__readonly:
                self[field_name] = field_type.default

    def update(self, **kwargs):
        for key, value in kwargs.items():
            self[key] = value

    def __setitem__(self, key, value):
        if key not in self.__types:
            raise KeyError('Unknown key for schema %r' % self.__schema)

        typ = self.__types[key]
        value = typ.from_python(value)

        if typ.TYPE.is_bytes:
            self.value.set_string(key, value)
        else:
            self.value.set_int(key, value)

    def __getitem__(self, key):
        typ = self.__types[key]
        if typ.TYPE.is_bytes:
            return typ.to_python(self.value.get_string(key))
        else:
            return typ.to_python(self.value.get_int(key))

    def __contains__(self, item):
        try:
            self.value.get_string(item)
            return True
        except KeyError:
            return False

    def __iter__(self):
        for key in self.__types:
            if key in self:
                yield key, self[key]

    @property
    def __dict__(self):
        return dict(self)

    def __repr__(self):
        return '%r' % dict(self)
