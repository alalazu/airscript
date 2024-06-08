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

from pprint import pprint
from typing import Any

import airscript.commands
from airscript import gateway, session
from airscript.model import configuration
from airscript.utils import runinfo
from pyAirlock.common import config, exception, log, utils


# global variables
mgmt_server = None


"""
User helper functions
"""
def gwLoad( fname: str=None, run_info: runinfo.RunInfo=None ):
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
                gws[name].mgmt = True
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

def pp( obj: Any ):
    pprint( obj, sort_dicts=False )

def ppsort( obj: Any ):
    pprint( obj )

def listConfigs( gw: gateway.Gateway ):
    airscript.commands.listConfigs( gw )

def listVHosts( cfg: configuration.Configuration, paths=None ):
    airscript.commands.listVHosts( cfg, paths=paths )

def listMappings( cfg: configuration.Configuration, paths=None ):
    airscript.commands.listMappings( cfg, paths=paths )

def listBackendgroups( cfg: configuration.Configuration, paths=None ):
    airscript.commands.listBackendgroups( cfg, paths=paths )

def listCertificates( cfg: configuration.Configuration, paths=None ):
    airscript.commands.listCertificates( cfg, paths=paths )

def listOpenAPI( cfg: configuration.Configuration, paths=None ):
    airscript.commands.listOpenAPI( cfg, paths=paths )

def listGraphQL( cfg: configuration.Configuration, paths=None ):
    airscript.commands.listGraphQL( cfg, paths=paths )

def listJWKS( cfg: configuration.Configuration, paths=None ):
    airscript.commands.listJWKS( cfg, paths=paths )

def listKerberos( cfg: configuration.Configuration, paths=None ):
    airscript.commands.listKerberos( cfg, paths=paths )

def listNetworkEndpoints( cfg: configuration.Configuration, paths=None ):
    airscript.commands.listNetworkEndpoints( cfg, paths=paths )

def listNodes( cfg: configuration.Configuration, paths=None ):
    airscript.commands.listNodes( cfg, paths=paths )

def listAPIPolicies( cfg: configuration.Configuration, paths=None ):
    airscript.commands.listAPIPolicies( cfg, paths=paths )

def listHostNames( cfg: configuration.Configuration, paths=None ):
    airscript.commands.listHostNames( cfg, paths=paths )

def listIPLists( cfg: configuration.Configuration, paths=None ):
    airscript.commands.listIPLists( cfg, paths=paths )

def listTemplates( cfg: configuration.Configuration, paths=None ):
    airscript.commands.listTemplates( cfg, paths=paths )

def listCfgInfo( cfg: configuration.Configuration, order="NVMBCHOGJIAKT" ):
    airscript.commands.listCfgInfo( cfg, order=order )

def validator( cfg: configuration.Configuration, selection: list[str]=['error','warning','info'], width: int=-1 ):
    airscript.commands.validator( cfg, selection, width=width )

def export( cfg: configuration.Configuration, fname: str ):
    airscript.commands.export( cfg, fname )
