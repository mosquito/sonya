from . import sophia
from .db import Database
from .document import Document


class Transaction:
    def __init__(self, tx):
        self.tx = tx

    def set(self, document):
        if not isinstance(document, Document):
            raise ValueError

        return self.tx.set(document.value)

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


class Environment:
    def __init__(self, path):
        """ Creates an environment
        :type path: str
        """
        self.path = path
        self.env = None
        self.databases = dict()
        self._create_env()

    def _create_env(self):
        self.env = sophia.Environment()
        self.env.set_string("sophia.path", self.path.encode())

        for db_name, db_kwargs in self.databases.items():
            db, kwargs = db_kwargs
            db.define(self, **kwargs)
            db.db = self.env.get_object(".".join(('db', db_name)))

    @property
    def engine_config(self):
        return self.env.configuration

    def __setitem__(self, key, value):
        if isinstance(value, bytes):
            return self.env.set_string(key, value)
        elif isinstance(value, int):
            return self.env.set_string(key, value)

        raise ValueError('Value must be str or int')

    def open(self):
        """ Open the environment

        :return bool
        """

        if self.env.is_closed:
            self._create_env()

        return self.env.open() == 0

    def __del__(self):
        if not self.env.is_closed:
            self.close()

    def __getitem__(self, item):
        return self.engine_config[item]

    def close(self):
        self.env.close()

    def database(self, name, schema, **kwargs):
        """ Declaring a new database

        :type name: str
        :type schema: Schema
        :return Database
        """
        db = Database(name, schema)
        db.define(self, **kwargs)

        database = self.env.get_object(".".join(('db', name)))
        db.db = database

        self.databases[name] = db, kwargs
        return db

    def transaction(self):
        """

        :return: sophia.Transaction
        """
        return Transaction(self.env.transaction())
