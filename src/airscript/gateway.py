# AirScript: Airlock Gateway Configuration Script Engine
# 
# Copyright (c) 2019-2024 Urs Zurbuchen <urs.zurbuchen@ergon.ch>
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


from airscript import session
from airscript.model import configuration
from airscript.utils import internal
from airscript.utils import cache
from pyAirlock import gateway
from pyAirlock.common import exception, log


SESSION_NAME_DEFAULT = "default"

class Gateway( object ):
    def __init__( self, name: str, hostname: str, key: str, run_info, peer: str=None, group: str=None ):
        """
        Initialise Gateway instance.
        
        name - short name
        hostname - FQDN for Airlock Gateway Config Center
        key - API key
        """
        self.name = name
        self.peer = peer
        self.group = group
        self.mgmt = False
        self._hostname = hostname
        self._key = key
        self._run_info = run_info
        self._cert = None
        self._tls_verify = True
        self._log = log.Log( self.__module__, run_info )
        self.configs = None
    
    def getName( self ) -> str:
        """ Return short name. """
        return self.name
    
    def getHost( self ) -> str:
        """ Return FQDN. """
        return self._hostname
    
    def getKey( self ) -> str:
        """ Return API key. """
        return self._key
    
    def getPeer( self ) -> str:
        return self.peer
    
    def getGroup( self ) -> str:
        return self.group
    
    def isPeerOf( self, peer: str ) -> bool:
        if self.peer == peer:
            return True
        return False
    
    def isMemberOf( self, group: str ) -> bool:
        if self.group == group:
            return True
        return False
    
    def setCertificate( self, certfile: str=None, pem: str=None ):
        """
        Define CA certificate file which signed Airlock Gateway's Config Center certificate.
        
        If Airlock Gateway Config Center uses a certificate not issued by any of the
        well-known certificate authorities (CAs) maintained in /etc/ssl/certs,
        the appropriate signing certificate must be specified here.
        """
        self._cert = {'file': certfile, 'pem': pem}
    
    def setTLSVerify( self, verify ):
        """
        Suppress server certificate checking.
        
        Passing in verify=False completely disables server certificate checking.
        While this may be easy for self-signed Airlock Gateway Config Center
        certificates, it should not be used in production.
        
        For an even stronger version, passing in verify=None also suppresses
        any warning messages related to the certificate.
        """
        self._tls_verify = verify
    
    def session( self, label: str=SESSION_NAME_DEFAULT ) -> gateway.Session:
        """
        Establish session with Airlock Gateway.
        
        Parameters:

        * `label`: pass in a name for the connection, default is SESSION_NAME_DEFAULT.

        Returns: connection handle on success or None on failure
        """
        sess = session.GatewaySession( label, self, self._run_info )
        # sess = gateway.Session( self._hostname, self._key, name=label, run_info=self._run_info )
        if self._cert:
            sess.setCertificate( certfile=self._cert['file'], pem=self._cert['pem'] )
        sess.setTLSVerify( self._tls_verify )
        if sess.connect():
            sess.session.post( "/configuration/configurations/load-empty-config", expect=[204] )
            self._log.verbose( "Connected to '%s'" % (self._hostname,) )
            return sess
        return None
    
