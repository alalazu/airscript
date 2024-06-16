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
from airscript.declarative import basedoc, connecteddoc, defaults, globaldoc
from airscript.model import configuration
from airscript.utils import output, runinfo, templating
from pyAirlock.common import lookup


class DConfig( object ):
    def __init__( self, run_info: runinfo.RunInfo=None, dname: str=None ):
        self._run = run_info
        if dname:
            self._dirname = dname
        else:
            self._dirname = self._run.config.get( 'declarative.config-dir', 'declarative' )
        if not os.path.isdir( self._dirname ):
            os.mkdir( self._dirname )
        defaults.init( self._run.config.get( 'declarative.defaults-dir' ))
        self._params_templating = {}
        infile = self._run.config.get( 'declarative.templating.settings-file' )
        if infile:
            try:
                with open( infile, "r" ) as fp:
                    self._params_templating = yaml.safe_load( fp )
            except FileNotFoundError:
                pass
            except yaml.scanner.ScannerError:
                pass
        self._reset()
    
    def load( self, env: str=None, raw: bool=False ):
        renderer = templating.TemplateHandler( cfg=self._run.config, raw=raw )
        self._reset()
        for fname in glob.glob( "*.yaml", root_dir=self._dirname ):
            print( f"- {fname}" )
            self._docs[fname] = {}
            try:
                for doc in yaml.safe_load_all( renderer.renderFile( os.path.join( self._dirname, fname ), self._params_templating )):
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
                    self._addDoc2Docs( declarative_doc, fname )
                    # self._docs[fname][declarative_doc.key] = declarative_doc
                    # self._map[declarative_doc.key] = (fname, declarative_doc)
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
                fname = self._run.config.get( 'declarative.export-file', 'all.yaml' )
            if fname[0] == '/':
                outfile = fname
            else:
                outfile = os.path.join( self._dirname, fname )
            print( f"- {outfile}" )
            with open( outfile, "w" ) as fp:
                yaml.dump_all( export_docs, stream=fp )
        return True
    
    def saveByMapping( self, env: str=None, force: bool=False ) -> bool:
        if not self._loaded:
            self.load( raw=True )
        if self._loaded != "raw" and not force:
            output.error( "Loaded config not in format 'raw' - reload or specify 'force=True'" )
            return False
        if None in self._docs:
            if env == None:
                env = 'default'
            doc: connecteddoc.ConnectedDoc
            for key, doc in self._docs[None].items():
                if doc.getKind() != 'Mapping':
                    continue
                appElements = self._getAppElementList( doc, env )
                if len( appElements ) < 2:
                    fname = self._fnameFromKind( doc.getKind() )
                    self._addDoc2Docs( doc, f"{fname}.yaml".lower() )
                else:
                    for item in appElements:
                        self._addDoc2Docs( item, f"{doc.getName()}.yaml".lower() )
            for key, doc in self._docs[None].items():
                if self._map[doc.key][0] == None:
                    fname = self._fnameFromKind( doc.getKind() )
                    self._addDoc2Docs( doc, f"{fname}.yaml".lower() )
            del self._docs[None]
        self.save( force=force )
    
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
            spec = { "attributes": declarative_doc.getSpec( env ) }
            if declarative_doc.connectionsSupported():
                spec['connections'] = declarative_doc.getConnections4Env( env )
            try:
                object_dicts[declarative_doc.getKind()].append( spec )
            except KeyError:
                object_dicts[declarative_doc.getKind()] = [spec]
        return { 'source': self._dirname, 'env': env, 'objects': object_dicts }

    def merge( self, cfg: configuration, env: str=None, force: bool=None ):
        if not self._loaded:
            self.load( raw=True )
        if self._loaded != "raw" and not force:
            output.error( "Loaded config not in format 'raw' - reload or specify 'force=True'" )
            return False
        item: element.ModelElement
        for key, object_map in cfg.objects.items():
            for item in object_map.values():
                if item.id < 0:
                    continue
                if key in ['hostnames', 'nodes', 'network_endpoints', 'routes']:
                    self._mergeGlobalDoc( item, env )
                else:
                    self._mergeConnectedDoc( item, env )
        for key, item in cfg.settings().items():
            if not item or key == 'templates':
                continue
            self._mergeBaseDoc( item, env )

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
    
    def _addDoc2Docs( self, doc: basedoc.BaseDoc, fname: str ):
        try:
            self._docs[fname][doc.key] = doc
        except KeyError:
            self._docs[fname] = {doc.key: doc}
        self._map[doc.key] = (fname, doc)

    def _fnameFromKind( self, kind: str ) -> str:
        if kind[:5] == 'Route':
            return '_route'
        elif kind[:4] == 'JWKS':
            return '_jwks'
        return f"_{kind}"

    def _countDocs( self ) -> int:
        counts = { '': 0 }
        for fname, doc_lst in self._docs.items():
            counts[''] += len( doc_lst )
            try:
                counts[fname] += len( doc_lst )
            except KeyError:
                counts[fname] = len( doc_lst )
        return counts

    def _mergeConnectedDoc( self, item: element.ModelElement, env: str=None ):
        doc = connecteddoc.ConnectedDoc( self.next_id, base_object=item, env=env, dconfig=self )
        self._mergeDoc( doc, env )

    def _mergeGlobalDoc( self, item: element.BaseElement, env: str=None ):
        doc = globaldoc.GlobalDoc( self.next_id, base_object=item, env=env, dconfig=self )
        self._mergeDoc( doc, env )

    def _mergeBaseDoc( self, item: element.BaseElement, env: str=None ):
        doc = basedoc.BaseDoc( self.next_id, base_object=item, env=env, dconfig=self )
        self._mergeDoc( doc, env )

    def _mergeDoc( self, doc: basedoc.BaseDoc, env ):
        fname: str
        base: basedoc.BaseDoc
        self.next_id += 1
        try:
            fname = self._map[doc.key][0]
        except KeyError:
            fname = None
            # fname = f"{doc.getKind()}.yaml".lower()
        if not fname:
            self._addDoc2Docs( doc, fname )
        else:
            try:
                base = self._docs[fname][doc.key]
            except KeyError:
                base = None
            if base:
                base.update( doc, env=env )
            else:
                self._addDoc2Docs( doc, fname )
                return

    def _getAppElementList( self, doc: connecteddoc.ConnectedDoc, env: str ) -> list:
        r = []
        connections = doc.getConnections4Env( env )
        for reltype, names in connections.items():
            if len( names ) > 1:
                return []
            connected_doc = self.findDoc( lookup.get( element.LOOKUP_TYPENAME2KIND, lookup.get( lookup.RELTYPE2NAME, reltype )), names[0] )
            if connected_doc:
                if doc.getConnectionOrderNr() > connected_doc.getConnectionOrderNr():
                    r += self._getAppElementList( connected_doc, env )
        return r + [doc]

    def _reset( self ):
        self._map = {}
        self._docs = {}
        self.next_id = 1
        self._loaded = None
        self._env = None
    
