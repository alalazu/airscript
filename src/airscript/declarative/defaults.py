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

import glob
import os
import yaml

from typing import Self

map_defaults = None

def init( dirname: str=None ):
    global map_defaults

    map_defaults = {}
    if dirname == None:
        # get defaults from samples directory
        dirname = os.path.join( os.sep.join( __file__.split( os.sep )[:-4] ),'samples','defaults' )
    if os.path.isdir( dirname ):
        for fname in glob.glob( "*.yaml", root_dir=dirname ):
            with open( os.path.join( dirname, fname ), "r" ) as fp:
                map_defaults[fname[:-5]] = yaml.safe_load( fp )

def get( type_name: str ) -> dict:
    global map_defaults

    if map_defaults == None:
        init()
    try:
        return map_defaults[type_name]
    except KeyError:
        return {}

