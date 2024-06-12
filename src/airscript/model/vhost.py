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

from airscript.base import element
from airscript.utils import output
from airscript.model import certificate, configuration
from pyAirlock.common import lookup


TYPENAME = 'virtual-host'
KIND = 'VirtualHost'

lookup.registerBoth( element.LOOKUP_TYPENAME2KIND, element.LOOKUP_KIND2TYPENAME, TYPENAME, KIND )

class VirtualHost( element.ModelElement ):
    RELATIONKEY = { "mapping": "mappings", "ssl-certificate": "ssl-certificate" }

    def __init__( self, parent, obj=None, id=None ):
        self._typename = TYPENAME
        self._path = 'virtual-hosts'
        self._kind = KIND
        element.ModelElement.__init__( self, parent, obj=obj, id=id )
    
    def me( self ):
        r = super().me()
        try:
            r['ipv4'] = self.attrs['networkInterface']['ipV4Address']
        except KeyError:
            r['ipv4'] = None
        return r
    
    def values( self ):
        tmp = super().values()
        try:
            ip = self.attrs['networkInterface']['ipV4Address']
        except KeyError:
            ip = None
        tmp.append( ip )
        return tmp
    
    def ipv4( self ):
        try:
            return self.attrs['networkInterface']['ipV4Address']
        except KeyError:
            return None

    """
    attribute setting
    """
    def setHostname( self, value ):
        if self.attrs == None:
            self.attrs = {}
        self.attrs['hostName'] = value
    
    def setIPv4( self, value ):
        if self.attrs == None:
            self.attrs = {}
        self.attrs['networkInterface'] = {}
        self.attrs['networkInterface']['ipV4Address'] = value
        
    """
    interactions with Gateway REST API
    """
    def connectCertificate( self, cert ):
        if type( cert ) != certificate.Certificate:
            output.Error( "This is not a certificate but %s" % (type(certificate),) )
            return False
        return self.relationshipAdd( cert )
    
    def connectMapping( self, mapping ):
        if type( mapping ) != mapping.Mapping:
            output.Error( "This is not a mapping but %s" % (type(mapping),) )
            return False
        return self.relationshipAdd( mapping )
    
    def disconnectCertificate( self, cert ):
        if type( cert ) != certificate.Certificate:
            output.Error( "This is not a certificate but %s" % (type(certificate),) )
            return False
        return self.relationshipDelete( cert )
    
    def disconnectMapping( self, mapping ):
        if type( mapping ) != mapping.Mapping:
            output.Error( "This is not a mapping but %s" % (type(mapping),) )
            return False
        return self.relationshipDelete( mapping )
    
    def crlDownload( self ):
        resp = self._parent.conn.get( "configuration/%s/%s/crl" % (self._path,self.id), accept='application/pkix-crl' )
        return resp.text
    
    def crlUpload( self, crlfile ):
        files = { 'file': open( crlfile, 'rb' ) }
        resp = self._parent.conn.upload( "configuration/%s/%s/crl" % (self._path,self.id), content='application/pkix-crl', files=files )
        if resp.status_code != 204:
            output.Error( "Deletion failed: %s (%s)" % (resp.status_code,resp.text) )
            return False
        return True
    
    def crlDelete( self ):
        resp = self._parent.conn.delete( "configuration/%s/%s/crl" % (self._path,self.id) )
        if resp.status_code != 204:
            output.Error( "Deletion failed: %s (%s)" % (resp.status_code,resp.text) )
            return False
        return True
    
