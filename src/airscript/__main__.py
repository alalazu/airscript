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
from airscript.utils import cmdline, console, scripts
from pyAirlock.common import config


def shell():
    run = scripts.init()

    if not run.cmd.get_scriptfile():
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
        init_files = run.cmd.get_initfiles()
        if not init_files or init_files == []:
            init_files = run.config.get( 'airscript.init.scripts' )
        if not init_files or init_files == []:
            init_files = ['/etc/airscript/init.air', os.path.expanduser( '~/.airscript/init.air' ), os.path.expanduser( '~/.airscript.rc' )]
            ignore_not_found = True
        run.setVerbose( run.config.get( 'airscript.verbose' ))
        run.setVerbose( run.cmd.is_verbose() )
        builtin_done = False
        abort = False
        for fname in ["(builtin)"] + init_files:
            if fname == "(builtin)":
                if builtin_done:
                    continue
                builtin_done = True
                python="from airscript import *"
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
        if not isinstance( run.cmd, cmdline.Cmdline ):
            print( "WARNING" )
            print( "'cmd' has been overwritten and is no longer related to command line" )
            header_printed = True
        if not isinstance( run.config, config.Config ):
            if not header_printed:
                print( "WARNING" )
            print( "'airscript_config' has been overwritten and is no longer related to loaded config file" )
        
        console.Console( locals=locals )
    else:
        # Script mode
        # - run airscript scripts without console interaction and initialisation files
        if run.cmd.get_initfiles():
            print( "Initialisation files are only supported in console-mode." )
            print( "When running a script, use Python's import facility.")
            sys.exit( 3 )
        script = run.cmd.get_scriptfile()
        params = run.cmd.get_scriptparams()

        spec = importlib.util.spec_from_file_location( "module.name", script )
        foo = importlib.util.module_from_spec( spec )
        sys.modules["module.name"] = foo
        foo.run = run
        spec.loader.exec_module( foo )
        # except OSError as e:
        #     print( f"{script}: {e.strerror}", file=sys.stderr )
