from .document import Document


class Transaction:
    __slots__ = 'tx', 'db'

    def __init__(self, db):
        self.db = db
        self.tx = db.db.transaction()

    def set(self, document):
        if not isinstance(document, Document):
            raise ValueError

        return self.tx.set(document.value)

    def get(self, **kwargs):
        if frozenset(kwargs.keys()) != self.db.schema.keys:
            raise ValueError('Not enough key fields')

        if self.db is None:
            raise RuntimeError("Can not get object on environment transaction")

        doc = self.tx.get(self.db.document(**kwargs).value)
        return Document(doc, self.db.schema, readonly=True)

    def delete(self, **kwargs):
        if self.db is None:
            raise RuntimeError("Can not get object on environment transaction")

        return self.tx.delete(self.db.document(**kwargs).value)

    def commit(self):
        return self.tx.commit()

    def rollback(self):
        return self.tx.rollback()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.tx.commit()
        else:
            self.tx.rollback()


class Database:
    def __init__(self, name, schema):
        self.name = name
        self.schema = schema
        self.environment = None
        self.db = None

    def define(self, environment, **kwargs):
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
        return Transaction(self)

    def document(self, **kwargs):
        doc = Document(self.db.document(), self.schema)
        doc.update(**kwargs)
        return doc

    def set(self, document):
        if not isinstance(document, Document):
            raise ValueError

        self.db.set(document.value)

    def get(self, **kwargs):
        if frozenset(kwargs.keys()) & self.schema.keys != self.schema.keys:
            raise ValueError('Not enough key fields')

        doc = self.document(**kwargs)
        return Document(self.db.get(doc.value), self.schema, readonly=True)

    def delete(self, **kwargs):
        doc = self.document(**kwargs)
        return self.db.delete(doc.value)

    def cursor(self, **query):
        for doc in self.db.cursor(query):
            yield Document(doc, self.schema, readonly=True)

    def __iter__(self):
        return self.cursor()

    def __len__(self):
        return len(self.db)

    def delete_many(self, **query):
        return self.db.delete_many(**query)
