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

import glob
import os
import yaml

from pprint import pprint as pp

from airscript.declarative import defaults, yaml_doc, templating
from airscript.model import baseObject, configuration
from airscript.utils import output, runinfo, typename

class DConfig( object ):
    def __init__( self, run_info: runinfo.RunInfo, dname: str=None ):
        self._run = run_info
        self._export_file = self._run.config.get( 'declarative.export-file', 'all.yaml' )
        if dname:
            self._dirname = dname
        else:
            self._dirname = self._run.config.get( 'declarative.config-dir', 'declarative' )
        if not os.path.isdir( self._dirname ):
            os.mkdir( self._dirname )
        defaults.init( self._run.config.get( 'declarative.defaults-dir' ))
        self._reset()
    
    def load( self, env: str=None, raw: bool=False ):
        renderer = templating.TemplateHandler( self._run.config, raw )
        self._reset()
        for fname in glob.glob( "*.yaml", root_dir=self._dirname ):
            print( f"- {fname}" )
            self._docs[fname] = {}
            try:
                for doc in yaml.safe_load_all( renderer.render( os.path.join( self._dirname, fname ))):
                    if not doc:
                        continue
                    declarative_doc = yaml_doc.Doc( self.next_id, yaml_dict=doc, env=env )
                    if declarative_doc.isInEnv( env ):
                        self._docs[fname][declarative_doc.key] = declarative_doc
                        self._map[declarative_doc.key] = fname
                    self.next_id += 1
            except yaml.scanner.ScannerError:
                # probably templating code - just ignore the file
                # should only happen in raw mode
                # upon merge & save, the documents defined in this file will be exported to 'declarative.export-file'
                pass
        self._env = env
        self._loaded = "raw" if raw else "config"

    def _load_org( self ):
        if not os.path.isdir( self._dirname ):
            return
        self._map = {}
        self._docs = { None: {} }
        for fname in glob.glob( "*.yaml", root_dir=self._dirname ):
            if fname != self._export_file:
                self._docs[fname] = {}
            with open( os.path.join( self._dirname, fname ), "r" ) as fp:
                if fname == self._export_file:
                    fname = None
                try:
                    for doc in yaml.safe_load_all( fp ):
                        if not doc:
                            continue
                        key = yaml_doc.create_key( yaml_dict=doc )
                        self._map[key] = fname
                        self._docs[fname][key] = yaml_doc.Doc( yaml_dict=doc )
                except yaml.scanner.ScannerError:
                    # probably templating code - just ignore the file
                    # upon merge & save, the documents defined in this file will be exported to 'declarative.export-file'
                    pass

    def loadRaw( self ):
        return self.load( raw=True )

    def save( self, force: bool=False ) -> bool:
        if not self._loaded:
            self.load( raw=True )
        if self._loaded != "raw" and not force:
            output.error( "Loaded config not in format 'raw' - reload or specify 'force=True'" )
            return False
        for fname, docs in self._docs.items():
            export_docs = []
            for _, doc in docs.items():
                export_docs.append( doc.export() )
            if fname == None:
                fname = self._export_file
            with open( os.path.join( self._dirname, fname ), "w" ) as fp:
                yaml.dump_all( export_docs, stream=fp )
        return True

    def build( self, env: str, force: bool=False ) -> configuration.Configuration:
        if not self._loaded:
            self.load( env=env )
        if self._loaded != "config" and not force:
            output.error( "Loaded config not in format 'config' - reload or specify 'force=True'" )
            return None
        docs = []
        lookup = {}
        # build structures
        for _, doc_lst in self._docs.items():
            for _, declarative_doc in doc_lst.items():
                if declarative_doc.isInEnv( env ):
                    docs.append( declarative_doc )
                    lookup[declarative_doc.key] = declarative_doc
        # remove unused documents
        while True:
            tbd = []
            changed = False
            for declarative_doc in docs:
                if declarative_doc.connectionsReduce2Env( env, lookup ):
                    changed = True
                if not declarative_doc.isConnected( env ):
                    tbd.append( declarative_doc )
            if tbd != []:
                for entry in tbd:
                    try:
                        del lookup[entry.key]
                    except KeyError:
                        pass
                    docs.remove( entry )
                changed = True
            if changed == False:
                break
        # create config
        cfg = configuration.Configuration( None, None, self._run.config )
        for declarative_doc in docs:
            #print( declarative_doc.key )
            #pp( declarative_doc.getSpec() )
            obj = cfg.addElement( declarative_doc.getKind(), id=declarative_doc.id )
            spec = { "id": declarative_doc.id, "attributes": declarative_doc.getSpec() }
            spec['relationships'] = {}
            for kind, lst in declarative_doc.getConnections( env ).items():
                tn = typename.getTypename( kind )
                spec['relationships'][tn] = { "data": [] }
                for name in lst:
                    key = yaml_doc.create_key( param_set=(kind, name) )
                    referred = lookup[key]
                    spec['relationships'][tn]['data'].append( { "type": tn, "id": referred.id })
            obj.loadData( spec )
            #obj = cfg.addElement( declarative_doc.getKind(), declarative_doc.id, { "id": declarative_doc.id, "attributes": declarative_doc.getSpec() } )
        return cfg

    def merge( self, cfg: configuration, env: str=None, force: bool=None ):
        if not self._loaded:
            self.load( raw=True )
        if self._loaded != "raw" and not force:
            output.error( "Loaded config not in format 'raw' - reload or specify 'force=True'" )
            return False
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
        doc = yaml_doc.Doc( self.next_id, base_object=item, env=env )
        self.next_id += 1
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

    def _reset( self ):
        self._map = {}
        self._docs = {}
        self.next_id = 1
        self._loaded = None
        self._env = None
    
