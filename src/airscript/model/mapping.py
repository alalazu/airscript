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
from airscript.model import backendgroup, configuration, mapping, openapi, template, vhost
from pyAirlock.common import lookup


TYPENAME = 'mapping'
KIND = 'Mapping'

lookup.registerBoth( element.LOOKUP_TYPENAME2KIND, element.LOOKUP_KIND2TYPENAME, TYPENAME, KIND )


class Mapping( element.ModelElement ):
    RELATIONKEY = { "virtual-host": "virtual-hosts",
                    "back-end-group": "back-end-groups",
                    "remote-json-web-key-set": "remote-json-web-key-sets",
                    "local-json-web-key-set": "local-json-web-key-sets",
                    "ip-address-list": None,
                    "icap-request-client-view": "icap-request-client-views",
                    "icap-request-backend-view": "icap-request-backend-views",
                    "icap-response-client-view": "icap-response-client-views",
                    "icap-response-backend-view": "icap-response-backend-views",
                    "mapping-template": "template"
                }

    def __init__( self, parent, obj=None, id=None ):
        self._typename = TYPENAME
        self._path = 'mappings'
        self._kind = KIND
        element.ModelElement.__init__( self, parent, obj=obj, id=id )
    
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
            return len( self.rels['template'] ) > 0
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
    def maintenance_page( self, enable: bool=False ) -> bool:
        """ Enable/disable maintenance page for mapping """
        return self._parent.conn.mapping.maintenance_page( self.id, enable=enable )
    
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
        mapping = self.rels['template'][0]['r']
        error = False
        while mapping:
            if force == False and mapping._attrs_modified:
                output.error( "Mapping {mapping.id} has pending updates - sync first" )
                error = True
            chain.insert( 0, mapping )
            if recursive and mapping.hasTemplate():
                mapping = mapping.rels['template'][0]['r']
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
    
