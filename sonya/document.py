class Document:
    def __init__(self, doc, schema):
        self.value = doc
        self.__schema = schema
        self.__types = {}

        for field_name, field_type in self.__schema:
            self.__types[field_name] = field_type

            if field_type.index is not None:
                self[field_name] = field_type.DEFAULT

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
            else:
                continue

    def __repr__(self):
        return '%r' % dict(self)
