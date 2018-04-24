from cpython cimport bool
from libc.stdint cimport int64_t
from libc.stdlib cimport calloc, free
from libc.string cimport memcpy, memcmp


cdef extern from "src/sophia.h" nogil:
    cdef void *sp_env()
    cdef void *sp_document(void *)
    cdef int sp_setstring(void*, const char*, const void*, int)
    cdef int sp_setint(void*, const char*, int64_t)
    cdef void *sp_getobject(void*, const char*)
    cdef void *sp_getstring(void*, const char*, int*)
    cdef int64_t sp_getint(void*, const char*)
    cdef int sp_open(void *)
    cdef int sp_destroy(void *)
    cdef int sp_set(void*, void*)
    cdef int sp_upsert(void*, void*)
    cdef int sp_delete(void*, void*)
    cdef void *sp_get(void*, void*)
    cdef void *sp_cursor(void*)
    cdef void *sp_begin(void *)
    cdef int sp_prepare(void *)
    cdef int sp_commit(void *)


class SophiaError(Exception): pass
class SophiaClosed(SophiaError): pass
class DocumentClosed(SophiaError): pass
class BadQuery(SophiaError): pass
class TransactionError(SophiaError): pass
class TransactionRollback(TransactionError): pass
class TransactionLocked(TransactionError): pass


cdef class Types:
    string = b'string'
    u64 = b'u64'
    u32 = b'u32'
    u16 = b'u16'
    u8 = b'u8'
    u64_rev = b'u64_rev'
    u32_rev = b'u32_rev'
    u16_rev = b'u16_rev'
    u8_rev = b'u8_rev'


cdef class cstring:
    """ Simple lazy string on dynamic memory """

    cdef readonly char *c_str
    cdef readonly size_t size

    @classmethod
    def from_string(cls, str string):
        return cls(string.encode())

    def __cinit__(self, bytes value):
        cdef size_t size
        cdef char* cvalue = value

        self.size = len(value)

        with nogil:
            self.c_str = <char*> calloc(self.size, sizeof(char))
            memcpy(<void*> self.c_str, <void*> cvalue, self.size)

    def __dealloc__(self):
        if self.c_str != NULL:
            free(self.c_str)

    def __str__(self):
        return "%r" % self.value

    def __repr__(self):
        return self.__str__()

    def value(self):
        return self.c_str[:self.size]

    def __eq__(self, cstring other):
        cdef int result

        if self.size != other.size:
            return False

        with nogil:
            result = memcmp(self.c_str, other.c_str, self.size)

        return True if result == 0 else False


cdef class Environment(object):
    cdef void *env
    cdef readonly bool _closed
    cdef readonly Configuration configuration

    def __check_error(self, int rc):
        if rc != -1:
            return rc

        error = self.get_string('sophia.error') or 'unknown error occurred.'
        raise SophiaError(error)

    def check_closed(self):
        if self._closed:
            raise SophiaClosed

    def __cinit__(self):
        self.env = sp_env()
        self._closed = False
        self.configuration = Configuration(self)

    @property
    def is_closed(self):
        return self._closed

    def open(self) -> int:
        self.check_closed()

        cdef int rc

        with nogil:
            rc = sp_open(self.env)

        return self.__check_error(rc)

    def close(self) -> int:
        self.check_closed()

        cdef int rc

        with nogil:
            rc = sp_destroy(self.env)

        self._closed = True

        return self.__check_error(rc)

    def __dealloc__(self):
        if not self._closed:
            self.close()

    def get_string(self, str key) -> bytes:
        self.check_closed()

        cdef char* buf
        cdef int nlen
        cdef cstring ckey = cstring.from_string(key)

        with nogil:
            buf = <char *>sp_getstring(self.env, ckey.c_str, &nlen)

        if buf == NULL:
            raise KeyError("Key %r not found in document" % key)

        value = buf[:nlen - 1]
        return value

    def get_int(self, str key) -> int:
        self.check_closed()

        cdef cstring ckey = cstring.from_string(key)
        cdef int64_t result

        with nogil:
            result = sp_getint(self.env, ckey.c_str)

        return result

    def set_string(self, str key, bytes value) -> int:
        self.check_closed()

        cdef int rc

        cdef cstring ckey = cstring.from_string(key)
        cdef cstring cvalue = cstring(value)

        with nogil:
            rc = sp_setstring(self.env, ckey.c_str, cvalue.c_str, cvalue.size)

        self.__check_error(rc)
        return rc

    def set_int(self, str key, int value) -> int:
        self.check_closed()

        cdef cstring ckey = cstring.from_string(key)
        cdef int64_t cvalue = value
        cdef int rc

        with nogil:
            rc = sp_setint(self.env, ckey.c_str, cvalue)

        self.__check_error(rc)
        return rc

    def get_object(self, str name) -> Database:
        self.check_closed()
        cdef cstring cname = cstring.from_string(name)

        db = Database(self, name)

        with nogil:
            db.db = sp_getobject(self.env, cname.c_str)

        if db.db == NULL:
            self.__check_error(-1)

        return db

    def transaction(self) -> Transaction:
        self.check_closed()
        return Transaction(self)


cdef class Configuration:
    cdef readonly Environment env

    def __cinit__(self, Environment env):
        self.env = env

    def __iter__(self):
        cdef void *cursor

        with nogil:
            cursor = sp_getobject(self.env.env, NULL);

        if cursor == NULL:
            error = self.env.get_string('sophia.error') or \
                    'unknown error occurred.'
            raise SophiaError(error)


        cdef char *key, *value
        cdef int key_len, value_len
        cdef void* obj

        try:
            while True:
                with nogil:
                    obj = sp_get(cursor, obj)

                if obj == NULL:
                    raise StopIteration

                with nogil:
                    key = <char*> sp_getstring(obj, 'key', &key_len)
                    value = <char*> sp_getstring(obj, 'value', &value_len)

                if key_len > 0:
                    key_len -= 1

                if value_len > 0:
                    value_len -= 1

                k = key[:key_len].decode()
                v = value[:value_len].decode()

                key_len = 0
                value_len = 0

                if v.isdigit():
                    v = int(v)

                yield k, v

        finally:
            if cursor != NULL:
                with nogil:
                    sp_destroy(cursor)


cdef class Transaction:
    cdef void* tx
    cdef Environment env
    cdef bool closed
    cdef readonly list __refs

    def __check_error(self, int rc):
        if rc != -1:
            return rc

        error = self.env.get_string('sophia.error') or 'unknown error occurred.'
        raise SophiaError(error)

    def __check_closed(self):
        if self.closed:
            raise TransactionError('Transaction closed')

        if self.env.is_closed:
            raise SophiaClosed("Environment closed")

    def __cinit__(self, Environment env):
        self.closed = True
        self.env = env

        with nogil:
            self.tx = sp_begin(env.env)

        if not self.tx:
            self.__check_error(-1)

        self.closed = False
        self.__refs = []

    def set(self, Document document) -> int:
        self.__check_closed()

        cdef int rc

        with nogil:
            rc = sp_set(self.tx, document.obj)
        document.obj = NULL

        self.__check_error(rc)
        self.__refs.append(Document)
        return rc

    def commit(self) -> int:
        self.__check_closed()

        cdef int rc

        with nogil:
            rc = sp_commit(self.tx)

        self.__check_error(rc)

        self.closed = True
        self.tx = NULL

        if rc == 0:
            return 0
        elif rc == 1:
            raise TransactionRollback
        elif rc == 2:
            raise TransactionLocked

    def rollback(self) -> int:
        self.__check_closed()

        with nogil:
            sp_destroy(self.tx)

        self.tx = NULL
        self.closed = True

    def __enter__(self):
        self.__check_closed()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
            return

        self.commit()


cdef class Database:
    cdef readonly str name
    cdef readonly Environment env
    cdef void* db

    def __cinit__(self, Environment env, str name):
        self.name = name
        self.env = env

    def __check_error(self, int rc):
        if rc != -1:
            return

        error = self.env.get_string('sophia.error') or 'unknown error occurred.'
        raise SophiaError(error)

    def document(self) -> Document:
        doc = Document(self)

        with nogil:
            doc.obj = sp_document(self.db)

        return doc

    def get(self, Document query) -> Document:
        result = Document(self)

        with nogil:
            result.obj = sp_get(self.db, query.obj)

        if result.obj == NULL:
            self.__check_error(-1)

        return result

    def set(self, Document document) -> int :
        cdef int rc

        with nogil:
            rc = sp_set(self.db, document.obj)

        return self.__check_error(rc)

    def delete(self, Document document) -> int:
        cdef int rc

        with nogil:
            rc = sp_delete(self.db, document.obj)

        return self.__check_error(rc)

    def cursor(self, dict query) -> Cursor:
        return Cursor(self.env, query, self)

    def transaction(self) -> Transaction:
        return self.env.transaction()


cdef class Cursor:
    cdef readonly Environment env
    cdef readonly Database db
    cdef readonly dict query

    def __cinit__(self, Environment env, dict query, Database db):
        self.db = db
        self.env = env
        self.query = query

    def __init__(self, Environment env, dict query, Database db):
        self.query.setdefault('order', '>=')

        if self.query['order'] not in ('>=', '<=', '>', '<'):
            raise ValueError('Invalid order')

    def __iter__(self):
        document = Document(self.db, external=True)

        cdef void* obj
        with nogil:
            obj = sp_document(self.db.db)

        if obj == NULL:
            error = self.env.get_string('sophia.error') or \
                    'unknown error occurred.'
            raise SophiaError(error)


        cdef void* cursor

        with nogil:
            cursor = sp_cursor(self.env.env)

        if not cursor:
            error = self.env.get_string('sophia.error') or \
                    'unknown error occurred.'
            raise SophiaError(error)


        document.obj = obj

        for key, value in self.query.items():
            if not isinstance(key, str):
                raise BadQuery("Bad key. Key must be str %r %r" % (
                    key, type(key)
                ))

            if isinstance(value, int):
                document.set_int(key, value)
            elif isinstance(value, bytes):
                document.set_string(key, value)
            elif isinstance(value, str):
                document.set_string(key, value.encode())
            else:
                raise BadQuery(
                    "Bad value. Value must be bytes or int not %r %r" % (
                        value, type(value)
                    )
                )

        try:
            while True:
                with nogil:
                    obj = sp_get(cursor, obj)

                if obj == NULL:
                    raise StopIteration
                else:
                    document.obj = obj
                    yield document
        finally:
            with nogil:
                sp_destroy(cursor)


cdef class Document:
    cdef void* obj
    cdef readonly Database db
    cdef char external
    cdef readonly list __refs

    def __check_closed(self):
        if self.closed:
            raise DocumentClosed

        if self.db.env.is_closed:
            raise SophiaClosed

    def __cinit__(self, Database db, external=False):
        self.db = db
        self.external = 1 if external else 0
        self.__refs = []

        if not self.external:
            with nogil:
                self.obj = sp_document(db.db)

            if self.obj == NULL:
                self.__check_error(-1)

    def __dealloc__(self):
        if self.obj != NULL and not self.external:
            with nogil:
                sp_destroy(self.obj)

        self.__refs.clear()
        self.obj = NULL

    @property
    def closed(self) -> bool:
        return self.obj == NULL

    def __check_error(self, int rc):
        if rc != -1:
            return

        error = self.db.env.get_string('sophia.error') or \
                'unknown error occurred.'
        raise SophiaError(error)


    def get_string(self, str key) -> bytes:
        self.__check_closed()

        cdef char* buf
        cdef int nlen
        cdef bytes bkey
        cdef cstring ckey = cstring.from_string(key)

        with nogil:
            buf = <char *>sp_getstring(self.obj, ckey.c_str, &nlen)

        if buf == NULL:
            raise KeyError('Key %r not found in the document' % key)

        cdef bytes value = buf[:nlen - 1]
        return value

    def get_int(self, str key) -> int:
        self.__check_closed()

        cdef cstring ckey = cstring.from_string(key)
        cdef int64_t result

        with nogil:
            result = sp_getint(self.obj, ckey.c_str)

        return result

    def set_string(self, str key, bytes value) -> int:
        self.__check_closed()

        cdef int rc
        cdef cstring ckey = cstring.from_string(key)
        cdef cstring cvalue = cstring(value)

        with nogil:
            rc = sp_setstring(self.obj, ckey.c_str, cvalue.c_str, cvalue.size)

        self.__check_error(rc)
        self.__refs.append(ckey)
        self.__refs.append(cvalue)
        return rc

    def set_int(self, str key, int value) -> int:
        self.__check_closed()

        cdef int rc
        cdef cstring ckey = cstring.from_string(key)
        cdef int64_t cvalue = value

        with nogil:
            rc = sp_setint(self.obj, ckey.c_str, cvalue)

        return self.__check_error(rc)
