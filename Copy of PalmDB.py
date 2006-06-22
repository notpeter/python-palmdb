Have to break this file into a few pieces:

*XML utilities
*Base plugin code
*Main body code (IE PalmDB.py that holds just the basics and __main__)
File derivative code?
*Plugins directory
*PDB processing code


#
#  $Id: PalmDB.py,v 1.11 2005/12/13 03:12:12 rprice Exp $
#
# Copyright 2006 Rick price <rick_price@users.sourceforge.net>
# This Python library is used to read/write Palm PDB files
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

#  This code was based on code written by Rob Tillotson <rob@pyrite.org>, but has been heavily
#  modified so that it is now basically code I have written.

# This file includes changes made (including better naming, comments and design changes) by Mark Edgington, many thanks Mark.


"""PRC/PDB file I/O in pure Python.

    This module allows access to Palm OS(tm) database files on the desktop 
    in pure Python. It is as simple as possible without (hopefully) being 
    too simple. As much as possible Python idioms have been used to make
    it easier to use and more versatile.
"""

__version__ = '$Id: PalmDB.py,v 1.11 2005/12/13 03:12:12 rprice Exp $'

__copyright__ = 'Copyright 2006 Rick Price <rick_price@users.sourceforge.net>'

#
# DBInfo structure:
#
#   int more
#   unsigned int flags
#   unsigned int miscflags
#   unsigned long type
#   unsigned long creator
#   unsigned int version
#   unsigned long modnum
#   time_t createDate, modifydate, backupdate
#   unsigned int index
#   char name[34]
#
#
# DB Header:
#   32 name
#   2  flags
#   2  version
#   4  creation time
#   4  modification time
#   4  backup time
#   4  modification number
#   4  appinfo offset
#   4  sortinfo offset
#   4  type
#   4  creator
#   4  unique id seed (garbage?)
#   4  next record list id (normally 0)
#   2  num of records for this header
#   (maybe 2 more bytes)
#
# Resource entry header: (if low bit of attr = 1)
#   4  type
#   2  id
#   4  offset
#
# record entry header: (if low bit of attr = 0)
#   4  offset
#   1  attributes
#   3  unique id
#
# then 2 bytes of 0
#
# then appinfo then sortinfo
#

import datetime,time
import sys, os, stat, struct

RESOURCE_ENTRY_SIZE = 10  # size of a resource entry
RECORD_ENTRY_SIZE = 8 # size of a record entry

PILOT_TIME_DELTA = 2082844800L

flagResource = 0x0001
flagReadOnly = 0x0002
flagAppInfoDirty = 0x0004
flagBackup = 0x0008
flagOpen = 0x8000
# 2.x
flagNewer = 0x0010
flagReset = 0x0020
#
flagExcludeFromSync = 0x0080

attrDeleted = 0x80
attrDirty = 0x40
attrBusy = 0x20
attrSecret = 0x10
attrArchived = 0x08

def attr2string( x):
    result = ''
    if x & attrDeleted:
        result += 'delete/'
    if x & attrDirty:
        result += 'dirty/'
    if x & attrBusy:
        result += 'busy/'
    if x & attrSecret:
        result += 'secret/'
    result = result + str(x & 0xf)
    return result


def _(x):
    return x

# Class to encapsulate PDB file plugin
class PDBFilePlugin:
	#+++ FIX THIS +++ This HAS to be redefined in child classes otherwise things won't work
	def getPDBCreatorID():
		return None

	#+++ FIX THIS +++ this will be called before any of the other functions are called
	def setVersion(version):
		pass

	def createCategoriesObject(self,raw):
		return Categories(raw)

        def palmDatabaseInfoObject(self,raw):
		return PalmDatabaseInfo(raw)

	def getDatabaseRecordFactory(self):
		return None # +++ FIX THIS +++ obviously this needs to be fixed

PDBPlugins={}
def registerPDBPlugin(PDBFilePluginClass):
	type=PDBFilePluginClass.getPDBCreatorID()
	if type == None:
		#+++ FIX THIS +++ need to throw a "what are you trying to do exception"
		pass
	PDBPlugins[type]=PDBFilePluginClass)

def select PDBPlugin(CreatorID):
#+++ FIX THIS +++ implement
# if we cannot find an appropriate plugin, default to one that can handle any type
	pass

#
#--------- Register Standard Plugins that come with Library ---------
#

#import ProgectPDBPlugin
#import StandardNotepadPDBPlugin

#registerPDBPLugin(ProgectPDBPlugin.plugin)
#registerPDBPLugin(StandardNotepadPDBPlugin.plugin)

#
#--------- Register Standard Plugins that come with Library ---------
#


def defaultRecordFactory(attributes,id,category):
    '''
    Default factory function for creating records.

    This function is the default factory used by PalmDatabase to create new records.
    attributes are the record attributes like (deleted,dirty, etc), id is the resource id, 
    category is the category of the record. The PalmDatabase code will call setRaw() on
    this object to set the raw data, and getRaw() to retrieve the raw data.
    '''
    return PRecord(attributes,id,category)

