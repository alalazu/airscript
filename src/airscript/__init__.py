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

"""
Airlock Gateway Configuration Script Engine.

AirScript is your scriptable Python interface to the Airlock Gateway
configuration REST API, providing access to configuration objects,
virtual hosts, mappings etc.

AirScript can be used interactively using its console which allows
you to easily interact with the REST API. it can also be used for
more complex operations for which a script has previously been created,
e.g. migrating an applications configuration from a test to a production
environment.

To start with it, you must provide information about your Airlock Gateways in
~/.airscript/config.yaml (other location possible)
    servers:
        - name: server-name-1
            hostname: 10.0.0.1
            apikey: ey...
            tls:
                verify: false
                ca-cart: |-
                    -----BEGIN CERTIFICATE-----
                    MIIGMTCCBBmgAwIBAgIBATANBgkqhkiG9w0BAQsFADCBpjELMAkGA1UEBhMCQ0gx
                    CzAJBgNVBAgTAlpIMREwDwYDVQQHEwhXZXR0c3dpbDEOMAwGA1UEChMFWnVza2Ex
                    FzAVBgNVBAsTDkluZnJhc3RydWN0dXJlMSkwJwYDVQQDEyBadXNrYSBDZXJ0aWZp
                    Y2F0ZSBBdXRob3JpdHkgMjAxNTEjMCEGCSqGSIb3DQEJARYUY2FAenVza2EubWFy
                    bWlyYS5jb20wIBcNMTUwNjE5MDgxODAwWhgPMjA1MDA2MTkwODE4MDBaMIGmMQsw
                    CQYDVQQGEwJDSDELMAkGA1UECBMCWkgxETAPBgNVBAcTCFdldHRzd2lsMQ4wDAYD
                    VQQKEwVadXNrYTEXMBUGA1UECxMOSW5mcmFzdHJ1Y3R1cmUxKTAnBgNVBAMTIFp1
                    c2thIENlcnRpZmljYXRlIEF1dGhvcml0eSAyMDE1MSMwIQYJKoZIhvcNAQkBFhRj
                    ...
                    /P4QVgI=
                    -----END CERTIFICATE-----
                ca-file: path-to-ca-file.pem

Explanation
    name: the identifier of your Gateway, e.g. the hostname
    hostname: <fqdn of Gateway Config Center, can also be IPv4>
    apikey: <Gateway API key used to authenticate, copy from Gateway:
        System Setup - System Admin - API Keys - API Key
    tls.ca-cert: <PEM-formatted signing certificate, must include chain>
    tls.ca-file: <pathname of server's signing certificate, must include chain>
    tls.verify: <'false' to disable certificate checking - never use in production>

As your first step in the console, you should probably call (assuming
you have a Gateway definition file ~/airscript/config.yaml:

    gws = airscript.gwLoad()
or
    gws = airscript.gwLoad( "src/config.yaml" )

if you don't.

This will populate a 'gws' array where you can access your Airlock Gateway
definitions, e.g. as 'gws["my-waf"]'.

To retrieve Airlock Gateway configuration information, run:

    cfg = gws['my-waf'].configurationFindActive()
    listVHosts( cfg )
    listMappings( cfg )
    listBackendgroups( cfg )

Please refer to the Airlock Gateway REST API documentation to understand how
it works, e.g. the requirements for loading and activating a configuration.
"""

import os

from colorama import Fore, Style

from airscript.model import configuration, gateway
from airscript.utils import output, runinfo
from pyAirlock.common import config, exception, log, utils


# global variables
mgmt_server = None


"""
User helper functions
"""
def gwLoad( fname: str=None, run_info=None ):
    """
    Load Airlock Gateway definitions and return array indexed by Gateway names.
    
    If loaded_config is specified, it must be of type pyAirlock.common.config.Config and contain a key 'servers'.
    Alternatively, you can specify the filename of the config file to load.

    This is usually the first function you call. As you need to do that
    for each and every AirScript invocation, you can automate it
    through ~/.airscript.rc
    
    Please refer to samples data or the module description above.
    """
    global mgmt_server

    out = log.Log( f"{__name__}.gwLoad", run_info )
    if run_info:
        airscript_config = run_info.config
    else:
        if fname:
            config_file = os.path.expanduser( fname )
        else:
            config_file = os.path.expanduser( "~/.airscript/config.yaml" )
        airscript_config = config.Config( config_file )
        try:
            airscript_config.load()
        except exception.AirlockFileNotFoundError():
            out.critical( f"Config file {config_file} does not exist" )
            return None
        except exception.AirlockConfigError():
            out.critical( f"Config file {config_file} is invalid" )
            return None
        run_info = runinfo.RunInfo( None, airscript_config, False, False )
    
    # get common tls settings
    common_verify = airscript_config.get( 'airscript.tls.verify' )
    common_ca_cert = airscript_config.get( 'airscript.tls.ca_cert' )
    common_ca_file = airscript_config.get( 'airscript.tls.ca_file' )

    # instantiate Gateways
    gws = {}
    try:
        groups = airscript_config.get( 'servers' )
    except TypeError as e:
        out.critical( f"Server list not found in config file {config_file} - no Gateways defined" )
        return gws
    idx = 0
    for group in groups:
        for server in groups[group]:
            idx += 1
            name = airscript_config.get( 'name', base=server )
            hostname = airscript_config.get( 'hostname', base=server )
            if hostname == None:
                hostname = utils.resolveDNS( name )
            if hostname == None:
                out.error( f"Server #{idx}: name or ip must be defined" )
                continue
            if name == None:
                name = hostname
            apikey = airscript_config.get( 'apikey', base=server )
            if apikey == None:
                out.error( f"Server {name}: apikey must be defined" )
                continue
            peer = airscript_config.get( 'peer', base=server )
            gws[name] = gateway.Gateway( name, hostname, apikey, run_info, peer=peer, group=group )
            if airscript_config.get( 'mgmt', base=server ):
                mgmt_server = gws[name]
            verify = common_verify
            ca_file = common_ca_file
            cert = common_ca_cert
            if 'tls' in server:
                verify = airscript_config.get( 'tls.verify', default=common_verify, base=server )
                if verify == None or verify == True:
                    cert = airscript_config.get( 'tls.ca-cert', base=server )
                    if cert == None:
                        ca_file = airscript_config.get( 'tls.ca-file', base=server )
                    if cert == None and ca_file == None:
                        cert = common_ca_cert
                        ca_file = common_ca_file
            if verify or verify == None:
                if ca_file != None:
                    gws[name].setCertificate( certfile=ca_file )
                if cert != None:
                    gws[name].setCertificate( pem=cert )
                gws[name].setTLSVerify( True )
            else:
                gws[name].setTLSVerify( False )
    
    title_printed = False
    for gw in gws:
        if not title_printed:
            out.verbose( "Loaded Gateway definitions for:" )
            title_printed = True
        out.verbose( f"  gws['{gw}'] @ {gws[gw].getHost()}" )
    return gws


def listConfigs( gw ):
    """
    List all Airlock Gateway configurations.
    
    Sample call: listConfigs( gws['my-waf'] )
    """
    out = log.Log( f"{__name__}.listConfigs" )
    if type( gw ) != gateway.Gateway:
        out.error( "This is not a Gateway but %s" % (type(gw),) )
        return 
    lst = gw.listConfigurations()
    len_id = 0
    len_comment = 0
    for entry in lst:
        len_id = max( len_id, len( str( entry[0] )))
        len_comment = max( len_comment, len( entry[1].comment ))
    len_comment = min( len_comment, 50 )
    for entry in lst:
        out.info( "%s%*s%s: %s%-*.*s %s%s%s" % (Fore.CYAN, len_id, entry[0], Style.RESET_ALL,
                                                   Fore.GREEN, len_comment, len_comment, entry[1].comment,
                                                   Fore.WHITE, entry[1].type, Style.RESET_ALL) )


def listVHosts( cfg, paths=None ):
    """
    List all virtual hosts defined by an Airlock Gateway configuration.
    
    'paths' is a list of attributes displayed instead of id/name. Specified in the form 'locking.application.response.compressionAllowed'
    """
    out = log.Log( f"{__name__}.listVHosts" )
    if type( cfg ) != configuration.Configuration:
        out.error( "This is not a configuration but %s" % (type(cfg),) )
        return
    lst = cfg.vhosts( sort='name' )
    if paths == None:
        col_len = output.getLengthsIdName( lst )
        for entry in lst:
            out.info( "%s%*s%s: %s%-*.*s %s(%s)%s" % (Fore.CYAN, col_len['id'], entry[0], Style.RESET_ALL,
                                                      Fore.GREEN, col_len['name'], col_len['name'], entry[1].name,
                                                      Fore.WHITE, entry[1].attrs['networkInterface']['ipV4Address'], Style.RESET_ALL) )
    else:
        output.listAttributes( lst, cfg.vhosts, paths )

def listMappings( cfg, paths=None ):
    """
    List all mappings defined by an Airlock Gateway configuration.
    
    'paths' is a list of attributes displayed instead of id/name. Specified in the form 'locking.application.response.compressionAllowed'
    """
    out = log.Log( f"{__name__}.listMappings" )
    if type( cfg ) != configuration.Configuration:
        out.error( "This is not a configuration but %s" % (type(cfg),) )
        return
    lst = cfg.listMappings()
    if paths == None:
        col_len = output.getLengthsIdName( lst )
        col_len['name'] = min( col_len['name'], 30 )
        for entry in lst:
            out.info( "%s%*s%s: %s%-*.*s %s%-*.*s %s%s%s" %
                       (Fore.CYAN, col_len['id'], entry[0], Style.RESET_ALL,
                        Fore.GREEN, col_len['name'], col_len['name'], entry[1].name,
                        Fore.YELLOW, 20, 20, entry[1].attrs['entryPath']['value'],
                        Fore.WHITE, entry[1].attrs['labels'], Style.RESET_ALL) )
    else:
        output.listAttributes( lst, cfg.mappings, paths )

def listBackendgroups( cfg, paths=None ):
    """
    List all virtual hosts defined by an Airlock Gateway configuration.
    
    'paths' is a list of attributes displayed instead of id/name. Specified in the form 'locking.application.response.compressionAllowed'
    
    Sample call sequence:
    cfg = gws['my-waf'].configurationFindActive()
    listBackendgroups( cfg )
    """
    out = log.Log( f"{__name__}.listBackendgroups" )
    if type( cfg ) != configuration.Configuration:
        out.error( "This is not a configuration but %s" % (type(cfg),) )
        return
    if paths == None:
        output.listIdName( cfg.listBackendGroups() )
    else:
        output.listAttributes( cfg.listBackendGroups(), cfg.backendgroups, paths )

def listCertificates( cfg, paths=None ):
    """
    List all SSL/TLS certificates defined by an Airlock Gateway configuration.
    
    'paths' is a list of attributes displayed instead of id/name. Specified in the form 'locking.application.response.compressionAllowed'
    """
    out = log.Log( f"{__name__}.listCertificates" )
    if type( cfg ) != configuration.Configuration:
        out.error( "This is not a configuration but %s" % (type(cfg),) )
        return
    if paths == None:
        output.listIdName( cfg.listCertificates() )
    else:
        output.listAttributes( cfg.listCertificates(), cfg.certs, paths )

def listOpenAPI( cfg, paths=None ):
    """
    List all OpenAPI specification documents defined by an Airlock Gateway configuration.
    
    'paths' is a list of attributes displayed instead of id/name. Specified in the form 'locking.application.response.compressionAllowed'
    """
    out = log.Log( f"{__name__}.listOpenAPI" )
    if type( cfg ) != configuration.Configuration:
        out.error( "This is not a configuration but %s" % (type(cfg),) )
        return
    if paths == None:
        output.listIdName( cfg.listOpenAPI() )
    else:
        output.listAttributes( cfg.listOpenAPI(), cfg.openapi, paths )

def listGraphQL( cfg, paths=None ):
    """
    List all GraphQL specification documents defined by an Airlock Gateway configuration.
    
    'paths' is a list of attributes displayed instead of id/name. Specified in the form 'locking.application.response.compressionAllowed'
    """
    out = log.Log( f"{__name__}.listGraphQL" )
    if type( cfg ) != configuration.Configuration:
        out.error( "This is not a configuration but %s" % (type(cfg),) )
        return
    if paths == None:
        output.listIdName( cfg.listGraphQL() )
    else:
        output.listAttributes( cfg.listGraphQL(), cfg.graphql, paths )

def listJWKS( cfg, paths=None ):
    """
    List all JWKS providers defined by an Airlock Gateway configuration.
    
    'paths' is a list of attributes displayed instead of id/name. Specified in the form 'locking.application.response.compressionAllowed'
    """
    out = log.Log( f"{__name__}.listJWKS" )
    if type( cfg ) != configuration.Configuration:
        out.error( "This is not a configuration but %s" % (type(cfg),) )
        return
    if paths == None:
        output.listIdName( cfg.listJWKS() )
    else:
        output.listAttributes( cfg.listJWKS(), cfg.jwks, paths )

def listKerberos( cfg, paths=None ):
    """
    List all Kerberos environments defined by an Airlock Gateway configuration.
    
    'paths' is a list of attributes displayed instead of id/name. Specified in the form 'locking.application.response.compressionAllowed'
    """
    out = log.Log( f"{__name__}.listKerberos" )
    if type( cfg ) != configuration.Configuration:
        out.error( "This is not a configuration but %s" % (type(cfg),) )
        return
    if paths == None:
        output.listIdName( cfg.listKerberos() )
    else:
        output.listAttributes( cfg.listKerberos(), cfg.kerberos, paths )

def listNetworkEndpoints( cfg, paths=None ):
    """
    List all network endpoints defined by an Airlock Gateway configuration.
    
    'paths' is a list of attributes displayed instead of id/name. Specified in the form 'locking.application.response.compressionAllowed'
    """
    out = log.Log( f"{__name__}.listNetworkEndpoints" )
    if type( cfg ) != configuration.Configuration:
        out.error( "This is not a configuration but %s" % (type(cfg),) )
        return
    if paths == None:
        output.listIdName( cfg.listNetworkEndpoints() )
    else:
        output.listAttributes( cfg.listNetworkEndpoints(), cfg.network_endpoints, paths )

def listNodes( cfg, paths=None ):
    """
    List all nodes defined by an Airlock Gateway configuration.
    
    'paths' is a list of attributes displayed instead of id/name. Specified in the form 'locking.application.response.compressionAllowed'
    """
    out = log.Log( f"{__name__}.listNodes" )
    if type( cfg ) != configuration.Configuration:
        out.error( "This is not a configuration but %s" % (type(cfg),) )
        return
    if paths == None:
        output.listIdName( cfg.listNodes() )
    else:
        output.listAttributes( cfg.listNodes(), cfg.nodes, paths )

def listAPIPolicies( cfg, paths=None ):
    """
    List all API policies defined by an Airlock Gateway configuration.
    
    'paths' is a list of attributes displayed instead of id/name. Specified in the form 'locking.application.response.compressionAllowed'
    """
    out = log.Log( f"{__name__}.listAPIPolicies" )
    if type( cfg ) != configuration.Configuration:
        out.error( "This is not a configuration but %s" % (type(cfg),) )
        return
    if paths == None:
        output.listIdName( cfg.listAPIPolicies() )
    else:
        output.listAttributes( cfg.listAPIPolicies(), cfg.apipolicy, paths )

def listHostNames( cfg, paths=None ):
    """
    List all hostnames defined by an Airlock Gateway configuration.
    
    'paths' is a list of attributes displayed instead of id/name. Specified in the form 'locking.application.response.compressionAllowed'
    """
    out = log.Log( f"{__name__}.listHostnames" )
    if type( cfg ) != configuration.Configuration:
        out.error( "This is not a configuration but %s" % (type(cfg),) )
        return
    if paths == None:
        output.listIdName( cfg.listHostNames() )
    else:
        output.listAttributes( cfg.listHostNames(), cfg.hostnames, paths )

def listIPLists( cfg, paths=None ):
    """
    List all IP lists defined by an Airlock Gateway configuration.
    
    'paths' is a list of attributes displayed instead of id/name. Specified in the form 'locking.application.response.compressionAllowed'
    """
    out = log.Log( f"{__name__}.listIPLists" )
    if type( cfg ) != configuration.Configuration:
        out.error( "This is not a configuration but %s" % (type(cfg),) )
        return
    lst = cfg.listIPLists()
    if paths == None:
        col_len = output.getLengthsIdName( lst )
        col_len['name'] = min( col_len['name'], 30 )
        for entry in lst:
            out.info( "%s%*s%s: %s%-*.*s %s%s%s" % (Fore.CYAN, col_len['id'], entry[0], Style.RESET_ALL,
                                                    Fore.GREEN, col_len['name'], col_len['name'], entry[1].name,
                                                    Fore.WHITE, entry[1].attrs['ips'], Style.RESET_ALL) )
    else:
        output.listAttributes( lst, cfg.iplists, paths )

def listTemplates( cfg, paths=None ):
    """
    List all mapping templates defined by an Airlock Gateway configuration.
    
    'paths' is a list of attributes displayed instead of id/name. Specified in the form 'locking.application.response.compressionAllowed'
    """
    out = log.Log( f"{__name__}.listTemplates" )
    if type( cfg ) != configuration.Configuration:
        out.error( "This is not a configuration but %s" % (type(cfg),) )
        return
    lst = cfg.listTemplates()
    if paths == None:
        len_id = 0
        len_name = 0
        for entry in lst:
            len_id = max( len_id, len( str( entry[1].id )))
            len_name = max( len_name, len( entry[0] ))
        len_name = min( len_name, 30 )
        for entry in lst:
            out.info( "%s%-*s%s: %s%*s%s" % (Fore.CYAN, len_name, entry[0], Style.RESET_ALL,
                                             Fore.GREEN, len_id, entry[1].id, Style.RESET_ALL) )
    else:
        output.listAttributes( lst, cfg.templates, paths, id_left=True )

def listCfgInfo( cfg, order="NVMBCHOGJIAKT" ):
    """
    List all configuration information.
    
    'order' specifies order of information. Default is 'NVMBCHOGJIAKT',
    listing nodes, virtual hosts, mappings, backend groups, certificates,
    hostnames, open api documents, graphql documents, JWKS providers,
    IP lists, API policies, Kerberos environments, and templates, in this order.
    """
    if type( cfg ) != configuration.Configuration:
        output.error( "This is not a configuration but %s" % (type(cfg),) )
        return
    printed = False
    for t in order:
        if printed:
            print()
        if t == 'N':
            output.label( "Nodes" )
            listNodes( cfg )
        elif t == 'V':
            output.label( "Virtual Hosts" )
            listVHosts( cfg )
        elif t == 'M':
            output.label( "Mappings" )
            listMappings( cfg )
        elif t == 'B':
            output.label( "Backend Groups" )
            listBackendgroups( cfg )
        elif t == 'C':
            output.label( "SSL/TLS certificates" )
            listCertificates( cfg )
        elif t == 'H':
            output.label( "Hostnames" )
            listHostNames( cfg )
        elif t == 'A':
            output.label( "API policies" )
            listAPIPolicies( cfg )
        elif t == 'O':
            output.label( "OpenAPI specification documents" )
            listOpenAPI( cfg )
        elif t == 'G':
            output.label( "GraphQL specification documents" )
            listGraphQL( cfg )
        elif t == 'J':
            output.label( "JWKS providers" )
            listJWKS( cfg )
        elif t == 'I':
            output.label( "IP lists" )
            listIPLists( cfg )
        elif t == 'T':
            output.label( "Templates" )
            listTemplates( cfg )
        elif t == 'K':
            output.label( "Kerberos environments" )
            listKerberos( cfg )
        printed = True
    
