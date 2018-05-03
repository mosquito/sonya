from . import sophia
from .db import Database


class Environment:
    def __init__(self, path):
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
            return self.env.set_int(key, value)

        raise ValueError('Value must be str or int')

    def open(self):
        if self.env.is_closed:
            self._create_env()

        return self.env.open() == 0

    @property
    def is_closed(self):
        return self.env.is_closed

    @property
    def is_opened(self):
        return self.env.is_opened

    def __del__(self):
        if not self.env.is_closed:
            self.close()

    def __getitem__(self, item):
        return self.engine_config[item]

    def __iter__(self):
        return iter(self.engine_config.items())

    def close(self):
        self.env.close()

    def database(self, name, schema, **kwargs):
        db = Database(name, schema)
        db.define(self, **kwargs)

        database = self.env.get_object(".".join(('db', name)))
        db.db = database

        self.databases[name] = db, kwargs
        return db
