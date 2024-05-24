#!/usr/bin/env python

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

import os
import argparse


class Cmdline( object ):
    """
    Parse commandline
    """
    def __init__( self, cmdline, description=None ):
        self._cmdline = cmdline
        if description == None:
            description = 'AirScript - the Airlock Gateay Configuration Script'
        parser = argparse.ArgumentParser( description=description )
        parser.add_argument( '-c', '--config', default=None, metavar='CONFIGFILE', action='store',
                                help='path to config file (default: ~/.airscript/config.yaml)', )
        parser.add_argument( '-i', '--init', default=None, action='append',
                                help='path to initialisation script(s), can be specified multiple times (default, in order: /etc/airscript/init.air, ~/.airscript.rc', ),
        parser.add_argument( '-v', '--verbose', default=False, action='store_true',
                                help='verbose output' )
        parser.add_argument( '-l', '--loglevel', type=int, default=31, action='store',
                                help='log level, bitmask of fatal (1), critical (2), error (4), warning (8), info (16), verbose (32), trace (64), debug (128) (default: 31)' )
        parser.add_argument( '-L', '--logfile', default=None, action='store',
                                help='log destination: stdout, stderr, or <filename> (default: None)' )
        parser.add_argument( '-V', '--version', default=False, action='store_true',
                                help='get version information' )
        parser.add_argument( 'args', help='script to execute and its parameters', metavar="path", nargs="*" )
        self._args = parser.parse_args( cmdline )

    def __repr__( self ):
        return f"Cmdline: {self._cmdline}"

    ## check options
    def is_verbose( self ):
        return self._args.verbose

    def is_version( self ):
        return self._args.version

    ## get option values
    def get_configfile( self ):
        if self._args.config == None:
            return os.path.expanduser( '~/.airscript/config.yaml' )
        return os.path.expanduser( self._args.config )
    
    def get_initfiles( self ):
        return self._args.init

    def get_loglevel( self ):
        return self._args.loglevel
    
    def get_logfile( self ):
        if self._args.logfile == "stdout":
            return "/dev/stdout"
        elif self._args.logfile == "stderr":
            return "/dev/stderr"
        return self._args.logfile
    
    def get_args( self ):
        return self._args.args
    
    def get_scriptfile( self ):
        try:
            return self._args.args[0]
        except IndexError:
            return None
    
    def get_scriptparams( self ):
        try:
            return self._args.args[1:]
        except IndexError:
            return None
    
