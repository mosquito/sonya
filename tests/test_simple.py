import pytest
from enum import IntEnum
from sonya import fields, Schema


class SexEnum(IntEnum):
    male = 0
    female = 1


class Users(Schema):
    name = fields.StringField(index=0)
    surname = fields.StringField(index=1)
    sex = fields.IntEnumField(SexEnum)
    age = fields.UInt8Field()


@pytest.fixture()
def users(sonya_env):
    db = sonya_env.database('users', Users())
    sonya_env.open()
    return db


def test_insert(users):
    with users.transaction() as tx:
        document = users.document(name='John', surname='Doe')
        document['sex'] = SexEnum.male
        document['age'] = 18

        expected = dict(document)
        tx.set(document)

    with users.transaction() as tx:
        document = tx.get(name='John', surname='Doe')

        assert dict(document) == expected


def test_transaction(users):
    tx = users.transaction()
    document = users.document(name='John', surname='Doe')
    document['sex'] = SexEnum.male
    document['age'] = 18

    expected = dict(document)
    tx.set(document)

    document = tx.get(name='John', surname='Doe')

    assert dict(document) == expected
    tx.rollback()

    with users.transaction() as tx:
        with pytest.raises(LookupError):
            tx.get(name='John', surname='Doe')
