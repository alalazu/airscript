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
from airscript.utils import templating
from pyAirlock.common import lookup


TYPENAME = 'license-response'
KIND = 'License'

lookup.registerBoth( element.LOOKUP_TYPENAME2KIND, element.LOOKUP_KIND2TYPENAME, TYPENAME, KIND )

class License( element.BaseElement ):
    def __init__( self, parent, obj=None, id=None ):
        self._typename = TYPENAME
        self._path = 'license'
        self._kind = KIND
        self._operations = "RUD"
        element.BaseElement.__init__( self, parent, obj=obj, id=id )
    
    def me( self ):
        r = super().me()
        r['owner'] = self.attrs['owner']
        r['environment'] = self.attrs['environment']
        r['backendHosts'] = self.attrs['backendHosts']
        return r
        
    def values( self ):
        tmp = super().values()
        tmp.append( self.attrs['owner'] )
        tmp.append( self.attrs['environment'] )
        tmp.append( self.attrs['backendHosts'] )
        return tmp
        
    def sync( self ) -> bool:
        """
        Sync license changes to Airlock Gateway

        Returns:
        - true: success, sync'ed
        - false: operation failed
        """
        classPointer = self._parent.conn.getAPI( self._typename )
        if classPointer == None:
            return False
        if self._deleted:
            classPointer.delete( self.id )
            return False
        if self._attrs_modified:
            data = { 'attributes': { 'license': self.attrs['rawLicense'] }, 'type': "license" }
            self.loadData( classPointer.update( id=self.id, data=data ))
            self._attrs_modified = False
        return True
    
    def _extractName( self, data: dict ) -> str|None:
        renderer = templating.TemplateHandler()
        name = renderer.renderString( self._parent.runtimeConfigGet( 'declarative.templating.license-name', '${owner}: ${environment} - ${backendHosts}' ), data['attributes'] )
        return name
            
