.. image:: https://api.travis-ci.org/mosquito/sonya.svg?branch=master
   :target: https://travis-ci.org/mosquito/sonya
   :height: 95 px
   :width: 215 px
   :alt: Sophia Library

.. image:: https://img.shields.io/pypi/v/sonya.svg
    :target: https://pypi.python.org/pypi/sonya/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/wheel/sonya.svg
    :target: https://pypi.python.org/pypi/sonya/

.. image:: https://img.shields.io/pypi/pyversions/sonya.svg
    :target: https://pypi.python.org/pypi/sonya/

.. image:: https://img.shields.io/pypi/l/sonya.svg
    :target: https://pypi.python.org/pypi/sonya/

.. _Sophia embedded database: http://sophia.systems/

Sonya
=====

`sonya`, fast Python bindings for `Sophia embedded database`_, v2.2.


About sonya:
++++++++++++

* Written in Cython for speed and low-overhead
* Clean, memorable APIs
* Extensive support for Sophia's features
* Python 2 **and** Python 3 support
* No 3rd-party dependencies besides Cython (for python>3)


About Sophia:
+++++++++++++

.. image:: http://sophia.systems/logo.png
   :target: http://sophia.systems/
   :alt: Sophia Library


* Document store
* ACID transactions
* MVCC, optimistic, non-blocking concurrency with multiple readers and writers.
* Multiple databases per environment
* Multiple- and single-statement transactions across databases
* Prefix searches
* Automatic garbage collection
* Hot backup
* Compression
* Multi-threaded compaction
* `mmap` support, direct I/O support
* APIs for variety of statistics on storage engine internals
* BSD licensed


Some ideas of where Sophia might be a good fit:

* Running on application servers, low-latency / high-throughput
* Time-series
* Analytics / Events / Logging
* Full-text search
* Secondary-index for external data-store

Limitations:
++++++++++++

.. _open an issue: https://github.com/mosquito/sonya/issues/new

* Not tested on Windows.

If you encounter any bugs in the library, please `open an issue`_,
including a description of the bug and any related traceback.

Installation
------------

.. _sophia: http://sophia.systems
.. _Cython: http://cython.org
.. _GitHub: https://github.com/mosquito/sonya
.. _PyPi: https://pypi.python.org/pypi/sonya/

The sophia_ sources are bundled with the `sonya` source
code, so the only thing you need to install is Cython_.
You can install from GitHub_ or from PyPi_.

Pip instructions:

.. code-block:: bash

    $ pip install Cython   # Optional
    $ pip install sonya


Or to install the latest code from master:

.. code-block:: bash

    $ pip install Cython   # Required
    $ pip install git+https://github.com/mosquito/sonya#egg=sonya


Git instructions:

.. code-block:: bash

    $ pip install Cython
    $ git clone https://github.com/mosquito/sonya
    $ cd sonya
    $ python setup.py build
    $ python setup.py install


To run the tests:

.. code-block:: python

    $ pip install pytest
    $ pytest tests


Overview
--------

.. _Sophia storage engine documentation: http://sophia.systems/v2.2/

Sonya
addition to normal dictionary operations, you can read slices of data that are
returned efficiently using cursors. Similarly, bulk writes using `update()` use
an efficient, atomic batch operation.

Despite the simple APIs, Sophia has quite a few advanced features. There is too
much to cover everything in this document, so be sure to check out the official
`Sophia storage engine documentation`_.

The next section will show how to perform common actions with `sonya`.

Using Sonya
-----------

Let's begin by import `sonya` and creating an environment. The environment
can host multiple databases, each of which may have a different schema. In this
example our database will store python objects as the key and value.
Finally we'll open the environment so we can start storing and retrieving data.

.. code-block:: python

   from sonya import Environment, fields, Schema


   class DictSchema(Schema):
       key = fields.PickleField(index=0)
       value = fields.PickleField()


   env = Environment('/tmp/test-env')
   db = env.database('test-database', DictSchema(), compression='zstd')
   env.open()

   document = db.document(key='foo', value=[1, 2, 3, 'bar'])

   # Insert a document
   db.set(document)

   print(db.get(key='foo'))
   # {'value': [1, 2, 3, 'bar'], 'key': 'foo'}


CRUD operations
+++++++++++++++

Sonya

.. code-block:: python

   from sonya import Environment, fields, Schema


   class DictSchema(Schema):
       key = fields.PickleField(index=0)
       value = fields.PickleField()


   env = Environment('/tmp/test-env')
   db = env.database('test-database', DictSchema(), compression='zstd')
   env.open()

   document = db.document(key='foo', value=[1, 2, 3, 'bar'])

   # Create a document
   db.set(document)

   # Read document
   document = db.get(key='foo')

   # Update the document
   document = db.document(key='foo', value=None)
   db.set(document)

   # Delete the document
   document = db.document(key='foo', value=None)
   db.delete(key='foo')

   # Iterate through the database
   for document in db.cursor():
      print(document)


Fetching ranges (Cursors)
+++++++++++++++++++++++++


Because Sophia is an ordered data-store, performing ordered range scans is
efficient. To retrieve a range of key-value pairs with Sonya
dictionary lookup with a `slice` instead.

For finer-grained control over iteration, or to do prefix-matching, Sonya
provides a cursor interface.

The `cursor()` method accepts special keyword parameter `order` and all
key fields:

* `order` (default=`>=`) -- semantics for matching the start key and ordering
  results.


.. code-block:: python

    from sonya import Environment, fields, Schema


    class IntSchema(Schema):
        key = fields.UInt32Field(index=0)
        value = fields.PickleField()


    env = Environment('/tmp/test-env')
    db = env.database('test-integer-db', IntSchema(), compression='zstd')
    env.open()


    with db.transaction() as tx:
        for i in range(10000):
            tx.set(db.document(key=i, value=None))

    # Iterate through the database
    for document in db.cursor(order='>=', key=9995):
        print(document)

    # {'key': 9995, 'value': None}
    # {'key': 9996, 'value': None}
    # {'key': 9997, 'value': None}
    # {'key': 9998, 'value': None}
    # {'key': 9999, 'value': None}


For prefix search use a part of the key and order:

.. code-block:: python

    from sonya import Environment, fields, Schema


    class StringSchema(Schema):
        key = fields.StringField(index=0)
        value = fields.PickleField()


    env = Environment('/tmp/test-env')
    db = env.database('test-string-db', IntSchema(), compression='zstd')
    env.open()


    with db.transaction() as tx:
        for i in range(10000):
            tx.set(db.document(key=str(i), value=None))

    # Iterate through the database
    for document in db.cursor(order='>=', key='999'):
        print(document)

    # {'value': None, 'key': '999'}
    # {'value': None, 'key': '9990'}
    # {'value': None, 'key': '9991'}
    # {'value': None, 'key': '9992'}
    # {'value': None, 'key': '9993'}
    # {'value': None, 'key': '9994'}
    # {'value': None, 'key': '9995'}
    # {'value': None, 'key': '9996'}
    # {'value': None, 'key': '9997'}
    # {'value': None, 'key': '9998'}
    # {'value': None, 'key': '9999'}



Transactions
++++++++++++

Sophia supports ACID transactions. Even better, a single transaction can cover
operations to multiple databases in a given environment.

Example usage:

.. code-block:: python

    class Users(Schema):
        name = fields.StringField(index=0)
        surname = fields.StringField(index=1)
        age = fields.UInt8Field()


    with users.transaction() as tx:
        tx.set(users.document(name='Jane', surname='Doe', age=19))
        tx.set(users.document(name='John', surname='Doe', age=18))

        # Raises LookupError
        db.get(name='John', surname='Doe')


Multiple transactions are allowed to be open at the same time, but if there are
conflicting changes, an exception will be thrown when attempting to commit the
offending transaction.


Configuring and Administering Sophia
------------------------------------

.. _configuration document: http://sophia.systems/v2.2/conf/sophia.html

Sophia can be configured using special properties on the `Sophia` and
`Database` objects. Refer to the `configuration document`_ for the details
on the  available options, including whether they are read-only, and the
expected data-type.

For example, to query Sophia's status, you can use the `status` property, which
is a readonly setting returning a string:

.. code-block:: python

    >>> print(env['sophia.status'])
    "online"


Other properties can be changed by assigning a new value to the property. For
example, to read and then increase the number of threads used by the scheduler:

.. code-block:: python

    >>> env['scheduler.threads'] = env['scheduler.threads'] + 2
    >>> env.open()
    >>> print(env['scheduler.threads'])
    8
    >>> print(dict(env))
    {'db.test-string-db.stat.cursor_latency': '0 0 0.0', ...}


.. _documentation: http://sophia.systems/v2.2/conf/sophia.html

Refer to the documentation_ for complete lists of settings.
Dotted-paths are translated into underscore-separated attributes.
