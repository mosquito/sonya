import ipaddress
from .integer import Int64Field, Int32Field


class IPv6Field(Int64Field):
    DEFAULT = '::'

    def from_python(self, value):
        return int(ipaddress.IPv6Address(value))

    def to_python(self, value):
        return ipaddress.IPv6Address(value)


class IPv4Field(Int32Field):
    DEFAULT = '0.0.0.0'

    def from_python(self, value):
        return int(ipaddress.IPv4Address(value))

    def to_python(self, value):
        return ipaddress.IPv4Address(value)
