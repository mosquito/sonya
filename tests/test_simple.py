import pytest
from enum import IntEnum
from sonya import fields, Schema


class SexEnum(IntEnum):
    male = -1
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
