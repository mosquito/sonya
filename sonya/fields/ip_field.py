import ipaddress
from .integer_field import UInt64Field, UInt32Field


class IPv6Field(UInt64Field):
    DEFAULT = ipaddress.IPv6Address('::')

    def from_python(self, value):
        return int(ipaddress.IPv6Address(value))

    def to_python(self, value):
        return ipaddress.IPv6Address(value)


class IPv4Field(UInt32Field):
    DEFAULT = ipaddress.IPv4Address('0.0.0.0')

    def from_python(self, value):
        return int(ipaddress.IPv4Address(value))

    def to_python(self, value):
        return ipaddress.IPv4Address(value)
