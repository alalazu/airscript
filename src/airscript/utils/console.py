# AirScript: Airlock (Gateway) Configuration Script
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
AirScript interactive console.

Based on the built-in Python console, this module provides the user interface
for AirScript.
"""

import atexit
import code
import os
import sys

import readline


class Console( code.InteractiveConsole ):
    def __init__( self, locals=None, filename="<console>" ):
        # use exception trick to pick up the current frame
        try:
            raise None
        except:
            x = sys.exc_info()
            frame = sys.exc_info()[2].tb_frame.f_back
        namespace = frame.f_globals.copy()
        namespace.update(frame.f_locals)
        code.InteractiveConsole.__init__( self, locals=namespace, filename=filename )
        self._historyfile = os.path.expanduser( "~/.airscript.history" )
        self._historyLoad()
        self.interact( banner="AirScript is ready" )
    
    def _historyLoad( self ):
        readline.parse_and_bind( "tab: complete" )
        if hasattr( readline, "read_history_file" ):
            try:
                readline.read_history_file( self._historyfile )
                self._len = readline.get_current_history_length()
            except FileNotFoundError:
                open( self._historyfile, 'wb' ).close()
                self._len = 0
            atexit.register( self._historySave )
    
    def _historySave( self ):
        new_len = readline.get_current_history_length()
        readline.set_history_length( 1000 )
        try:
            readline.append_history_file( new_len - self._len, self._historyfile )
        except AttributeError:
            # potential issue of pyReadline on Windows
            pass
        readline.write_history_file( self._historyfile )
    
