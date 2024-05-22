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

from airscript.utils import internal, output
from airscript.model import baseObject, mapping

from typing import Union


class Backendgroup( baseObject.BaseObject ):
    def __init__( self, parent, obj=None, id=None ):
        self._typename = 'back-end-group'
        self._path = 'back-end-groups'
        baseObject.BaseObject.__init__( self, parent, obj=obj, id=id )
    
    def items( self ):
        value = super().items()
        value['hosts'] = self._hosts
        return value
    
    def values( self ):
        tmp = super().values()
        tmp.append( self._hosts )
        return tmp
    
    def hosts( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._hosts, id=id, name=name, ids=ids, filter=filter, sort=sort )
    
    def addHost( self, hostdef: dict=None ):
        host = Backend( hostdef )
        self._hosts.append( host )
        self._attrs_modified = True
        return host

    def loadData( self, data: dict, update: bool=False ):
        super().loadData( data, update=update )
        self._hosts = []
        for be in self.attrs['backendHosts']:
            self._hosts.append( Backend( be ))
        del self.attrs['backendHosts']
    
    def datafy( self, attrs: dict=None, addon: dict=None ) -> str:
        hosts = [h.dict() for h in self._hosts]
        return super().datafy( attrs=attrs, addon={'backendHosts': hosts} )
    
    """
    interactions with Gateway REST API
    """
    def connectMapping( self, mapping_object ):
        if type( mapping_object ) != mapping.Mapping:
            output.Error( "This is not a mapping but %s" % (type(mapping_object),) )
            return False
        return self.relationshipAdd( mapping )
    
    def disconnectMapping( self, mapping_object ):
        if type( mapping_object ) != mapping.Mapping:
            output.Error( "This is not a mapping but %s" % (type(mapping_object),) )
            return False
        return self.relationshipDelete( mapping_object )
    

class Backend( object ):
    def __init__( self, obj: dict=None ):
        if obj:
            self.protocol = obj['protocol']
            self.hostName = obj['hostName']
            try:
                self.port = obj['port']
            except KeyError:
                self.port = 80 if self.protocol.casefold() == 'http' else 443
            self.mode = obj['mode']
            self.spare = obj['spare']
            self.weight = obj['weight']
        else:
            self.protocol = 'HTTP'
            self.hostName = ''
            self.port = 80 if self.protocol.casefold() == 'http' else 443
            self.mode = 'ENABLED'
            self.spare = False
            self.weight = 100
    
    def __repr__( self ):
        return f"{self.protocol}://{self.hostName}:{self.port}"
    
    def dict( self ):
        return self.__dict__

