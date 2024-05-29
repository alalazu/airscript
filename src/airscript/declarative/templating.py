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

from mako.template import Template
from mako import exceptions

from pyAirlock.common import config


class TemplateHandler( object ):
    def __init__( self, cfg: config.Config, raw=False ):
        self._airscript_module_dir = cfg.get( 'declarative.templating-module-dir', 'templates/modules' )
        self._raw = raw
        self._params = {}

    ''' render template '''
    def render( self, fname ):
        template = Template( filename=fname, module_directory=self._airscript_module_dir )
        if self._raw:
            return template.source
        try:
            return template.render( **self._params )
        except:
            print( exceptions.html_error_template().render() )
            return ""
    
