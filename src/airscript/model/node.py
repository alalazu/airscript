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

from airscript.utils import output
from airscript.model import baseObject, certificate


class Node( baseObject.BaseObject ):
    def __init__( self, parent, obj=None, id=None ):
        self._typename = 'node'
        self._path = 'nodes'
        self._kind = 'GatewayClusterNode'
        baseObject.BaseObject.__init__( self, parent, obj=obj, id=id )
    
    def loadData( self, data: dict, update: bool=False ):
        super().loadData( data, update=update )
        self.name = self.attrs['hostName']
    
    """
    interactions with Gateway REST API
    """
    def connectCertificate( self, cert ):
        if type( cert ) != certificate.Certificate:
            output.Error( "This is not a certificate but %s" % (type(certificate),) )
            return False
        return self.relationshipAdd( cert )
    
    def disconnectCertificate( self, cert ):
        if type( cert ) != certificate.Certificate:
            output.Error( "This is not a certificate but %s" % (type(certificate),) )
            return False
        return self.relationshipDelete( cert )
    
