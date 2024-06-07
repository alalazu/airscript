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
from typing import Union

from airscript.base import element
from airscript.declarative import basedoc, connecteddoc, defaults, globaldoc, templating
from airscript.model import configuration
from airscript.utils import output, runinfo

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
                    if doc['apiVersion'] == 'gateway.airlock.com/settings-v1alpha':
                        declarative_doc = basedoc.BaseDoc( self.next_id, yaml_dict=doc, env=env, dconfig=self )
                    elif doc['apiVersion'] == 'gateway.airlock.com/global-v1alpha':
                        declarative_doc = basedoc.BaseDoc( self.next_id, yaml_dict=doc, env=env, dconfig=self )
                    elif doc['apiVersion'] == 'gateway.airlock.com/connected-v1alpha':
                        declarative_doc = connecteddoc.ConnectedDoc( self.next_id, yaml_dict=doc, env=env, dconfig=self )
                    else:
                        output.error( f"Invalid API: {doc['apiVersion']}" )
                        continue
                    # if declarative_doc.isInEnv( env ):
                    #     self._docs[fname][declarative_doc.key] = declarative_doc
                    #     self._map[declarative_doc.key] = (fname, declarative_doc)
                    self._docs[fname][declarative_doc.key] = declarative_doc
                    self._map[declarative_doc.key] = (fname, declarative_doc)
                    self.next_id += 1
            except yaml.scanner.ScannerError as e:
                # probably templating code - just ignore the file
                # should only happen in raw mode
                # upon merge & save, the documents defined in this file will be exported to 'declarative.export-file'
                print( e )
                pass
        self._env = env
        self._loaded = "raw" if raw else "config"
    
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

    def build( self, env: str, force: bool=False ) -> dict:
        declarative_doc: Union[basedoc.BaseDoc,connecteddoc.ConnectedDoc]
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
                elif declarative_doc.isInEnv( None ):
                    lookup[declarative_doc.key] = declarative_doc
        # remove unused documents
        while True:
            tbd = []
            changed = False
            for declarative_doc in docs:
                if declarative_doc.connectionsSupported():
                    if declarative_doc.connectionsReduce2Env( env, lookup ):
                        changed = True
                    # if not declarative_doc.isConnected( env ) and not declarative_doc.isNode():       # node has no connections but we need it
                    #     tbd.append( declarative_doc )
                    if not declarative_doc.isConnected( env ) and not declarative_doc.isNode():       # node has no connections but we need it
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
        object_dicts = {}
        for declarative_doc in docs:
            #print( declarative_doc.key )
            #pp( declarative_doc.getSpec() )
            spec = { "attributes": declarative_doc.getSpec( env ) }
            if declarative_doc.connectionsSupported():
                spec['connections'] = declarative_doc.getConnections( env )
            # for kind, lst in declarative_doc.getConnections( env ).items():
            #     tn = typename.getTypename( kind )
            #     spec['relationships'][tn] = { "data": [] }
            #     for name in lst:
            #         key = yaml_doc.create_key( param_set=(kind, name) )
            #         referred = lookup[key]
            #         spec['relationships'][tn]['data'].append( { "type": tn, "id": referred.id })
            try:
                object_dicts[declarative_doc.getKind()].append( spec )
            except KeyError:
                object_dicts[declarative_doc.getKind()] = [spec]
        return { 'source': self._dirname, 'env': env, 'objects': object_dicts }

    # def buildNode( self, name: str, env: str=None, force: bool=False ) -> dict:
    #     declarative_doc: yaml_doc.Doc
    #     if not self._loaded:
    #         self.load( env=env )
    #     if self._loaded != "config" and not force:
    #         output.error( "Loaded config not in format 'config' - reload or specify 'force=True'" )
    #         return None
    #     docs = []
    #     lookup = {}
    #     # build structures
    #     for _, doc_lst in self._docs.items():
    #         for _, declarative_doc in doc_lst.items():
    #             if declarative_doc.isNode():
    #                 docs.append( declarative_doc )
    #                 lookup[declarative_doc.key] = declarative_doc
    #     # create config
    #     object_dicts = {}
    #     for declarative_doc in docs:
    #         if declarative_doc.getName() == name:
    #             spec = { "attributes": declarative_doc.getSpec(), 'connections': {} }
    #             try:
    #                 object_dicts[declarative_doc.getKind()].append( spec )
    #             except KeyError:
    #                 object_dicts[declarative_doc.getKind()] = [spec]
    #     return { 'source': self._dirname, 'env': env, 'objects': object_dicts }

    # def buildConnections( self, env: str, force: bool=False ) -> configuration.Configuration:
    #     if not self._loaded:
    #         self.load( env=env )
    #     if self._loaded != "config" and not force:
    #         output.error( "Loaded config not in format 'config' - reload or specify 'force=True'" )
    #         return None
    #     docs = []
    #     lookup = {}
    #     # build structures
    #     for _, doc_lst in self._docs.items():
    #         for _, declarative_doc in doc_lst.items():
    #             if declarative_doc.isInEnv( env ):
    #                 docs.append( declarative_doc )
    #                 lookup[declarative_doc.key] = declarative_doc
    #     # remove unused documents
    #     while True:
    #         tbd = []
    #         changed = False
    #         for declarative_doc in docs:
    #             if declarative_doc.connectionsReduce2Env( env, lookup ):
    #                 changed = True
    #             if not declarative_doc.isConnected( env ):
    #                 tbd.append( declarative_doc )
    #         if tbd != []:
    #             for entry in tbd:
    #                 try:
    #                     del lookup[entry.key]
    #                 except KeyError:
    #                     pass
    #                 docs.remove( entry )
    #             changed = True
    #         if changed == False:
    #             break
    #     # create config
    #     cfg = configuration.Configuration( None, None, self._run.config )
    #     cfg.comment = f"Declarative ({self._dirname}, env {env})"
    #     for declarative_doc in docs:
    #         #print( declarative_doc.key )
    #         #pp( declarative_doc.getSpec() )
    #         obj = cfg.addElement( declarative_doc.getKind(), id=declarative_doc.id )
    #         spec = { "id": declarative_doc.id, "attributes": declarative_doc.getSpec() }
    #         spec['relationships'] = {}
    #         for kind, lst in declarative_doc.getConnections( env ).items():
    #             tn = lookup.get( element.LOOKUP_TYPENAME, kind )
    #             spec['relationships'][tn] = { "data": [] }
    #             for name in lst:
    #                 key = yaml_doc.create_key( param_set=(kind, name) )
    #                 referred = lookup[key]
    #                 spec['relationships'][tn]['data'].append( { "type": tn, "id": referred.id })
    #         obj.loadData( spec )
    #         #obj = cfg.addElement( declarative_doc.getKind(), declarative_doc.id, { "id": declarative_doc.id, "attributes": declarative_doc.getSpec() } )
    #     return cfg

    def merge( self, cfg: configuration, env: str=None, force: bool=None ):
        if not self._loaded:
            self.load( raw=True )
        if self._loaded != "raw" and not force:
            output.error( "Loaded config not in format 'raw' - reload or specify 'force=True'" )
            return False
        for key, object_map in cfg.objects.items():
            print( key )
            for item in object_map.values():
                if key in ['hostnames', 'nodes', 'network_endpoints', 'routes']:
                    self._mergeGlobalDoc( item, env )
                else:
                    self._mergeConnectedDoc( item, env )
        settings = cfg.settings()
        for key, item in settings.items():
            print( key )
            if not item or key == 'templates':
                continue
            self._mergeBaseDoc( item, env )
        # for item in cfg.vhosts().values():
        #     self._docMerge( item, env )
        # for item in cfg.mappings().values():
        #     self._docMerge( item, env )
        # for item in cfg.backendgroups().values():
        #     self._docMerge( item, env )
        # for item in cfg.certificates().values():
        #     self._docMerge( item, env )
        # for item in cfg.jwks().values():
        #     self._docMerge( item, env )
        # for item in cfg.openapi().values():
        #     self._docMerge( item, env )
        # for item in cfg.graphql().values():
        #     self._docMerge( item, env )
        # for item in cfg.hostnames().values():
        #     self._docMerge( item, env )
        # for item in cfg.icap().values():
        #     self._docMerge( item, env )
        # for item in cfg.iplists().values():
        #     self._docMerge( item, env )
        # for item in cfg.kerberos().values():
        #     self._docMerge( item, env )
        # for item in cfg.apipolicy().values():
        #     self._docMerge( item, env )
        # for item in cfg.networkendpoints().values():
        #     self._docMerge( item, env )
        # for item in cfg.nodes().values():
        #     self._docMerge( item, env )

    def findDoc( self, kind: str, name: str ) -> Union[basedoc.BaseDoc,connecteddoc.ConnectedDoc]:
        key = basedoc.create_key( param_set=(kind, name) )
        try:
            return self._map[key][1]
        except KeyError:
            return None
    
    def inheritanceTree( self ) -> dict:
        r = {}
        for map in self._docs.values():
            for key, doc in map.items():
                if doc.isConnected( self._env ):
                    r[key] = doc.inheritanceTree( doc )
        return r
    
    def _mergeConnectedDoc( self, item: element.ModelElement, env: str=None ):
        doc = connecteddoc.ConnectedDoc( self.next_id, base_object=item, env=env, dconfig=self )
        self._mergeDoc( doc, env )

    def _mergeGlobalDoc( self, item: element.BaseElement, env: str=None ):
        doc = globaldoc.GlobalDoc( self.next_id, base_object=item, env=env, dconfig=self )
        self._mergeDoc( doc, env )

    def _mergeBaseDoc( self, item: element.BaseElement, env: str=None ):
        doc = basedoc.BaseDoc( self.next_id, base_object=item, env=env, dconfig=self )
        self._mergeDoc( doc, env )

    def _mergeDoc( self, doc, env ):
        fname: str
        base: basedoc.BaseDoc
        self.next_id += 1
        try:
            fname = self._map[doc.key][0]
        except KeyError:
            fname = None
        if not fname:
            try:
                self._docs[None][doc.key] = doc
            except KeyError:
                self._docs[None] = {doc.key: doc}
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
    
