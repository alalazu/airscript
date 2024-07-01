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
._anomalyshield_applications - dictionary of Anomaly Shield applications
._anomalyshield_rules - dictionary of Anomaly Shield rules
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
._trafficmatchers - dictionary of Anomaly Shield traffic matchers
._triggers - dictionary of Anomaly Shield triggers
._vhosts - dictionary of virtual hosts
"""

import datetime
from typing import Union

from airscript.base import element, element_helpers
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
from airscript.model import route
from airscript.model import template
from airscript.model import vhost
from airscript.model import validator

from airscript.anomalyshield import application as anomalyshield_application
from airscript.anomalyshield import rule as anomalyshield_rule
from airscript.anomalyshield import traffic_matcher as anomalyshield_traffic_matcher
from airscript.anomalyshield import trigger as anomalyshield_trigger

from airscript.system_settings import anomalyshield as anomalyshield_settings
from airscript.system_settings import default_route as default_route_settings
from airscript.system_settings import dynamic_ip_blacklist as dynamic_ip_blacklist_settings
from airscript.system_settings import license
from airscript.system_settings import log as log_settings
from airscript.system_settings import reporting as reporting_settings
from airscript.system_settings import network_services as network_services_settings
from airscript.system_settings import session as session_settings

from airscript.utils import internal
from pyAirlock.common import lookup
from pyAirlock.common import exception, log, utils


# TYPENAME2KIND = {
#     "api-policy-service": "APIPolicyService",
#     "back-end-group": "BackendGroup",
#     "ssl-certificate": "TLSCertificate",
#     "graphql-document": "GraphQLDocument",
#     "host": "Host",
#     "icap-environment": "ICAPEnvironment",
#     "ip-address-list": "IPList",
#     "local-json-web-key-set": "JWKSLocal",
#     "remote-json-web-key-set": "JWKSRemote",
#     "kerberos-environment": "KerberosEnvironment",
#     "mapping": "Mapping",
#     "allowed-network-endpoint": "AllowedNetworkEndpoint",
#     "node": "GatewayClusterNode",
#     "openapi-document": "OpenAPIDocument",
#     "mapping-template": "MappingTemplate",
#     "virtual-host": "VirtualHost",
# }
# KIND2TYPENAME = {
#     "APIPolicyService": "api-policy-service",
#     "BackendGroup": "back-end-group",
#     "TLSCertificate": "ssl-certificate",
#     "GraphQLDocument": "graphql-document",
#     "Host": "host",
#     "ICAPEnvironment": "icap-environment",
#     "IPList": "ip-address-list",
#     "JWKSLocal": "local-json-web-key-set",
#     "JWKSRemote": "remote-json-web-key-set",
#     "KerberosEnvironment": "kerberos-environment",
#     "Mapping": "mapping",
#     "AllowedNetworkEndpoint": "allowed-network-endpoint",
#     "GatewayClusterNode": "node",
#     "OpenAPIDocument": "openapi-document",
#     "MappingTemplate": "mapping-template",
#     "VirtualHost": "virtual-host",
# }
# LISTKEY2TYPENAME = {
#     "apipolicy": "api-policy-service",
#     "anomalyshield_applications": "anomaly-shield-application",
#     "anomalyshield_rules": "anomaly-shield-rule",
#     "backendgroups": "back-end-group",
#     "certs": "ssl-certificate",
#     "graphql": "graphql-document",
#     "hostnames": "host",
#     "icap": "icap-environment",
#     "iplists": "ip-address-list",
#     "jwks": "local-json-web-key-set",
#     "jwks": "remote-json-web-key-set",
#     "kerberos": "kerberos-environment",
#     "mappings": "mapping",
#     "network_endpoints": "allowed-network-endpoint",
#     "nodes": "node",
#     "openapi": "openapi-document",
#     "routes": "route-ipv4-destination",
#     "routes": "route-ipv6-destination",
#     "routes": "route-ipv4-source",
#     "routes": "route-ipv6-source",
#     "templates": "mapping-template",
#     "trafficmatchers": "anomaly-shield-traffic-matcher",
#     "triggers": "anomaly-shield-trigger",
#     "vhosts": "virtual-host",
# }
RELATIONSHIP_ORDER = {
    "api-policy-service": 1000,
    "anomaly-shield-application": 4600,
    "anomaly-shield-rule": 4400,
    "anomaly-shield-traffic-macher": 4200,
    "anomaly-shield-trigger": 4000,
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
    "route-ipv4-destination": 10,
    "route-ipv6-destination": 11,
    "route-ipv4-source": 12,
    "route-ipv6-source": 13,
    "mapping-template": 0,
    "virtual-host": 5200,
}


class Configuration( object ):
    def __init__( self, obj, conn, airscript_config ):
        """
        conn: session.GatewaySession
        """
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
        self.objects = {}
        self._settings = {}
        self._loaded = False
        self._ordered_types = None
        self._log = log.Log( self.__module__ )
        self._reset()
    
    def __repr__( self ):
        return str( { 'id': self.id, 'comment': self.comment, 'type': self.type } )
    
    def runtimeConfigGet( self, path: str, default: str=None ):
        return self._airscript_config.get( path, default )
    
    def clear( self ):
        self._reset()
        self._loaded = False
    
    def getObjects( self, type_name: str ) -> dict:
        if type_name == "api-policy-service":
            obj = self.objects[api_policy.TYPENAME]
        elif type_name == "anomaly-shield-application":
            obj = self.objects[anomalyshield_application.TYPENAME]
        elif type_name == "anomaly-shield-rule":
            obj = self.objects[anomalyshield_rule.TYPENAME]
        elif type_name == "anomaly-shield-traffic-matcher":
            obj = self.objects[anomalyshield_traffic_matcher.TYPENAME]
        elif type_name == "anomaly-shield-trigger":
            obj = self.objects[anomalyshield_trigger.TYPENAME]
        elif type_name == "back-end-group":
            obj = self.objects[backendgroup.TYPENAME]
        elif type_name == "ssl-certificate":
            obj = self.objects[certificate.TYPENAME]
        elif type_name == "graphql-document":
            obj = self.objects[graphql_object.TYPENAME]
        elif type_name == "host":
            obj = self.objects[host.TYPENAME]
        elif type_name == "icap-environment":
            obj = self.objects[icap_object.TYPENAME]
        elif type_name == "ip-address-list":
            obj = self.objects[iplist.TYPENAME]
        elif type_name in ["local-json-web-key-set", "remote-json-web-key-set", "jwks"]:
            obj = self.objects['jwks']
        elif type_name == "kerberos-environment":
            obj = self.objects[kerberos_object.TYPENAME]
        elif type_name == "mapping":
            obj = self.objects[mapping.TYPENAME]
        elif type_name == "allowed-network-endpoint":
            obj = self.objects[network_endpoint.TYPENAME]
        elif type_name == "node":
            obj = self.objects[node.TYPENAME]
        elif type_name == "openapi-document":
            obj = self.objects[openapi_object.TYPENAME]
        elif type_name == "mapping-template":
             obj = self._settings['templates']
        elif type_name in ["route-ipv4-destination", "route-ipv6-destination", "route-ipv4-source", "route-ipv6-source", "routes"]:
            obj = self.objects['routes']
        elif type_name == "virtual-host":
            obj = self.objects[vhost.TYPENAME]
        return obj

    def getListFunc( self, type_name: str ):
        if type_name == "api-policy-service":
            func = self.apipolicy
        elif type_name == "anomaly-shield-application":
            func = self.anomalyshield_applications
        elif type_name == "anomaly-shield-rule":
            func = self.anomalyshield_rules
        elif type_name == "anomaly-shield-traffic-matcher":
            func = self.anomalyshield_trafficmatchers
        elif type_name == "anomaly-shield-trigger":
            func = self.anomalyshield_triggers
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
        elif type_name in ["route-ipv4-destination", "route-ipv6-destination", "route-ipv4-source", "route-ipv6-source"]:
            func = self.routes
        elif type_name == "virtual-host":
            func = self.vhosts
        return func
    
    def load( self ) -> bool:
        """ Retrieve configuration data (vhosts, mappings etc.) from Airlock Gateway using REST API. """
        if self.conn:
            if self._loaded == False:
                if self.id == 'new':
                    r = True
                    # r = self.conn.configuration.create()
                    # if r:
                    #     self.id = 'empty'
                elif self.id == 'empty':
                    r = True
                else:
                    self._log.verbose( "Fetching configuration data from '{}'".format( self.conn.getName() ))
                    r = self.conn.configuration.load( self.id )
                if r == None:
                    self._log.error( "Loading failed: not found" )
                else:
                    self._loaded = True
        else:
            self._log.error( "Loading failed: not connected to any gateway" )
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
            element_type = self._ordered_types[k]
            for cfg_item in self.objects[element_type].values():
                if isinstance( cfg_item, list ):
                    for item in cfg_item:
                        item.sync()
                        self._addElement2ObjectMap( item )
                else:
                    cfg_item.sync()
            # remove deleted objects
            print( f"Removing deleted objects: {element_type}" )
            objs = [k for k,v in self.objects[element_type].items() if not isinstance( v, element.BaseElement ) or v.isDeleted()]
            for key in objs:
                del self.objects[element_type][key]
        # for settings in self._settings.values():
        #     settings.sync()
    
    def elementOrderNr( self, type_name: str ) -> int:
        try:
            return RELATIONSHIP_ORDER[type_name]
        except KeyError:
            return 0
    
    def elementOrderList( self ):
        if not self._ordered_types:
            self._orderTypes()
        return sorted( self._ordered_types )
    
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
                params = {'comment': comment}
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
    
    def download( self, fname: str=None ) -> str|bool:
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
    
    def upload( self, fname ) -> bool:
        """
        Import Airlock Gateway configuration.
        
        'fname' is the filename of a valid Airlock Gateway configuration, in zipped format,
        which you previously downloaded using, e.g.:
        
        session.configurationFindActive().download()
        
        NEVER try to manually create an Airlock Gateway configuration XML file!
        """
        try:
            if self.conn.configuration.upload( self, fname, verify=True ):
                return True
        except exception.AirlockFileNotFoundError:
            self._log.error( f"Upload: file '{fname}' not found" )
            return False
        self._log.error( "Upload: failed" )
        return False
    
    def declarativeImport( self, declarative: dict ) -> bool:
        # format of declarative:
        # { 'source': path_to_config_dir, 'env': env, 'objects': { kind: [{ 'attributes': object, 'connections': {kind: [names]} }] }}
        if self._loaded == False:
            if self.load() == False:
                return False
            self.getAll()
        self.comment = f"Declarative ({declarative['source']}, env {declarative['env']})"
        # create objects without connecting them
        for item_kind, item_lists_per_kind in declarative['objects'].items():
            print( f"{item_kind}:" )
            type_name = lookup.get( element.LOOKUP_KIND2TYPENAME, item_kind )
            for item in item_lists_per_kind:
                if not 'relationships' in item:
                    item['relationships'] = {}
                obj = self.createElement( type_name, data={'attributes': item['attributes']} )
                obj.sync()
                if isinstance( obj, element.ModelElement ):
                    try:
                        obj.declarativeStoreConnections( item['connections'] )
                    except KeyError:
                        pass
                    self._addElement2ObjectMap( obj )
                print( f"  {obj}" )
        # establish connections
        obj: element.ModelElement
        print( "Establish connections" )
        for key, object_map in self.objects.items():
            print( f"{key}" )
            for obj in object_map.values():
                if isinstance( obj, element.ModelElement ):
                    connections = obj.declarativeGetConnections()
                    if connections:
                        for reltype, names in connections.items():
                            for name in names:
                                type_name = lookup.get( lookup.RELTYPE2NAME, reltype )
                                ref = self._findByName( self.getObjects( type_name), name )
                                print( f"- {obj.name} -> {ref.getKind()}:{ref.name}" )
                                obj.addRel( ref, reltype, load=True, backlink=True )
        self.sync()
        #self.save()
        return True
    
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
    
    def apipolicy( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._apipolicy, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def anomalyshield_applications( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._anomalyshield_applications, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def anomalyshield_rules( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._anomalyshield_rules, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def anomalyshield_trafficmatcher( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._trafficmatchers, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def anomalyshield_triggers( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._triggers, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def backendgroups( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._backendgroups, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def certificates( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._certs, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def graphql( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._graphql, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def hostnames( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._hostnames, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def icap( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._icap, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def iplists( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._iplists, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def jwks( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._jwks, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def kerberos( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._kerberos, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def mappings( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._mappings, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def networkendpoints( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._network_endpoints, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def nodes( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._nodes, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def openapi( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._openapi, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def routes( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._routes, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def templates( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._templates, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def vhosts( self, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
        return internal.itemList( self._vhosts, id=id, name=name, ids=ids, filter=filter, sort=sort )

    def settings( self, subset: str=None ) -> dict:
        try:
            return self._settings[subset]
        except KeyError:
            return self._settings
    
    def addElement( self, type_name: str, id: str=None, data: dict=None ):
        obj = self.createElement( type_name, id=id, data=data )
        return self._addElement2ObjectMap( obj )
    
    def createElement( self, type_name: str, id: str=None, data: dict=None ):
        if type_name in ["api-policy-service", "APIPolicyService"]:
            obj = self.addAPIPolicy( id=id, data=data )
        elif type_name == "anomaly-shield-application":
            obj = self.addAnomalyShieldApplication( id=id, data=data )
        elif type_name == "anomaly-shield-rule":
            obj = self.addAnomalyShieldRule( id=id, data=data )
        elif type_name == "anomaly-shield-traffic-matcher":
            obj = self.addAnomalyShieldTrafficMatcher( id=id, data=data )
        elif type_name == "anomaly-shield-trigger":
            obj = self.addAnomalyShieldTrigger( id=id, data=data )
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
        elif type_name == "route-ipv4-destination":
            obj = self.addRoute( id=id, data=data, ipv4=True, source=False )
        elif type_name == "route-ipv6-destination":
            obj = self.addRoute( id=id, data=data, ipv4=False, source=False )
        elif type_name == "route-ipv4-source":
            obj = self.addRoute( id=id, data=data, ipv4=True, source=True )
        elif type_name == "route-ipv6-source":
            obj = self.addRoute( id=id, data=data, ipv4=False, source=True )
        elif type_name in ["mapping-template", "MappingTemplate"]:
            obj = self.addTemplate( id=id, data=data )
        elif type_name in ["virtual-host", "VirtualHost"]:
            obj = self.addVHost( id=id, data=data )
        
        elif type_name == anomalyshield_settings.TYPENAME:
            obj = self.addAnomalyShieldSettings( id=id, data=data )
        elif type_name == default_route_settings.TYPENAME:
            obj = self.addDefaultRouteSettings( id=id, data=data )
        elif type_name == dynamic_ip_blacklist_settings.TYPENAME:
            obj = self.addDynamicIPBlacklistSettings( id=id, data=data )
        elif type_name == license.TYPENAME:
            obj = self.addLicense( id=id, data=data )
        elif type_name == log_settings.TYPENAME:
            obj = self.addLogSettings( id=id, data=data )
        elif type_name == network_services_settings.TYPENAME:
            obj = self.addNetworkServicesSettings( id=id, data=data )
        elif type_name == reporting_settings.TYPENAME:
            obj = self.addReportingSettings( id=id, data=data )
        elif type_name == session_settings.TYPENAME:
            obj = self.addSessionSettings( id=id, data=data )
        
        return obj

    def _settingsFindLoad( self, category: str, data: dict=None ) -> element.BaseElement:
        obj: element.BaseElement
        if self._settings[category]:
            obj = self._settings[category]
            if data:
                data['id'] = obj.id
                obj.loadData( data=data )
                return obj
        else:
            return None

    def addAnomalyShieldSettings( self, id: str=None, data: dict=None ) -> anomalyshield_settings.AnomalyShieldSettings:
        obj: anomalyshield_settings.AnomalyShieldSettings
        obj = self._settingsFindLoad( 'anomalyshield', data )
        if not obj:
            obj = anomalyshield_settings.AnomalyShieldSettings( self, obj=data, id=id )
        return obj

    def addDefaultRouteSettings( self, id: str=None, data: dict=None ) -> default_route_settings.DefaultRouteSettings:
        obj: default_route_settings.DefaultRouteSettings
        obj = self._settingsFindLoad( 'defaultroute', data )
        if not obj:
            obj = default_route_settings.DefaultRouteSettings( self, obj=data, id=id )
        return obj

    def addDynamicIPBlacklistSettings( self, id: str=None, data: dict=None ) -> dynamic_ip_blacklist_settings.DynamicIPBlackListSettings:
        obj: dynamic_ip_blacklist_settings.DynamicIPBlackListSettings
        obj = self._settingsFindLoad( 'dynamicip', data )
        if not obj:
            obj = dynamic_ip_blacklist_settings.DynamicIPBlackListSettings( self, obj=data, id=id )
        return obj

    def addLicense( self, id: str=None, data: dict=None ) -> license.License:
        obj: license.License
        obj = self._settingsFindLoad( 'license', data )
        if not obj:
            obj = license.License( self, obj=data, id=id )
        return obj

    def addLogSettings( self, id: str=None, data: dict=None ) -> log_settings.LogSettings:
        obj: log_settings.LogSettings
        obj = self._settingsFindLoad( 'log', data )
        if not obj:
            obj = log_settings.LogSettings( self, obj=data, id=id )
        return obj

    def addNetworkServicesSettings( self, id: str=None, data: dict=None ) -> network_services_settings.NetworkServicesSettings:
        obj: network_services_settings.NetworkServicesSettings
        obj = self._settingsFindLoad( 'network_services', data )
        if not obj:
            obj = network_services_settings.NetworkServicesSettings( self, obj=data, id=id )
        return obj

    def addReportingSettings( self, id: str=None, data: dict=None ) -> reporting_settings.ReportingSettings:
        obj: reporting_settings.ReportingSettings
        obj = self._settingsFindLoad( 'reporting', data )
        if not obj:
            obj = reporting_settings.ReportingSettings( self, obj=data, id=id )
        return obj

    def addSessionSettings( self, id: str=None, data: dict=None ) -> session_settings.SessionSettings:
        obj: session_settings.SessionSettings
        obj = self._settingsFindLoad( 'session', data )
        if not obj:
            obj = session_settings.SessionSettings( self, obj=data, id=id )
        return obj

    def _loadObject( self, type_name: str, id: str=None, data: dict=None ) -> element.BaseElement|element.ModelElement:
        objects = self.getObjects( type_name )
        try:
            obj = objects[id]
        except KeyError:
            obj = None
        if obj and data:
            obj.loadData( data=data )
        return obj

    def addAnomalyShieldApplication( self, id: str=None, data: dict=None ) -> anomalyshield_application.AnomalyShieldApplication:
        obj = self._loadObject( anomalyshield_application.TYPENAME, id, data )
        if not obj:
            obj = anomalyshield_application.AnomalyShieldApplication( self, obj=data, id=id )
        return obj

    def addAnomalyShieldRule( self, id: str=None, data: dict=None ) -> anomalyshield_rule.AnomalyShieldRule:
        obj = self._loadObject( anomalyshield_rule.TYPENAME, id, data )
        if not obj:
            obj = anomalyshield_rule.AnomalyShieldRule( self, obj=data, id=id )
        return obj

    def addAnomalyShieldTrafficMatcher( self, id: str=None, data: dict=None ) -> anomalyshield_traffic_matcher.AnomalyShieldTrafficMatcher:
        obj = self._loadObject( anomalyshield_traffic_matcher.TYPENAME, id, data )
        if not obj:
            obj = anomalyshield_traffic_matcher.AnomalyShieldTrafficMatcher( self, obj=data, id=id )
        return obj

    def addAnomalyShieldTrigger( self, id: str=None, data: dict=None ) -> anomalyshield_trigger.AnomalyShieldTrigger:
        obj = self._loadObject( anomalyshield_trigger.TYPENAME, id, data )
        if not obj:
            obj = anomalyshield_trigger.AnomalyShieldTrigger( self, obj=data, id=id )
        return obj

    def addAPIPolicy( self, id: str=None, data: dict=None ) -> api_policy.APIPolicy:
        obj = self._loadObject( api_policy.TYPENAME, id, data )
        if not obj:
            obj = api_policy.APIPolicy( self, obj=data, id=id )
        return obj
    
    def addBackendGroup( self, id: str=None, data: dict=None ) -> backendgroup.Backendgroup:
        obj = self._loadObject( backendgroup.TYPENAME, id, data )
        if not obj:
            obj = backendgroup.Backendgroup( self, obj=data, id=id )
        return obj
    
    def addCertificate( self, id: str=None, data: dict=None ) -> certificate.Certificate:
        obj = self._loadObject( certificate.TYPENAME, id, data )
        if not obj:
            obj = certificate.Certificate( self, obj=data, id=id )
        return obj
    
    def addGraphQL( self, id: str=None, data: dict=None ) -> graphql_object.GraphQL:
        obj = self._loadObject( graphql_object.TYPENAME, id, data )
        if not obj:
            obj = graphql_object.GraphQL( self, obj=data, id=id )
        return obj
    
    def addHostName( self, id: str=None, data: dict=None ) -> host.Host:
        obj = self._loadObject( host.TYPENAME, id, data )
        if not obj:
            obj = host.Host( self, obj=data, id=id )
        return obj
    
    def addICAP( self, id: str=None, data: dict=None ) -> icap_object.ICAP:
        obj = self._loadObject( icap_object.TYPENAME, id, data )
        if not obj:
            obj = icap_object.ICAP( self, obj=data, id=id )
        return obj
    
    def addIPList( self, id: str=None, data: dict=None ) -> iplist.IPList:
        obj = self._loadObject( iplist.TYPENAME, id, data )
        if not obj:
            obj = iplist.IPList( self, obj=data, id=id )
        return obj
    
    def addJWKS( self, id: str=None, data: dict=None, remote: bool=True ) -> jwks_object.JWKS:
        obj = self._loadObject( 'jwks', id, data )
        if not obj:
            obj = jwks_object.JWKS( self, obj=data, id=id, remote=remote )
        return obj
    
    def addKerberos( self, id: str=None, data: dict=None ) -> kerberos_object.Kerberos:
        obj = self._loadObject( kerberos_object.TYPENAME, id, data )
        if not obj:
            obj = kerberos_object.Kerberos( self, obj=data, id=id )
        return obj
    
    def addMapping( self, id: str=None, data: dict=None ) -> mapping.Mapping:
        obj = self._loadObject( mapping.TYPENAME, id, data )
        if not obj:
            obj = mapping.Mapping( self, obj=data, id=id )
        return obj
    
    def addNetworkEndpoint( self, id: str=None, data: dict=None ) -> network_endpoint.NetworkEndpoint:
        obj = self._loadObject( network_endpoint.TYPENAME, id, data )
        if not obj:
            obj = network_endpoint.NetworkEndpoint( self, obj=data, id=id )
        return obj
    
    def addNode( self, id: str=None, data: dict=None ) -> node.Node:
        obj = self._loadObject( node.TYPENAME, id, data )
        if not obj:
            if data:
                for found in self._nodes.values():
                    try:
                        if found.name == data['attributes']['hostName'] or (not found.name and (self.conn.getHost() == data['attributes']['hostName'] or self.conn.getNodename() == data['attributes']['hostName'])):
                            obj = found
                            data['id'] = obj.id
                            obj.loadData( data=data )
                            break
                    except KeyError:
                        pass
            if not obj:
                obj = node.Node( self, obj=data, id=id )
        return obj

    def addOpenAPI( self, id: str=None, data: dict=None ) -> openapi_object.OpenAPI:
        obj = self._loadObject( openapi_object.TYPENAME, id, data )
        if not obj:
            obj = openapi_object.OpenAPI( self, obj=data, id=id )
        return obj
    
    def addRoute( self, id: str=None, data: dict=None, ipv4: bool=True, source: bool=True ) -> route.Route:
        obj = self._loadObject( 'routes', id, data )
        if not obj:
            obj = route.Route( self, obj=data, id=id, ipv4=ipv4, source=source )
        return obj
    
    def addTemplate( self, id: str=None, data: dict=None ) -> template.Template:
        obj = self._loadObject( template.TYPENAME, id, data )
        if not obj:
            obj = template.Template( self, obj=data, id=id )
        return obj
    
    def addVHost( self, id: str=None, data: dict=None ) -> vhost.VirtualHost:
        obj = self._loadObject( vhost.TYPENAME, id, data )
        if not obj:
            obj = vhost.VirtualHost( self, obj=data, id=id )
        return obj
    
    def getAPIPolicies( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all APIPolicy documents of this configuration from Airlock Gateway.
        
        This function must be executed before ._apipolicy is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        for entry in self.conn.api_policy.read():
            self._addElement2ObjectMap( self.addAPIPolicy( id=element_helpers.extractId( entry ), data=entry ))
        return self._apipolicy
    
    def getAnomalyShieldApplications( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all Anomaly Shield applications of this configuration from Airlock Gateway.
        
        This function must be executed before ._anomalyshield_applications is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        for entry in self.conn.anomalyshield_application.read():
            self._addElement2ObjectMap( self.addAnomalyShieldApplication( id=element_helpers.extractId( entry ), data=entry ))
        return self._anomalyshield_applications
    
    def getAnomalyShieldRules( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all Anomaly Shield rules of this configuration from Airlock Gateway.
        
        This function must be executed before ._anomalyshield_rules is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        for entry in self.conn.anomalyshield_rule.read():
            self._addElement2ObjectMap( self.addAnomalyShieldRule( id=element_helpers.extractId( entry ), data=entry ))
        return self._anomalyshield_rules
    
    def getAnomalyShieldTrafficMatchers( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all Anomaly Shield traffic matchers of this configuration from Airlock Gateway.
        
        This function must be executed before ._trafficmatchers is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        for entry in self.conn.anomalyshield_trafficmatcher.read():
            self._addElement2ObjectMap( self.addAnomalyShieldTrafficMatcher( id=element_helpers.extractId( entry ), data=entry ))
        return self._trafficmatchers
    
    def getAnomalyShieldTriggers( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all Anomaly Shield triggers of this configuration from Airlock Gateway.
        
        This function must be executed before ._triggers is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        for entry in self.conn.anomalyshield_trigger.read():
            self._addElement2ObjectMap( self.addAnomalyShieldTrigger( id=element_helpers.extractId( entry ), data=entry ))
        return self._triggers
    
    def getBackendGroups( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all backend groups of this configuration from Airlock Gateway.
        
        This function must be executed before ._backendgroups is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        for entry in self.conn.backendgroup.read():
            self._addElement2ObjectMap( self.addBackendGroup( id=element_helpers.extractId( entry ), data=entry ))
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
            self._addElement2ObjectMap( self.addCertificate( id=element_helpers.extractId( entry ), data=entry ))
        return self._certs
    
    def getGraphQL( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all GraphQL documents of this configuration from Airlock Gateway.
        
        This function must be executed before ._graphql is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        for entry in self.conn.graphql.read():
            self._addElement2ObjectMap( self.addGraphQL( id=element_helpers.extractId( entry ), data=entry ))
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
            self._addElement2ObjectMap( self.addHostName( id=element_helpers.extractId( entry ), data=entry ))
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
            self._addElement2ObjectMap( self.addICAP( id=element_helpers.extractId( entry ), data=entry ))
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
            self._addElement2ObjectMap( self.addIPList( id=element_helpers.extractId( entry ), data=entry ))
        return self._iplists
    
    def getJWKS( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all JWKS definitions of this configuration from Airlock Gateway.
        
        This function must be executed before ._jwks is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        for entry in self.conn.jwks_local.read():
            self._addElement2ObjectMap( self.addJWKS( id=element_helpers.extractId( entry ), data=entry, remote=False ))
        for entry in self.conn.jwks_remote.read():
            self._addElement2ObjectMap( self.addJWKS( id=element_helpers.extractId( entry ), data=entry ))
        return self._jwks
    
    def getKerberos( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all Kerberos Environments of this configuration from Airlock Gateway.
        
        This function must be executed before ._kerberos is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        for entry in self.conn.kerberos.read():
            self._addElement2ObjectMap( self.addKerberos( id=element_helpers.extractId( entry ), data=entry ))
        return self._kerberos
    
    def getMappings( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all mappings of this configuration from Airlock Gateway.
        
        This function must be executed before ._mappings is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        for entry in self.conn.mapping.read():
            self._addElement2ObjectMap( self.addMapping( id=element_helpers.extractId( entry ), data=entry ))
        return self._mappings
    
    def getNetworkEndpoints( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all NetworkEndpoint documents of this configuration from Airlock Gateway.
        
        This function must be executed before ._network_endpoints is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        for entry in self.conn.network_endpoint.read():
            self._addElement2ObjectMap( self.addNetworkEndpoint( id=element_helpers.extractId( entry ), data=entry ))
        return self._network_endpoints
    
    def getNodes( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all nodes of this configuration from Airlock Gateway.
        
        This function must be executed before ._nodes is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        for entry in self.conn.node.read():
            self._addElement2ObjectMap( self.addNode( id=element_helpers.extractId( entry ), data=entry ))
        return self._nodes
    
    def getOpenAPI( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all OpenAPI documents of this configuration from Airlock Gateway.
        
        This function must be executed before ._openapi is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        for entry in self.conn.openapi.read():
            self._addElement2ObjectMap( self.addOpenAPI( id=element_helpers.extractId( entry ), data=entry ))
        return self._openapi
    
    def getRoutes( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all route definitions of this configuration from Airlock Gateway.
        
        This function must be executed before ._routes is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        for entry in self.conn.routes_ipv4_destination.read():
            self._addElement2ObjectMap( self.addRoute( id=element_helpers.extractId( entry ), data=entry, ipv4=True, source=False ))
        for entry in self.conn.routes_ipv6_destination.read():
            self._addElement2ObjectMap( self.addRoute( id=element_helpers.extractId( entry ), data=entry, ipv4=False, source=False ))
        for entry in self.conn.routes_ipv4_source.read():
            self._addElement2ObjectMap( self.addRoute( id=element_helpers.extractId( entry ), data=entry, ipv4=True, source=True ))
        for entry in self.conn.routes_ipv6_source.read():
            self._addElement2ObjectMap( self.addRoute( id=element_helpers.extractId( entry ), data=entry, ipv4=False, source=True ))
        return self._routes
    
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
                self._addElement2ObjectMap( self.addTemplate( id=element_helpers.extractId( entry ), data=entry ))
        return self._templates
    
    def getVHosts( self ) -> Union[list[dict], None]:
        """
        Use REST API to fetch all virtual hosts of this configuration from Airlock Gateway.
        
        This function must be executed before ._vhosts is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        for entry in self.conn.vhost.read():
            self._addElement2ObjectMap( self.addVHost( id=element_helpers.extractId( entry ), data=entry ))
        return self.vhosts()
    
    def getSettingsLicense( self ) -> Union[dict, None]:
        """
        Use REST API to fetch licesne from Airlock Gateway.
        
        This function must be executed before .settings['license'] is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        entry = self.conn.license.read()
        self._settings['license'] = license.License( self, obj=entry )
        return self._settings['license']
    
    def getSettingsAnomalyShield( self ) -> Union[dict, None]:
        """
        Use REST API to fetch licesne from Airlock Gateway.
        
        This function must be executed before .settings['anomalyshield'] is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        entry = self.conn.settings_anomalyshield.read()
        self._settings['anomalyshield'] = anomalyshield_settings.AnomalyShieldSettings( self, obj=entry )
        return self._settings['anomalyshield']
    
    def getSettingsLog( self ) -> Union[dict, None]:
        """
        Use REST API to fetch licesne from Airlock Gateway.
        
        This function must be executed before .settings['log'] is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        entry = self.conn.settings_log.read()
        self._settings['log'] = log_settings.LogSettings( self, obj=entry )
        return self._settings['log']
    
    def getSettingsNetworkServices( self ) -> Union[dict, None]:
        """
        Use REST API to fetch licesne from Airlock Gateway.
        
        This function must be executed before .settings['network_services'] is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        entry = self.conn.settings_network_services.read()
        self._settings['network_services'] = network_services_settings.NetworkServicesSettings( self, obj=entry )
        return self._settings['network_services']
    
    def getSettingsReporting( self ) -> Union[dict, None]:
        """
        Use REST API to fetch licesne from Airlock Gateway.
        
        This function must be executed before .settings['reporting'] is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        entry = self.conn.settings_reporting.read()
        self._settings['reporting'] = reporting_settings.ReportingSettings( self, obj=entry )
        return self._settings['reporting']
    
    def getSettingsRoute( self ) -> Union[dict, None]:
        """
        Use REST API to fetch licesne from Airlock Gateway.
        
        This function must be executed before .settings['defaultroute'] is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        entry = self.conn.settings_route.read()
        self._settings['defaultroute'] = default_route_settings.DefaultRouteSettings( self, obj=entry )
        return self._settings['defaultroute']
    
    def getSettingsSession( self ) -> Union[dict, None]:
        """
        Use REST API to fetch licesne from Airlock Gateway.
        
        This function must be executed before .settings['session'] is filled-in and you can modify the settings.
        """
        if self._loaded == False:
            if self.load() == False:
                return None
        entry = self.conn.settings_session.read()
        self._settings['session'] = session_settings.SessionSettings( self, obj=entry )
        return self._settings['session']
    
    def getAll( self ):
        """
        Use REST API to fetch most configuration items from Airlock Gateway
        """
        self._log.verbose( "- Nodes" )
        self.getNodes()
        self._log.verbose( "- API policies" )
        self.getAPIPolicies()
        self._log.verbose( "- Anomaly Shield applications" )
        self.getAnomalyShieldApplications()
        self._log.verbose( "- Anomaly Shield rules" )
        self.getAnomalyShieldRules()
        self._log.verbose( "- Anomaly Shield traffic matchers" )
        self.getAnomalyShieldTrafficMatchers()
        self._log.verbose( "- Anomaly Shield triggers" )
        self.getAnomalyShieldTriggers()
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
        self._log.verbose( "- Routes" )
        self.getRoutes()
        self._log.verbose( "- Virtual hosts" )
        self.getVHosts()
        self._log.verbose( "- Settings: license" )
        self.getSettingsLicense()
        self._log.verbose( "- Settings: anomaly shield" )
        self.getSettingsAnomalyShield()
        self._log.verbose( "- Settings: log" )
        self.getSettingsLog()
        self._log.verbose( "- Settings: network services" )
        self.getSettingsNetworkServices()
        self._log.verbose( "- Settings: reporting" )
        self.getSettingsReporting()
        self._log.verbose( "- Settings: (default) route" )
        self.getSettingsRoute()
        self._log.verbose( "- Settings: session" )
        self.getSettingsSession()
        self._log.verbose( "- Mapping templates" )
        self.getTemplates()
    
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
    
    def listVHosts( self ) -> list[dict[vhost.VirtualHost]]:
        """ Return sorted list of virtual hosts. """
        if self._vhosts == None:
            self.getVHosts()
        return self._listSorted( self._vhosts, key='name' )
        # return sorted( self._vhosts.items(), key=internal.itemgetter_lc_name )
    
    def listMappings( self ) -> list[dict[mapping.Mapping]]:
        """ Return sorted list of mappings. """
        if self._mappings == None:
            self.getMappings()
        return self._listSorted( self._mappings, key='name' )
        # return sorted( self._mappings.items(), key=internal.itemgetter_lc_name )
    
    def listAPIPolicies( self ) -> list[dict[api_policy.APIPolicy]]:
        """ Return sorted list of APIPolicy documents. """
        if self._apipolicy == None:
            self.getAPIPolicies()
        return self._listSorted( self._apipolicy )
    
    def listBackendGroups( self ) -> list[dict[backendgroup.Backendgroup]]:
        """ Return sorted list of backend groups. """
        if self._backendgroups == None:
            self.getBackendGroups()
        return self._listSorted( self._backendgroups )
    
    def listCertificates( self ) -> list[dict[certificate.Certificate]]:
        """ Return sorted list of SSL/TLS certificates. """
        if self._certs == None:
            self.getCertificates()
        return self._listSorted( self._certs )
    
    def listJWKS( self ) -> list[dict[jwks_object.JWKS]]:
        """ Return sorted list of JSON Web Token Key Sets. """
        if self._jwks == None:
            self.getJWKS()
        return self._listSorted( self._jwks )
    
    def listOpenAPI( self ) -> list[dict[openapi_object.OpenAPI]]:
        """ Return sorted list of OpenAPI documents. """
        if self._openapi == None:
            self.getOpenAPI()
        return self._listSorted( self._openapi )
    
    def listGraphQL( self ) -> list[dict[graphql_object.GraphQL]]:
        """ Return sorted list of GraphQL documents. """
        if self._graphql == None:
            self.getGraphQL()
        return self._listSorted( self._graphql )
    
    def listHostNames( self ) -> list[dict[host.Host]]:
        """ Return sorted list of Host documents. """
        if self._hostnames == None:
            self.getHostNames()
        return self._listSorted( self._hostnames )
    
    def listICAP( self ) -> list[dict[icap_object.ICAP]]:
        """ Return sorted list of ICAP environments. """
        if self._icap == None:
            self.getICAP()
        return self._listSorted( self._icap )
    
    def listIPLists( self ) -> list[dict[iplist.IPList]]:
        """ Return sorted list of IP lists. """
        if self._iplists == None:
            self.getIPLists()
        return self._listSorted( self._iplists, key='name' )
        # return sorted( self._iplists.items(), key=internal.itemgetter_lc_1 )
    
    def listNetworkEndpoints( self ) -> list[dict[network_endpoint.NetworkEndpoint]]:
        """ Return sorted list of Network Endpoints. """
        if self._network_endpoints == None:
            self.getNetworkEndpoints()
        return self._listSorted( self._network_endpoints )
    
    def listKerberos( self ) -> list[dict[kerberos_object.Kerberos]]:
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
        
    def findJWKS( self, name, criteria=None ):
        """ Return list of JSON Web Token Key Sets whose name contains 'name'. """
        if self._jwks == None:
            self.getJWKS()
        if criteria == None:
            return [ self._findByName( self._jwks, name ) ]
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
        
    def findOpenAPI( self, name, criteria=None ):
        """ Return list of OpenAPI documents whose name contains 'name'. """
        if self._openapi == None:
            self.getOpenAPI()
        if criteria == None:
            return [ self._findByName( self._openapi, name ) ]
        self._log.warning( "Criteria search not implemented yet" )
        return None
        
    def findVHost( self, name, criteria=None ):
        """ Return list of virtual hosts whose name contains 'name'. """
        if self._vhosts == None:
            self.getVHosts()
        if criteria == None:
            return [ self._findByName( self._vhosts, name ) ]
        self._log.warning( "Criteria search not implemented yet" )
        return None
        
    def deleteNode( self, value ) -> bool:
        """ Delete node from this configuration. """
        if not type( value ) == node.Node:
            self._log.error( "This is not a virtual host but %s" % (type(value),) )
            return False
        if value.delete() == False:
            return False
        del self._nodes[value.id]
        return True
        
    def deleteVHost( self, value ) -> bool:
        """ Delete virtual host from this configuration. """
        if not type( value ) == vhost.VirtualHost:
            self._log.error( "This is not a virtual host but %s" % (type(value),) )
            return False
        if value.delete() == False:
            return False
        del self._vhosts[value.id]
        return True
        
    def deleteMapping( self, value ) -> bool:
        """ Delete mapping from this configuration. """
        if not type( value ) == mapping.Mapping:
            self._log.error( "This is not a mapping but %s" % (type(value),) )
            return False
        if value.delete() == False:
            return False
        del self._mappings[value.id]
        return True
        
    def deleteAPIPolicy( self, value ) -> bool:
        """ Delete APIPolicy document from this configuration. """
        if not type( value ) == api_policy.APIPolicy:
            self._log.error( "This is not a APIPolicy document but %s" % (type(value),) )
            return False
        if value.delete() == False:
            return False
        del self._apipolicy[value.id]
        return True
        
    def deleteBackendGroup( self, value ) -> bool:
        """ Delete backend group from this configuration. """
        if not type( value ) == backendgroup.Backendgroup:
            self._log.error( "This is not a backendgroup but %s" % (type(value),) )
            return False
        if value.delete() == False:
            return False
        del self.values[backendgroup.id]
        return True
        
    def deleteCertificate( self, value ) -> bool:
        """ Delete SSL/TLS certificate from this configuration. """
        if not type( value ) == certificate.Certificate:
            self._log.error( "This is not a certificate but %s" % (type(value),) )
            return False
        if value.delete() == False:
            return False
        del self._certs[value.id]
        return True
        
    def deleteJWKS( self, value ) -> bool:
        """ Delete JSON Web Token Key Set from this configuration. """
        if not type( value ) == jwks_object.JWKS:
            self._log.error( "This is not a JWKS but %s" % (type(value),) )
            return False
        if value.delete() == False:
            return False
        del self._jwks[value.id]
        return True
        
    def deleteOpenAPI( self, value ) -> bool:
        """ Delete OpenAPI document from this configuration. """
        if not type( value ) == openapi_object.OpenAPI:
            self._log.error( "This is not a OpenAPI document but %s" % (type(value),) )
            return False
        if value.delete() == False:
            return False
        del self._openapi[value.id]
        return True
        
    def deleteGraphQL( self, value ) -> bool:
        """ Delete GraphQL document from this configuration. """
        if not type( value ) == graphql_object.GraphQL:
            self._log.error( "This is not a GraphQL document but %s" % (type(value),) )
            return False
        if value.delete() == False:
            return False
        del self._graphql[value.id]
        return True
        
    def deleteHostname( self, value ) -> bool:
        """ Delete Host document from this configuration. """
        if not type( value ) == host.Host:
            self._log.error( "This is not a Host document but %s" % (type(value),) )
            return False
        if value.delete() == False:
            return False
        del self._hostnames[value.id]
        return True
        
    def deleteICAP( self, value ) -> bool:
        """ Delete ICAP environment from this configuration. """
        if not type( value ) == icap_object.ICAP:
            self._log.error( "This is not a ICAP document but %s" % (type(value),) )
            return False
        if value.delete() == False:
            return False
        del self._icap[value.id]
        return True
        
    def deleteIPList( self, value ) -> bool:
        """ Delete IP list from this configuration. """
        if not type( value ) == iplist.IPList:
            self._log.error( "This is not a IP list but %s" % (type(value),) )
            return False
        if value.delete() == False:
            return False
        del self._iplists[value.id]
        return True
    
    def deleteNetworkEndpoint( self, value ) -> bool:
        """ Delete NetworkEndpoint from this configuration. """
        if not type( value ) == network_endpoint.NetworkEndpoints:
            self._log.error( "This is not a NetworkEndpoint but %s" % (type(value),) )
            return False
        if value.delete() == False:
            return False
        del self._network_endpoints[value.id]
        return True
        
    def deleteKerberos( self, value ) -> bool:
        """ Delete KerberosEnvironment from this configuration. """
        if not type( value ) == kerberos_object.Kerberos:
            self._log.error( "This is not a KerberosEnvironment but %s" % (type(value),) )
            return False
        if value.delete() == False:
            return False
        del self._kerberos[value.id]
        return True
        
    def _reset( self ):
        self.objects = {
            api_policy.TYPENAME: {},
            anomalyshield_application.TYPENAME: {},
            anomalyshield_rule.TYPENAME: {},
            anomalyshield_traffic_matcher.TYPENAME: {},
            anomalyshield_trigger.TYPENAME: {},
            backendgroup.TYPENAME: {},
            certificate.TYPENAME: {},
            graphql_object.TYPENAME: {},
            host.TYPENAME: {},
            icap_object.TYPENAME: {},
            iplist.TYPENAME: {},
            'jwks': {},
            kerberos_object.TYPENAME: {},
            mapping.TYPENAME: {},
            node.TYPENAME: {},
            openapi_object.TYPENAME: {},
            network_endpoint.TYPENAME: {},
            'routes': {},
            vhost.TYPENAME: {},
        }
        self._apipolicy = self.objects[api_policy.TYPENAME]
        self._anomalyshield_applications = self.objects[anomalyshield_application.TYPENAME]
        self._anomalyshield_rules = self.objects[anomalyshield_rule.TYPENAME]
        self._trafficmatchers = self.objects[anomalyshield_traffic_matcher.TYPENAME]
        self._triggers = self.objects[anomalyshield_trigger.TYPENAME]
        self._backendgroups = self.objects[backendgroup.TYPENAME]
        self._certs = self.objects[certificate.TYPENAME]
        self._graphql = self.objects[graphql_object.TYPENAME]
        self._hostnames = self.objects[host.TYPENAME]
        self._icap = self.objects[icap_object.TYPENAME]
        self._iplists = self.objects[iplist.TYPENAME]
        self._jwks = self.objects['jwks']
        self._kerberos = self.objects[kerberos_object.TYPENAME]
        self._mappings = self.objects[mapping.TYPENAME]
        self._nodes = self.objects[node.TYPENAME]
        self._openapi = self.objects[openapi_object.TYPENAME]
        self._network_endpoints = self.objects[network_endpoint.TYPENAME]
        self._routes = self.objects['routes']
        self._vhosts = self.objects[vhost.TYPENAME]

        self._settings = {
            'anomalyshield': None,
            'defaultroute': None,
            'dynamicip': None,
            'license': None,
            'log': None,
            'network_services': None,
            'reporting': None,
            'session': None,
            'templates': {},
        }
        self._templates = self._settings['templates']
    
    def _listSorted( self, list_of_dicts: list[dict], key: str='id' ):
        if not type( list_of_dicts ) == dict:
            self._log.error( "Wrong object type: %s" % (type(list_of_dicts),) )
            return []
        if key == 'name':
            func = internal.itemgetter_lc_name
        else:
            func = internal.itemgetter_id
        return sorted( (v for v in list_of_dicts.values() if not v.isDeleted()), key=func )
    
    def _addElement2ObjectMap( self, obj: element.ModelElement ) -> element.ModelElement:
        if obj.id:
            self.getObjects( obj.getTypeName() )[obj.id] = obj
        else:
            try:
                self.getObjects( obj.getTypeName() )[None].append( obj )
            except KeyError:
                self.getObjects( obj.getTypeName() )[None] = [obj]
        return obj
    
    def _findByName( self, objects, name ) -> element.ModelElement:
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
        
