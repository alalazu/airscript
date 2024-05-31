 # AirScript: Airlock (Gateway) Configuration Script
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

"""
Airlock Gateway Configuration

This class represents a complete Airlock Gateway Configuration and consists of most config items

._apipolicy - dictionary of API policies
._backendgroups - dictionary of backend groups
._certs - dictionary of SSL/TLS certificates
._graphql - dictionary of GraphQL documents
._hostnames - dictionary of hostnames
._icap - dictionary of ICAP environments
._iplists - dictionary of IP lists
._jwks - dictionary of JSON Web Token Key Sets
._kerberos - dictionary of Kerberos Environments
._mappings - dictionary of mappings
._network_endpoints - dictionary of allowed network endpoints
._nodes - dictionary of nodes
._openapi - dictionary of OpenAPI documents
._templates - dictionary of mapping templates
._vhosts - dictionary of virtual hosts
"""

import datetime
from typing import Union

from airscript.model import api_policy
from airscript.model import backendgroup
from airscript.model import certificate
from airscript.model import graphql as graphql_object
from airscript.model import host
from airscript.model import icap as icap_object
from airscript.model import iplist
from airscript.model import jwks as jwks_object
from airscript.model import kerberos as kerberos_object
from airscript.model import mapping
from airscript.model import network_endpoint
from airscript.model import node
from airscript.model import openapi as openapi_object
from airscript.model import template
from airscript.model import vhost
from airscript.model import validator

from airscript.model import baseObject, gateway
from pyAirlock.gateway.config_api import gateway as gw_api

from airscript.utils import internal
from pyAirlock.common import log, utils


TYPENAME2KIND = {
    "api-policy-service": "APIPolicyService",
    "back-end-group": "BackendGroup",
    "ssl-certificate": "TLSCertificate",
    "graphql-document": "GraphQLDocument",
    "host": "Host",
    "icap-environment": "ICAPEnvironment",
    "ip-address-list": "IPList",
    "local-json-web-key-set": "JWKSLocal",
    "remote-json-web-key-set": "JWKSRemote",
    "kerberos-environment": "KerberosEnvironment",
    "mapping": "Mapping",
    "allowed-network-endpoint": "AllowedNetworkEndpoint",
    "node": "GatewayClusterNode",
    "openapi-document": "OpenAPIDocument",
    "mapping-template": "MappingTemplate",
    "virtual-host": "VirtualHost",
}
KIND2TYPENAME = {
    "APIPolicyService": "api-policy-service",
    "BackendGroup": "back-end-group",
    "TLSCertificate": "ssl-certificate",
    "GraphQLDocument": "graphql-document",
    "Host": "host",
    "ICAPEnvironment": "icap-environment",
    "IPList": "ip-address-list",
    "JWKSLocal": "local-json-web-key-set",
    "JWKSRemote": "remote-json-web-key-set",
    "KerberosEnvironment": "kerberos-environment",
    "Mapping": "mapping",
    "AllowedNetworkEndpoint": "allowed-network-endpoint",
    "GatewayClusterNode": "node",
    "OpenAPIDocument": "openapi-document",
    "MappingTemplate": "mapping-template",
    "VirtualHost": "virtual-host",
}
LISTKEY2TYPENAME = {
    "apipolicy": "api-policy-service",
    "backendgroups": "back-end-group",
    "certs": "ssl-certificate",
    "graphql": "graphql-document",
    "hostnames": "host",
    "icap": "icap-environment",
    "iplists": "ip-address-list",
    "jwks": "local-json-web-key-set",
    "jwks": "remote-json-web-key-set",
    "kerberos": "kerberos-environment",
    "mappings": "mapping",
    "network_endpoints": "allowed-network-endpoint",
    "nodes": "node",
    "openapi": "openapi-document",
    "templates": "mapping-template",
    "vhosts": "virtual-host",
}
RELATIONSHIP_ORDER = {
    "api-policy-service": 1000,
    "back-end-group": 5000,
    "ssl-certificate": 2000,
    "graphql-document": 1100,
    "host": 1,
    "icap-environment": 3,
    "ip-address-list": 1200,
    "local-json-web-key-set": 3200,
    "remote-json-web-key-set": 3200,
    "kerberos-environment": 3000,
    "mapping": 6000,
    "allowed-network-endpoint": 2,
    "node": 3100,
    "openapi-document": 1300,
    "mapping-template": 0,
    "virtual-host": 4000,
}


class Configuration( object ):
    def __init__( self, obj, conn: gw_api.GW, airscript_config ):
        if obj != None:
            self.id = obj['id']
            self.comment = utils.getDictValue( obj, 'attributes.comment', "" )
            self.type = obj['attributes']['configType']
            self.createdAt = obj['attributes']['createdAt']
            self.timestamp = datetime.datetime.fromisoformat( self.createdAt )
        else:
            self.id = 'new'
            self.comment = ''
            self.type = 'NEW'
            now = datetime.datetime.now()
            self.timestamp = now.timestamp()
            self.createdAt = now.strftime("%Y-%m-%d %H:%M:%S")
        self.conn = conn
        self._airscript_config = airscript_config
        self._loaded = False
        self._ordered_types = None
        self._log = log.Log( self.__module__ )
        self._reset()
    
    def __repr__( self ):
        return str( { 'id': self.id, 'comment': self.comment, 'type': self.type } )
    
    def clear( self ):
        self._reset()
        self._loaded = False
    
    def getObjects( self, type_name: str ) -> dict:
        if type_name == "api-policy-service":
            obj = self.objects['apipolicy']
        elif type_name == "back-end-group":
            obj = self.objects['backendgroups']
        elif type_name == "ssl-certificate":
            obj = self.objects['certs']
        elif type_name == "graphql-document":
            obj = self.objects['graphql']
        elif type_name == "host":
            obj = self.objects['hostnames']
        elif type_name == "icap-environment":
            obj = self.objects['icap']
        elif type_name == "ip-address-list":
            obj = self.objects['iplists']
        elif type_name == "local-json-web-key-set":
            obj = self.objects['jwks']
        elif type_name == "remote-json-web-key-set":
            obj = self.objects['jwks']
        elif type_name == "kerberos-environment":
            obj = self.objects['kerberos']
        elif type_name == "mapping":
            obj = self.objects['mappings']
        elif type_name == "allowed-network-endpoint":
            obj = self.objects['network_endpoints']
        elif type_name == "node":
            obj = self.objects['nodes']
        elif type_name == "openapi-document":
            obj = self.objects['openapi']
        elif type_name == "mapping-template":
            obj = self.objects['templates']
        elif type_name == "virtual-host":
            obj = self.objects['vhosts']
        return obj

    def getListFunc( self, type_name: str ):
        if type_name == "api-policy-service":
            func = self.apipolicy
        elif type_name == "back-end-group":
            func = self.backendgroups
        elif type_name == "ssl-certificate":
            func = self.certificates
        elif type_name == "graphql-document":
            func = self.graphql
        elif type_name == "host":
            func = self.hostnames
        elif type_name == "icap-environment":
            func = self.icap
        elif type_name == "ip-address-list":
            func = self.iplists
        elif type_name == "local-json-web-key-set":
            func = self.jwks
        elif type_name == "remote-json-web-key-set":
            func = self.jwks
        elif type_name == "kerberos-environment":
            func = self.kerberos
        elif type_name == "mapping":
            func = self.mappings
        elif type_name == "allowed-network-endpoint":
            func = self.networkendpoints
        elif type_name == "node":
            func = self.nodes
        elif type_name == "openapi-document":
            func = self.openapi
        elif type_name == "mapping-template":
            func = self.templates
        elif type_name == "virtual-host":
            func = self.vhosts
        return func
    
    def connectGateway( self, gw: gateway.Gateway, label: str ) -> bool:
        self.conn = gw.session( label=label )
        if not self.conn:
            return False
        if not gw.connect( label=label ):
            return False
        gw.configurationCreate( label=label )

    def load( self ) -> bool:
        """ Retrieve configuration data (vhosts, mappings etc.) from Airlock Gateway using REST API. """
        if self.conn:
            if self._loaded == False:
                if self.id == 'new xxxx':
                    r = self.conn.configuration.create()
                else:
                    self._log.verbose( "Fetching configuration data from '{}'".format( self.conn.getName() ))
                    r = self.conn.configuration.load( self.id )
                if r == None:
                    self._log.error( "Loading failed: not found" )
                else:
                    self._loaded = True
        return self._loaded
    
    def loadAll( self ) -> bool:
        r = self.load()
        if r:
            self.getAll()
        return r
    
    def sync( self ):
        """ Upload all changed items and establish connections """
        # keep order, allows linking directly at sync
        if not self._ordered_types:
            self._orderTypes()
        for k in sorted( self._ordered_types ):
            element = self._ordered_types[k]
            for cfg_item in self.objects[element].values():
                if isinstance( cfg_item, list ):
                    for item in cfg_item:
                        item.sync()
                else:
                    cfg_item.sync()
            # remove deleted objects
            objs = [k for k,v in self.objects[element].items() if v.isDeleted()]
            for key in objs:
                del self.objects[element][key]
    
    def elementOrderNr( self, type_name: str ) -> int:
        try:
            return RELATIONSHIP_ORDER[type_name]
        except KeyError:
            return 0
    
    def elementOrderList( self ):
        return sorted( RELATIONSHIP_ORDER, key=lambda s: int(RELATIONSHIP_ORDER[s]) )
    
    def activate( self, comment: str=None ) -> bool:
        """
        Activate this configuration.
        
        A comment is required. When updating an existing configuration or when the comment property of a new configuration is unset,
        the comment has to be specified when calling `activate`.
        If you absolutely don't want to specify one (against all best practices), you may pass comment=\"\".
        
        Make sure to have called .update() on all modified items.
        """
        if not self.conn:
            return False
        if self._loaded or self.comment == "":
            if comment == None:
                self._log.warning( "No comment specified! If you don't want to specify one, please use '<obj>.activate( comment=\"\" )'" )
                return False
            elif comment != "":
                params = {'comment': comment }
        else:
            params = {'comment': self.comment}
        resp = self.conn.post( "/configuration/configurations/activate", data=params, timeout=60 )
        if resp.status_code != 200:
            self._log.error( "Activation failed: %s" % (resp.status_code,) )
            return False
        return True
    
    def save( self, comment: str=None ) -> bool:
        """
        Save this configuration.
        
        A comment is required. When updating an existing configuration or when the comment property of a new configuration is unset,
        the comment has to be specified when calling `activate`.
        If you absolutely don't want to specify one (against all best practices), you may pass comment=\"\".
        
        Make sure to have called .update() on all modified items.
        """ 
        if not self.conn:
            return False
        if self._loaded or self.comment == "":
            if comment == None:
                self._log.warning( "No comment specified! If you don't want to specify one, please use '<obj>.activate( comment=\"\" )'" )
                return False
            elif comment != "":
                params = {'comment': comment }
        else:
            params = {'comment': self.comment}
        resp = self.conn.post( "/configuration/configurations/save", data=params )
        if resp.status_code != 200:
            self._log.error( "Save failed: %s (%s)" % (resp.status_code,resp.text) )
            return False
        return True
    
    def delete( self ):
        """ Delete this configuration. """ 
        if not self.conn:
            return False
        resp = self.conn.delete( "/configuration/configurations/%s" % (self.id,) )
        if resp.status_code != 204:
            self._log.error( "Deletion failed: %s (%s)" % (resp.status_code,resp.text) )
            return False
        return True
    
    def export( self, fname: str=None ) -> str:
        """ Download configuration from Airlock Gateway as a zip file. """
        if not self.conn:
            return False
        if fname:
            zip_file = fname
        else:
            zip_file = "{}/{}-{}.zip".format( self._airscript_config.get( "airscript.download-dir"), self.conn.getName(), self.id )
        self.conn.configuration.export( self.id, zip_file )
        self._log.verbose( f"Configuration saved to '{zip_file}'" )
        return zip_file
    
    # def _convertRelationships( self, my_prio: int, declarative_element: dict ):
    #     obj: baseObject.BaseObject
    #     declarative_element['relationships'] = {}
    #     for kind, names in declarative_element['connections'].items():
    #         type_name = KIND2TYPENAME[kind]
    #         print( f"- {type_name} - {RELATIONSHIP_ORDER[type_name]}")
    #         if RELATIONSHIP_ORDER[type_name] > my_prio:
    #             continue
    #         objects = self.getObjects( type_name )
    #         for name in names:
    #             print( f"  - {name}" )
    #             obj = self._findByName( objects, name )
    #             if obj:
    #                 declarative_element['relationships'][obj.getPath()].append( {'type': type_name, 'id': obj.id} )
    #     del declarative_element['connections']

    def declarativeImport( self, declarative: dict, env: str=None ):
        # format of declarative:
        # { 'source': self._dirname, 'env': env, 'objects': { kind: [{ 'attributes': object, 'connections': {kind: [names]} }] }}
        self.comment = f"Declarative ({declarative['source']}, env {declarative['env']})"
        # create objects without connecting them
        for item_kind, item_lists_per_kind in declarative['objects'].items():
            type_name = KIND2TYPENAME[item_kind]
            for item in item_lists_per_kind:
                if not 'relationships' in item:
                    item['relationships'] = {}
                obj = self.createElement( type_name, data={'attributes': item['attributes']} )
                obj.sync()
                obj.declarativeStoreConnections( item['connections'] )
                print( f"{item_kind}: {obj}" )
                self._addElement2ObjectMap( obj )
        # establish connections
        for object_map in self.objects.values():
            for obj in object_map.values():
                connections = obj.declarativeGetConnections()
                if connections:
                    for ref_kind, names in connections.items():
                        for name in names:
                            ref = self._findByName( self.getObjects( KIND2TYPENAME[ref_kind] ), name )
                            obj.addRel( ref, load=True, backlink=True )
        self.sync()

        ## keep order, allows linking directly when adding config elements
        # orderedKinds = {}
        # idx = 0
        # for kind in declarative['objects'].keys():
        #     try:
        #         orderedKinds[RELATIONSHIP_ORDER[KIND2TYPENAME[kind]]] = kind
        #     except KeyError:
        #         idx += 1
        #         orderedKinds[idx] = kind
        # for prio in sorted( orderedKinds ):
        #     kind = orderedKinds[prio]
        #     type_name = KIND2TYPENAME[kind]
        #     for item in declarative['objects'][kind]:
        #         # print( f"{item['attributes']['name']}: {type_name} - {prio}" )
        #         #self._convertRelationships( prio, item )
        #         #connections = item['connections']
        #         #del item['connections']
        #         if not 'relationships' in item:
        #             item['relationships'] = {}
        #         obj = self.createElement( type_name, data={'attributes': item['attributes'], 'relationships': item['relationships']} )
        #         #item['connections'] = connections
        #         obj.sync()
        #         print( obj )
        #         self._addElement2ObjectMap( obj )
        #         self._declarativeCreateRelationshipEntry( obj, kind, declarative['objects'] )
        self.save()
    
    def _declarativeCreateRelationshipEntry( self, obj: baseObject.BaseObject, my_kind: str, declarative_objects: dict ):
        # declarative_objects: { kind: [{ 'attributes': object, 'connections': {kind: [names]} }] }
        for item_kind, item_lists_per_kind in declarative_objects.items():
            for item in item_lists_per_kind:
                for ref_kind, names in item['connections'].items():
                    if ref_kind != my_kind:
                        continue
                    if RELATIONSHIP_ORDER[KIND2TYPENAME[item_kind]] < RELATIONSHIP_ORDER[KIND2TYPENAME[my_kind]]:
                        # connection to config element which has already/just yet been created
                        # 
                        continue
                    if obj.name in names:
                        if not 'relationships' in item:
                            item['relationships'] = {}
                        try:
                            item['relationships'][obj.getPath()]['data'].append( {'type': obj.getTypeName(), 'id': obj.id} )
                        except KeyError:
                            item['relationships'][obj.getPath()] = {'data':[{'type': obj.getTypeName(), 'id': obj.id}]}

    def validate( self ) -> dict:
        """ Retrieve validation messages for this configuration. """
        if not self.conn:
            return [ validator.Validator( self, obj={ "code" : "NOT_CONNECTED", "title" : "not connected to Airlock Gateway",
                                                      "detail" : "The configuration is not associated with a connection to an Airlock Gateway. No operations will succeed until connection is established using .connectGateway()",
                                                      "source" : { "pointer" : None },
                                                      "meta" : { "type" : "airscript", "severity" : "ERROR", "model" : None } } ) ]
        if self._loaded == False:
            if self.load() == False:
                return {}
        self.messages = []
        resp = self.conn.get( "/configuration/validator-messages" )
        if resp.text != "":
            for entry in resp.json()['data']:
                self.messages.append( validator.Validator( self, obj=entry ))
        if len( self.messages ) == 0:
            return {}
        else:
            error = []
            warning = []
            info = []
            for entry in self.messages:
                if entry.attrs['meta']['severity'] == "ERROR":
                    error.append( entry )
                elif entry.attrs['meta']['severity'] == "WARNING":
                    warning.append( entry )
                elif entry.attrs['meta']['severity'] == "INFO":
                    info.append( entry )
            return { "error": error, "warning": warning, "info": info }
    
    def nodes( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._nodes, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def vhosts( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._vhosts, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def mappings( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._mappings, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def apipolicy( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._apipolicy, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def backendgroups( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._backendgroups, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def certificates( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._certs, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def jwks( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._jwks, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def openapi( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._openapi, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def graphql( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._graphql, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def hostnames( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._hostnames, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def icap( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._icap, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def iplists( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._iplists, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def kerberos( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._kerberos, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def networkendpoints( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._network_endpoints, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def templates( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._templates, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def addElement( self, type_name: str, id: str=None, data: dict=None ):
        obj = self.createElement( type_name, id=id, data=data )
        return self._addElement2ObjectMap( obj )
    
    def createElement( self, type_name: str, id: str=None, data: dict=None ):
        if type_name in ["api-policy-service", "APIPolicyService"]:
            obj = self.addAPIPolicy( id=id, data=data )
        elif type_name in ["back-end-group", "BackendGroup"]:
            obj = self.addBackendGroup( id=id, data=data )
        elif type_name in ["ssl-certificate", "TLSCertificate"]:
            obj = self.addCertificate( id=id, data=data )
        elif type_name in ["graphql-document", "GraphQLDocument"]:
            obj = self.addGraphQL( id=id, data=data )
        elif type_name in ["host", "Host"]:
            obj = self.addHostName( id=id, data=data )
        elif type_name in ["icap-environment", "ICAPEnvironment"]:
            obj = self.addICAP( id=id, data=data )
        elif type_name in ["ip-address-list", "IPList"]:
            obj = self.addIPList( id=id, data=data )
        elif type_name in ["local-json-web-key-set", "JWKSLocal"]:
            obj = self.addJWKS( id=id, data=data, remote=False )
        elif type_name in ["remote-json-web-key-set", "JWKSRemote"]:
            obj = self.addJWKS( id=id, data=data, renmote=True )
        elif type_name in ["kerberos-environment", "KerberosEnvironment"]:
            obj = self.addKerberos( id=id, data=data )
        elif type_name in ["mapping", "Mapping"]:
            obj = self.addMapping( id=id, data=data )
        elif type_name in ["allowed-network-endpoint", "AllowedNetworkEndpoint"]:
            obj = self.addNetworkEndpoint( id=id, data=data )
        elif type_name in ["node", "GatewayClusterNode"]:
            obj = self.addNode( id=id, data=data )
        elif type_name in ["openapi-document", "OpenAPIDocument"]:
            obj = self.addOpenAPI( id=id, data=data )
        elif type_name in ["mapping-template", "MappingTemplate"]:
            obj = self.addTemplate( id=id, data=data )
        elif type_name in ["virtual-host", "VirtualHost"]:
            obj = self.addVHost( id=id, data=data )
        return obj

    def _addElement2ObjectMap( self, obj: baseObject.BaseObject ) -> baseObject.BaseObject:
        if obj.id:
            self.getObjects( obj.getTypeName() )[obj.id] = obj
        else:
            try:
                self.getObjects( obj.getTypeName() )[None].append( obj )
            except KeyError:
                self.getObjects( obj.getTypeName() )[None] = [obj]
        return obj
    
    def addNode( self, id: str=None, data: dict=None ) -> node.Node:
        if id in self._nodes:
            obj = self._nodes[id]
            if data:
                obj.loadData( data=data )
        else:
            obj = node.Node( self, obj=data, id=id )
        return obj

    def addVHost( self, id: str=None, data: dict=None ) -> vhost.VirtualHost:
        if id in self._vhosts:
            obj = self._vhosts[id]
            if data:
                obj.loadData( data=data )
        else:
            obj = vhost.VirtualHost( self, obj=data, id=id )
        return obj
    
    def addMapping( self, id: str=None, data: dict=None ) -> mapping.Mapping:
        if id in self._mappings:
            obj = self._mappings[id]
            if data:
                obj.loadData( data=data )
        else:
            obj = mapping.Mapping( self, obj=data, id=id )
        return obj
    
    def addTemplate( self, id: str=None, data: dict=None ) -> template.Template:
        if id in self._templates:
            obj = self._templates[id]
            if data:
                obj.loadData( data=data )
        else:
            obj = template.Template( self, obj=data, id=id )
        return obj
    
    def addAPIPolicy( self, id: str=None, data: dict=None ) -> api_policy.APIPolicy:
        if id in self._apipolicy:
            obj = self._apipolicy[id]
            if data:
                obj.loadData( data=data )
        else:
            obj = api_policy.APIPolicy( self, obj=data, id=id )
        return obj
    
    def addBackendGroup( self, id: str=None, data: dict=None ) -> backendgroup.Backendgroup:
        if id in self._backendgroups:
            obj = self._backendgroups[id]
            if data:
                obj.loadData( data=data )
        else:
            obj = backendgroup.Backendgroup( self, obj=data, id=id )
        return obj
    
    def addCertificate( self, id: str=None, data: dict=None ) -> certificate.Certificate:
        if id in self._certs:
            obj = self._certs[id]
            if data:
                obj.loadData( data=data )
        else:
            obj = certificate.Certificate( self, obj=data, id=id )
        return obj
    
    def addJWKS( self, id: str=None, data: dict=None, remote: bool=True ) -> jwks_object.JWKS:
        if id in self._jwks:
            obj = self._jwks[id]
            if data:
                obj.loadData( data=data )
        else:
            obj = jwks_object.JWKS( self, obj=data, id=id, remote=remote )
        return obj
    
    def addOpenAPI( self, id: str=None, data: dict=None ) -> openapi_object.OpenAPI:
        if id in self._openapi:
            obj = self._openapi[id]
            if data:
                obj.loadData( data=data )
        else:
            obj = openapi_object.OpenAPI( self, obj=data, id=id )
        return obj
    
    def addGraphQL( self, id: str=None, data: dict=None ) -> graphql_object.GraphQL:
        if id in self._graphql:
            obj = self._graphql[id]
            if data:
                obj.loadData( data=data )
        else:
            obj = graphql_object.GraphQL( self, obj=data, id=id )
        return obj
    
    def addHostName( self, id: str=None, data: dict=None ) -> host.Host:
        if id in self._hostnames:
            obj = self._hostnames[id]
            if data:
                obj.loadData( data=data )
        else:
            obj = host.Host( self, obj=data, id=id )
        return obj
    
    def addICAP( self, id: str=None, data: dict=None ) -> icap_object.ICAP:
        if id in self._icap:
            obj = self._icap[id]
            if data:
                obj.loadData( data=data )
        else:
            obj = icap_object.ICAP( self, obj=data, id=id )
        return obj
    
    def addIPList( self, id: str=None, data: dict=None ) -> iplist.IPList:
        if id in self._iplists:
            obj = self._iplists[id]
            if data:
                obj.loadData( data=data )
        else:
            obj = iplist.IPList( self, obj=data, id=id )
        return obj
    
    def addNetworkEndpoint( self, id: str=None, data: dict=None ) -> network_endpoint.NetworkEndpoint:
        if id in self._network_endpoints:
            obj = self._network_endpoints[id]
            if data:
                obj.loadData( data=data )
        else:
            obj = network_endpoint.NetworkEndpoint( self, obj=data, id=id )
        return obj
    
    def addKerberos( self, id: str=None, data: dict=None ) -> kerberos_object.Kerberos:
        if id in self._kerberos:
            obj = self._kerberos[id]
            if data:
                obj.loadData( data=data )
        else:
            obj = kerberos_object.Kerberos( self, obj=data, id=id )
        return obj
    
    def getNodes( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all nodes of this configuration from Airlock Gateway.
        
        This function must be executed before ._nodes is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        for entry in self.conn.node.read():
            self._addElement2ObjectMap( self.addNode( id=entry['id'], data=entry ))
        return self._nodes
    
    def getVHosts( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all virtual hosts of this configuration from Airlock Gateway.
        
        This function must be executed before ._vhosts is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        for entry in self.conn.vhost.read():
            self._addElement2ObjectMap( self.addVHost( id=entry['id'], data=entry ))
        return self.vhosts()
    
    def getMappings( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all mappings of this configuration from Airlock Gateway.
        
        This function must be executed before ._mappings is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        for entry in self.conn.mapping.read():
            self._addElement2ObjectMap( self.addMapping( id=entry['id'], data=entry ))
        return self._mappings
    
    def getTemplates( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all mapping templates of this configuration from Airlock Gateway.
        
        This function must be executed before ._templates is filled-in.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        resp = self.conn.get( "/configuration/templates/mappings" )
        if resp.text != "":
            for entry in resp.json()['data']:
                self._addElement2ObjectMap( self.addTemplate( id=entry['id'], data=entry ))
        return self._templates
    
    def getAPIPolicies( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all APIPolicy documents of this configuration from Airlock Gateway.
        
        This function must be executed before ._apipolicy is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        for entry in self.conn.api_policy.read():
            self._addElement2ObjectMap( self.addAPIPolicy( id=entry['id'], data=entry ))
        return self._apipolicy
    
    def getBackendGroups( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all backend groups of this configuration from Airlock Gateway.
        
        This function must be executed before ._backendgroups is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        for entry in self.conn.backendgroup.read():
            self._addElement2ObjectMap( self.addBackendGroup( id=entry['id'], data=entry ))
        return self._backendgroups
    
    def getCertificates( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all SSL/TLS certificates of this configuration from Airlock Gateway.
        
        This function must be executed before ._certs is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        for entry in self.conn.certificate.read():
            self._addElement2ObjectMap( self.addCertificate( id=entry['id'], data=entry ))
        return self._certs
    
    def getJWKS( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all JWKS definitions of this configuration from Airlock Gateway.
        
        This function must be executed before ._jwks is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        for entry in self.conn.jwks_local.read():
            self._addElement2ObjectMap( self.addJWKS( id=entry['id'], data=entry, remote=False ))
        for entry in self.conn.jwks_remote.read():
            self._addElement2ObjectMap( self.addJWKS( id=entry['id'], data=entry ))
        return self._jwks
    
    def getOpenAPI( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all OpenAPI documents of this configuration from Airlock Gateway.
        
        This function must be executed before ._openapi is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        for entry in self.conn.openapi.read():
            self._addElement2ObjectMap( self.addOpenAPI( id=entry['id'], data=entry ))
        return self._openapi
    
    def getGraphQL( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all GraphQL documents of this configuration from Airlock Gateway.
        
        This function must be executed before ._graphql is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        for entry in self.conn.graphql.read():
            self._addElement2ObjectMap( self.addGraphQL( id=entry['id'], data=entry ))
        return self._graphql
    
    def getHostNames( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all Host documents of this configuration from Airlock Gateway.
        
        This function must be executed before ._hostnames is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        for entry in self.conn.host.read():
            self._addElement2ObjectMap( self.addHostName( id=entry['id'], data=entry ))
        return self._hostnames
    
    def getICAP( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all ICAP documents of this configuration from Airlock Gateway.
        
        This function must be executed before ._icap is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        for entry in self.conn.icap.read():
            self._addElement2ObjectMap( self.addICAP( id=entry['id'], data=entry ))
        return self._icap
    
    def getIPLists( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all IP lists of this configuration from Airlock Gateway.
        
        This function must be executed before ._iplists is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        for entry in self.conn.iplist.read():
            self._addElement2ObjectMap( self.addIPList( id=entry['id'], data=entry ))
        return self._iplists
    
    def getNetworkEndpoints( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all NetworkEndpoint documents of this configuration from Airlock Gateway.
        
        This function must be executed before ._network_endpoints is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        for entry in self.conn.network_endpoint.read():
            self._addElement2ObjectMap( self.addNetworkEndpoint( id=entry['id'], data=entry ))
        return self._network_endpoints
    
    def getKerberos( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all Kerberos Environments of this configuration from Airlock Gateway.
        
        This function must be executed before ._kerberos is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        for entry in self.conn.kerberos.read():
            self._addElement2ObjectMap( self.addKerberos( id=entry['id'], data=entry ))
        return self._kerberos
    
    def getAll( self ):
        """
        Use REST API to fetch most configuration items from Airlock Gateway
        """
        self._log.verbose( "- Nodes" )
        self.getNodes()
        self._log.verbose( "- API policies" )
        self.getAPIPolicies()
        self._log.verbose( "- Backend groups" )
        self.getBackendGroups()
        self._log.verbose( "- Certificates" )
        self.getCertificates()
        self._log.verbose( "- GraphQL" )
        self.getGraphQL()
        self._log.verbose( "- Hostnames" )
        self.getHostNames()
        self._log.verbose( "- ICAP" )
        self.getICAP()
        self._log.verbose( "- IP lists" )
        self.getIPLists()
        self._log.verbose( "- JWKS" )
        self.getJWKS()
        self._log.verbose( "- Kerberos" )
        self.getKerberos()
        self._log.verbose( "- Mappings" )
        self.getMappings()
        self._log.verbose( "- Network endpoints" )
        self.getNetworkEndpoints()
        self._log.verbose( "- OpenAPI" )
        self.getOpenAPI()
        self._log.verbose( "- Virtual hosts" )
        self.getVHosts()
    
    def mappingFromTemplate( self, template ) -> bool:
        """ Create new mapping from template. """
        if not self.conn:
            return False
        params = { 'data': { 'type': 'create-mapping-from-template', 'id': template.id }}
        resp = self.conn.post( "/configuration/mappings/create-from-template", data=params)
        if resp.status_code != 201:
            self._log.error( "Create failed: %s (%s)" % (resp.status_code,resp.text) )
            return False
        if resp.text != "":
            for entry in resp.json()['data']:
                m = mapping.Mapping( entry, self.conn )
                self._mappings[m.id] = m
        return True
    
    def mappingImport( self, fname ) -> bool:
        """
        Upload configuration zip file to Airlock Gateway.
        
        This function can be used to migrate mappings from server to server,
        e.g. across environments.
        """
        if not self.conn:
            return False
        files = { 'file': open( fname, 'rb' ) }
        resp = self.conn.uploadCopy( "/configuration/mappings/import-mapping", accept='application/zip', files=files )
        if resp.status_code != 200:
            self._log.error( "Import failed: %s (%s)" % (resp.status_code,resp.text) )
            return False
        if self._mappings != None:
            self.getMappings()
        return True
    
    def listNodes( self ) -> list[dict[node.Node]]:
        """ Return sorted list of nodes. """
        if self._nodes == None:
            self.getNodes()
        return self._listSorted( self._nodes, key='name' )
        # return sorted( self._nodes.items(), key=internal.itemgetter_lc_name )
    
    def listVHosts( self ):
        """ Return sorted list of virtual hosts. """
        if self._vhosts == None:
            self.getVHosts()
        return self._listSorted( self._vhosts, key='name' )
        # return sorted( self._vhosts.items(), key=internal.itemgetter_lc_name )
    
    def listMappings( self ):
        """ Return sorted list of mappings. """
        if self._mappings == None:
            self.getMappings()
        return self._listSorted( self._mappings, key='name' )
        # return sorted( self._mappings.items(), key=internal.itemgetter_lc_name )
    
    def listAPIPolicies( self ):
        """ Return sorted list of APIPolicy documents. """
        if self._apipolicy == None:
            self.getAPIPolicies()
        return self._listSorted( self._apipolicy )
    
    def listBackendGroups( self ):
        """ Return sorted list of backend groups. """
        if self._backendgroups == None:
            self.getBackendGroups()
        return self._listSorted( self._backendgroups )
    
    def listCertificates( self ):
        """ Return sorted list of SSL/TLS certificates. """
        if self._certs == None:
            self.getCertificates()
        return self._listSorted( self._certs )
    
    def listJWKS( self ):
        """ Return sorted list of JSON Web Token Key Sets. """
        if self._jwks == None:
            self.getJWKS()
        return self._listSorted( self._jwks )
    
    def listOpenAPI( self ):
        """ Return sorted list of OpenAPI documents. """
        if self._openapi == None:
            self.getOpenAPI()
        return self._listSorted( self._openapi )
    
    def listGraphQL( self ):
        """ Return sorted list of GraphQL documents. """
        if self._graphql == None:
            self.getGraphQL()
        return self._listSorted( self._graphql )
    
    def listHostNames( self ):
        """ Return sorted list of Host documents. """
        if self._hostnames == None:
            self.getHostNames()
        return self._listSorted( self._hostnames )
    
    def listICAP( self ):
        """ Return sorted list of ICAP environments. """
        if self._icap == None:
            self.getICAP()
        return self._listSorted( self._icap )
    
    def listIPLists( self ):
        """ Return sorted list of IP lists. """
        if self._iplists == None:
            self.getIPLists()
        return self._listSorted( self._iplists, key='name' )
        # return sorted( self._iplists.items(), key=internal.itemgetter_lc_1 )
    
    def listNetworkEndpoints( self ):
        """ Return sorted list of Network Endpoints. """
        if self._network_endpoints == None:
            self.getNetworkEndpoints()
        return self._listSorted( self._network_endpoints )
    
    def listKerberos( self ):
        """ Return sorted list of Network Endpoints. """
        if self._kerberos == None:
            self.getKerberos()
        return self._listSorted( self._kerberos )
    
    def listTemplates( self ):
        """ Return sorted list of mapping templates. """
        if self._templates == None:
            self.getTemplates()
        return self._listSorted( self._templates, key='name' )
        # return sorted( self._templates.items(), key=internal.itemgetter_lc_0 )
    
    def listLabels( self ):
        """ Return sorted list of labels assigned to any mapping. """
        if self._mappings == None:
            return []
        s = set()
        for m in self._mappings.values():
            s = s.union( set( m.attrs['labels'] ))
        return sorted( s )
        # r = []
        # for m in self._mappings.values():
        #     r.extend( [x for x in m.attrs['labels']] )
        # r.sort()
        # i = 1
        # while i < len(r):
        #     if r[i] == r[i-1]:
        #         del r[i]
        #         continue
        #     i += 1
        # return r
    
    def findVHost( self, name, criteria=None ):
        """ Return list of virtual hosts whose name contains 'name'. """
        if self._vhosts == None:
            self.getVHosts()
        if criteria == None:
            return [ self._findByName( self._vhosts, name ) ]
        self._log.warning( "Criteria search not implemented yet" )
        return None
        
    def findMapping( self, name, criteria=None ):
        """ Return list of mappings whose name contains 'name'. """
        if self._mappings == None:
            self.getMappings()
        if criteria == None:
            return [ self._findByName( self._mappings, name ) ]
        self._log.warning( "Criteria search not implemented yet" )
        return None
        
    def findBackendgroup( self, name, criteria=None ):
        """ Return list of backend groups whose name contains 'name'. """
        if self._backendgroups == None:
            self.getBackendGroups()
        if criteria == None:
            return [ self._findByName( self._backendgroups, name ) ]
        self._log.warning( "Criteria search not implemented yet" )
        return None
        
    def findCertificate( self, name, criteria=None ):
        """ Return list of SSL/TLS certificates whose name contains 'name'. """
        if self._certs == None:
            self.getCertificates()
        if criteria == None:
            return [ self._findByName( self._certs, name ) ]
        self._log.warning( "Criteria search not implemented yet" )
        return None
        
    def findJWKS( self, name, criteria=None ):
        """ Return list of JSON Web Token Key Sets whose name contains 'name'. """
        if self._jwks == None:
            self.getJWKS()
        if criteria == None:
            return [ self._findByName( self._jwks, name ) ]
        self._log.warning( "Criteria search not implemented yet" )
        return None
        
    def findOpenAPI( self, name, criteria=None ):
        """ Return list of OpenAPI documents whose name contains 'name'. """
        if self._openapi == None:
            self.getOpenAPI()
        if criteria == None:
            return [ self._findByName( self._openapi, name ) ]
        self._log.warning( "Criteria search not implemented yet" )
        return None
        
    def findGraphQL( self, name, criteria=None ):
        """ Return list of GraphQL documents whose name contains 'name'. """
        if self._graphql == None:
            self.getGraphQL()
        if criteria == None:
            return [ self._findByName( self._graphql, name ) ]
        self._log.warning( "Criteria search not implemented yet" )
        return None
        
    def findIPList( self, name, criteria=None ):
        """ Return list of IP lists whose name contains 'name'. """
        if self._iplists == None:
            self.getIPLists()
        if criteria == None:
            return [ self._findByName( self._iplists, name ) ]
        self._log.warning( "Criteria search not implemented yet" )
        return None
        
    def deleteNode( self, value ):
        """ Delete node from this configuration. """
        if not type( value ) == node.Node:
            self._log.error( "This is not a virtual host but %s" % (type(value),) )
            return False
        if value.delete() == False:
            return False
        del self._nodes[value.id]
        return True
        
    def deleteVHost( self, value ):
        """ Delete virtual host from this configuration. """
        if not type( value ) == vhost.VirtualHost:
            self._log.error( "This is not a virtual host but %s" % (type(value),) )
            return False
        if value.delete() == False:
            return False
        del self._vhosts[value.id]
        return True
        
    def deleteMapping( self, value ):
        """ Delete mapping from this configuration. """
        if not type( value ) == mapping.Mapping:
            self._log.error( "This is not a mapping but %s" % (type(value),) )
            return False
        if value.delete() == False:
            return False
        del self._mappings[value.id]
        return True
        
    def deleteAPIPolicy( self, apiPolicy ):
        """ Delete APIPolicy document from this configuration. """
        if not type( apiPolicy ) == api_policy.APIPolicy:
            self._log.error( "This is not a APIPolicy document but %s" % (type(apiPolicy),) )
            return False
        if apiPolicy.delete() == False:
            return False
        del self._apipolicy[apiPolicy.id]
        return True
        
    def deleteBackendGroup( self, value ):
        """ Delete backend group from this configuration. """
        if not type( value ) == backendgroup.Backendgroup:
            self._log.error( "This is not a backendgroup but %s" % (type(value),) )
            return False
        if value.delete() == False:
            return False
        del self.values[backendgroup.id]
        return True
        
    def deleteCertificate( self, value ):
        """ Delete SSL/TLS certificate from this configuration. """
        if not type( value ) == certificate.Certificate:
            self._log.error( "This is not a certificate but %s" % (type(value),) )
            return False
        if value.delete() == False:
            return False
        del self._certs[value.id]
        return True
        
    def deleteJWKS( self, value ):
        """ Delete JSON Web Token Key Set from this configuration. """
        if not type( value ) == jwks_object.JWKS:
            self._log.error( "This is not a JWKS but %s" % (type(value),) )
            return False
        if value.delete() == False:
            return False
        del self._jwks[value.id]
        return True
        
    def deleteOpenAPI( self, value ):
        """ Delete OpenAPI document from this configuration. """
        if not type( value ) == openapi_object.OpenAPI:
            self._log.error( "This is not a OpenAPI document but %s" % (type(value),) )
            return False
        if value.delete() == False:
            return False
        del self._openapi[value.id]
        return True
        
    def deleteGraphQL( self, value ):
        """ Delete GraphQL document from this configuration. """
        if not type( value ) == graphql_object.GraphQL:
            self._log.error( "This is not a GraphQL document but %s" % (type(value),) )
            return False
        if value.delete() == False:
            return False
        del self._graphql[value.id]
        return True
        
    def deleteHostname( self, host ):
        """ Delete Host document from this configuration. """
        if not type( host ) == host.Host:
            self._log.error( "This is not a Host document but %s" % (type(host),) )
            return False
        if host.delete() == False:
            return False
        del self._hostnames[host.id]
        return True
        
    def deleteICAP( self, icap_env ):
        """ Delete ICAP environment from this configuration. """
        if not type( icap_env ) == icap_object.ICAP:
            self._log.error( "This is not a ICAP document but %s" % (type(icap_env),) )
            return False
        if icap_env.delete() == False:
            return False
        del self._icap[icap_env.id]
        return True
        
    def deleteIPList( self, value ):
        """ Delete IP list from this configuration. """
        if not type( value ) == iplist.IPList:
            self._log.error( "This is not a IP list but %s" % (type(value),) )
            return False
        if value.delete() == False:
            return False
        del self._iplists[value.id]
        return True
    
    def deleteNetworkEndpoint( self, nep ):
        """ Delete NetworkEndpoint from this configuration. """
        if not type( nep ) == network_endpoint.NetworkEndpoints:
            self._log.error( "This is not a NetworkEndpoint but %s" % (type(nep),) )
            return False
        if nep.delete() == False:
            return False
        del self._network_endpoints[nep.id]
        return True
        
    def deleteKerberos( self, krb ):
        """ Delete KerberosEnvironment from this configuration. """
        if not type( krb ) == kerberos_object.Kerberos:
            self._log.error( "This is not a KerberosEnvironment but %s" % (type(krb),) )
            return False
        if krb.delete() == False:
            return False
        del self._kerberos[krb.id]
        return True
        
    def _reset( self ):
        self.objects = {
            'apipolicy': {},
            'backendgroups': {},
            'certs': {},
            'graphql': {},
            'hostnames': {},
            'icap': {},
            'iplists': {},
            'jwks': {},
            'kerberos': {},
            'mappings': {},
            'nodes': {},
            'openapi': {},
            'network_endpoints': {},
            'templates': {},
            'vhosts': {},
        }
        self._apipolicy = self.objects['apipolicy']
        self._backendgroups = self.objects['backendgroups']
        self._certs = self.objects['certs']
        self._graphql = self.objects['graphql']
        self._hostnames = self.objects['hostnames']
        self._icap = self.objects['icap']
        self._iplists = self.objects['iplists']
        self._jwks = self.objects['jwks']
        self._kerberos = self.objects['kerberos']
        self._mappings = self.objects['mappings']
        self._nodes = self.objects['nodes']
        self._openapi = self.objects['openapi']
        self._network_endpoints = self.objects['network_endpoints']
        self._templates = self.objects['templates']
        self._vhosts = self.objects['vhosts']
    
    def _listSorted( self, list_of_dicts: list[dict], key: str='id' ):
        if not type( list_of_dicts ) == dict:
            self._log.error( "Wrong object type: %s" % (type(list_of_dicts),) )
            return []
        if key == 'name':
            func = internal.itemgetter_lc_name
        else:
            func = internal.itemgetter_id
        return sorted( (v for v in list_of_dicts.values() if not v.isDeleted()), key=func )
    
    def _findByName( self, objects, name ):
        for k,v in objects.items():
            if k:
                v = [v]
            for item in v:
                if item.isDeleted():
                    continue
                if item.name == name:
                    return objects[k]
                # elif name in item.name:
                #     r.append( objects[k] )
        return None
    
    def _orderTypes( self ):
        self._ordered_types = {}
        idx = 0
        for k in self.objects.keys():
            try:
                self._ordered_types[RELATIONSHIP_ORDER[k]] = k
            except KeyError:
                self._ordered_types[idx] = k
                idx += 1
        
