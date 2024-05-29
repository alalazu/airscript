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

from airscript.utils import output, typename
from airscript.model import baseObject, template
from airscript.model import backendgroup, mapping, openapi, vhost


TYPENAME = 'mapping'
KIND = 'Mapping'

typename.register( TYPENAME, KIND )

class Mapping( baseObject.BaseObject ):
    def __init__( self, parent, obj=None, id=None ):
        self._typename = TYPENAME
        self._path = 'mappings'
        self._kind = KIND
        baseObject.BaseObject.__init__( self, parent, obj=obj, id=id )
    
    def me( self ):
        r = super().me()
        if self.name != None:
            r['path'] = self.attrs['entryPath']['value']
            r['labels'] = self.attrs['labels']
        else:
            r['path'] = None
            r['labels'] = None
        return r
        
    def values( self ):
        tmp = super().values()
        tmp.append( self.attrs['entryPath']['value'] )
        tmp.append( self.attrs['labels'] )
        return tmp
    
    """
    attribute operations
    """
    def hasLabel( self, label ):
        if label.lower() in map( str.lower, self.attrs['labels'] ):
            return True
        return False
    
    def hasAuth( self ):
        return self.attrs['access']['authorizedRoles'] != []
    
    def hasTemplate( self ):
        try:
            return len( self.rels['mapping'] ) > 0
        except KeyError:
            return False
    
    def isProduction( self ):
        return self.attrs['operationalMode'] == 'PRODUCTION'
    
    def isMaintained( self ):
        return self.attrs['enableMaintenancePage']
    
    def isBlocking( self ):
        return self.attrs['threatHandling'] == 'BLOCK'
    
    """
    interactions with Gateway REST API
    """
    def pull( self, recursive: bool=True, force: bool=False ) -> bool:
        """
        Pull settings from template
        Supports hierarchy and starts with top-most template
        """
        if not self.hasTemplate():
            output.error( "Mapping does not depend on template" )
            return False
        # build template chain
        chain = []
        mapping = self.rels['mapping'][0]['r']
        error = False
        while mapping:
            if force == False and mapping._attrs_modified:
                output.error( "Mapping {mapping.id} has pending updates - sync first" )
                error = True
            chain.insert( 0, mapping )
            if recursive and mapping.hasTemplate():
                mapping = mapping.rels['mapping'][0]['r']
                if mapping in chain:
                    output.error( "Mapping {mapping.id}: cyclic source mapping dependencies - pulling not possible" )
                    error = True
            else:
                mapping = None
        if error:
            return
        for mapping in chain:
            #print( f"Pulling from source mapping {mapping.id}: {mapping.name}" )
            mapping.loadData( mapping._parent.conn.mapping.post( "pull-from-source-mapping", mapping.id, expect=[200] ))
        return True
    
    def connectVirtualhost( self, vhost_object ):
        if type( vhost_object ) != vhost.VirtualHost:
            output.error( f"This is not a virtual host but {type(vhost_object)}" )
            return False
        return self.relationshipAdd( vhost_object )
    
    def connectBackendgroup( self, bgroup ):
        if type( bgroup ) != backendgroup.Backendgroup:
            output.error( f"This is not a backendgroup but {type(bgroup)}" )
            return False
        return self.relationshipAdd( bgroup )
    
    def connectOpenapi( self, document ):
        if type( document ) != openapi.OpenAPI:
            output.error( f"This is not a OpenAPI document but {type(document)}" )
            return False
        return self.relationshipAdd( document )
    
    def connectMapping( self, mapping_object ):
        if type( mapping_object ) != mapping.Mapping:
            output.error( f"This is not a mapping but {type(mapping_object)}" )
            return False
        return self.relationshipAdd( mapping_object )
    
    def connectTemplate( self, template_object ):
        if type( template_object ) != template.Template:
            output.error( f"This is not a template but {type(template_object)}" )
            return False
        return self.relationshipAdd( template_object )
    
    def disconnectVirtualhost( self, vhost_object ):
        if type( vhost_object ) != vhost.VirtualHost:
            output.error( f"This is not a virtual host but {type(vhost_object)}" )
            return False
        return self.relationshipDelete( vhost_object )
    
    def disconnectBackendgroup( self, bgroup ):
        if type( bgroup ) != backendgroup.Backendgroup:
            output.error( f"This is not a backendgroup but {type(bgroup)}" )
            return False
        return self.relationshipDelete( bgroup )
    
    def disconnectOpenapi( self, document ):
        if type( document ) != openapi.OpenAPI:
            output.error( f"This is not a OpenAPI document but {type(document)}" )
            return False
        return self.relationshipDelete( document )
    
    def disconnectMapping( self, mapping_object ):
        if type( mapping_object ) != mapping.Mapping:
            output.error( f"This is not a mapping but {type(mapping_object)}" )
            return False
        return self.relationshipDelete( mapping_object )
    
    def disconnectTemplate( self, template_object ):
        if type( template_object ) != template.Template:
            output.error( f"This is not a template but {type(template_object)}" )
            return False
        return self.relationshipDelete( template_object )
    
    def export( self ):
        resp = self._parent.conn.get( "configuration/mappings/%s/export-mapping" % (self.id,), accept="application/zip" )
        if resp.status_code != 200:
            output.error( f"Export failed: {resp.status_code} ({resp.text})" )
            return resp
        return resp
    
