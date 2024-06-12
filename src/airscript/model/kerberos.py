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
from airscript.utils import output
from airscript.model import backendgroup, configuration
from pyAirlock.common import lookup


TYPENAME = 'kerberos-environment'
KIND = 'KerberosEnvironment'

lookup.registerBoth( element.LOOKUP_TYPENAME2KIND, element.LOOKUP_KIND2TYPENAME, TYPENAME, KIND )

class Kerberos( element.ModelElement ):
    def __init__( self, parent, obj=None, id=None ):
        self._typename = TYPENAME
        self._path = 'kerberos-environments'
        self._kind = KIND
        element.ModelElement.__init__( self, parent, obj=obj, id=id )
    
    """
    interactions with Gateway REST API
    """
    def connectBackendGroup( self, cert ):
        if type( cert ) != backendgroup.Backendgroup:
            output.Error( "This is not a certificate but %s" % (type(backendgroup),) )
            return False
        return self.relationshipAdd( cert )
    
    def disconnectBackendGroup( self, cert ):
        if type( cert ) != backendgroup.Backendgroup:
            output.Error( "This is not a certificate but %s" % (type(backendgroup),) )
            return False
        return self.relationshipDelete( cert )
    
