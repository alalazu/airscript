# AirScript: Airlock (Gateway) Configuration Script
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

"""
AirScript Gateway Session Keep-Alive.

Keeps session to Gateway alive by regularly sending idempotent requests.
"""

import datetime
import threading
import time

from colorama import Fore, Style

from airscript import session
from airscript.utils import output
from pyAirlock.common import exception, log

class KeepAlive( threading.Thread ):
    def __init__( self ):
        super().__init__()
        self._sessions = []
        self.daemon = True
        self._log = log.Log( self.__module__ )
        self._signal = threading.Event()
    
    def add( self, conn: session.GatewaySession, interval: int=300 ):
        self._sessions.append( KeepAliveSession( conn, interval ))
        if not self.is_alive():
            self.start()
        elif len( self._sessions ) == 1:
            self.signal()
    
    def list( self ):
        out = log.Log( f"{__name__}.list" )
        rows = []
        for sess in self._sessions:
            rows.append( [sess.getName(), sess.getLast(), sess.interval, sess.count, sess.errors] )
        lengths = output.getLengthsColumns( rows )
        for row in rows:
            out.info( "%s%-*s%s: %s%*s%s %s%*s%s %s%*s%s %s%*s%s" % 
                      (Fore.CYAN, lengths[0], row[0], Style.RESET_ALL,
                       Fore.GREEN, lengths[1], row[1], Style.RESET_ALL,
                       Fore.WHITE, lengths[2], row[2], Style.RESET_ALL,
                       Fore.WHITE, lengths[3], row[3], Style.RESET_ALL,
                       Fore.RED, lengths[4], row[4], Style.RESET_ALL,
                      ) )

    def remove( self, conn ):
        idx = 0
        while idx < len( self._sessions ):
            if self._sessions[idx].conn == conn:
                break
            idx += 1
        try:
            if idx < len( self._sessions ):
                del self._sessions[idx]
                return True
        except UnboundLocalError:
            pass
        return False
    
    # def list( self ):
    #     return self._sessions

    def signal( self ):
        self._signal.set()
    
    def run( self ):
        self._log.debug( "KeepAlive: worker thread started" )
        self._signal.clear()
        while True:
            next = 0
            for sess in self._sessions:
                now = int( time.time() )       # in loop because keepalive request may take some time
                if sess.next <= now:
                    # send keepalive request
                    sess.keepalive()
                    sess.next = now + sess.interval
                if next == 0:
                    next = sess.next
                elif next > sess.next:
                    next = sess.next
            if next > 0:
                seconds = next - int( time.time() )
                if seconds > 0:
                    if self._signal.wait( seconds ):
                        # signal received
                        break
            else:
                self._log.debug( f"KeepAlive: wait for gateway in list" )
                self._signal.wait()
                self._signal.clear()
        self._log.debug( "KeepAlive: worker thread terminated" )


class KeepAliveSession( object ):
    def __init__( self, conn: session.GatewaySession, interval: int=300 ):
        self.conn = conn
        self.interval = interval
        self.next = int( time.time() ) + self.interval
        self.last = 0
        self.count = 0
        self.errors = 0
    
    def __repr__( self ):
        return str( { "name": self.getName(), "interval": self.interval, "next": self.next, "last": self.last, "count": self.count, "errors": self.errors } )
    
    def getName( self ):
        return self.conn.getName()
    
    def getLast( self ):
        if self.last == 0:
            return None
        return datetime.datetime.fromtimestamp( self.last )
    
    def getNext( self ):
        return datetime.datetime.fromtimestamp( self.next )
    
    def getConnection( self ):
        return self.conn
    
    def keepalive( self ):
        try:
            if self.conn:
                self.conn.keepalive()
                self.last = int( time.time() )
        except exception.AirlockError:
            self.errors += 1
        self.count += 1
    
