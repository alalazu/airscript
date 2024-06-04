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

import copy
import json
import pprint
import re

from typing import Self

from airscript.utils import cache
from airscript.utils import internal
from airscript.utils import output


class ReadOnlyObject( object ):
    def __init__( self, parent, obj=None, id=None ):
        try:
            self.id = int( id )
            # self.id = id
        except (ValueError, TypeError):
            self.id = id
        self.name = None
        self.attrs = {}
        self.rels = {}
        self.backlinks = {}
        self._parent = parent
        if obj:
            self.loadData( obj )
        if self.id:
            self._attrs_modified = False
            self._rels_modified = False
        else:
            self._attrs_modified = True
            self._rels_modified = True
        if not hasattr( self, '_typename' ):
            self._typename = ""         # overwritten by individual object types
        if not hasattr( self, '_path' ):
            self._path = ""             # overwritten by individual object types
        if not hasattr( self, '_kind' ):
            self._kind = ""             # overwritten by individual object types
        self._deleted = False
        self._rels_deleted = {}
        self._connections = None
        if self._parent.conn != None:
            if not cache.isCached( self._parent.conn.getName(), type( self )):
                cache.cacheAttributeKeys( self._parent.conn.getName(), type( self ), internal.collectKeyNames( self.attrs ))
    
    def __repr__( self ):
        return str( self.me() )
    
    def getId( self ):
        return self.id
    
    def getName( self ):
        return self.name
    
    def getTypeName( self ):
        return self._typename
    
    def getPath( self ):
        return self._path
    
    def getKind( self ):
        return self._kind
    
    def items( self ):
        return { 'id': self.id, 'name': self.name, 
                 'attributes': self.attrs, 
                 'relationships': self.rels }
    
    def me( self ):
        if self.name != None:
            return { 'id': self.id, 'name': self.name }
        else:
            return { 'id': self.id, 'name': None }

    def values( self ):
        return [ self.id, self.name ]
    
    def pretty( self ):
        pprint.pprint( self.items() )
    
    def getAttrs( self ):
        return self.attrs
    
    def printAttrs( self ):
        pprint.pprint( self.attrs )
    
    def getRels( self ):
        return self.rels
    
    def printRels( self ):
        pprint.pprint( self.rels )
    
    def isDeleted( self ):
        return self._deleted
    
    def filter( self, filter: list[dict] ) -> bool:
        """ Check if object matches filter specification

        Filter is a list of or'ed conditions.
        Each condition is a dict of and'ed attribute names and matching values.
        Name is:
        - 'name'
        - 'id'
        - path to attribute, e.g. locking.application.response.compressionAllowed
        Value is:
        - a constant (number, boolean)
        - a regexp (strings)
        - None: value does not matter but attribute needs to have one
        """
        for condition in filter:
            r = True
            for name, value in condition.items():
                match = False
                if name == 'name':
                    match = re.match( value, self.name )
                elif name == 'id':
                    match = re.match( str( value ), self.id )
                else:
                    attr = self.get( name )
                    if attr == None and value == None:
                        match = True
                    elif isinstance( value, bool ):
                        match = attr == value
                    elif isinstance( value, int ) or isinstance( value, float ):
                        match = attr == value
                    else:
                        match = re.match( value, attr )
                if not match:
                    r = False
                    break
            if r:
                break
        return r
    
    def loadData( self, data: dict, update: bool=False ):
        self.id = self._extractId( data )
        self.attrs = data['attributes']
        self._attrs_modified = True
        try:
            self.name = self.attrs['name']
        except KeyError:
            self.name = None
        if not update and 'relationships' in data:
            for grp,d in data['relationships'].items():
                if isinstance( d['data'], list ):
                    for item in d['data']:
                        self._addRel( item )
                else:
                    self._addRel( d['data'] )
            self._rels_modified = False

    def delete( self ) -> bool:
        self._deleted = True
        for type_name in self.rels:
            while len( self.rels[type_name] ):
                self.deleteRel( self.rels[type_name][0].reference, markOnly=False )
    
    def get( self, path: str ):
        """ Return attribute value.
        
        'path' specifies identity of attribute. It is of the form 'locking.application.response.compressionAllowed'.
        For correct attribute paths, please refer to the Airlock Gateway REST API documentation.
        """
        array = path.split( '.' )
        attr = self._findAttribute( array )
        if attr != None:
            return attr[array[-1]]
        else:
            return None
    
    def set( self, path: str, value ) -> bool:
        """ Set attribute value.
        
        'path' specifies identity of attribute. It is of the form 'locking.application.response.compressionAllowed'.
        For correct attribute paths, please refer to the Airlock Gateway REST API documentation.
        """
        array = path.split( '.' )
        attr = self._findAttribute( array )
        if isinstance( attr[array[-1]], list ) and not isinstance( value, list ):
            value = [ value ]
        if attr[array[-1]] != value:
            attr[array[-1]] = value
            self._attrs_modified = True
        return True
    
    def append( self, path: str, value ) -> bool:
        """ Append value to list attribute.
        
        'path' specifies identity of attribute. It is of the form 'locking.application.response.compressionAllowed'.
        For correct attribute paths, please refer to the Airlock Gateway REST API documentation.
        """
        array = path.split( '.' )
        attr = self._findAttribute( array )
        if not isinstance( attr[array[-1]], list ):
            return False
        if not value in attr[array[-1]]:
            attr[array[-1]].append( value )
            self._attrs_modified = True
        return True
    
    def remove( self, path: str, value ) -> bool:
        """ Remove value from list attribute.
        
        'path' specifies identity of attribute. It is of the form 'locking.application.response.compressionAllowed'.
        For correct attribute paths, please refer to the Airlock Gateway REST API documentation.
        """
        array = path.split( '.' )
        attr = self._findAttribute( array )
        if not isinstance( attr[array[-1]], list ):
            return False
        try:
            attr[array[-1]].remove( value )
        except ValueError:
            return False
        self._attrs_modified = True
        return True
    
    def setName( self, value: str ):
        self.name = value
        self._attrs_modified = True
    
    def setAttributes( self, attrs: dict ):
        self.attrs = attrs
        self._attrs_modified = True
        try:
            self.name = self.attrs['name']
        except KeyError:
            pass
    
    def copyAttributes( self, obj: Self ):
        if type( obj ) != type( self ):
            output.error( f"Type mismatch: parameter should be '{type(self)}' but is '{type(obj)}'" )
            return False
        if obj.attrs == None:
            output.error( "Parameter does not have attributes set" )
            return False
        self.attrs = copy.deepcopy( obj.attrs )
        self._attrs_modified = True
        return True
    
    def copyAttributeKeys( self, obj: Self ):
        if type( obj ) != type( self ):
            output.error( f"Type mismatch: parameter should be '{type(self)}' but is '{type(obj)}'" )
            return False
        if obj.attrs == None:
            output.error( "Parameter does not have attributes set" )
            return False
        self.attrs = self._copyDictKeys( obj.attrs )
        self._attrs_modified = True
        return True
    
    def copyRelationships( self, obj: Self ):
        if type( obj ) != type( self ):
            output.error( f"Type mismatch: parameter should be '{type(self)}' but is '{type(obj)}'" )
            return False
        if obj.rels == {} and self.rels == {}:
            return True
        else:
            self.rels = self._copyDictKeys( obj.attrs )
        self._rels_modified = True
        return True
    
    def addRel( self, reference: Self, load: bool=False, backlink: bool=False ):
        v = Relationship( reference, load )
        type_name = reference.getTypeName()
        if self._typename == reference._typename and backlink:
            try:
                self.backlinks[type_name].append( v )
            except KeyError:
                self.backlinks[type_name] = [ v ]
        elif self._findRel( reference ) == None:
            try:
                self.rels[type_name].append( v )
            except KeyError:
                self.rels[type_name] = [ v ]
            self._rels_modified = True

    def deleteRel( self, reference: Self, removeBacklink: bool=True, markOnly: bool=True ) -> bool:
        rel = self._findRel( reference )
        if rel == None:
            return False
        if markOnly:
            rel.status = 'del'
        else:
            self._delRel( rel )
        self._rels_modified = True
        if removeBacklink:
            reference.deleteRel( self, removeBacklink=False, markOnly=markOnly )
        return True
    
    def checkRel( self, reference: Self ) -> bool:
        rel = self._findRel( reference )
        if rel == None:
            return False
        return True

    def listRelWithKind( self ) -> dict:
        r = {}
        for type_name in self.rels:
            kind = self.rels[type_name][0].reference.getKind()
            r[kind] = [ref.reference.name for ref in self.rels[type_name]]
        return r

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
        classPointer = self._parent.conn.getAPI( self._typename )
        if classPointer == None:
            return False
        if self._deleted:
            classPointer.delete( self.id )
            return False
        if self._attrs_modified:
            if self.id:
                self.loadData( classPointer.update( self.id, data=self.datafy() ), update=True )
            else:
                self.loadData( classPointer.create( data=self.datafy() ), update=True )
            self._attrs_modified = False
        if self._rels_modified:
            for grp, lst in self.rels.items():
                #relPointer = self._parent.conn.getAPI( grp )
                for rel in lst:
                    if rel.reference.isDeleted():
                        # nohing o do if oher obje is deleed relaionship will be removed auomaiall
                        continue
                    if rel.status == 'del':
                        if not classPointer.removeConnection( connection=grp, id=self.id, relation_id=rel.reference.id ):
                            output.error( f"Sync error for {self._typename}-{self.name}: failed to remove connection to {grp}{rel.reference.name}" )
                        entry = rel.reference._findRel( self )
                        rel.reference.rels[self._typename].remove( entry )
                    elif rel.status == 'new':
                        if self._parent.elementOrderNr( self._typename ) < self._parent.elementOrderNr( grp ):
                            continue
                        if classPointer.addConnection( connection=grp, id=self.id, relation_id=rel.reference.id ):
                            rel.status = ''
                        else:
                            output.error( f"Sync error for {self._typename}-{self.name}: failed to add connection to {grp}{rel.reference.name}" )
                # remove deleted relationship from object
                self.rels[grp][:] = [x for x in self.rels[grp] if x.status != 'del']
            self._rels_modified = False
        return True
            
    def datafy( self, attrs: dict=None, addon: dict=None ) -> str:
        if attrs == None:
            attrs = self.attrs
        obj = self._objectify( attrs )
        if addon:
            for k, v in addon.items():
                obj['attributes'][k] = v
        if self.id != None:
            obj['id'] = str( self.id )
        return obj
    
    def jsonize( self, attrs: dict=None, addon: dict=None ) -> str:
        return json.dumps( self.datafy( attrs=attrs, addon=addon ))
    
    def declarativeExport( self ) -> dict:
        out = {
                'apiVersion': 'gateway.airlock.com/v1alpha',
                'kind': self._kind,
                'metadata': {
                    'name': self.name,
                    'environments': [],
                },
                'connections': {},
                'spec': self.getAttrs()
        }
        try:
            del out['spec']['name']
        except KeyError:
            pass
        for type_name in self.rels:
            kind = self.rels[type_name][0].reference.getKind()
            out['connections'][kind] = [ref.reference.name for ref in self.rels[type_name]]
        return out
    
    def declarativeStoreConnections( self, connections: dict ):
        self._connections = connections

    def declarativeGetConnections( self ) -> dict|None:
        return self._connections

    def declarativeClearConnections( self ):
        self._connections = None


    """
    interactions with Gateway REST API
    """
    
    """
    internal methodes
    """
    def _objectify( self, attrs: dict={} ):
        return { 'attributes': attrs, 'type': self._typename }
    
    def _findAttribute( self, array: list[str] ):
        attr = self.attrs
        for entry in array[:-1]:
            try:
                if attr == None:
                    attr = self.attrs[entry]
                else:
                    attr = attr[entry]
            except KeyError:
                output.error( f"Invalid path specified - '{entry}' not found" )
                return None
        return attr

    def _notImplemented( self ):
        output.error( "Operation not available" )
        return False
    
    def _copyDictKeys( self, attrs ):
        new = {}
        for k,v in attrs.items():
            if type( v ) == dict:
                new[k] = self._copyDictKeys( v )
            elif type( v ) == int:
                new[k] = 0
            elif type( v ) == str:
                new[k] = ""
            elif type( v ) == bool:
                new[k] = False
            elif type( v ) == list:
                new[k] = []
            else:
                new[k] = None
        return new
    
    def _addRel( self, item ):
        type_name = item['type']
        obj = self._parent.addElement( type_name, id=self._extractId( item ))
        if type_name != "mapping-template":
            obj.addRel( self, backlink=True )
        self.addRel( obj )
    
    def _delRel( self, rel ):
        type_name = rel.reference.getTypeName()
        try:
            self.rels[type_name].remove( rel )
        except KeyError:
            pass

    def _findRel( self, reference ) -> dict:
        type_name = reference.getTypeName()
        try:
            for rel in self.rels[type_name]:
                if rel.reference == reference:
                    return rel
        except KeyError:
            pass
        return None

    def _extractId( self, data: dict ) -> int|str|None:
        try:
            return int( data['id'] )
        except (ValueError, TypeError) as e:
            return data['id']
        except KeyError:
            return None
    

class ModelElement( ReadOnlyObject ):
    def __init__( self, parent, obj=None, id=None ):
        ReadOnlyObject.__init__( self, parent, obj=obj, id=id )
        if obj == None:
            self._shadow = None
        else:
            self._shadow = copy.deepcopy( obj['attributes'] )
    
    """
    interactions with Gateway REST API
    """
    # def create( self ):
    #     resp = self._parent.conn.post( f"configuration/{self._path}", data=self.jsonize() )
    #     if resp.status_code != 201:
    #         output.error( f"Creation failed: {resp.status_code} ({resp.text})" )
    #         return False
    #     self.__init__( resp.json()['data'], self._parent.conn )
    #     return True
    
    # def update( self ):
    #     diff = self._diffDict( self.attrs, self._shadow )
    #     resp = self._parent.conn.patch( f"configuration/{self._path}/{self.id}", data=self.jsonize( diff ) )
    #     if resp.status_code != 200:
    #         output.error( f"Update failed: {resp.status_code} ({resp.text})" )
    #         return False
    #     resp_attrs = resp.json()['data']['attributes']
    #     diff = self._diffDict( resp_attrs, self.attrs )
    #     if diff != {}:
    #         output.error( "Updated objects differs from our view:" )
    #         output.error( f"{diff}" )
    #         return False
    #     self.attrs = resp_attrs
    #     self._shadow = copy.deepcopy( resp_attrs )
    #     return True
    
    # def delete( self ):
    #     resp = self._parent.conn.delete( f"configuration/{self._path}/{self.id}" )
    #     if resp.status_code != 204:
    #         output.error( f"Delete failed: {resp.status_code} ({resp.text})" )
    #         return False
    #     # compare self.attrs and resp.json['attributes']
    #     return True
    
    def relationshipAdd( self, rel, relPath=None ):
        obj = { 'data': { 'type': rel.getTypeName(), 'id': rel.id }}
        if relPath == None:
            relPath = self._getRelationshipPath( rel )
        resp = self._parent.conn.post( f"configuration/{self._path}/{self.id}/relationship/{relPath}", data=json.dumps( obj ))
        if resp.status_code != 204:
            output.error( f"Relationship add failed: {resp.status_code} ({resp.text})" )
            return False
        return True
    
    def relationshipDelete( self, rel, relPath=None ):
        obj = { 'data': { 'type': rel.getTypeName(), 'id': rel.id }}
        if relPath == None:
            relPath = self._getRelationshipPath( rel )
        resp = self._parent.conn.delete( f"configuration/{self._path}/{self.id}/relationship/{relPath}", data=json.dumps( obj ))
        if resp.status_code != 204:
            output.error( f"Relationship delete failed: {resp.status_code} ({resp.text})" )
            return False
        return True
    
    """
    demultiplexer
    """
    def connect( self, obj ):
        methodname = "connect{}".format( type( obj ).__name__.capitalize() )
        method = getattr( type( self ), methodname, None )
        if callable( method ) == False:
            output.error( "Unable to connect {} to {}".format( type( obj ).__name__, type( self ).__name__ ))
            return False
        return method( self, obj )
    
    def disconnect( self, obj ):
        methodname = "disconnect{}".format( type( obj ).__name__.capitalize() )
        method = getattr( type( self ), methodname, None )
        if callable( method ) == False:
            output.error( "Unable to disconnect {} to {}".format( type( obj ).__name__, type( self ).__name__ ))
            return False
        return method( self, obj )
    
    """
    internal methods
    """
    def _getRelationshipPath( self, rel ):
        relPath = rel.getPath()
        if relPath == 'ssl-certificates':
            relPath = 'ssl-certificate'
        elif relPath == 'back-end-groups':
            relPath = 'back-end-group'
        elif relPath == 'api-security/openapi-documents':
            relPath = 'openapi-document'
        elif relPath == 'api-security/graphql-documents':
            relPath = 'graphql-document'
        elif relPath == 'templates/mappings':
            relPath = 'template'
        return relPath
    
    def _diffDict( self, attrs, shadow ):
        diff = {}
        for k,v in attrs.items():
            if not k in shadow:
                diff[k] = v
                continue
            if type( v ) == dict:
                subdiff = self._diffDict( v, shadow[k] )
                if subdiff != {}:
                    diff[k] = subdiff
                continue
            if v != shadow[k]:
                diff[k] = v
        return diff
    

class Relationship( object ):
    def __init__( self, reference: ReadOnlyObject, load: bool=False ):
        self.reference = reference
        self.status = '' if load == False else 'new'
    
    def __repr__( self ):
        return str( { "ref": self.reference, "status": self.status } )

