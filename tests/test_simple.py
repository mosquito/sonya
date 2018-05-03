import uuid
from random import choice, randint

import pytest
from enum import IntEnum
from sonya import fields, Schema


class SexEnum(IntEnum):
    male = -1
    female = 1


class UsersSchema(Schema):
    name = fields.StringField(index=0)
    surname = fields.StringField(index=1)
    sex = fields.IntEnumField(SexEnum)
    age = fields.UInt8Field()


class SequenceSchema(Schema):
    key = fields.UInt32Field(index=0)


@pytest.fixture()
def users(sonya_env):
    db = sonya_env.database('users', UsersSchema())
    sonya_env.open()
    return db


@pytest.fixture()
def sequence(sonya_env):
    db = sonya_env.database('sequence', SequenceSchema())
    sonya_env.open()
    return db


def test_insert(users):
    with users.transaction() as tx:
        document = users.document(name='Jane', surname='Doe')
        document['sex'] = SexEnum.female
        document['age'] = 19

        tx.set(document)

        document = users.document(name='John', surname='Doe')
        document['sex'] = SexEnum.male
        document['age'] = 18

        expected = dict(document)
        tx.set(document)

    with users.transaction() as tx:
        document = tx.get(name='John', surname='Doe')

        assert dict(document) == expected

    with users.transaction() as tx:
        tx.delete(name='John', surname='Doe')

        with pytest.raises(LookupError):
            tx.get(name='John', surname='Doe')


def test_no_transaction(users):
    document = users.document(name='John', surname='Doe')
    document['sex'] = SexEnum.male
    document['age'] = 18

    expected = dict(document)

    users.set(document)
    document = users.get(name='John', surname='Doe')

    assert dict(document) == expected

    with pytest.raises(ValueError):
        users.get(name='John')


def test_transaction(users):
    tx = users.transaction()
    document = users.document(name='John', surname='Doe')
    document['sex'] = SexEnum.male
    document['age'] = 18

    expected = dict(document)
    tx.set(document)

    document = tx.get(name='John', surname='Doe')

    with pytest.raises(ValueError):
        tx.get(name='John')

    assert dict(document) == expected
    tx.rollback()

    with users.transaction() as tx:
        with pytest.raises(LookupError):
            tx.get(name='John', surname='Doe')

        with pytest.raises(ValueError):
            tx.get(name='John')


def test_cursor(users):
    with users.transaction() as tx:
        tx.set(
            users.document(
                name='Jane',
                surname='Doe',
                sex=SexEnum.female,
                age=19
            )
        )

        tx.set(
            users.document(
                name='John',
                surname='Doe',
                sex=SexEnum.male,
                age=18
            )
        )

    for document in users.cursor():
        assert document['name'] in ('John', 'Jane')
        assert document['surname'] == 'Doe'
        assert document['sex'] in (SexEnum.female, SexEnum.male)
        assert document['age'] in (18, 19)


def test_length(users):
    for i in range(1000):
        assert len(users) == i

        users.set(
            users.document(
                name=uuid.uuid4().hex,
                surname=uuid.uuid4().hex,
                sex=choice([SexEnum.female, SexEnum.male]),
                age=randint(1, 100)
            )
        )


def test_delete_many(sequence):
    for i in range(5000):
        sequence.set(sequence.document(key=i))

    assert len(sequence) == 5000
    assert sequence.delete_many(order='<', key=100) == 100
    assert len(sequence) == 4900

    assert sequence.delete_many(order='>=', key=4000) == 1000
    assert len(sequence) == 3900

    assert sequence.delete_many() == 3900
    assert len(sequence) == 0

