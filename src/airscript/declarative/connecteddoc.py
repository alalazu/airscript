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

from typing import Self

from airscript.declarative import basedoc
from airscript.base import element
from pyAirlock.common import lookup, utils


class ConnectedDoc( basedoc.BaseDoc ):
    def __init__( self, id: str=None, base_object: element.ModelElement=None, yaml_dict: dict=None, env: str=None, dconfig=None ):
        super().__init__( id=id, base_object=base_object, yaml_dict=yaml_dict, env=env, dconfig=dconfig )
        if base_object:
            self._connections = { env if env else "default": base_object.listRelWithKind() }
        else:
            if env:
                base = utils.getDictValue( yaml_dict, 'metadata.connections.default', {} )
                ovrl = utils.getDictValue( yaml_dict, f'metadata.connections.{env}', {} )
                for k,v in base.items():
                    if not k in ovrl:
                        ovrl[k] = v
                self._connections = { env: ovrl }
            else:
                self._connections = utils.getDictValue( yaml_dict, 'metadata.connections', {} )
    
    def connectionsSupported( self ) -> bool:
        return True
    
    def isConnected( self, env: str=None ) -> bool:
        try:
            if len( self._connections['default'] ) > 0:
                return True
        except KeyError:
            pass
        if env:
            try:
                if len( self._connections[env] ) > 0:
                    return True
            except (KeyError, TypeError):
                pass
        return False
    
    def isNode( self ) -> bool:
        try:
            return self._kind == "GatewayClusterNode" and self._spec['hostName']
        except KeyError:
            return False
    
    def getConnections( self ) -> dict:
        return self._connections
    
    def getConnections4Env( self, env: str=None ) -> dict:
        r = {}
        try:
            return self._connections[env]
        except KeyError:
            return {}
    
    def _connKeyExtractReltype( self, key: str ) -> str:
        try:
            reltype, name = key.split( ':' )
        except ValueError:
            return key
        return reltype
    
    def _connKeyExtractName( self, key: str ) -> str:
        try:
            reltype, name = key.split( ':' )
        except ValueError:
            return key
        return name
    
    def getConnectionOrderNr( self ) -> int:
        if self._base_object == None:
            return 0
        return self._base_object.getRelationshipOrderNr()

    def export( self ) -> dict:
        r =  super().export()
        r['apiVersion'] = 'gateway.airlock.com/connected-v1alpha'
        if self._connections:
            r['metadata']['connections'] = self._connections
        return r
    
    def update( self, doc: Self, env: str=None ):
        self._connections[env] = doc._base_object.listRelWithKind()
        self._changelog.replace( "metadata.connections", self._connections[env] )
        super().update( doc, env=env )

    def connectionsReduce2Env( self, env: str, valid_docs: dict ) -> bool:
        removed = False
        try:
            base = self._connections['default']
        except KeyError:
            base = {}
        try:
            ovrl = self._connections[env]
            if not ovrl:
                ovrl = {}
        except KeyError:
            ovrl = {}
        connections = self._overwriteValues( base, ovrl )
        for reltype, lst in connections.items():
            # $$$
            # kind = lookup.get( element.LOOKUP_KIND2TYPENAME, lookup.get( lookup.RELTYPE2NAME, reltype ))
            kind = lookup.get( element.LOOKUP_TYPENAME2KIND, lookup.get( lookup.RELTYPE2NAME, reltype ))
            if not kind:
                kind = reltype
            to_be_deleted = []
            for ref in lst:
                if not f"{kind}:{ref}" in valid_docs:
                    to_be_deleted.append( ref )
                    removed = True
            try:
                self._connections[env][reltype] = list( set(connections[reltype]) - set(to_be_deleted) )
            except KeyError:
                self._connections[env] = { reltype: list( set(connections[reltype]) - set(to_be_deleted) ) }
        return removed
    
        for type_name, lst in connections.items():
            tbd = []
            for ref in lst:
                if not f"{type_name}:{ref}" in lookup:
                    tbd.append( ref )
                    removed = True
            try:
                self._connections[env][type_name] = list( set(connections[type_name]) - set(tbd) )
            except KeyError:
                self._connections[env] = { type_name: list( set(connections[type_name]) - set(tbd) ) }
        return removed
