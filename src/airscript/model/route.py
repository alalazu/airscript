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


TYPENAME_DST_V4 = 'route-ipv4-destination'
KIND_DST_V4 = 'RouteDestinationIPv4'
TYPENAME_DST_V6 = 'route-ipv6-destination'
KIND_DST_V6 = 'RouteDestinationIPv6'
TYPENAME_SRC_V4 = 'route-ipv4-source'
KIND_SRC_V4 = 'RouteSourceIPv4'
TYPENAME_SRC_V6 = 'route-ipv6-source'
KIND_SRC_V6 = 'RouteSourceIPv6'

lookup.registerBoth( element.LOOKUP_TYPENAME2KIND, element.LOOKUP_KIND2TYPENAME, TYPENAME_DST_V4, KIND_DST_V4 )
lookup.registerBoth( element.LOOKUP_TYPENAME2KIND, element.LOOKUP_KIND2TYPENAME, TYPENAME_DST_V6, KIND_DST_V6 )
lookup.registerBoth( element.LOOKUP_TYPENAME2KIND, element.LOOKUP_KIND2TYPENAME, TYPENAME_SRC_V4, KIND_SRC_V4 )
lookup.registerBoth( element.LOOKUP_TYPENAME2KIND, element.LOOKUP_KIND2TYPENAME, TYPENAME_SRC_V6, KIND_SRC_V6 )

class Route( element.ModelElement ):
    def __init__( self, parent, obj=None, id=None, ipv4=True, source=True ):
        self._ipv4 = ipv4
        self._source = source
        if ipv4:
            if not source:
                self._typename = TYPENAME_DST_V4
                self._path = 'routes/ipv4/destination'
                self._kind = KIND_DST_V4
            else:
                self._typename = TYPENAME_SRC_V4
                self._path = 'routes/ipv4/source'
                self._kind = KIND_SRC_V4
        else:
            if not source:
                self._typename = TYPENAME_DST_V6
                self._path = 'routes/ipv6/destination'
                self._kind = KIND_DST_V6
            else:
                self._typename = TYPENAME_SRC_V6
                self._path = 'routes/ipv6/source'
                self._kind = KIND_SRC_V6
        element.ModelElement.__init__( self, parent, obj=obj, id=id )

    def me( self ):
        r = super().me()
        r['ipv4'] = self._ipv4 if self.name != None else None
        r['source'] = self._source if self.name != None else None
        return r
        
    def values( self ):
        tmp = super().values()
        tmp.append( self._ipv4 )
        tmp.append( self._source )
        return tmp
    
