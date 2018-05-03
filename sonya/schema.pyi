from typing import Generator, FrozenSet, Dict
from .fields import BaseField


class SchemaBase(object):
    _fields = ...   # type: Dict[str, BaseField]

    def __init__(self, *args, **kwargs):
        self.__keys = ...   # type: FrozenSet[str]

    def __iter__(self) -> Generator[str, BaseField]: ...

    @property
    def keys(self) -> FrozenSet[str]: ...

    @property
    def fields(self) -> Dict[str, BaseField]: ...


class Schema(SchemaBase): ...
