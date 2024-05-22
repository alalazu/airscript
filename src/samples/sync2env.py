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
sync2env <label>
	load source config
	delete all mappings without label (disconnect from other elements, too)
	for each other config element category, in reverse "connection" order
		delete (now) unconnected config elements
	# this should be target config, now
	
	for each target server
		load config
		for each config element category, in "connection" order
			for each config element in source config
				apply config element to target config, creating if it does not exist
				connect to other (already existing) elements
			for each config element in target config
				delete if not updated
		sync config
		activate

Usage: airscript sync2env.py <env>
"""

"""
The following global variables are pre-defined:
- run.cmd
- run.airscript_config
- run.verbose
- run.is_console
- run.log_level
- run.log_file
"""

import airscript
import atexit
from pprint import pprint as pp
from pyAirlock.common import log, output
from airscript.utils import keepalive

funcNames = {
	"apipolicy": "apipolicy",
	"backendgroup": "backendgroups",
	"cert": "certificates",
	"graphql": "graphql",
	"host": "hosts",
	"icap": "icap",
	"iplist": "iplists",
	"jwks": "jwks",
	"kerberos": "kerberos",
	"mapping": "mappings",
	"network_endpoint": "networkendpoints",
	"node": "nodes",
	"openapi": "openapi",
	"template": "templates",
	"vhost": "vhosts"
}

out = output.Info()

out.yellow( "Loading gateway definitions" )
gws=airscript.gwLoad( run_info=run )

out.yellow( "Load source config" )
gw=gws['vm']
#gw=gws['cuenca']
out.green( f"Connecting to '{gw.getName()}'" )
gw.connect()
atexit.register( gw.disconnect )
c=gw.configurationFindActive()
out.green( "Fetching active config" )
c.loadAll()
_ka = keepalive.KeepAlive()
_ka.add( gw, interval=30 )

target_env = run.cmd.get_scriptparams()[0]
out.yellow( f"Prepare config for environment {target_env}" )
out.green( f"Delete all mappings not labeled with {target_env}" )
for _,m in c.mappings().items():
  if not "PROD".casefold() in map(str.casefold, m.attrs['labels']):
    print( f"- {m.id}: {m.name}" )
    m.delete()

out.green( "Delete unconnected config elements" )
for elementName in c.elementOrderList():
  out.green( f"- {elementName}" )
  funcPointer = getattr( c, funcNames[elementName], None )
  for _,element in funcPointer().items():
    if element.rels == {}:
      print( f"{element.id}: {element.rels}" )
