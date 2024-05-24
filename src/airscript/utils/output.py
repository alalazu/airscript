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

from colorama import Fore, Style


def error( msg, end="\n" ):
    print( Fore.RED + "Error: %s" % (msg,) + Style.RESET_ALL, end=end )

def warn( msg, end="\n" ):
    print( Fore.YELLOW + "Warning: %s" % (msg,) + Style.RESET_ALL, end=end )

def info( msg, end="\n" ):
    print( Fore.GREEN + msg + Style.RESET_ALL )

def label( msg, end="\n" ):
    print( Fore.WHITE + msg + Style.RESET_ALL )

def msg( msg, end="\n" ):
    print( Fore.CYAN + msg + Style.RESET_ALL )

def getLengthsColumns( lst: list, columns: list[int]=None, lengths: list=[] ) -> list[int]:
    try:
        cols = len( columns )
    except TypeError:
        cols = len( lst[0] )
    if lengths == []:
        for idx in range( cols ):
            try:
                lengths.append( columns[idx] )
            except (TypeError, IndexError):
                lengths.append( 0 )
    for entry in lst:
        if isinstance( entry, list ):
            items = entry
        else:
            items = entry.values()
        for idx in range( cols ):
            try:
                lengths[idx] = max( lengths[idx], len( str( items[idx] )))
            except TypeError:
                pass
    return lengths

def getLengthsIdName( lst ):
    lengths = getLengthsColumns( [x[1] for x in lst], [0,4] )
    return { 'id': lengths[0], 'name': lengths[1] }
    
def listIdName( lst ):
    len = getLengthsIdName( lst )
    for entry in lst:
        print( "%s%*s%s: %s%-*s%s" % (Fore.CYAN, len['id'], entry[0], Style.RESET_ALL,
                                      Fore.GREEN, len['name'], entry[1].name, Style.RESET_ALL) )

def listAttributes( lst, objects, paths, id_left=False ):
    if not type( objects ) == dict:
        error( "Wrong object type: %s" % (type(objects),) )
        return
    if not type( paths ) == list:
        error( "'paths' must be a list" )
        return
    if not type( lst ) == list:
        error( "'lst' must be a list" )
        return
    len_id = 0
    len_name = 0
    len_attributes={}
    attributes={}
    for entry in lst:
        attributes[entry[0]] = {}
        len_id = max( len_id, len( str( entry[0] )))
        len_name = max( len_name, len( entry[1].name ))
        for idx in range( len( paths )):
            value = objects[entry[0]].get( paths[idx] )
            try:
                len_attributes[idx] = max( len_attributes[idx], len( str( value )))
            except KeyError:
                len_attributes[idx] = len( str( value ))
            attributes[entry[0]][idx] = str( value )
    len_name = min( len_name, 20 )
    for entry in lst:
        value = ""
        for idx in range( len( attributes[entry[0]] )):
            value += "%-*s " % (len_attributes[idx], attributes[entry[0]][idx])
        if id_left == False:
            print( "%s%*s%s: %s%-*.*s %s%s%s" % (Fore.CYAN, len_id, entry[0], Style.RESET_ALL,
                                                 Fore.GREEN, len_name, len_name, entry[1].name,
                                                 Fore.WHITE, value, Style.RESET_ALL) )
        else:
            print( "%s%-*s%s: %s%-*.*s %s%s%s" % (Fore.CYAN, len_id, entry[0], Style.RESET_ALL,
                                                 Fore.GREEN, len_name, len_name, entry[1].name,
                                                 Fore.WHITE, value, Style.RESET_ALL) )


"""
"""

def maxlen( lst, attrname ):
    length = 0
    for entry in lst:
        print( "%s" % (entry,) )
        if length < len( getattr( lst, attrname )):
            length = len( getattr( lst, attrname ))
    return length

