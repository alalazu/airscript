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

from typing import Any, Self

class EnvValue( object ):
    def __init__( self, value: Any, env: Self=None ):
        if not env:
            self._default = value
            self._values = {}
        else:
            self._default = None
            self._values = { env: value }
    
    def __repr__( self ) -> str:
        return str( self.export() )
    
    def __getstate__( self ) -> dict:
        return self.export()
    
    def set( self, value: Any ):
        self._default = value
    
    def add( self, env: str, value: Any ):
        if env:
            self._values[env] = value
        else:
            self._default = value
    
    def get( self, env: str=None ) -> Any:
        try:
            return self._values[env]
        except KeyError:
            return self._default
    
    def export( self ) -> dict:
        r = {}
        if self._default:
            r["##env##"] = self._default
        for env, value in self._values.items():
            r[f"##env##{env}"] = value
        return r
    
