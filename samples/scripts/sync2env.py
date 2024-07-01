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


def del_mappings( cfg, target_env="PROD", verbose:bool =False ):
	out.yellow( f"Preparing config for environment {target_env}" )
	out.green( f"Deleting all mappings not labeled with {target_env}" )
	for _,m in cfg.mappings().items():
		if not "PROD".casefold() in map(str.casefold, m.attrs['labels']):
			if verbose:
				out.grey( f"- del:  {m.id}: {m.name} - {m.attrs['labels']}" )
			m.delete()
		else:
			if verbose:
				out.grey( f"- keep: {m.id}: {m.name} - {m.attrs['labels']}" )

def del_others( cfg, verbose: bool=False ):
	out.green( "Deleting unconnected config elements" )
	for elementName in reversed( cfg.elementOrderList() ):
		if elementName in ["mapping", "template"]:
			continue
		out.green( f"- {elementName}" )
		object_list = cfg.getObjects( elementName )
		for _,element in object_list.items():
			keep = False
			# $$$
			# needs to changed - rels keys are not typenames
			for typename,lst_rels in element.rels.items():
				if cfg.elementOrderNr( elementName ) > cfg.elementOrderNr( typename ):
					continue
				if lst_rels != None and lst_rels != []:
					keep = True
					break
				if verbose:
					if keep:
						out.grey( f"keep: {element.id}: {element.name} - {element.rels}" )
					else:
						out.grey( f"del:  {element.id}: {element.name}" )
				element.delete()

def load_source( server ):
	out.yellow( "Loading source config" )
	out.green( f"Connecting to '{server.getName()}'" )
	if server.connect():
		atexit.register( server.disconnect )
		c = server.configurationFindActive()
		out.green( "Fetching active config" )
		c.loadAll()
		return c
	return None

def sync2env( run ):
	out = output.Info()
	log.set_level( 15 )

	target_env = run.cmd.get_args()
	if not target_env or target_env == []:
		die( "Usage: sync2env <target_env>" )
	target_env = target_env[0]
	verbose = run.config.get( 'tools.sync2env.debug', False )

	out.yellow( "Loading gateway definitions" )
	gws = airscript.gwLoad( run_info=run )

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
		out.yellow( f"Sync2Env completed, {count} server(s) updated" )
	else:
		out.red( f"No servers updated for {target_env}" )

if __name__ == "__main__":
    sync2env( scripts.init() )
