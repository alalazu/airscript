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

from typing import Self

from airscript.declarative import changelog, defaults, envvalue
from airscript.model import baseObject

re_marker = None


def create_key( item: baseObject.ReadOnlyObject ):
    return "{}:{}".format( item.getKind(), item.getName() )


class Doc( object ):
    def __init__( self, item: baseObject.ReadOnlyObject, env: str=None ):
        self._item = item
        self._kind = item.getKind()
        self._name = item.name
        self._environments = [ env ] if env != None else None
        self._connections = { env if env else "default": item.listRelWithKind() }
        self._changelog = changelog.ChangeLog
        self.key = create_key( item )
        self._spec = self._copyNonDefaults( item.getAttrs(), defaults.get( self._kind ))
        try:
            del self._spec['name']
        except KeyError:
            pass
    
    def export( self ) -> dict:
        r =  {
                'apiVersion': 'gateway.airlock.com/v1alpha',
                'kind': self._kind,
                'metadata': {
                    'name': self._name,
                },
                'connections': self._connections,
                'spec': self._spec,
        }
        if self._environments:
            r['metadata']['environments'] = self._environments
        return r
    
    def update( self, doc: Self, env: str=None ):
        if not env in self._environments:
            self._environments.append( env )
            self._changelog.add( f"metadata.environments", env )
        self._connections[env] = doc._item.listRelWithKind()
        self._changelog.replace( f"metadata.connections", self._connections[env] )
        self._updateValues( self._spec, doc, defaults.get( self._kind ), "", env )

    def _hasTemplateMarker( self, txt: str ) -> bool:
        if txt == None:
            return False
        return r"${" in txt
        """
        global re_marker

        if txt == None:
            return False
        if re_marker == None:
            re_marker = re.compile( r".*\${.*" )
        return re_marker.match( txt )
        """

    def _updateValues( self, target: dict, source: dict, defaults: dict, path: str, env: str=None ):
        for key, value in source.items():
            if not key in target:
                # if key is not defined for target doc, use default value
                # if there is no default, set new value
                if not key in defaults:
                    self._changelog.update( f"{path}.{key}", None, value )
                    target[key] = value
                continue
            if isinstance( value, dict ):
                try:
                    defaults = defaults[key]
                except KeyError:
                    defaults = {}
                self._updateValues( target[key], value, defaults, "{path}.{key}", env )
                continue
            if not env:
                # no environment defined for config
                # set new default value, unless previous value has template marker
                if isinstance( target[key], envvalue.envValue ):
                    original = target[key].get()
                    if not self._hasTemplateMarker( original ):
                        self._changelog.update( f"{path}.{key}", original, value )
                        target[key].set( value )
                elif not self._hasTemplateMarker( target[key] ):
                    self._changelog.update( f"{path}.{key}", target[key], value )
                    target[key] = value
            else:
                # environment-specific config
                # set environment value, unless previous value has template marker
                if isinstance( target[key], envvalue.envValue ):
                    original = target[key].get( env=env )
                    if not self._hasTemplateMarker( original ):
                        self._changelog.update( f"{path}.{key}", original, value )
                        target[key].add( env, value )
                else:
                    self._changelog.update( f"{path}.{key}", target[key], value )
                    target[key] = envvalue.EnvValue( value )
                    target[key].add( env, value )

    def _copyNonDefaults( self, source: dict, defaults: dict ) -> dict:
        r = {}
        for key, value in source.items():
            if isinstance( value, dict ):
                try:
                    defaults_subdict = defaults[key]
                except KeyError:
                    defaults_subdict = {}
                value = self._copyNonDefaults( value, defaults_subdict )
                if value == {}:
                    continue
            if isinstance( value, list ):
                lst = []
                try:
                    defaults_subdict = defaults[key]
                except KeyError:
                    defaults_subdict = {}
                if isinstance( defaults_subdict, list ):
                    try:
                        defaults_subdict = defaults_subdict[0]
                    except IndexError:
                        defaults_subdict = {}
                for entry in value:
                    if isinstance( entry, dict ):
                        entry = self._copyNonDefaults( entry, defaults_subdict )
                    if entry != {}:
                        lst.append( entry )
                if lst == []:
                    continue
                value = lst
            # do not copy value if is the same as in defaults
            try:
                if defaults[key] == value:
                    continue
            except KeyError:
                pass
            r[key] = value
        return r

