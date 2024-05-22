#!/usr/bin/python3

"""
AirScript: Airlock (Gateway) Configuration Script

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

import importlib.util

import sys
import os

from airscript.utils import const
from airscript.utils import cmdline, console, runinfo
from pyAirlock.common import config, exception, log


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


# get commandline options
cmd = cmdline.Cmdline( sys.argv[1:] )
if cmd.is_version():
    print( f"{const.Name}: Version {const.VERSION}" )
    sys.exit( 0 )

airscript_config = get_config( cmd )
if not airscript_config:
    sys.exit( 1 )

run = runinfo.RunInfo( cmd, airscript_config, False, True )
run.setLogLevel( cmd.get_loglevel() )
run.setLogFile( cmd.get_logfile() )
log1 = log.Log( "airscript", run, handler_init=True )
log2 = log.Log( "pyAirlock", run, handler_init=True )

if not cmd.get_scriptfile():
    # Console mode
    # - interact with AirScript and Airlock Gateways
    # - can prepare work environment with initialisation files
    #       !!! load initialisation files must not be run in a function !!!
    #       !!! otherwise, variables defined in the scripts will not be available in console !!!
    #       default is, in the following order:
    #           /etc/airscript/init.air
    #           ~/.airscript/init.air
    #           ~/.airscript.rc
    #        can be overwritten in configfile
    #          airscript:
    #            init:
    #              - ...
    #        or on commandline: -i <file> (can be given multiple times)
    print( "Welcome to AirScript - the Airlock Gateay Configuration Script - Version %s" % (const.VERSION,) )

    run.setConsole( True )
    ignore_not_found = False
    init_files = cmd.get_initfiles()
    if not init_files or init_files == []:
        init_files = airscript_config.get( 'airscript.init.scripts' )
    if not init_files or init_files == []:
        init_files = ['/etc/airscript/init.air', os.path.expanduser( '~/.airscript/init.air' ), os.path.expanduser( '~/.airscript.rc' )]
        ignore_not_found = True
    run.setVerbose( airscript_config.get( 'airscript.verbose' ))
    run.setVerbose( cmd.is_verbose() )
    builtin_done = False
    abort = False
    for fname in ["(builtin)"] + init_files:
        if fname == "(builtin)":
            if builtin_done:
                continue
            builtin_done = True
            python="import airscript"
        else:
            fname = histfile=os.path.expanduser( fname )
            try:
                with open( fname, "rb" ) as fp:
                    python = fp.read()
            except OSError as e:
                if ignore_not_found:
                    continue
                print( f"{fname}: {e}", file=sys.stderr )
                abort = True
        if run.verbose:
            print( f"Init script '{fname}'" )
        exec( python )
    if abort:
        sys.exit( 2 )
    
    header_printed = False
    if not isinstance( cmd, cmdline.Cmdline ):
        print( "WARNING" )
        print( "'cmd' has been overwritten and is no longer related to command line" )
        header_printed = True
    if not isinstance( airscript_config, config.Config ):
        if not header_printed:
            print( "WARNING" )
        print( "'airscript_config' has been overwritten and is no longer related to loaded config file" )
    
    console = console.Console( locals=locals )
else:
    # Script mode
    # - run airscript scripts without console interaction and initialisation files
    if cmd.get_initfiles():
        print( "Initialisation files are only supported in console-mode." )
        print( "When running a script, use Python's import facility.")
        sys.exit( 3 )
    script = cmd.get_scriptfile()
    params = cmd.get_scriptparams()

    spec = importlib.util.spec_from_file_location( "module.name", script )
    foo = importlib.util.module_from_spec( spec )
    sys.modules["module.name"] = foo
    foo.run = run
    spec.loader.exec_module( foo )
    # except OSError as e:
    #     print( f"{script}: {e.strerror}", file=sys.stderr )
