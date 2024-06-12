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

from airscript.utils import output
from airscript.base import element
from airscript.model import configuration, mapping
from pyAirlock.common import lookup


TYPENAME = 'api-policy-service'
KIND = 'APIPolicyService'

lookup.registerBoth( element.LOOKUP_TYPENAME2KIND, element.LOOKUP_KIND2TYPENAME, TYPENAME, KIND )

class APIPolicy( element.ModelElement ):
    RELATIONKEY = { "mapping": "mappings" }
    
    def __init__( self, parent, obj=None, id=None ):
        self._typename = TYPENAME
        self._path = 'api-policy-services'
        self._kind = KIND
        element.ModelElement.__init__( self, parent, obj=obj, id=id )
    
    """
    interactions with Gateway REST API
    """
    def connectMapping( self, mapping_object ):
        if type( mapping_object ) != mapping.Mapping:
            output.Error( "This is not a mapping but %s" % (type(mapping_object),) )
            return False
        return self.relationshipAdd( mapping_object )
    
    def disconnectMapping( self, mapping_object ):
        if type( mapping_object ) != mapping.Mapping:
            output.Error( "This is not a mapping but %s" % (type(mapping_object),) )
            return False
        return self.relationshipDelete( mapping_object )
    
