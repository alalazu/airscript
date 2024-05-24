"""
AirScript: Airlock Gateway Configuration Script Engine

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

"""
Report status on Airlock Gateways:
- name
- group
- nodename
- software version
- last config activation

Usage: airscript status-report.py [name ...]
"""

"""
The following global variables are pre-defined if run within AirScript shell:
- run.cmd
- run.airscript_config
- run.verbose
- run.is_console
- run.log_level
- run.log_file
"""

import sys

import airscript

from airscript.utils import scripts
from pyAirlock.common import exception, log, output


def add( info: dict, lengths: dict, key: str, value: str ):
    info[key] = value
    try:
        l = len( value )
    except TypeError:
        l = 4
    if lengths[key] < l:
        lengths[key] = l

def status_report( run ):
    # get commandline options
    out = output.Info()
    log.set_level( 15 )

    servers = airscript.gwLoad( None, run )
    nodes = run.cmd.get_scriptparams()
    if nodes == None or nodes == []:
        nodes = servers.keys()

    lengths = {'name': 0, 'group': 0, 'nodename': 0, 'version': 0, 'activation': 0 }
    infos = {'title': {}}
    add( infos['title'], lengths, 'name', "Name" )
    add( infos['title'], lengths, 'group', "Group" )
    add( infos['title'], lengths, 'nodename', "Nodename" )
    add( infos['title'], lengths, 'version', "Version" )
    add( infos['title'], lengths, 'activation', "Activation time" )
    for node in nodes:
        if not node in servers:
            out.nocolor( f"{node}: unknown server" )
        gw = servers[node]
        out.grey( f"{chr( 27 )}[KConnecting to '{node}'", end=chr( 13 ))
        if gw.connect():
            try:
                cfg = gw.configurationFindActive()
            except exception.AirlockCommunicationError:
                cfg = None
        else:
            cfg = None
        infos[node] = {}
        add( infos[node], lengths, 'name', node )
        add( infos[node], lengths, 'group', gw.group )
        if cfg:
            add( infos[node], lengths, 'nodename', gw.nodename )
            add( infos[node], lengths, 'version', gw.version )
            add( infos[node], lengths, 'activation', cfg.createdAt )
            gw.disconnect()
        else:
            add( infos[node], lengths, 'nodename', "n/a" )
            add( infos[node], lengths, 'version', "n/a" )
            add( infos[node], lengths, 'activation', "<unreachable>" )

    for node, info in infos.items():
        if node == 'title':
            out.green( "{:<{w1}} {:<{w2}} {:<{w3}} {:<{w4}} {:<{w5}}".format( info['name'], info['group'], info['nodename'], info['version'], info['activation'],
                                                                            w1=lengths['name'], w2=lengths['group'], w3=lengths['nodename'], w4=lengths['version'], w5=lengths['activation'] ))
        elif info['nodename'] != 'n/a':
            out.yellow( "{:<{w1}} {:<{w2}} {:<{w3}} {:<{w4}} {:<{w5}}".format( info['name'], info['group'], info['nodename'], info['version'], info['activation'],
                                                                            w1=lengths['name'], w2=lengths['group'], w3=lengths['nodename'], w4=lengths['version'], w5=lengths['activation'] ))
        else:
            out.grey( "{:<{w1}} {:<{w2}} {:<{w3}} {:<{w4}} {:<{w5}}".format( info['name'], info['group'], info['nodename'], info['version'], info['activation'],
                                                                            w1=lengths['name'], w2=lengths['group'], w3=lengths['nodename'], w4=lengths['version'], w5=lengths['activation'] ))

if __name__ == "__main__" or __name__ == "module.name":
    status_report( scripts.init() )
