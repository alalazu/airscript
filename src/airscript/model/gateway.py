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


from airscript.model import configuration
from airscript.utils import internal
from airscript.utils import cache
from pyAirlock.common import log
from pyAirlock.gateway.config_api import gateway as gw_api
from pyAirlock.common import exception


class Gateway( object ):
    def __init__( self, name: str, hostname: str, key: str, run_info, peer: str=None, group: str=None ):
        """
        Initialise Gateway instance.
        
        name - short name
        hostname - FQDN for Airlock Gateway Config Center
        key - API key
        """
        self.name = name
        self.peer = peer
        self.group = group
        self.version = None
        self.nodename = None
        self.mgmt = False
        self._run_info = run_info
        self._conn = gw_api.GW( name, hostname, key, self._run_info )
        self._log = log.Log( self.__module__, run_info )
        self.configs = None
    
    def getName( self ) -> str:
        """ Return short name. """
        return self.name
    
    def getHost( self ) -> str:
        """ Return FQDN. """
        return self._conn.getHost()
    
    def getKey( self ) -> str:
        """ Return API key. """
        return self._conn.getKey()
    
    def getConnection( self ):
        return self._conn
    
    def getVersion( self ) -> str:
        """ Return Gateway version """
        return self.version
    
    def getPeer( self ) -> str:
        return self.peer
    
    def getGroup( self ) -> str:
        return self.group
    
    def isPeerOf( self, peer: str ) -> bool:
        if self.peer == peer:
            return True
        return False
    
    def isMemberOf( self, group: str ) -> bool:
        if self.group == group:
            return True
        return False
    
    def setCertificate( self, certfile: str=None, pem: str=None ):
        """
        Define CA certificate file which signed Airlock Gateway's Config Center certificate.
        
        If Airlock Gateway Config Center uses a certificate not issued by any of the
        well-known certificate authorities (CAs) maintained in /etc/ssl/certs,
        the appropriate signing certificate must be specified here.
        """
        self._conn.setCertificate( certfile=certfile, pem=pem )
    
    def setTLSVerify( self, verify ) -> bool:
        """
        Suppress server certificate checking.
        
        Passing in verify=False completely disables server certificate checking.
        While this may be easy for self-signed Airlock Gateway Config Center
        certificates, it should not be used in production.
        
        For an even stronger version, passing in verify=None also suppresses
        any warning messages related to the certificate.
        """
        return self._conn.setTLSVerify( verify )
    
    def isActive( self ) -> bool:
        """
        Check if Airlock Gateway is active node in an active/passive cluster
        
        Returns:
        * True if node is active or if node is not in an active/passive cluster
        * False if node is the passive partner
        """
        return self._conn.isActive()
    
    def connect( self ) -> bool:
        """ Establish session with Airlock Gateway. """
        try:
            if self._conn.connect() == False:
                return False
            self._log.verbose( "Connected to '%s'" % (self.name,) )
            self.version = self._conn.getVersion()
            self.nodename = self._conn.getNodename()
            return True
        except exception.AirlockConnectionError:
            return False
    
    def disconnect( self ):
        """ Disconnect from Airlock Gateway, closing administrator session. """
        self._conn.disconnect()
        self.configs = None
        cache.cacheRemoveGateway( self.name )

    def getConfigurations( self ):
        """ Retrieve all configurations from Airlock Gateway and store in attribute .configs """
        self.configs = {}
        resp = self._conn.get( "/configuration/configurations" )
        for c in resp.json()['data']:
            self.configs[c['id']] = configuration.Configuration( c, self._conn, self._run_info.config )
        self._log.verbose( "%d configurations available - list using .configs or .listConfigs()" % (len( self.configs ),) )
    
    def listConfigurations( self ):
        """
        List all Airlock Gateway configurations.
        
        Sample call: gws['my-waf'].listConfigurations()
        """
        if self.configs == None:
            self.getConfigurations()
        return sorted( self.configs.items(), key=internal.itemgetter_id, reverse=True )
    
    def configurationFindActive( self ):
        """
        Load all Airlock Gateway configurations and return the currently active one.
        
        Returns None if Airlock Gateway has no active configuration.
        """
        if self.configs == None:
            self.getConfigurations()
        for c in self.configs.values():
            if c.type == 'CURRENTLY_ACTIVE':
                return c
        return None
    
    def configurationCreate( self ):
        """
        Create a new empty configuration.
        """
        self._conn.post( "/configuration/configurations/load-empty-config", expect=[204] )
        self.configs['_new'] = configuration.Configuration( None, self._conn, self._run_info.config )
        return self.configs['_new']
    
    def configurationImport( self, fname ):
        """
        Import Airlock Gateway configuration.
        
        'fname' is the filename of a valid Airlock Gateway configuration, in zipped format,
        which you previously downloaded using, e.g.:
        
        gws['my-waf'].configurationFindActive().export()
        
        NEVER try to manually create an Airlock Gateway configuration!
        """
        files = { 'file': open( fname, 'rb' ) }
        resp = self._conn.upload( "/configuration/configurations/import", content='application/zip', files=files )
        if resp.status_code != 200:
            self._log.error( "Import failed: %s (%s)" % (resp.status_code,resp.text) )
            return False
        if self.configs != None:
            self.getConfigurations()
        return True
    
    def configurationDelete( self, cfg ):
        """ Remove configuration from Airlock Gateway. """
        if type( cfg ) != configuration.Configuration:
            self._log.error( "This is not a configuration but %s" % (type(cfg),) )
            return False
        cfg.delete()
        resp = self._conn.delete( "/configuration/configurations/%s" % (cfg.id,) )
        if resp.status_code != 204:
            self._log.error( "Deletion failed: %s (%s)" % (resp.status_code,resp.text) )
            return False
        try:
            del self.configs[cfg.id]
        except KeyError:
            self._log.error( "No such configuration" )
        return True
    
    def status( self ) -> dict:
        """
        Retrieve node status

        Returns: dict according to [API documentation](https://docs.airlock.com/gateway/latest/rest-api/config-rest-api.html#get-node-status)
        """
        return self._conn.status()

    def failoverState( self ):
        """
        Retrieve failover state
        
        Returns:
        * active
        * passive
        * standalone
        * offline
        """
        return self._conn.failoverState()
    
