"""
AirScript: Airlock (Gateway) Configuration Script

Copyright (c) 2019-2024 Urs Zurbuchen <urs.zurbuchen@ergon.ch>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

import pem

from cryptography import x509
from cryptography.hazmat.backends import default_backend

from airscript.base import element
from airscript.utils import output
from airscript.model import vhost
from pyAirlock.common import lookup


TYPENAME = 'ssl-certificate'
KIND = 'TLSCertificate'

lookup.registerBoth( element.LOOKUP_TYPENAME2KIND, element.LOOKUP_KIND2TYPENAME, TYPENAME, KIND )

class Certificate( element.ModelElement ):
    RELATIONKEY = { "virtual-host": "virtual-hosts", "remote-json-web-key-set": "remote-json-web-key-sets" }
    
    def __init__( self, parent, obj=None, id=None ):
        self._typename = TYPENAME
        self._path = 'ssl-certificates'
        self._kind = KIND
        element.ModelElement.__init__( self, parent, obj=obj, id=id )
    
    def loadData( self, data: dict, update: bool=False ):
        element.ModelElement.loadData( self, data=data, update=update )
        if self._parent.conn == None or self._parent.conn.getVersion() >= 7.6:
            attr_name = "certificate"
        else:
            attr_name = "serverCertificate"
        for pem_cert in pem.parse( bytes( self.attrs[attr_name], 'ascii' )):
            if type( pem_cert ) == Certificate:
                break
        cert = x509.load_pem_x509_certificate( pem_cert.as_bytes(), default_backend() )
        #self.name = ".".join( x.value for x in cert.subject )
        self.name = "<undefined>"
        for x in cert.subject:
            if x.rfc4514_attribute_name == 'CN':
                self.name = x.value
                break
    
    """
    interactions with Gateway REST API
    """
    def connectVirtualhost( self, vhost_object ):
        if not isinstance( vhost_object, vhost.VirtualHost ):
            output.Error( "This is not a virtual host but %s" % ( type( vhost_object ),) )
            return False
        return self.relationshipAdd( vhost_object )
    
    def disconnectVirtualhost( self, vhost_object ):
        if not isinstance( vhost_object, vhost.VirtualHost ):
            output.Error( "This is not a virtual host but %s" % ( type( vhost_object ),) )
            return False
        return self.relationshipDelete( vhost_object )
    
    def sync( self ) -> bool:
        """
        Sync changes to current object to Airlock Gateway
        - Set all attributes
        - Link relations to object types which should already have been updated
        - Other relations are (later) linked from the other object types back to here

        Returns:
        - true: success, sync'ed
        - false: delete element
        """
        if not 'passphrase' in self.attrs:
            self.attrs['passphrase'] = ''
            del_passphrase = True
        else:
            del_passphrase = False
        r = super().sync()
        if del_passphrase:
            try:
                del self.attrs['passphrase']
            except KeyError:
                pass
        return r
    
