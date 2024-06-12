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

from airscript.base import element
from airscript.model import configuration
from pyAirlock.common import lookup


TYPENAME = 'route-default'
KIND = 'DefaultRouteSettings'

lookup.registerBoth( element.LOOKUP_TYPENAME2KIND, element.LOOKUP_KIND2TYPENAME, TYPENAME, KIND )

class DefaultRouteSettings( element.BaseElement ):
    def __init__( self, parent, obj=None, id=None ):
        self._typename = TYPENAME
        self._path = 'routes/default'
        self._kind = KIND
        self._operations = "RU"
        element.BaseElement.__init__( self, parent, obj=obj, id=id )
    
    def me( self ):
        r = super().me()
        r['default_gateway'] = self.attrs['ipv4']['gateway']
        return r
    
    def values( self ):
        tmp = super().values()
        tmp.append( self.attrs['ipv4']['gateway'] )
        return tmp
    
