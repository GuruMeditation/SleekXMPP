"""
    SleekXMPP: The Sleek XMPP Library
    See the file LICENSE for copying permission.
"""

from __future__ import absolute_import

import logging
import base64
import sys
import hashlib
import socket as Socket
import time

from sleekxmpp import plugins
from sleekxmpp import stanza
from sleekxmpp.basexmpp import BaseXMPP
from sleekxmpp.xmlstream import XMLStream, RestartStream
from sleekxmpp.xmlstream import StanzaBase, ET
from sleekxmpp.xmlstream.matcher import *
from sleekxmpp.xmlstream.handler import *


log = logging.getLogger(__name__)


class ServerXMPP(BaseXMPP):

    """
    SleekXMPP's basic XMPP server.

    Methods:
        connect              -- Overrides XMLStream.connect.
        incoming_filter      -- Overrides XMLStream.incoming_filter.
        start_stream_handler -- Overrides XMLStream.start_stream_handler.
    """

    def __init__(self, jid, host, port,
                 plugin_config={}, plugin_whitelist=[]):
        """
        Arguments:
            jid              -- The JID of the component.
            host             -- The server accepting the component.
            port             -- The port used to connect to the server.
            plugin_config    -- A dictionary of plugin configurations.
            plugin_whitelist -- A list of desired plugins to load
                                when using register_plugins.
        """
        default_c2s_ns = 'jabber:client'
        default_s2s_ns = 'jabber:server'
        BaseXMPP.__init__(self, default_c2s_ns)

        self.auto_authorize = None
        self.stream_header = "<stream:stream version=\"1.0\"  %s %s %s from='%s'>" % (
                'xmlns="%s"' % default_c2s_ns ,
                'xmlns:stream="%s"' % self.stream_ns,
                'id="%s"' % self.new_id(),
                jid)
        self.stream_footer = "</stream:stream>"
        self.server_host = host
        self.server_port = port
        self.set_jid(jid)
        self.plugin_config = plugin_config
        self.plugin_whitelist = plugin_whitelist
        self.is_component = True
        self.use_tls = True
        self.tls_ok = False

        self.register_handler(
                Callback('StartTLS',
                         MatchXPath('{%s}starttls' % 'urn:ietf:params:xml:ns:xmpp-tls'),
                         self._handle_starttls))


    def listen(self):
        """
        Listen port.

        """
        log.debug("Listening from %s:%s" % (self.server_host,
                                               self.server_port))
        return self.listen2(self.server_host,
                                       self.server_port)


    def listen2(self, host='', port=0, use_ssl=False,
                use_tls=True):
        """
        Create a new socket and listen.

        Arguments:
            host      -- The name of the desired server for the connection.
            port      -- Port to connect to on the server.
            use_ssl   -- Flag indicating if SSL should be used.
            use_tls   -- Flag indicating if TLS should be used.
        """
        if host and port:
            self.address = (host, int(port))

        self.is_client = True
        # Respect previous SSL and TLS usage directives.
        if use_ssl is not None:
            self.use_ssl = use_ssl
        if use_tls is not None:
            self.use_tls = use_tls

#        listened = self.state.transition('unlistened', 'listened',
#                                          func=self._listen)
        listened = self._listen()
        return listened

    def _listen(self):
        self.stop.clear()
        self.socket = self.socket_class(Socket.AF_INET, Socket.SOCK_STREAM)
        self.socket.settimeout(None)
        if self.use_ssl and self.ssl_support:
            log.debug("Socket Wrapped for SSL")
            ssl_socket = ssl.wrap_socket(self.socket)
            if hasattr(self.socket, 'socket'):
                # We are using a testing socket, so preserve the top
                # layer of wrapping.
                self.socket.socket = ssl_socket
            else:
                self.socket = ssl_socket

        try:
            log.debug("Listening from %s:%s" % self.address)
            self.socket.bind(self.address)
            self.socket.listen(1)
            self.event("listened", direct=True)
            return self.accept()
        except Socket.error as serr:
            error_msg = "Could not listen from %s:%s. Socket Error #%s: %s"
            log.error(error_msg % (self.address[0], self.address[1],
                                       serr.errno, serr.strerror))
            time.sleep(1)
            return False

    def accept(self):
        try:
            conn, addr = self.socket.accept()
            self.set_socket(conn, ignore=True)
            log.debug("Accept connection from %s" % (str(addr)))
            #this event is where you should set your application state
            self.event("connected", direct=True)
            return True
        except:
            error_msg = "Could not accept connection from %s:%s."
            log.error(error_msg % (addr[0], addr[1]))
            time.sleep(1)
            return False


    def start_tls(self):
        """
        Perform handshakes for TLS.

        If the handshake is successful, the XML stream will need
        to be restarted.
        """
        if self.ssl_support:
            log.info("Negotiating TLS")
            log.info("Using SSL version: %s" % str(self.ssl_version))
            if self.ca_certs is None:
                cert_policy = ssl.CERT_NONE
            else:
                cert_policy = ssl.CERT_REQUIRED

            ssl_socket = ssl.wrap_socket(self.socket,
                                         ssl_version=self.ssl_version,
                                         server_side=True,
                                         do_handshake_on_connect=False,
                                         ca_certs=self.ca_certs,
                                         cert_reqs=cert_policy)

            if hasattr(self.socket, 'socket'):
                # We are using a testing socket, so preserve the top
                # layer of wrapping.
                self.socket.socket = ssl_socket
            else:
                self.socket = ssl_socket
            self.socket.do_handshake()
            self.set_socket(self.socket)
            return True
        else:
            log.warning("Tried to enable TLS, but ssl module not found.")
            return False



    def connect(self):
        """
        Connect to the server.

        Overrides XMLStream.connect.
        """
        log.debug("Connecting to %s:%s" % (self.server_host,
                                               self.server_port))
        return XMLStream.connect(self, self.server_host,
                                       self.server_port)


    def incoming_filter(self, xml):
        """
        Pre-process incoming XML stanzas by converting any 'jabber:client'
        namespaced elements to the component's default namespace.

        Overrides XMLStream.incoming_filter.

        Arguments:
            xml -- The XML stanza to pre-process.
        """
        if xml.tag.startswith('{jabber:client}'):
            xml.tag = xml.tag.replace('jabber:client', self.default_ns)

        # The incoming_filter call is only made on top level stanza
        # elements. So we manually continue filtering on sub-elements.
        for sub in xml:
            self.incoming_filter(sub)

        return xml


    def start_stream_handler(self, xml):
        """
        Once the streams are established, attempt to handshake
        with the server to be accepted as a component.

        Overrides XMLStream.start_stream_handler.

        Arguments:
            xml -- The incoming stream's root element.
        """
        if self.use_tls and not self.tls_ok:
            stream_features = ET.Element('stream:features')
            starttls = ET.Element('{%s}starttls' % 'urn:ietf:params:xml:ns:xmpp-tls')
            required = ET.Element('required')
            starttls.append(required)
            stream_features.append(starttls)
            self.send_xml(stream_features)

        else:
            self.event("session_start")



    def _handle_starttls(self, xml):
        """

        Arguments:
            xml -- The reply handshake stanza.
        """

        if self.use_tls and not self.tls_ok:
            response = ET.Element('{urn:ietf:params:xml:ns:xmpp-tls}proceed')
            if self.send_xml(response):
                self.tls_ok = True
                self.start_tls()
            
