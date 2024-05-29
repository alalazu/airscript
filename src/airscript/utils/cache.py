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

import time


"""
Global caching variables
"""

_cachedTypes = {}
_cachedAttributeKeyNames = []
_cachedAttributeKeyPaths = []
_cachedAttributeKeysMap = {}


def isCached( gateway_name, typename ):
    global _cachedTypes
    entry = _getCacheGatewayEntry( gateway_name )
    if entry == None:
        return False
    if typename in entry:
        return True
    return False

def cacheAttributeKeys( gateway_name, typename, keyList ):
    for key in keyList:
        pos = key.find( "." )
        if pos >= 0:
            if not key in _cachedAttributeKeyPaths:
                _cachedAttributeKeyPaths.append( key )
        else:
            if not key in _cachedAttributeKeyNames:
                _cachedAttributeKeyNames.append( key )
        if not key in _cachedAttributeKeysMap.keys():
            _cachedAttributeKeysMap[key] = { gateway_name: [typename] }
        else:
            try:
                if not typename in _cachedAttributeKeysMap[key][gateway_name]:
                    _cachedAttributeKeysMap[key][gateway_name].append( typename )
            except KeyError:
                _cachedAttributeKeysMap[key][gateway_name] = [typename]
    entry = _getCacheGatewayEntry( gateway_name )
    if entry == None:
        entry = {}
        _cachedTypes[gateway_name] = entry
    entry[typename] = time.time()

def getAttributeKeyNames():
    return _cachedAttributeKeyNames

def getAttributeKeyPaths():
    return _cachedAttributeKeyPaths

def cacheRemoveGateway( gateway_name ):
    entry = _getCacheGatewayEntry( gateway_name )
    if entry == None:
        return
    for key_map in _cachedAttributeKeysMap.items():
        if not gateway_name in key_map[1].keys():
            continue
        del key_map[1][gateway_name]
        if len( key_map[1] ) == 0:
            ''' last entry - remove from key name cache '''
            pos = key_map[0].find( "." )
            if pos >= 0:
                idx = _cachedAttributeKeyPaths.index( key_map[0] )
                del _cachedAttributeKeyPaths[idx]
            else:
                idx = _cachedAttributeKeyNames.index( key_map[0] )
                del _cachedAttributeKeyNames[idx]

def _getCacheGatewayEntry( gateway_name ):
    try:
        return _cachedTypes[gateway_name]
    except KeyError:
        return None

