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

NAME = 'AirScript'
VERSION = '6'
URL = 'http://airscript.sourceforge.net/'
DESC = 'Airlock Gateway Configuration Script Engine'
LONGDESC = '''AirScript is your scriptable Python interface to the Airlock Gateway
configuration REST API, providing access to configuration objects,
virtual hosts, mappings etc.

AirScript can be used interactively using its console which allows
you to easily interact with the REST API. it can also be used for
more complex operations for which a script has previously been created,
e.g. migrating an applications configuration from a test to a production
environment.
'''
PLATFORM = 'Developed and tested on Linux, others might work'
