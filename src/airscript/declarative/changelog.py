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

from typing import Any

class ChangeLog( object ):
    def __init__( self ):
        self._log = []
    
    def update( self, key: str, old: Any, new: Any ):
        self._log.append({'op': 'upd', 'key': key, 'old': old, 'new': new })
    
    def add( self, key: str, new: Any ):
        self._log.append({'op': 'add', 'key': key, 'new': new })
    
    def replace( self, key: str, new: Any ):
        self._log.append({'op': 'rpl', 'key': key, 'new': new })
    

