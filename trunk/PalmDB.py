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

import PalmDatabase

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
	PDBPlugins[type]=PDBFilePluginClass

def getPDBPlugin(CreatorID):
	pass
#+++ FIX THIS +++ implement
# if we cannot find an appropriate plugin, default to one that can handle any type

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

def filterForRecordsByCategory(records,category=None):
    '''
    This function lets you filter a list of records by category.

    When passed a list of records, and the appropriate category it will
    return a list of records that match the criteria.  When category=None,
    all records are returned.
    '''
    return filter(lambda x : (category == None or x.category == category), records)

def filterForModifiedRecords(records):
    '''
    This function returns a list of modified records from a list of records.

    When passed a list of records, this function will return a list of the modified records.
    '''
    return filter(lambda x : x.attr & attrModified, records)

def filterOutDeletedRecords(records):
    '''
    This function returns a list of non-deleted records from a list of records.

    When passed a list of records, this function will return a list of the non-deleted records.
    '''
    return filter(lambda x : x.attr & attrDeleted, records)

def resetRecordDirtyFlags(records):
    '''
    This function resets the dirty bit on a list of records.

    When passed a list of records, this function will reset the dirty bit on each record.
    '''
    for record in records:
        record.attr = record.attr & ~attrDirty

class File(PalmDatabase.PalmDatabase):
    """
    Class for directly reading from / writing to PDB files.

    Arguments are as follows:

    fileName:       name of file to be read/written
    
    recordFactory:  a function which is called to return record objects during
                    loading of file.  Optional; usually not necessary to specify.

    read:           Attempt to load the data contained in the specified file.
                    Should be set to False if creating a new file which does
                    not yet exist.

    writeBack:      When this is set to True, deleting the object will cause 
                    any changes to the database to be written back to the most
                    recently specified file (specified for reading or writing).
    """
    
    def __init__(self, fileName=None, recordFactory=None, read=True, writeBack=False):
        PalmDatabase.__init__(self)
        self.fileName = fileName
        self.writeBack = writeBack
        if recordFactory <> None:
            self.setDatabaseRecordFactory(recordFactory)

        if self.fileName and read:
            self.load(fileName)

    def __del__(self):
        if self.writeBack and self.fileName:
            self.save()

    def load(self, fileName=None):
        '''
        Open fileName and load the Palm database file contents.  If no filename
        provided, then attempt to load the file specified in the self.fileName
        class varaiable.
        
        Any existing records of this object are cleared prior to loading the
        new info.
        '''
        
        if not fileName:
            if not self.fileName:
                raise UserWarning, "No filename specified from which to load data"
        else:
            self.fileName = fileName # store current filename as class variable
        f = open(self.fileName, 'rb')
        data = f.read()
        self.fromByteArray(data)
        f.close()

    def close(self):
        """
        Deprecated. Just a wrapper for backward compatibility.  There is little
        benefit to using this function.  Use save() instead.
        """
        if self.writeBack: self.save()
    
    def save(self, fileName=None, saveCopyOnly=False):
        '''
        Save the Palm database to the specified file, or if no file is specified,
        attept to save it to the file from which the current database was loaded.
        
        By default, when a filename is specified, it becomes the new default
        filename (the one written to when just a save() is called without
        arguments).
        
        If saveCopyOnly is True, then only a *copy* of the current database is
        saved to the specified file, but the default filename (self.fileName)
        is not changed.

        '''
        if self.fileName: # if a filename is defined
            if not fileName: # by default save to same file
                if self.dirty: # if no filename given, only write if dirty
                    f = open(self.fileName, 'wb')
                    f.write(self.toByteArray())
                    f.close()
            else: #  if a filename is given, write to it with no regard for its "dirtyness"
                if not saveCopyOnly:
                    self.fileName = fileName # set new filename class variable
        	    f = open(fileName, 'wb')
	            f.write(self.toByteArray())
                    f.close()
	            self.dirty = False # now 'clean' since it's been saved
                else:
                    raise UserWarning, "Cannot save: no fileName available"


if __name__ == "__main__":
#    toPrint=getXMLFromProgectPDB('lbPG-tutorial.PDB')
#    print toPrint
	pass
