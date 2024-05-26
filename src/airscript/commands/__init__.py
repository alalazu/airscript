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
Airscript commands
"""

import yaml
from colorama import Fore, Style

from airscript.model import configuration, gateway
from airscript.utils import output
from pyAirlock.common import log


def listConfigs( gw ):
    """
    List all Airlock Gateway configurations.
    
    Sample call: listConfigs( gws['my-waf'] )
    """
    out = log.Log( f"{__name__}.listConfigs" )
    if type( gw ) != gateway.Gateway:
        out.error( f"This is not a Gateway but {type(gw)}" )
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
        out.error( f"This is not a configuration but {type(cfg)}" )
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
        out.error( f"This is not a configuration but {type(cfg)}" )
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
        out.error( f"This is not a configuration but {type(cfg)}" )
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
        out.error( f"This is not a configuration but {type(cfg)}" )
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
        out.error( f"This is not a configuration but {type(cfg)}" )
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
        out.error( f"This is not a configuration but {type(cfg)}" )
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
        out.error( f"This is not a configuration but {type(cfg)}" )
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
        out.error( f"This is not a configuration but {type(cfg)}" )
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
        out.error( f"This is not a configuration but {type(cfg)}" )
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
        out.error( f"This is not a configuration but {type(cfg)}" )
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
        out.error( f"This is not a configuration but {type(cfg)}" )
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
        out.error( f"This is not a configuration but {type(cfg)}" )
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
        out.error( f"This is not a configuration but {type(cfg)}" )
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
        out.error( f"This is not a configuration but {type(cfg)}" )
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
        output.error( f"This is not a configuration but {type(cfg)}" )
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
    
def validator( cfg, selection: list[str], width: int=-1 ):
    if type( cfg ) != configuration.Configuration:
        output.error( f"This is not a configuration but {type(cfg)}" )
        return
    r = cfg.validate()
    sel = [x.casefold() for x in selection]
    lengths = []
    if "error" in sel:
        lst_error = [[entry.attrs['meta']['severity'], entry.attrs['meta']['model']['type'], entry.attrs['meta']['model']['id'], entry.attrs['title'], entry.attrs['detail']] for entry in r['error']]
        lengths = output.getLengthsColumns( lst_error, columns=[7,12,0,0,0] )
        # lengths = output.getLengthsColumns( r['error'], columns=[7,12,0,0] )
    if "warning" in sel:
        lst_warning = [[entry.attrs['meta']['severity'], entry.attrs['meta']['model']['type'], entry.attrs['meta']['model']['id'], entry.attrs['title'], entry.attrs['detail']] for entry in r['warning']]
        lengths = output.getLengthsColumns( lst_warning, columns=[7,12,0,0,0], lengths=lengths )
        # lengths = output.getLengthsColumns( r['warning'], columns=[7,12,0,0], lengths=lengths )
    if "info" in sel:
        lst_info = [[entry.attrs['meta']['severity'], entry.attrs['meta']['model']['type'], entry.attrs['meta']['model']['id'], entry.attrs['title'], entry.attrs['detail']] for entry in r['info']]
        lengths = output.getLengthsColumns( lst_info, columns=[7,12,0,0,0], lengths=lengths )
        # lengths = output.getLengthsColumns( r['info'], columns=[7,12,0,0], lengths=lengths )
    if width > 0:
        fixed = lengths[2] + 8
        total = sum( lengths ) - lengths[2]
        for idx in range( len( lengths )):
            if idx == 2:
                continue
            calc = int( lengths[idx] * (width - fixed) / total + 0.5 )
            if idx == 0 and calc < 3:
                fixed += (3 - calc)
                calc = 3
            lengths[idx] = calc
        if sum( lengths ) + 8 > width:
            lengths[-1] -= (sum( lengths ) + 8 - width)
    if "error" in sel:
        _messages_out( lst_error, lengths, Fore.RED )
    if "warning" in sel:
        _messages_out( lst_warning, lengths, Fore.YELLOW )
    if "info" in sel:
        _messages_out( lst_info, lengths, Fore.GREEN )

def _messages_out( messages: dict, lengths: list[int], color=Fore.RED ):
    for entry in messages:
        output.info( "%s%-*s%s: %s%-*s %s%*s: %-*s - %s%s%s" % (color, lengths[0], entry[0][:lengths[0]], Style.RESET_ALL,
                                                              Fore.CYAN, lengths[1], entry[1][:lengths[1]],
                                                              Fore.WHITE, lengths[2], entry[2][:lengths[2]], lengths[3], entry[3][:lengths[3]],
                                                              color, entry[4][:lengths[4]], Style.RESET_ALL))

def export( cfg, outfile: str ):
    docs = []
    for item in cfg.vhosts().values():
        docs.append( item.declarativeExport() )
    for item in cfg.mappings().values():
        docs.append( item.declarativeExport() )
    for item in cfg.backendgroups().values():
        docs.append( item.declarativeExport() )
    for item in cfg.certificates().values():
        docs.append( item.declarativeExport() )
    for item in cfg.jwks().values():
        docs.append( item.declarativeExport() )
    for item in cfg.openapi().values():
        docs.append( item.declarativeExport() )
    for item in cfg.graphql().values():
        docs.append( item.declarativeExport() )
    for item in cfg.hostnames().values():
        docs.append( item.declarativeExport() )
    for item in cfg.icap().values():
        docs.append( item.declarativeExport() )
    for item in cfg.iplists().values():
        docs.append( item.declarativeExport() )
    for item in cfg.kerberos().values():
        docs.append( item.declarativeExport() )
    for item in cfg.apipolicy().values():
        docs.append( item.declarativeExport() )
    for item in cfg.networkendpoints().values():
        docs.append( item.declarativeExport() )
    with open( outfile, "w" ) as fp:
        yaml.dump_all( docs, stream=fp )

