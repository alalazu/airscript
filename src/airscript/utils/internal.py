"""
AirScript: Airlock (Gateway) Configuration Script

Copyright (c) 2019-2024 Urs Zurbuchen <urs.zurbuchen@ergon.ch>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

import re
from operator import attrgetter, itemgetter
from typing import Union

def itemgetter_lc_0( obj ) -> str:
    """
    Return lowercased operator.itemgetter() keys
    """
    x = str( itemgetter(0)(obj) )
    return x.lower()

def itemgetter_lc_1( obj ) -> str:
    """
    Return lowercased operator.itemgetter() keys
    """
    x = str( itemgetter(1)(obj) )
    return x.lower()

def itemgetter_lc_id( obj ) -> str:
    """
    Return lowercased id
    """
    x = str( attrgetter('id')(obj) )
    return x.lower()

def itemgetter_lc_name( obj ) -> str:
    """
    Return lowercased name
    """
    x = str( attrgetter('name')(obj) )
    return x.lower()

def itemgetter_id( obj ) -> int:
    """
    Return operator.itemgetter() keys as integer
    """
    try:
        return int( itemgetter(0)(obj) )
    except ValueError:
        return 0

def itemgetter_nr_1( obj ) -> int:
    """
    Return operator.itemgetter() keys as integer
    """
    try:
        return int( itemgetter(1)(obj) )
    except ValueError:
        return 0

def collectKeyNames( dictionary, path="", level=1 ) -> list[str|int]:
    lst = []
    for key, value in dictionary.items():
        if type( value ) is dict:
            lst.extend( collectKeyNames( value, path + key + '.', level +1 ))
            lst.append( key )
        else:
            lst.append( "%s%s" % (path,key) )
            if path != "":
                lst.append( key )
    return lst

def itemList( objects: dict, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, sort: str=None ) -> dict:
    """
    Get list of objects
    - name: regexp of name(s) to match
    - ids: list of ids to return
    - filter: dict of attribute conditions to match: {op: =|>|<|>=|<=|eq|gt|lt|ge|le|in, attribute: value}, default for op is eq

    Returns dict of dicts
    """
    if name:
        re_name = re.compile( f"^{name}$" )
    else:
        re_name = None
    if id:
        try:
            ids.append( id )
        except AttributeError:
            ids = [id]
    if ids:
        ids = [str(x) for x in ids]
    result = {}
    idx = -1
    for k,v in objects.items():
        if isinstance( v, list ):
            for item in v:
                if _itemFilter( item, id=id, name=name, ids=ids, filter=filter, re_name=re_name ):
                    result[idx] = v
                    idx -= 1
        elif _itemFilter( v, id=id, name=name, ids=ids, filter=filter, re_name=re_name ):
            result[k] = v
    if sort:
        if sort == 'name':
            func = itemgetter_lc_name
        else:
            func = itemgetter_id
        # return sorted( (v for v in result.items() if not v[1].isDeleted()), key=func )
        r = {}
        s = sorted( (v for v in result.values() if not v.isDeleted()), key=func )
        for entry in s:
            r[entry.id] = entry
        return r
    else:
        return result

def _itemFilter( item, id: Union[str|int]=None, name: str=None, ids: list[str|int]=None, filter: dict=None, re_name=None ) -> bool:
    if item.isDeleted():
        return False
    if name and not re_name.match( item.name ):
        return False
    if ids and not item.id in ids:
        return False
    if filter and not item.filter( filter ):
        return False
    return True
