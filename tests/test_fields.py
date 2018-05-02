from enum import IntEnum
from functools import partial
from itertools import product

import pytest
import uuid

from sonya import fields, Schema


class DummyEnum(IntEnum):
    cold = -30
    hot = +30


FIELD_TYPES = [
    fields.StringField,
    fields.BytesField,
    fields.PickleField,
    fields.Int8Field,
    fields.Int16Field,
    fields.Int32Field,
    fields.Int64Field,
    fields.UInt8Field,
    fields.UInt16Field,
    fields.UInt32Field,
    fields.UInt64Field,
    fields.UInt8ReverseField,
    fields.UInt16ReverseField,
    fields.UInt32ReverseField,
    fields.UInt64ReverseField,
    fields.PickleField,
    fields.IPv4Field,
    fields.IPv6Field,
    fields.MessagePackField,
    fields.JSONField,
    fields.FloatField,
    fields.UUIDField,
    partial(fields.IntEnumField, DummyEnum)
]


class TestSchema(Schema):
    pass


def schema_generator():
    for key_field, value_field in product(FIELD_TYPES, FIELD_TYPES):
        key = key_field(index=0)
        value = value_field()

        schema = TestSchema()
        schema._fields = {
            uuid.uuid4().hex[:8]: key,
            uuid.uuid4().hex[:8]: value,
        }

        schema._keys = [(uuid.uuid4().hex[:8], key)]

        yield schema


@pytest.mark.parametrize('schema', schema_generator())
def test_random_schema(schema, sonya_env):
    expected = {key: field.default for key, field in schema}

    db = sonya_env.database(uuid.uuid4().hex, schema)
    sonya_env.open()

    with db.transaction():
        document = db.document()
        db.set(document)

    with db.transaction():
        document = db.get(**expected)

        assert dict(document) == expected
