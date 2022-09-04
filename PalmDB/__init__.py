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

# This file includes changes made (including better naming, comments and design changes)
# by Mark Edgington, many thanks Mark.


"""PRC/PDB file I/O in pure Python.

    This module allows access to Palm OS(tm) database files on the desktop
    in pure Python. It is as simple as possible without (hopefully) being
    too simple. As much as possible Python idioms have been used to make
    it easier to use and more versatile.
"""

__copyright__ = 'Copyright 2006 Rick Price <rick_price@users.sourceforge.net>'

from . import PalmDatabase
from . import PluginManager
from PalmDB.DesktopApplications import READ
from PalmDB.DesktopApplications import WRITE


def filterForRecordsByCategory(records, category=None):
    '''
    This function lets you filter a list of records by category.

    When passed a list of records, and the appropriate category it will
    return a list of records that match the criteria.  When category=None,
    all records are returned.
    '''
    return [x for x in records if (category is None or x.getCategory() == category)]


def filterForResourcesByTypeID(records, type=None, id=None):
    '''
    This function lets you filter a list of resources by type and/or id.

    When passed a list of resources, and the appropriate filter it will
    return a list of resources that match the criteria.
    '''
    return [x for x in records if (
        (type is None or x.getResourceType() == type) and (id is None or x.getResourceID() == id)
    )]


def filterForModifiedRecords(records):
    '''
    This function returns a list of modified records from a list of records.

    When passed a list of records, this function will return a list of the modified records.
    '''
    return [x for x in records if x.attributes['dirty']]


def filterOutDeletedRecords(records):
    '''
    This function returns a list of non-deleted records from a list of records.

    When passed a list of records, this function will return a list of the non-deleted records.
    '''
    return [x for x in records if x.attributes['deleted']]


def resetRecordDirtyFlags(records):
    '''
    This function resets the dirty bit on a list of records.

    When passed a list of records, this function will reset the dirty bit on each record.
    '''
    for record in records:
        record.attr = record.attributes['dirty'] = False


# +++ FIX THIS +++ The following functions are broken because they have not been updated
class PDBFile(PalmDatabase.PalmDatabase):
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

    def __init__(self, fileName=None, read=True, writeBack=False):
        PalmDatabase.PalmDatabase.__init__(self)
        self.fileName = fileName
        self.writeBack = writeBack

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
                raise UserWarning("No filename specified from which to load data")
        else:
            self.fileName = fileName  # store current filename as class variable

        pluginList = PluginManager.getPluginsForFile(self.fileName, READ)
        if not pluginList:
            raise UserWarning((
                'Could not determine Palm application type, please specify.'
                'This is highly unlikely to happen since a default plugin should be chosen.'))
        if len(pluginList) > 1:
            raise UserWarning('Could not uniquely determine Palm application plugin type, please specify.')
        self.plugin = pluginList[0]
        self.plugin.readPalmDBFromFile(self, self.fileName)

    def close(self):
        """
        Deprecated. Just a wrapper for backward compatibility.  There is little
        benefit to using this function.  Use save() instead.
        """
        if self.writeBack:
            self.save()

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
        # if no filename at all we can't do anything
        if not fileName and not self.fileName:
            raise UserWarning("Cannot save: no fileName available")

        # if we are not saveCopyOnly, then save the filename we have been given
        if fileName and not saveCopyOnly:
            self.fileName = fileName

        # if fileName was not specified, and we don't have changes, just return
        if not fileName and not self.dirty:
            return

        if fileName:
            fileNameToUse = fileName
        else:
            fileNameToUse = self.fileName

        self.plugin.writePalmDBToFile(self, fileNameToUse)

        if not saveCopyOnly:
            self.dirty = False  # now 'clean' since it's been saved

    def saveApplicationFile(self, fileName):
        # We are now writing out a desktop type file, see what we can use...
        apps = self.plugin.getSupportedApplicationsForFile(fileName, WRITE)
        if len(apps) == 0:
            raise UserWarning('Could not determine desktop application type from filename, please specify.')
        elif len(apps) > 1:
            parser.error('More than one supported desktop application type for file, please specify one specifically.')
        self.desktopApplicationID = apps[0]

        self.plugin.saveToApplicationFile(self, self.desktopApplicationID, fileName)

    def readApplicationFile(self, fileName):
        pluginList = PluginManager.getPluginsForFile(fileName, READ)
        if not pluginList:
            raise UserError('Could not determine Palm application type, please specify.')
        if len(pluginList) > 1:
            raise UserError('Could not uniquely determine Palm application plugin type, please specify.')
        self.plugin = pluginList[0]

        # Determine the application type we can use to read the file
        apps = self.plugin.getSupportedApplicationsForFile(fileName, READ)
        if len(apps) == 0:
            raise UserError('Could not determine desktop application type, please specify.')
        elif len(apps) > 1:
            raise UserError('More than one supported desktop application type for file, please specify one specifically.')
        self.desktopApplicationID = apps[0]

        self.plugin.loadFromApplicationFile(self, self.desktopApplicationID, fileName)


if __name__ == "__main__":
    ProgectDB = PDBFile('lbPG-tutorial.pdb')
    ProgectDB.saveApplicationFile('lbPG-tutorial.pgt')

    ProgectDB2 = PDBFile('lbPG-tutorial2.pdb', writeBack=True, read=False)
    ProgectDB2.readApplicationFile('lbPG-tutorial.pgt')

    ProgectDB2.save()
