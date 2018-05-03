import pytest

try:
    from tempfile import TemporaryDirectory
except ImportError:
    from backports.tempfile import TemporaryDirectory

from sonya import Schema, Environment, fields


@pytest.fixture()
def sonya_env():
    with TemporaryDirectory() as env_path:
        env = Environment(env_path)

        try:
            yield env
        finally:
            env.close()


class BytesSchema(Schema):
    key = fields.BytesField(index=0)
    value = fields.BytesField()


@pytest.fixture()
def bytes_db(sonya_env):
    """
    :type sonya_env: Environment
    """

    if sonya_env.is_opened:
        sonya_env.close()

    db = sonya_env.database(
        'bytes-database',
        BytesSchema(),
        compression='zstd'
    )

    sonya_env.open()
    return db


class StringSchema(Schema):
    key = fields.StringField(index=0)
    value = fields.StringField()


@pytest.fixture()
def string_db(sonya_env):
    """

    :type sonya_env: Environment
    """
    if sonya_env.is_opened:
        sonya_env.close()

    db = sonya_env.database(
        'string-database',
        StringSchema(),
        compression='zstd'
    )

    sonya_env.open()
    return db
