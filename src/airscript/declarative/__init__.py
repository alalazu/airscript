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

import os
import yaml

from airscript.declarative import yaml_doc
from airscript.model import baseObject, configuration

class DConfig( object ):
    def __init__( self, run_info, dname: str=None ):
        self._run = run_info
        if dname:
            self._dirname = dname
        else:
            self._dirname = self._run.config.get( 'declarative.dirname', 'declarative' )
        self._export_file = self._run.config.get( 'declarative.export-file', 'all.yaml' )
        self._map = {}
        self._docs = { None: {} }
    
    def load( self ):
        pass

    def save( self ):
        if not os.path.isdir( self._dirname ):
            os.mkdir( self._dirname )
        for fname, lst in self._docs.items():
            export_docs = []
            for _, doc in lst.items():
                export_docs.append( doc.export() )
            if fname == None:
                fname = self._export_file
            with open( os.path.join( self._dirname, fname ), "w" ) as fp:
                yaml.dump_all( export_docs, stream=fp )

    def merge( self, cfg: configuration, env: str=None ):
        for item in cfg.vhosts().values():
            self._docMerge( item, env )
        for item in cfg.mappings().values():
            self._docMerge( item, env )
        for item in cfg.backendgroups().values():
            self._docMerge( item, env )
        for item in cfg.certificates().values():
            self._docMerge( item, env )
        for item in cfg.jwks().values():
            self._docMerge( item, env )
        for item in cfg.openapi().values():
            self._docMerge( item, env )
        for item in cfg.graphql().values():
            self._docMerge( item, env )
        for item in cfg.hostnames().values():
            self._docMerge( item, env )
        for item in cfg.icap().values():
            self._docMerge( item, env )
        for item in cfg.iplists().values():
            self._docMerge( item, env )
        for item in cfg.kerberos().values():
            self._docMerge( item, env )
        for item in cfg.apipolicy().values():
            self._docMerge( item, env )
        for item in cfg.networkendpoints().values():
            self._docMerge( item, env )

    def _docMerge( self, item: baseObject.ReadOnlyObject, env: str=None ):
        doc = yaml_doc.Doc( item, env )
        try:
            fname = self._map[doc.key]
        except KeyError:
            fname = None
        if not fname:
            self._docs[None][doc.key] = doc
        else:
            try:
                base = self._docs[fname][doc.key]
            except KeyError:
                print( "merge: what should never happen, did!" )
                return
            base.update( doc, env=env )
            try:
                pass
            except KeyError:
                self._docs[fname] = [ doc ]

