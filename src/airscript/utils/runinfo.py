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
import platform

class RunInfo( object ):
    def __init__( self, cmd, config, verbose: bool, is_console: bool, log_level: int=31 ):
        self.cmd = cmd
        self.config = config
        self.verbose = verbose
        self.console = is_console
        self.log_level = log_level
        if platform.system() == "Windows":
            self.log_file = os.path.expanduser( "~/log/pyAirlock.log" )
        else:
            self.log_file = "/var/log/pyAirlock/pyAirlock.log"
    
    def isVerbose( self ):
        return self.verbose

    def setVerbose( self, verbose: bool ) -> bool:
        org = self.verbose
        if isinstance( verbose, bool ):
            self.verbose = verbose
        return org
    
    def isConsole( self ):
        return self.console

    def setConsole( self, console: bool ) -> bool:
        org = self.console
        if isinstance( console, bool ):
            self.console = console
        return org
    
    def setLogLevel( self, log_level: int ) -> int:
        org = self.log_level
        if isinstance( log_level, int ):
            self.log_level = log_level
        return org
    
    def setLogFile( self, log_file: str ) -> str:
        org = self.log_file
        if isinstance( log_file, str ):
            self.log_file = log_file
        return org
    
