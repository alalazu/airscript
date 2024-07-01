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
Toggle maintenance page for mapping

Usage: airscript maintenance.py <gateway> <mapping>

	load current config
	find mapping by name
	toggle maintenance page
	activate
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

import airscript
import atexit
import sys

from pprint import pprint as pp
from airscript.utils import scripts
from pyAirlock.common import log, output


out = output.Info()

def die( msg: str ):
    out.red( msg )
    sys.exit( 1 )

def warn( msg: str ):
	out.yellow( msg )

def maintenance( run ):
	out = output.Info()
	log.set_level( 15 )

	args = run.cmd.get_args()
	if not args or args == [] or len( args ) < 2:
		die( "Usage: maintenance <gateway> <mapping_name> [...]" )
	gateway_name = args[0]
	mapping_names = args[1:]

	out.yellow( "Loading gateway definitions" )
	gws = airscript.gwLoad( run_info=run )
	if gateway_name not in gws:
		die( f"Unknown gateway '{gateway_name}'" )
	
	session = gws[gateway_name].session()
	if not session:
		die( f"Unable to connect to '{gateway_name}'" )
	cfg = session.configurationFindActive()
	cfg.loadAll()

	for name in mapping_names:
		m = cfg.mappings( name=name )
		if not m:
			warn( f"Mapping '{name}' not found" )
		
	mgmt_server = None
	for name, server in gws.items():
		if server.mgmt:
			mgmt_server = server
			break
	if not mgmt_server:
		die( "No management server defined - set property 'mgmt: true' in config" )

	src_cfg = load_source( mgmt_server )
	if not src_cfg:
		die( f"Unable to read configuration from management server '{mgmt_server.getName()}'" )
	del_mappings( src_cfg, target_env = target_env, verbose=verbose )
	del_others( src_cfg, verbose=verbose )

	out.yellow( "Updating target servers" )
	count = 0
	for name,server in gws.items():
		if server.group.casefold() != target_env.casefold():
			continue
		if server == mgmt_server:
			pass
			# continue
		count += 1
		out.green( f"- {name}" )
		session = server.session()
		target_cfg = session.configurationFindActive()
		target_cfg.loadAll()
		for elementName in src_cfg.elementOrderList():
			if elementName in ["mapping-template", "node"]:
				continue
			source_list = src_cfg.getObjects( elementName )
			trgPointer = target_cfg.getListFunc( elementName )
			if verbose:
				out.grey( f"{elementName}" )
			for _,src_element in source_list.items():
				if src_element.isDeleted():
					continue
				trg_dict = trgPointer( id=src_element.id )
				if trg_dict == {}:
					# add config element
					if verbose:
						out.grey( f"- new: {trg_element.name}" )
					pass
				else:
					# update config element
					trg_element = list( trg_dict.values() )[0]
					trg_element.copyAttributes( src_element )
					if verbose:
						out.grey( f"- upd: {trg_element.name}" )
		if verbose:
			out.grey( f"sync'ing to {name}" )
		target_cfg.sync()
		target_cfg.save( comment=f"Env sync'ed for {target_env} from {mgmt_server.getName()}" )
		# if verbose:
		# 	out.grey( "validating" )
		# target_cfg.validate()
		# if verbose:
		# 	out.grey( "activating" )
		# target_cfg.activate( comment=f"Env sync'ed for {target_env} from {mgmt_server.getName()}" )
		session.disconnect()
	if count > 0:
		out.yellow( f"Completed, maintenance toggled" )
	else:
		out.red( f"No servers updated for {target_env}" )

if __name__ == "__main__":
    maintenance( scripts.init() )
