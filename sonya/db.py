from .document import Document


class Database:
    def __init__(self, name, schema):
        """
        :type environment: Environment
        :type schema: Schema
        :type name: str
        """
        self.name = name
        self.schema = schema
        self.environment = None
        self.db = None

    def define(self, environment, **kwargs):
        """
        :type environment: Environment
        """
        self.environment = environment
        self.environment["db"] = self.name.encode()

        key_base = ".".join(("db", self.name, 'scheme'))

        for field_name, field_type in self.schema:
            self.environment[key_base] = field_name.encode()
            k = ".".join((key_base, field_name))
            self.environment[k] = field_type.value()

        for key, value in kwargs.items():
            if isinstance(value, str):
                value = value.encode()

            self.environment['.'.join(('db', self.name, key))] = value

        return self

    def transaction(self):
        return self.environment.transaction()

    def create_document(self, **kwargs):
        doc = Document(self.db.document(), self.schema)
        doc.update(**kwargs)
        return doc

    def set(self, document):
        if not isinstance(document, Document):
            raise ValueError

        self.db.set(document.value)

    def get(self, **kwargs):
        doc = self.create_document(**kwargs)
        return self.db.get(doc.value)
