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
Helper functions for AirScript scripts
"""

import importlib.metadata
import os
import sys

from colorama import init as colorama_init

from airscript.utils import cmdline, runinfo
from pyAirlock.common import config, exception, log


def init():
    # get commandline options
    cmd = cmdline.Cmdline( sys.argv[1:] )
    if cmd.is_version():
        print( f"{importlib.metadata.metadata('airscript')['Name']}: Version {importlib.metadata.metadata('airscript')['Version']}" )
        sys.exit( 0 )

    airscript_config = get_config( cmd )
    if not airscript_config:
        sys.exit( 1 )

    run = runinfo.RunInfo( cmd, airscript_config, False, True )
    run.setLogLevel( cmd.get_loglevel() )
    run.setLogFile( cmd.get_logfile() )
    log1 = log.Log( "airscript", run, handler_init=True )
    log2 = log.Log( "pyAirlock", run, handler_init=True )
    colorama_init()
    return run


def get_config( cmd ):
    if cmd.get_configfile():
        config_file = os.path.expanduser( cmd.get_configfile() )
    else:
        config_file = os.path.expanduser( "~/.airscript/config.yaml" )
    cfg = config.Config( config_file )
    try:
        cfg.load()
    except exception.AirlockFileNotFoundError:
        print( f"Config file {config_file} does not exist - please create it first", file=sys.stderr )
        return None
    except exception.AirlockConfigError:
        print( f"Config file {config_file} is invalid - cannot continue", file=sys.stderr )
        return None
    return cfg
