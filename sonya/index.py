from .sophia import Types


class BaseIndex:
    TYPE = None


class IntIndex(BaseIndex):
    TYPE = Types.u64


class BytesIndex(BaseIndex):
    TYPE = Types.string

