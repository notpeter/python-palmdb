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

import struct
import Util
import PluginManager

class PalmHeaderInfo:
	# Header Struct
	PDBHeaderStructString='>32shhLLLlll4s4sllh'
	PDBHeaderStructSize=struct.calcsize(PDBHeaderStructString)
	# Header Flags
	flagResourcePosition = 0
	flagReadOnlyPosition = 1
	flagAppInfoDirtyPosition = 2
	flagBackupPosition = 3
	flagOpenPosition = 15
	# 2.x
	flagNewerPosition = 4
	flagResetPosition = 5
	flagExcludeFromSyncPosition = 7

HeaderInfo=PalmHeaderInfo()

class PalmDatabase:
    '''
    This class encapsulates a Palm database.

    To initialize the class with the database call fromByteArray with
    the Palm database data.
    For example:
    f = open('palmdb.pdb','rb')
    data = f.read()
    self.fromByteArray(data)
    f.close()
    '''
    def __init__(self):
	self.attributes={}
	self.reset()

    def reset(self):
        '''
        Reset all class data to the defaults.
        '''
        self.attributes.clear()

        self.records = []
        self.dirty = False
	self.categoriesObject=None
	self.applicationInformationObject=None
	self.sortBlockObject=None

    def _getPlugin(self):
	return PluginManager.getPDBPlugin(self.attributes['creatorID'])

    def isResourceDatabase(self):
	return self.attributes['flagResource']

    def getCreatorID(self):
	return self.attributes['creatorID']

    def _headerInfoFromByteArray(self,raw):
        '''
	Initialize Palm Database Header Data
	'''
        if len(raw) < HeaderInfo.PDBHeaderStructSize: raise ValueError, _("Too little data passed in.")

        (fileName, flags, version, \
	createdTime, modifiedTime, backedUpTime, \
	modificationNumber, applicationInformationOffset, sortInformationOffset, \
        databaseType, creatorID, uid, \
	nextRecord, numberOfRecords) \
        = struct.unpack(HeaderInfo.PDBHeaderStructString, raw[:HeaderInfo.PDBHeaderStructSize])

	# Do some sanity checking
        if nextRecord or applicationInformationOffset < 0 or sortInformationOffset < 0 or numberOfRecords < 0:
            raise ValueError, _("Invalid database header.")

	self.attributes['fileName']=fileName.split('\0')[0]
	self.attributes['databaseType']=databaseType
	self.attributes['creatorID']=creatorID
	self.attributes['createdTime']=Util.crackPalmDate(createdTime)
	self.attributes['modifiedTime']=Util.crackPalmDate(modifiedTime)
	self.attributes['backedUpTime']=Util.crackPalmDate(backedUpTime)
	self.attributes['modificationNumber']=modificationNumber
	self.attributes['version']=version
	self.attributes['uid']=uid
	self.attributes['nextRecord']=nextRecord

	self.attributes['flagReset']=bool(Util.getBits(flags,PalmHeaderInfo.flagResetPosition))
	self.attributes['flagResource']=bool(Util.getBits(flags,PalmHeaderInfo.flagResourcePosition))
	self.attributes['flagNewer']=bool(Util.getBits(flags,PalmHeaderInfo.flagNewerPosition))
	self.attributes['flagExcludeFromSync']=bool(Util.getBits(flags,PalmHeaderInfo.flagExcludeFromSyncPosition))
	self.attributes['flagAppInfoDirty']=bool(Util.getBits(flags,PalmHeaderInfo.flagAppInfoDirtyPosition))
	self.attributes['flagReadOnly']=bool(Util.getBits(flags,PalmHeaderInfo.flagReadOnlyPosition))
	self.attributes['flagBackup']=bool(Util.getBits(flags,PalmHeaderInfo.flagBackupPosition))
	self.attributes['flagOpen']=bool(Util.getBits(flags,PalmHeaderInfo.flagOpenPosition))

	return (applicationInformationOffset,sortInformationOffset,numberOfRecords)

    def _headerInfoToByteArray(self):
        '''
        Get raw data to marshall class.

        This function returns the binary form of the Palm database header.
        You need to copy the bytes returned by this function to the beginning of the 
        Palm database file. The string returned will be calcsize() bytes long.
        '''
	flag=0
	flag=Util.setBits(flags,self.attributes['flagReset'],PalmHeaderInfo.flagResetPosition)
	flag=Util.setBits(flag,self.attributes['flagResource'],PalmHeaderInfo.flagResourcePosition)
	flag=Util.setBits(flag,self.attributes['flagNewer'],PalmHeaderInfo.flagNewerPosition)
	flag=Util.setBits(flag,self.attributes['flagExcludeFromSync'],PalmHeaderInfo.flagExcludeFromSyncPosition)
	flag=Util.setBits(flag,self.attributes['flagAppInfoDirty'],PalmHeaderInfo.flagAppInfoDirtyPosition)
	flag=Util.setBits(flag,self.attributes['flagReadOnly'],PalmHeaderInfo.flagReadOnlyPosition)
	flag=Util.setBits(flag,self.attributes['flagBackup'],PalmHeaderInfo.flagBackupPosition)
	flag=Util.setBits(flag,self.attributes['flagOpen'],PalmHeaderInfo.flagOpenPosition)

        raw = struct.pack(HeaderInfo.PDBHeaderStructString,
            self.attributes['fileName'],
            flag,
            self.attributes['version'],
            Util.packPalmDate(self.attributes['createdTime']),
            Util.packPalmDate(self.attributes['modifyDate']),
            Util.packPalmDate(self.attributes['backupDate']),
            self.attributes['modificationNumber'],
            self.attributesappinfo_offset,
            self.attributessortinfo_offset,
            self.attributes['databaseType'],
            self.attributes['creatorID'],
            self.attributes['uid'],
            self.attributes['nextRecord'],
            self.__len__())
        return raw

    def toXML(self):
        returnValue=''
	
	plugin=self._getPlugin()

	PalmHeaderAttributes=Util.returnDictionaryAsXML(self.attributes)
	PalmHeaderAttributes=Util.returnAsXMLItem('PalmHeader',PalmHeaderAttributes,escape=False)

	returnValue+=plugin.getXMLVersionHeader(self)
	returnValue+=plugin.getXMLFileHeader(self)
	returnValue+=PalmHeaderAttributes
	if self.categoriesObject:
		returnValue+=self.categoriesObject.toXML()
	if self.applicationInformationObject:
		returnValue+=self.applicationInformationObject.toXML()
	if self.sortBlockObject:
		returnValue+=self.sortBlockObject.toXML()
	returnValue+=plugin.getRecordsAsXML(self)
	returnValue+=plugin.getXMLFileFooter(self)
	return returnValue

    def getAppBlock(self): return self.appblock and self.appblock or None
    def setAppBlock(self, raw):
        self.dirty = True
        self.appblock = raw

    def getSortBlock(self): return self.sortblock and self.sortblock or None
    def setSortBlock(self, raw):
        self.dirty = True
        self.appblock = raw

    # sequence/map API Begins
    def __len__(self): return len(self.records)
    def __add__(self,addend2):
        """
        permits one to create a new PDB which contains the palm header, AppBlock,
        and SortBlock of the first addend, and concatenates the record list
        of both addends into the new record list.
        Example:
        newDb = db1 + db2
        now newDb is a separate object, a copy of db1, with the records of db2
        tacked on to the record list.
        """
        newRecordList = copy.deepcopy(self.records) + copy.deepcopy(addend2.records)
        newDatabase = copy.deepcopy(self)
        newDatabase.records = newRecordList
        newDatabase.palmDBInfo._updateNumberOfRecords(newDatabase)
        return newDatabase
    
    def __getitem__(self, index):
        return self.records[index]
    def __setitem__(self, index,record):
        self.records[index]=record
        self.dirty = True
    def __delitem__(self, index):
        del(self.records[index])
        self.dirty = True
        self.palmDBInfo._updateNumberOfRecords(self)
    def clear(self):
        self.records = []
        self.dirty = True
        self.palmDBInfo._updateNumberOfRecords(self)
    def append(self,record):
        self.records.append(record)
        self.dirty = True
        self.palmDBInfo._updateNumberOfRecords(self)
    def insert(self,index,record):
        self.records.insert(index,record)
        self.dirty = True
        self.palmDBInfo._updateNumberOfRecords(self)
    def remove(self,record):
        "Remove the first record with the specified ID"
        self.records.remove(record)
        self.dirty = True
        self.palmDBInfo._updateNumberOfRecords(self)
    def index(self,record):
        return self.records.index(record)
    def __contains__(self,record):
        return self.records.__contains__(record)
    # Sequence/map API Ends


    # Load/Save API Begins
    def _parseRecordOffset(self, hstr):
        '''
        This function parses out a record entry from the corresponding segment
        of binary data taken from the PDB file (hstr), and returns the offset.
        '''
        
        if self.isResourceDatabase():
            (resourceType, id, offset) = struct.unpack('>4shl', hstr)
        else:
            (offset, auid) = struct.unpack('>ll', hstr)

	return offset;
        
    def fromByteArray(self, raw, headerOnly = False):
        '''
        This function initializes this class instance, clearing the instance's
        existing data, and populating it using the complete raw data read from a PDB.

        For example:
        x = PalmDB.PalmDatabase()
        f = open('palmdb.pdb','rb')
        data = f.read()
        x.fromByteArray(data)
        f.close()

        If you just want to read the header pass True as a second parameter,
        this is useful to, for example, check the creator id without needing
        to read all records

        For example:
        x = PalmDB.PalmDatabase()
        f = open( folder + name, 'rb')
        data = f.read()
        f.close()

        x.fromByteArray(data, True)
        info = x.getPalmDBInfo()
        if info[ 'creatorID'] == 'Gtkr':
            ...
        '''

        # clear all existing records
        self.reset()

	(applicationInformationOffset,sortInformationOffset,numberOfRecords)=self._headerInfoFromByteArray(raw)

        if headerOnly:
            return

	# grab the plugin to create things
	plugin=self._getPlugin()

        # assign some needed variables that were retrieved from the header
        rawsize = len(raw) # length of entire database

        palmHeaderSize = PalmHeaderInfo.PDBHeaderStructSize
	palmRecordEntrySize=plugin.getPalmRecordEntrySize(self)

        # debugging
#        print 'Debug: Scanning PDB of size', rawsize
#        print 'Debug: AppInfo at', applicationInformationOffset
#        print 'Debug: SortInfo at', sortInformationOffset
#        print 'Debug: Found', numberOfRecords, 'records'
#        print 'Debug: Palm Header Size %d'%(palmHeaderSize)

        #-----BEGIN: INSTANTIATE AND APPEND DATABASE RECORDS / RESOURCES------

        first_offset = 0        # need this to find the sort/app info blocks

        # next two maintain state for the loop
        prev_offset = rawsize    # track the offset of the previous block, but we are going backwards to simplify the algorithm

	# check to make sure the Palm database is big enough to at least contain the records it says it does
        if palmHeaderSize + palmRecordEntrySize * numberOfRecords > rawsize:
            raise IOError, _("Error: database not big enough to have %d records")%(numberOfRecords)

#        print "Debug: Header size (%d), Number of records (%d)"%(palmRecordEntrySize,numberOfRecords)
        # create records for each Palm record
        # have to use -1 as the final number, because range never reaches it, it always stops before it
        for count in range(numberOfRecords-1,-1,-1):
#            print "Debug: count (%d)"%(count)
            startingRecordOffset=count*palmRecordEntrySize+palmHeaderSize
            # we have to offset by one because we have to skip the Palm header
            endingRecordOffset = (count+1)*palmRecordEntrySize + palmHeaderSize
            
            # extract the raw data for the current record/resource entry
            hstr=raw[startingRecordOffset:endingRecordOffset]

#            print "Debug: using range of %d to %d"%(startingRecordOffset,endingRecordOffset)
            # make sure we got the data we are looking for
            if (not hstr) or (len(hstr) <> palmRecordEntrySize):
                raise IOError, _("Error: problem reading record entry, size was (%d), size should have been (%d)")%(len(hstr),palmRecordEntrySize)

            # parse the record entry
            offset=self._parseRecordOffset(hstr)

            # Create an instance of the record
            # recordMaker is either createRecordFromByteArray() or createResourceFromByteArray()
	    record = plugin.createPalmDatabaseRecord(self)
	    if not record:
                raise ValueError, _("Error: did not receive a PalmRecord back from the createPalmDatabaseRecord call into the plugin.problem reading record")

            # Check for problems
            try:
                if offset > rawsize:
                    raise IOError, _("Error: Invalid offset (%d), off end of database")%(offset)

                if offset > prev_offset:
                        raise IOError, _("Error: Invalid offset (%d), greater than previous offset (records being processed in reverse order)")%(offset)

                # populate the record with the chunk data that it points to
                record.fromByteArray(hstr,raw[offset:prev_offset])

                # Add to beginning of self.records list because we are going backwards
                self.records.insert(0,record)
                prev_offset = offset
	    except:
	        None
        #-------END: INSTANTIATE AND APPEND DATABASE RECORDS / RESOURCES-------


        # Now take care of the sortinfo and appinfo blocks
        
        # The Order of the major blocks is as follows:
        # Palm DB Header
        # List of Record Header Entries
        # AppInfo block
        # SortInfo block
        # Sequence of DB record data entries


        # Calculate SortInfo block size
        # If no block, then of course size is zero
        # If we have records, then the offset of the first record is the bounds of the sortinfo block because they are on the end
        # Otherwise, the bounds must be the end of the file
        sortinfo_size=0
        if sortInformationOffset: # if there is no SortInfo block, the offset=0
            if numberOfRecords > 0:
                # prev_offset is the beginning of the first record's data chunk
                sortinfo_size=prev_offset-sortInformationOffsets
            else: # if there are no records, then the SortInfo block ends at the end of the database
                sortinfo_size=rawsize-sortInformationOffset

        # Calculate the AppInfo block size
        # If we have a sort block, the offset to that is what bounds the AppInfo block
        # Otherwise, if we have records, then the offset of the first record is what bounds the AppInfo block
        # Finally if none of the previous things are true, then the boundary is the end of the file
        appinfo_size=0
        if applicationInformationOffset: # if there is no AppInfo block, the offset=0
            if sortInformationOffset > 0: # if there is a SortInfo block
                appinfo_size=sortInformationOffset-applicationInformationOffset
            elif numberOfRecords > 0:
                appinfo_size=prev_offset-applicationInformationOffset
            else:
                appinfo_size=rawsize-applicationInformationOffset

        if appinfo_size < 0:
            raise IOError, _("Error: bad database header AppInfo Block size < 0 (%d)")%(appinfo_size)

        if sortinfo_size < 0:
            raise IOError, _("Error: bad database header SortInfo Block size < 0 (%d)")%(sortinfo_size)

        if appinfo_size: # if AppInfo block exists
            applicationInfoBlock = raw[applicationInformationOffset:applicationInformationOffset+appinfo_size]
            if len(applicationInfoBlock) != appinfo_size:
                raise IOError, _("Error: failed to read appinfo block")

	    self.categoriesObject=plugin.createCategoriesObject(self)
	    if self.categoriesObject <> None:
		    self.categoriesObject.fromByteArray(applicationInfoBlock)
		    applicationInfoBlock=applicationInfoBlock[self.categoriesObject.categoryBlockSize:]
		
            self.applicationInformationObject=plugin.createApplicationInformationObject(self)
	    if self.applicationInformationObject:
		self.applicationInformationObject.fromByteArray(applicationInfoBlock)

        if sortinfo_size: # if SortInfo block exists
            sortInfoBlock = raw[sortInformationOffset:sortInformationOffset+sortinfo_size]
            if len(sortInfoBlock) != sortinfo_size:
                raise IOError, _("Error: failed to read sortinfo block")

            self.sortBlockObject=plugin.createSortBlockObject(self)
	    if self.sortBlockObject:
		self.sortBlockObject.fromByteArray(applicationInfoBlock)

    def toByteArray(self):
        '''
        This function returns the data for the complete Palm database as a
        string, which can then be written directly as a PDB file.

        For example:
        x = PalmDB.PalmDatabase()
        [ ... various operations on the database
                    (adding/changing/deleting records, etc.) ...]
        f = open('palmdb.pdb', 'wb')
        f.write(x.toByteArray())
        f.close()       
        '''
        
        palmHeaderSize = PalmHeaderInfo.PDBHeaderStructSize

        # first, we need to precalculate the offsets.
        if self.isResourceDatabase():
            entries_len = RESOURCE_ENTRY_SIZE * len(self.records)
        else: 
            entries_len = RECORD_ENTRY_SIZE * len(self.records)

        offset = palmHeaderSize + entries_len + 2  #position following the entries
        if self.appblock:
            applicationInformationOffset = offset
            offset = offset + len(self.appblock)
        else:
            applicationInformationOffset = 0

        if self.sortblock:
            sortInformationOffset = offset
            offset = offset + len(self.sortblock)
        else:
            sortInformationOffset = 0

        # make list containing offsets for record/resource data-chunk locations
        rec_offsets = []
        for x in self.records:
            rec_offsets.append(offset)
            offset = offset + len(x.getRaw())

        # begin to assemble the string to return (raw); start with database header
        raw = self.palmDBInfo.getRaw()

        entries = [] # a list which holds all of the record/resource entries
        record_data = [] # holds record/resource data-chunks
        # populate the lists...
        for x, offset in map(None, self.records, rec_offsets):
            if self.isResourceDatabase():
                record_data.append(x.getRaw())
                entries.append(struct.pack('>4shl', x.type, x.id, offset))
            else:
                record_data.append(x.getRaw())
                a = ((x.attr | x.category) << 24) | x.id
                entries.append(struct.pack('>ll', offset, a))

        # add the record/resource entries onto the data to be returned
        for x in entries: 
            raw = raw + x

        raw = raw + '\0\0' # padding?  dunno, it's always there

        # add the AppInfo and/or SortInfo blocks
        if self.appblock: raw = raw + self.appblock
        if self.sortblock: raw = raw + self.sortblock

        # finally, add the record/resource data chunks
        for x in record_data: 
            raw = raw + x

        return raw
    # Load/Save API Ends

if __name__ == "__main__":
	print 'running file'
	a=PalmDatabase()
	print 'finished'
