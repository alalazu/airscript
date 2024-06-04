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

from airscript.utils import output
from airscript.model import baseObject, vhost


class Certificate( baseObject.ModelElement ):
    def __init__( self, parent, obj=None, id=None ):
        self._typename = 'ssl-certificate'
        self._path = 'ssl-certificates'
        self._kind = 'TLSCertificate'
        baseObject.ModelElement.__init__( self, parent, obj=obj, id=id )
    
    def loadData( self, data: dict, update: bool=False ):
        baseObject.ModelElement.loadData( self, data=data, update=update )
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
    
