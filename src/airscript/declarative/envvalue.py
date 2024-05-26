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

class EnvValue( object ):
    def __init__( self, value: Any ):
        self._default = value
        self._values = {}
    
    def set( self, value: Any ):
        self._default = value
    
    def add( self, env: str, value: Any ):
        self._values[env] = value
    
    def get( self, env: str=None ) -> Any:
        try:
            return self._values[env]
        except KeyError:
            return None
    
    def export( self ) -> dict:
        r = { "##env##": self._default }
        for env, value in self._values.items():
            r[f"##env##{env}"] = value
        return r
    
