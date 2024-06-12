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
from airscript.base import element
from airscript.model import configuration, mapping
from pyAirlock.common import lookup


REMOTE_TYPENAME = 'remote-json-web-key-set'
REMOTE_KIND = 'JWKSRemote'
LOCAL_TYPENAME = 'local-json-web-key-set'
LOCAL_KIND = 'JWKSLocal'

lookup.registerBoth( element.LOOKUP_TYPENAME2KIND, element.LOOKUP_KIND2TYPENAME, REMOTE_TYPENAME, REMOTE_KIND )
lookup.registerBoth( element.LOOKUP_TYPENAME2KIND, element.LOOKUP_KIND2TYPENAME, LOCAL_TYPENAME, LOCAL_KIND )

class JWKS( element.ModelElement ):
    RELATIONKEY = { "mapping": "mappings" }
    
    def __init__( self, parent, obj=None, id=None, remote=True ):
        self._remote = remote
        if remote:
            self._typename = REMOTE_TYPENAME
            self._path = 'json-web-key-sets/remotes'
            self._kind = REMOTE_KIND
        else:
            self._typename = LOCAL_TYPENAME
            self._path = 'json-web-key-sets/locals'
            self._kind = LOCAL_KIND
        element.ModelElement.__init__( self, parent, obj=obj, id=id )
    
    def me( self ):
        r = super().me()
        r['remote'] = self._remote if self.name != None else None
        return r
        
    def values( self ):
        tmp = super().values()
        tmp.append( self._remote )
        return tmp
    
    """
    interactions with Gateway REST API
    """
    def connectMapping( self, mapping_object ):
        if type( mapping_object ) != mapping.Mapping:
            output.Error( "This is not a mapping but %s" % (type(mapping_object),) )
            return False
        return self.relationshipAdd( mapping_object )
    
    def disconnectMapping( self, mapping_object ):
        if type( mapping_object ) != mapping.Mapping:
            output.Error( "This is not a mapping but %s" % (type(mapping_object),) )
            return False
        return self.relationshipDelete( mapping_object )
    
