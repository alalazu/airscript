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
Download configuration from named Airlock Gateway and export as declarative

Usage: airscript declarative-export.py [name ...]
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

import atexit
import airscript

from airscript.utils import keepalive, scripts
from airscript import declarative
from pyAirlock.common import output


def declarative_export( run ):
    out = output.Info()

    servers = airscript.gwLoad( None, run )
    nodes = run.cmd.get_scriptparams()
    print( nodes )
    if nodes == None or nodes == []:
        nodes = servers.keys()

    for node in nodes:
        if not node in servers:
            out.nocolor( f"{node}: unknown server" )
        gw = servers[node]
        out.green( f"Establishing session with '{gw.getName()}'" )
        sess = gw.session()
        if sess:
            atexit.register( sess.disconnect )
            out.green( "Fetching active config" )
            c = sess.configurationFindActive()
            c.loadAll()
            _ka = keepalive.KeepAlive()
            _ka.add( sess, interval=30 )
        else:
            out.red( "Failed" )
            continue

        out.green( "Preparing declarative config" )
        d = declarative.DConfig( run )
        out.green( "Merging config to declarative" )
        d.loadRaw()
        d.merge( c, env="demo" )
        out.green( "Exporting" )
        d.saveByMapping( "demo" )
        sess.disconnect()


if __name__ == "__main__" or __name__ == "module.name":
    declarative_export( scripts.init() )
