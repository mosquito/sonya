import os
from collections import defaultdict
from threading import RLock

from . import sophia, fields
from .db import Database
from .schema import Schema


class SystemSchema(Schema):
    id = fields.UInt16Field(index=0)
    name = fields.StringField(index=1)
    index = fields.UInt16Field(index=2)
    key = fields.StringField()
    value = fields.StringField()


class Environment:
    _LOCKS = defaultdict(RLock)

    def __init__(self, path):
        self.path = path
        self._system = Database('schema', SystemSchema())
        self.env = None
        self._system_env = None
        self._system_db = None
        self.databases = set([])
        self._create_env()

    @property
    def _lock(self):
        return self._LOCKS[self.path]

    def _create_system_env(self):
        with self._lock:
            env = sophia.Environment()
            path = os.path.join(self.path, 'system')

            if not os.path.exists(path):
                os.makedirs(path)

            env['sophia.path'] = path
            env['scheduler.threads'] = 1

            system_schema_define = SystemSchema().define_db(
                'schema',
                ('compaction.cache', 8),
                compression='lz4',
                mmap=1,
            )

            for key, value in system_schema_define:
                env[key] = value

        return env

    def _create_env(self):
        with self._lock:
            self.env = sophia.Environment()
            self.env["sophia.path"] = self.path

            if self._system_env is None:
                self._system_env = self._create_system_env()
                self._system_db = self._system_env.get_object('db.schema')
                self._system_env.open()

            databases = {}

            for doc in self._system_db.cursor({'order': '>'}):
                db_id = str(doc.get_int('id'))
                name = doc.get_string('name').decode()
                key = doc.get_string('key').decode()
                value = doc.get_string('value')

                self.env[key] = value
                databases[db_id] = name
                print((key, value))

            for db_id, db_name in databases.items():
                db_conf_id = self.env.configuration["db.%s.id" % db_name]
                assert db_conf_id == db_id, \
                    'Wrong schema %r is not %r for db %r' % (
                        db_id, db_conf_id, db_name
                    )

            for db in self.databases:
                db.environment = self

    @property
    def engine_config(self):
        return self.env.configuration

    def __setitem__(self, key, value):
        self.env[key] = value

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
            self.close(reopen=False)

    def __getitem__(self, item):
        return self.env[item][:-1].decode()

    def __iter__(self):
        return iter(self.engine_config.items())

    def close(self, reopen=True):
        self.env.close()
        self._system_env.close()
        self._system_env = None

        if reopen:
            self._create_env()

    def _compare_schema(self, db_name, definition):
        db_prefix = "db.%s" % db_name

        current_definition = {
            (k, v) for k, v in self.engine_config.items()
            if k.startswith(db_prefix)
        }

        if not current_definition:
            return None

        scheme_prefix = 'db.%s.scheme.' % db_name

        current_schema = set(
            filter(
                lambda x: x in definition and scheme_prefix in x[0],
                current_definition
            )
        )

        new_schema = set(
            filter(
                lambda x: scheme_prefix in x[0],
                definition
            )
        )

        if current_schema - new_schema:
            return False

        param_prefix = 'db.%s.' % db_name
        scheme_prefix = 'db.%s.scheme' % db_name

        current_parameters = set(
            filter(
                lambda x: (
                    x in definition and
                    param_prefix in x[0] and
                    scheme_prefix not in x[0]
                ),
                current_definition
            )
        )

        new_parameters = set(
            filter(
                lambda x: (
                    x in definition and
                    param_prefix in x[0] and
                    scheme_prefix not in x[0]
                ),
                definition
            )
        )

        for param in new_parameters:
            if param not in current_parameters:
                return False

        return True

    def database(self, name, schema, **kwargs):
        with self._lock:
            db = Database(name, schema)
            scheme = list(schema.define_db(name, **kwargs))

            current_schema_is_equal = self._compare_schema(name, scheme)

            if current_schema_is_equal is None:
                for key, value in scheme:
                    self.env[key] = value

                db_id = self.env.configuration['db.%s.id' % name]

                for idx, key_value in enumerate(scheme):
                    key, value = key_value

                    doc = self._system_db.document()
                    doc['id'] = db_id
                    doc['index'] = idx
                    doc['key'] = key
                    doc['name'] = name
                    doc['value'] = value

                    self._system_db.set(doc)
            elif not current_schema_is_equal:
                raise RuntimeError('Database already exists '
                                   'with different scheme')

            db.environment = self

            database = self.env.get_object("db.%s" % name)
            db.db = database

            self.databases.add(db)

        return db
