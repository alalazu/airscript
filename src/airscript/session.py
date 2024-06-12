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
from pyAirlock import gateway
from pyAirlock.common import exception, log


SESSION_NAME_DEFAULT = "default"

class GatewaySession( object ):
    def __init__( self, name: str, gw, run_info ):
        """
        A single REST API session with an Airlock Gateway.
        
        name - short name
        gw - Airlock Gateway
        """
        self.name = name
        self.session = None
        self._gw = gw
        self._run_info = run_info
        self._cert = None
        self._tls_verify = True
        self._version = None
        self._nodename = None
        self._log = log.Log( self.__module__, run_info )
        self.configs = None
    
    def getName( self ) -> str:
        """ Return short name. """
        return self.name
    
    def getGateway( self ) -> gateway.Session:
        """ Return Airlock Gateway object """
        return self._gw
    
    def connect( self, label: str=None ) -> bool:
        """
        Establish session with Airlock Gateway.
        
        Parameters:

        * `label`: pass in a name under which connection can be retrieved, default is SESSION_NAME_DEFAULT.

        Returns: connection handle on success or None on failure
        """
        conn = gateway.Session( self._gw.getHost(), self._gw.getKey(), name=label, run_info=self._run_info )
        if self._cert:
            conn.setCertificate( certfile=self._cert['file'], pem=self._cert['pem'] )
        conn.setTLSVerify( self._tls_verify )
        try:
            if conn.connect() == False:
                return False
        except exception.AirlockConnectionError:
            return False
        conn.post( "/configuration/configurations/load-empty-config", expect=[204] )
        self._log.verbose( "Connected to '%s'" % (self.name,) )
        self._version = conn.getVersion()
        self._nodename = conn.getNodename()
        self.session = conn
        return True
    
    def disconnect( self ):
        """ Disconnect from Airlock Gateway, closing administrator session. """
        if self.session:
            self.session.disconnect()
            self.session = None
        self._version = None
        self._nodename = None
        self.configs = None
        cache.cacheRemoveGateway( self.name )

    def keepalive( self ):
        if self.session:
            self.session.keepalive()
    
    def setCertificate( self, certfile: str=None, pem: str=None ):
        """
        Define CA certificate file which signed Airlock Gateway's Config Center certificate.
        
        If Airlock Gateway Config Center uses a certificate not issued by any of the
        well-known certificate authorities (CAs) maintained in /etc/ssl/certs,
        the appropriate signing certificate must be specified here.
        """
        self._cert = {'file': certfile, 'pem': pem}
    
    def setTLSVerify( self, verify ):
        """
        Suppress server certificate checking.
        
        Passing in verify=False completely disables server certificate checking.
        While this may be easy for self-signed Airlock Gateway Config Center
        certificates, it should not be used in production.
        
        For an even stronger version, passing in verify=None also suppresses
        any warning messages related to the certificate.
        """
        self._tls_verify = verify
    
    def getConfigurations( self ):
        """ Retrieve all configurations from Airlock Gateway and store in attribute .configs """
        self.configs = {}
        resp = self.session.get( "/configuration/configurations" )
        for c in resp.json()['data']:
            self.configs[c['id']] = configuration.Configuration( c, self.session, self._run_info.config )
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
        if self.configs == None:
            self.getConfigurations()
        self.session.post( "/configuration/configurations/load-empty-config", expect=[204] )
        self.configs['_new'] = configuration.Configuration( None, self.session, self._run_info.config )
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
        resp = self.session.upload( "/configuration/configurations/import", content='application/zip', files=files )
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
        resp = self.session.delete( "/configuration/configurations/%s" % (cfg.id,) )
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
        return self.session.status()

    def failoverState( self ):
        """
        Retrieve failover state
        
        Returns:
        * active
        * passive
        * standalone
        * offline
        """
        return self.session.failoverState()
    
