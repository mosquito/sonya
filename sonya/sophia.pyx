from cpython cimport bool
from libc.stdint cimport int64_t, int32_t
from libc.stdlib cimport calloc, free
from libc.string cimport memcpy, memcmp

from collections import namedtuple

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
class DocumentClosed(SophiaClosed): pass

class BadQuery(SophiaError): pass

class TransactionError(SophiaError): pass
class TransactionRollback(TransactionError): pass
class TransactionLocked(TransactionError): pass


IndexType = namedtuple('IndexType', ('value', 'is_bytes'))


cdef class Types:
    string = IndexType(b'string', True)
    u64 = IndexType(b'u64', False)
    u32 = IndexType(b'u32', False)
    u16 = IndexType(b'u16', False)
    u8 = IndexType(b'u8', False)
    u64_rev = IndexType(b'u64_rev', False)
    u32_rev = IndexType(b'u32_rev', False)
    u16_rev = IndexType(b'u16_rev', False)
    u8_rev = IndexType(b'u8_rev', False)


cdef class cstring:
    """ Simple lazy string on dynamic memory """

    cdef readonly char *c_str
    cdef readonly size_t size

    @classmethod
    def from_string(cls, str string):
        return cls(string.encode())

    def __cinit__(self, bytes value):
        cdef char* cvalue = value
        self.size = len(value)

        with nogil:
            self.c_str = <char*> calloc(self.size + 1, sizeof(char))
            memcpy(<void*> self.c_str, <void*> cvalue, self.size)

    def __dealloc__(self):
        if self.c_str != NULL:
            free(self.c_str)

    def __str__(self):
        return "%r" % self.value

    def __repr__(self):
        return self.__str__()

    @property
    def value(self):
        return self.c_str[:self.size]

    def __eq__(self, cstring other):
        cdef int result

        if self.size != other.size:
            return False

        with nogil:
            result = memcmp(self.c_str, other.c_str, self.size)

        return result == 0


cdef class Environment(object):
    cdef void *env
    cdef readonly bool _closed
    cdef readonly Configuration _configuration

    def __check_error(self, int rc):
        if rc != -1:
            return rc

        try:
            error = self.get_string('sophia.error').decode('utf-8', 'ignore')
        except KeyError:
            error = 'unknown error occurred.'

        raise SophiaError(error)

    def check_closed(self):
        if self._closed:
            raise SophiaClosed("Environment closed")

    def __cinit__(self):
        self.env = sp_env()
        self._closed = None
        self._configuration = Configuration(self)

    @property
    def configuration(self) -> dict:
        return dict(self._configuration)

    @property
    def is_closed(self):
        return self._closed

    @property
    def is_opened(self):
        return self._closed is not None

    def open(self) -> int:
        self.check_closed()

        cdef int rc

        with nogil:
            rc = sp_open(self.env)

        return self.__check_error(rc)

    def close(self) -> int:
        self.check_closed()

        cdef int rc

        if self.is_opened and self.env != NULL:
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

        value = buf[:nlen]
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
        return Transaction(self)


cdef class Configuration:
    cdef readonly Environment env

    def __cinit__(self, Environment env):
        self.env = env

    def __iter__(self):
        self.env.check_closed()

        cdef void *cursor

        with nogil:
            cursor = sp_getobject(self.env.env, NULL)

        if cursor == NULL:
            try:
                error = self.env.get_string('sophia.error').decode('utf-8', 'ignore')
            except KeyError:
                error = 'unknown error occurred.'

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
    cdef readonly Environment env
    cdef readonly bool closed
    cdef readonly list __refs

    def __check_error(self, int rc):
        if rc != -1:
            return rc

        try:
            error = self.env.get_string('sophia.error').decode('utf-8', 'ignore')
        except KeyError:
            error = 'unknown error occurred.'

        raise SophiaError(error)

    def __check_closed(self):
        if self.closed:
            raise TransactionError('Transaction closed')

        self.env.check_closed()

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

        if document.closed:
            raise DocumentClosed

        cdef int rc

        with nogil:
            rc = sp_set(self.tx, document.obj)
        document.obj = NULL

        self.__check_error(rc)
        self.__refs.append(Document)
        return rc

    def get(self, Document query) -> Document:
        cdef void* result_ptr = NULL

        cdef Database db = query.db

        with nogil:
            result_ptr = sp_get(self.tx, query.obj)
            # sp_get destroy object inside
            query.obj = NULL

        if result_ptr == NULL:
            raise LookupError

        result = Document(db, external=True, readonly=True)
        result.obj = result_ptr
        result.external = False
        return result

    def delete(self, Document query):
        cdef int rc

        with nogil:
            rc = sp_delete(self.tx, query.obj)
            query.obj = NULL

        return self.__check_error(rc)

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

        if self.tx != NULL:
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
            return rc

        try:
            error = self.env.get_string('sophia.error').decode('utf-8', 'ignore')
        except KeyError:
            error = 'unknown error occurred.'

        raise SophiaError(error)

    def document(self) -> Document:
        doc = Document(self)

        with nogil:
            doc.obj = sp_document(self.db)

        return doc

    def get(self, Document query) -> Document:
        cdef void* result_ptr = NULL

        with nogil:
            result_ptr = sp_get(self.db, query.obj)
            # sp_get destroy object inside
            query.obj = NULL

        if result_ptr == NULL:
            raise LookupError

        result = Document(self, external=True, readonly=True)
        result.obj = result_ptr
        result.external = False
        return result

    def set(self, Document document) -> int:
        cdef int rc

        if document.closed:
            raise DocumentClosed

        with nogil:
            rc = sp_set(self.db, document.obj)
            document.obj = NULL

        return self.__check_error(rc)

    def delete(self, Document document) -> int:
        cdef int rc

        with nogil:
            rc = sp_delete(self.db, document.obj)
            document.obj = NULL

        return self.__check_error(rc)

    cdef int32_t get_length(self) nogil:
        cdef void* obj
        cdef void* cursor
        cdef size_t result = 0

        obj = sp_document(self.db)

        if obj == NULL:
            return -1

        cursor = sp_cursor(self.env.env)

        if not cursor:
            return -1

        while True:
            obj = sp_get(cursor, obj)

            if obj != NULL:
                result += 1
            else:
                break

        if cursor != NULL:
            sp_destroy(cursor)

        return result

    def __len__(self) -> int:
        cdef int32_t result = 0

        with nogil:
            result = self.get_length()

        return self.__check_error(result)

    def cursor(self, dict query) -> Cursor:
        return Cursor(self.env, query, self)

    def transaction(self) -> Transaction:
        self.env.check_closed()
        return self.env.transaction()

    def delete_many(self, **query):
        query.setdefault('order', '>=')

        if query['order'] not in ('>=', '<=', '>', '<'):
            raise ValueError('Invalid order')

        cdef void* obj

        with nogil:
            obj = sp_document(self.db)

        if obj == NULL:
            self.__check_error(-1)

        prefix = '%s.scheme.' % self.name
        key_fields = []

        for key, value in self.env._configuration:
            if not key.startswith(prefix):
                continue

            if isinstance(value, int):
                continue

            if ',key(' not in value:
                continue

            key_fields.append((
                key.replace(prefix, '').encode(),
                'string' in value
            ))

        cdef size_t key_num = len(key_fields)

        cdef char **keys = <char**> calloc(sizeof(char*), key_num)
        cdef char *str_key = <char*> calloc(sizeof(char), key_num)

        for idx, item in enumerate(key_fields):
            key, is_str = item

            keys[idx] = key
            str_key[idx] = is_str

        document = Document(self, external=True)
        document.obj = obj

        for key, value in query.items():
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

        document.obj = NULL

        cdef void* tx
        cdef void* cursor

        with nogil:
            cursor = sp_cursor(self.env.env)
            tx = sp_begin(self.env.env)

        if tx == NULL or cursor == NULL:
            self.__check_error(-1)

        cdef size_t result = 0
        cdef void *rm_obj
        cdef char* str_v
        cdef int64_t int_v
        cdef int nlen

        with nogil:
            while True:
                obj = sp_get(cursor, obj)

                if obj == NULL:
                    if cursor != NULL:
                        sp_destroy(cursor)
                    break

                rm_obj = sp_document(self.db)

                for i in range(key_num):
                    k = keys[i]

                    if str_key[i]:
                        str_v = <char *>sp_getstring(obj, keys[i], &nlen)

                        sp_setstring(rm_obj, keys[i], str_v, nlen)
                        nlen = 0
                    else:
                        int_v = sp_getint(obj, keys[i])
                        sp_setint(rm_obj, keys[i], int_v)

                    str_v = b''
                    int_v = 0

                sp_delete(tx, rm_obj)
                result += 1

            sp_commit(tx)

        free(str_key)
        free(keys)

        return result


cdef class Cursor:
    cdef readonly Environment env
    cdef readonly Database db
    cdef readonly dict query

    def __raise_error(self):
        try:
            error = self.env.get_string(
                'sophia.error'
            ).decode('utf-8', 'ignore')
        except KeyError:
            error = 'unknown error occurred.'

        raise SophiaError(error)

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
            self.__raise_error()

        cdef void* cursor

        with nogil:
            cursor = sp_cursor(self.env.env)

        if not cursor:
            self.__raise_error()

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
                    document.obj = NULL
        finally:
            if cursor != NULL:
                with nogil:
                    sp_destroy(cursor)


cdef class Document:
    cdef void* obj
    cdef readonly Database db
    cdef char external
    cdef readonly list __refs
    cdef readonly bool readonly

    def __check_closed(self):
        if self.closed:
            raise DocumentClosed

        if self.db.env.is_closed:
            raise SophiaClosed

    def __cinit__(self, Database db, external=False, readonly=False):
        self.db = db
        self.external = 1 if external else 0
        self.__refs = []
        self.readonly = readonly

        if not self.external:
            with nogil:
                self.obj = sp_document(db.db)

            if self.obj == NULL:
                self.__check_error(-1)

    def __dealloc__(self):
        if self.obj != NULL and not self.external:
            with nogil:
                sp_destroy(self.obj)

        self.__refs[:] = []
        self.obj = NULL

    @property
    def closed(self) -> bool:
        return self.obj == NULL

    def __check_error(self, int rc):
        if rc != -1:
            return

        try:
            error = self.db.env.get_string(
                'sophia.error'
            ).decode('utf-8', 'ignore')
        except KeyError:
            error = 'unknown error occurred.'

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

        cdef bytes value = buf[:nlen]
        return value

    def get_int(self, str key) -> int:
        self.__check_closed()

        cdef cstring ckey = cstring.from_string(key)
        cdef int64_t result

        with nogil:
            result = sp_getint(self.obj, ckey.c_str)

        return result

    def set_string(self, str key, bytes value) -> int:
        if self.readonly:
            raise RuntimeError('read-only document')

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
        if self.readonly:
            raise RuntimeError('read-only document')

        self.__check_closed()

        cdef int rc
        cdef cstring ckey = cstring.from_string(key)
        cdef int64_t cvalue = value

        with nogil:
            rc = sp_setint(self.obj, ckey.c_str, cvalue)

        return self.__check_error(rc)
