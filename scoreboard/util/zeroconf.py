"""Zeroconf services."""

import dbus

try:
    import avahi

    _NO_AVAHI = False
except ImportError:
    # will not work in the basic virtualenv
    _NO_AVAHI = True


class ZeroconfService(object):
    """Publish a network service with zeroconf using avahi."""

    def __init__(self, name, port, stype="_http._tcp", domain="", host="", text=""):
        """Initialize."""
        self.name = name
        self.stype = stype
        self.domain = domain
        self.host = host
        self.port = port
        self.text = text

    def publish(self, ipv4_only=True):
        """Publish service."""
        if _NO_AVAHI is True:
            return
        bus = dbus.SystemBus()
        server = dbus.Interface(
            bus.get_object(avahi.DBUS_NAME, avahi.DBUS_PATH_SERVER),
            avahi.DBUS_INTERFACE_SERVER,
        )

        g = dbus.Interface(
            bus.get_object(avahi.DBUS_NAME, server.EntryGroupNew()),
            avahi.DBUS_INTERFACE_ENTRY_GROUP,
        )

        if ipv4_only:
            proto = avahi.PROTO_INET
        else:
            proto = avahi.PROTO_UNSPEC

        g.AddService(
            avahi.IF_UNSPEC,
            proto,
            dbus.UInt32(0),
            self.name,
            self.stype,
            self.domain,
            self.host,
            dbus.UInt16(self.port),
            self.text,
        )

        g.Commit()
        self.group = g

    def unpublish(self):
        """Unpublish service."""
        if _NO_AVAHI is True:
            return
        self.group.Reset()
