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
from airscript.utils import internal, output
from airscript.model import configuration, mapping
from pyAirlock.common import lookup

from typing import Union

TYPENAME = 'back-end-group'
KIND = 'BackendGroup'

lookup.registerBoth( element.LOOKUP_TYPENAME2KIND, element.LOOKUP_KIND2TYPENAME, TYPENAME, KIND )


class Backendgroup( element.ModelElement ):
    RELATIONKEY = { "mapping": "mappings", "ssl-certificate": "client-certificate" }
    
    def __init__( self, parent, obj=None, id=None ):
        self._typename = TYPENAME
        self._path = 'back-end-groups'
        self._kind = KIND
        element.ModelElement.__init__( self, parent, obj=obj, id=id )
    
    def items( self ):
        value = super().items()
        value['hosts'] = self._hosts
        return value
    
    def values( self ):
        tmp = super().values()
        tmp.append( self._hosts )
        return tmp
    
    def getAttrs( self ):
        r = super().getAttrs()
        r['backendHosts'] = [host.export() for host in self._hosts.values()]
        return r
    
    def hosts( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._hosts, id=id, name=name, ids=ids, filter=filter, sort=sort )
    
    def addHost( self, hostdef: dict=None ):
        host = Backend( hostdef )
        self._hosts.append( host )
        self._attrs_modified = True
        return host

    def loadData( self, data: dict, update: bool=False ):
        super().loadData( data, update=update )
        self._hosts = {}
        idx = 0
        for be in self.attrs['backendHosts']:
            self._hosts[idx] = Backend( None, be, idx )
            idx += 1
        del self.attrs['backendHosts']
    
    def datafy( self, attrs: dict=None, addon: dict=None ) -> str:
        hosts = [h.dict() for h in self._hosts.values()]
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
    

class Backend( element.ModelElement ):
    def __init__( self, parent, obj=None, id=None ):
        try:
            self.id = id
        except (ValueError, TypeError):
            self.id = id
        self.name = None
        self.attrs = {}
        self.rels = {}
        self.backlinks = {}
        self._parent = parent
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
        self._typename = ""         # overwritten by individual object types
        self._path = ""             # overwritten by individual object types
        self._kind = ""             # overwritten by individual object types
        self._deleted = False
        self._attrs_modified = False
        self._rels_modified = False
        self._rels_deleted = {}
    
    def __repr__( self ):
        return f"{self.protocol}://{self.hostName}:{self.port}"
    
    def dict( self ):
        return { 'hostName': self.hostName, 'protocol': self.protocol, 'port': self.port, 'mode': self.mode, 'spare': self.spare, 'weight': self.weight }
    
    def export( self ):
        return {
            'protocol': self.protocol,
            'hostName': self.hostName,
            'port': self.port,
            'mode': self.mode,
            'spare': self.spare,
            'weight': self.weight
        }

