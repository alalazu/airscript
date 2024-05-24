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
from airscript.model import baseObject
from airscript.model import mapping


class JWKS( baseObject.BaseObject ):
    def __init__( self, parent, obj=None, id=None, remote=True ):
        self._remote = remote
        if remote:
            self._typename = 'remote-json-web-key-set'
            self._path = 'json-web-key-sets/remotes'
        else:
            self._typename = 'local-json-web-key-set'
            self._path = 'json-web-key-sets/locals'
        baseObject.BaseObject.__init__( self, parent, obj=obj, id=id )
    
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
    
