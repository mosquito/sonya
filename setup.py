try:
    from setuptools import setup, Extension, find_packages
except ImportError:
    from distutils.core import setup, Extension, find_packages


try:
    from Cython.Build import cythonize

    extensions = cythonize([
        Extension(
            "sonya.sophia",
            ["sonya/sophia.pyx", "sonya/src/sophia.c"],
        ),
    ], force=True, emit_linenums=False, quiet=True)

except ImportError:
    import warnings
    warnings.warn('Cython not installed, using pre-generated C source file.')
    extensions = [
        Extension(
            "sonya.sophia",
            ["sonya/sophia.c", "sonya/src/sophia.c"],
        ),
    ]

setup(
    name='sonya',
    version='0.6.6',
    description='Python bindings for the sophia database.',
    long_description=open('README.rst').read(),
    author='Dmitry Orlov',
    author_email="me@mosquito.su",
    ext_modules=extensions,
    license='BSD',
    include_package_data=True,
    packages=find_packages(exclude=['tests']),
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: MacOS',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
    python_requires=">=2.7.*, <4",
    install_requires=[
        'six',
    ],
    extras_require={
        'develop': [
            'Cython',
            'pytest',
            'backports.tempfile',
            'msgpack-python',
        ],
        'msgpack': [
            'msgpack-python',
        ],
        ':python_version < "3"': ['py2-ipaddress', 'enum34'],
    },
)
