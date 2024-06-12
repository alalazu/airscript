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
from airscript.base import element
from pyAirlock.common import utils


def create_key( base_object: element.BaseElement=None, yaml_dict: dict=None, param_set: set=None ):
    if base_object:
        return "{}:{}".format( base_object.getKind(), base_object.getName() )
    elif yaml_dict:
        return "{}:{}".format( yaml_dict['kind'], utils.getDictValue( yaml_dict, 'metadata.name' ))
    else:
        return "{}:{}".format( param_set[0], param_set[1] )


class BaseDoc( object ):
    def __init__( self, id: str=None, base_object: element.BaseElement=None, yaml_dict: dict=None, env: str=None, dconfig=None ):
        self.id = id
        self._base_object = base_object
        self._dconfig = dconfig
        if base_object:
            self._kind = base_object.getKind()
            try:
                self._name = base_object.name
            except AttributeError:
                self._name = None
            self._environments = [ env ] if env != None else []
            self._parents = None
            self.key = create_key( base_object=base_object )
            self._spec = self._copyNonDefaults( base_object.getAttrs(), defaults.get( self._kind ))
        else:
            self._kind = yaml_dict['kind']
            self._name = utils.getDictValue( yaml_dict, 'metadata.name' )
            self._spec = self._loadYAML( yaml_dict['spec'] )
            if env:
                self._spec = self._reduce2Env( self._spec, env )
            self._environments = utils.getDictValue( yaml_dict, 'metadata.environments', [] )
            self._parents = utils.getDictValue( yaml_dict, 'metadata.inherit', [] )
            self.key = create_key( yaml_dict=yaml_dict )
        self._changelog = changelog.ChangeLog()
        try:
            del self._spec['name']
        except KeyError:
            pass
    
    def __repr__( self ) -> str:
        return str( { 'kind': self._kind, 'name': self._name, 'env': self._environments } )
    
    def getKind( self ) -> str:
        return self._kind
    
    def getName( self ) -> str:
        return self._name
    
    def isInEnv( self, env: str ) -> bool:
        if env and env in self._environments:
            return True
        if not env and 'default' in self._environments:
            return True
        return False
    
    def getSpec( self, env: str ) -> dict:
        r = self._inheritSpec( defaults.get( self._kind ), self, env )
        r = self._overwriteValues( r, self._reduce2Env( self._spec, env ))
        r['name'] = self._name
        return r
    
    def getParents( self ) -> list:
        return self._parents
    
    def connectionsSupported( self ) -> bool:
        return False
    
    def export( self ) -> dict:
        r =  {
                'apiVersion': 'gateway.airlock.com/settings-v1alpha',
                'kind': self._kind,
                'metadata': {},
                'spec': self._dictify( self._spec ),
        }
        if self._name:
            r['metadata']['name'] = self._name
        if self._environments:
            r['metadata']['environments'] = self._environments
        if self._parents:
            r['metadata']['inherit'] = self._parents
        return r
    
    def _dictify( self, spec: dict ) -> dict:
        r = {}
        for k,v in spec.items():
            if isinstance( v, envvalue.EnvValue ):
                r[k] = v.export()
            elif isinstance( v, dict ):
                r[k] = self._dictify( v )
            else:
                r[k] = v
        return r
    
    def update( self, doc: Self, env: str=None ):
        if env:
            if self._environments:
                if not env in self._environments:
                    self._environments.append( env )
            else:
                self._environments = [ env ]
            self._changelog.add( f"metadata.environments", env )
        else:
            env = "default"
        self._updateValues( self._spec, doc._spec, defaults.get( self._kind ), "", env )

    def inheritanceTree( self, doc: Self ) -> dict:
        if doc._parents == None or doc._parents == []:
            return {}
        r = {}
        for name in doc._parents:
            parent_doc = self._dconfig.findDoc( self._kind, name )
            r[name] = self.inheritanceTree( parent_doc )
        return r
    
    def _hasTemplateMarker( self, txt: str ) -> bool:
        if txt == None:
            return False
        try:
            return r"${" in txt
        except TypeError:
            return False

    def _updateValues( self, target: dict, source: dict, defaults: dict, path: str, env: str=None ):
        """
        Update yaml document with values of config element retrieved from Airlock Gateway (merge).
        Values equal to those in `defaults` dict are skipped.
        """
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
                if isinstance( target[key], envvalue.EnvValue ):
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
                if isinstance( target[key], envvalue.EnvValue ):
                    original = target[key].get( env=env )
                    if not self._hasTemplateMarker( original ):
                        self._changelog.update( f"{path}.{key}", original, value )
                        target[key].add( env, value )
                else:
                    self._changelog.update( f"{path}.{key}", target[key], value )
                    target[key] = envvalue.EnvValue( value )
                    target[key].add( env, value )

    def _copyNonDefaults( self, source: dict, defaults: dict ) -> dict:
        """
        Copy non-default values of config element retrieved from Airlock Gateway to yaml document (initialisation)
        """
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
            elif isinstance( value, list ):
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

    def _overwriteValues( self, base: dict, overlay: dict ) -> dict:
        """
        Deep merge overlay onto base dicts
        """
        r = {}
        for key, value in base.items():
            if isinstance( value, dict ):
                try:
                    new_value = self._overwriteValues( value, overlay[key] )
                except KeyError:
                    # no values to overwrite, keep base as is
                    new_value = value
            elif isinstance( value, list ):
                try:
                    lst = overlay[key]
                    value_list = []
                except KeyError:
                    # no values to overwrite, keep base as is
                    lst = []
                    value_list = value
                for entry in lst:
                    if isinstance( entry, dict ):
                        try:
                            default_values = value[0]
                        except IndexError:
                            default_values = {}
                        value_list.append ( self._overwriteValues( default_values, entry ))
                    else:
                        value_list.append( entry )
                new_value = value_list
            else:
                try:
                    new_value = overlay[key]
                except KeyError:
                    new_value = value
            r[key] = new_value
        for key, value in overlay.items():
            if not key in r:
                r[key] = value
        return r

    def _extractEnvValues( self, source: dict, env: str ) -> dict:
        r = {}
        for key, value in source.items():
            if isinstance( value, envvalue.EnvValue ):
                if key[0:7] == "##env##":
                    if key[7:] != env:
                        continue
                    pass
            elif isinstance( value, dict ):
                r[key] = self._extractEnvValues( value, env )
            elif isinstance( value, list ):
                r[key] = []
                for entry in value:
                    if isinstance( entry, dict ):
                        try:
                            tmp = value[0]
                        except IndexError:
                            tmp = {}
                        r[key].append( self._extractEnvValues( tmp, env ))
                    else:
                        r[key].append( entry )
            else:
                r[key] = value
        return r
    
    def _check4EnvVarKey( self, data: dict ) -> bool:
        for key in data:
            if "##env##" in key:
                return True
        return False

    def _loadYAML( self, data: dict ) -> dict:
        r = {}
        for key, value in data.items():
            if isinstance( value, dict ):
                if self._check4EnvVarKey( value ):
                    r[key] = self._loadEnvValue( value )
                else:
                    r[key] = self._loadYAML( value )
            elif isinstance( value, list ):
                r[key] = []
                for entry in value:
                    if isinstance( entry, dict ):
                        if self._check4EnvVarKey( value ):
                            r[key].append( self._loadEnvValue( entry ))
                        else:
                            r[key].append( self._loadYAML( entry ))
                    else:
                        r[key].append( entry )
            else:
                r[key] = value
        return r
    
    def _loadEnvValue( self, data: dict ) -> envvalue.EnvValue:
        r = None
        for key, value in data.items():
            if isinstance( value, dict ):
                env_value = self._loadYAML( value )
            elif isinstance( value, list ):
                env_value = []
                for entry in value:
                    if isinstance( entry, dict ):
                        env_value.append( self._loadYAML( entry ))
                    else:
                        env_value.append( entry )
            else:
                env_value = value
            env = key[7:] if key != "##env##" else None
            if r == None:
                r = envvalue.EnvValue( env_value, env=env )
            else:
                r.add( env, env_value )
        return r
    
    def _reduce2Env( self, data: dict, env: str ) -> dict:
        """
        Reduce dict to contain on values for specific environment
        """
        r = {}
        for key, value in data.items():
            if isinstance( value, envvalue.EnvValue ):
                r[key] = value.get( env )
            elif isinstance( value, dict ):
                r[key] = self._reduce2Env( value, env )
            elif isinstance( value, list ):
                r[key] = []
                for entry in value:
                    if isinstance( entry, dict ):
                        r[key].append( self._reduce2Env( entry, env ))
                    else:
                        r[key].append( entry )
            else:
                r[key] = value
        return r

    def _inheritSpec( self, base, doc: Self, env: str ) -> dict:
        """
        Go up inheritance tree overlaying parent values onto previous layers
        """
        if doc._parents != None and doc._parents != []:
            for name in doc._parents:
                parent_doc = self._dconfig.findDoc( self._kind, name )
                base = self._inheritSpec( base, parent_doc, env )
        return self._overwriteValues( base, self._reduce2Env( doc._spec, env ))
    
