from sonya import Database


def test_version(bytes_db):
    """
    :type bytes_db: Database
    """
    assert bytes_db.environment['sophia.version'] == '2.2'


def test_status(bytes_db):
    """
    :type bytes_db: Database
    """
    assert bytes_db.environment['sophia.status'] == 'online'
