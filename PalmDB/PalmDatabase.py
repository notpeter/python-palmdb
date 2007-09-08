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
import traceback
import PluginManager

from gettext import gettext as _

from PalmDB.Util import crackPalmDate
from PalmDB.Util import packPalmDate
from PalmDB.Util import getBits
from PalmDB.Util import setBits
from PalmDB.Util import returnDictionaryAsXML
from PalmDB.Util import returnAsXMLItem
from PalmDB.Util import dictionaryFromXMLDOMNode

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
		self.clear()

	def clear(self):
		'''
		Resets all class data to the defaults.
		'''
#		creatorID=self.attributes.get('creatorID',None)
		self.attributes.clear()
#		self.attributes['creatorID']=creatorID

		self.records = []
		self.dirty = False
		self.dirty = True

	def _getPlugin(self):
		return PluginManager.getPDBPluginByType(self.attributes.get('creatorID',None),self.attributes.get('databaseType',None))

	def isResourceDatabase(self):
		return self.attributes.get('flagResource',False)

	def getCreatorID(self):
		return self.attributes['creatorID']
	def setCreatorID(self,creatorID):
		self.attributes['creatorID']=creatorID
		self.dirty = True
	def getTypeID(self):
		return self.attributes['databaseType']
	def setTypeID(self,typeID):
		self.attributes['databaseType']=typeID
		self.dirty = True
	def getFilename(self):
		return self.attributes['PalmFileName']
	def setFilename(self,filename):
		self.attributes['PalmFileName']=filename

	def getCategoriesObject(self):
		return self.attributes.get('_categoriesObject',None)
	def setCategoriesObject(self,categoriesObject):
		self.attributes['_categoriesObject']=categoriesObject
		self.dirty = True

	def getApplicationInformationObject(self):
		return self.attributes.get('_applicationInformationObject',None)
	def setApplicationInformationObject(self,applicationInformationObject):
		self.attributes['_applicationInformationObject']=applicationInformationObject
		self.dirty = True

	def getSortBlockObject(self):
		return self.attributes.get('_sortBlockObject',None)
	def setSortBlockObject(self, sortBlockObject):
		self.attributes['_sortBlockObject']=sortBlockObject
		self.dirty = True

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

		self.attributes['fileName']=fileName.split('\0')[0].decode('palmos')
		self.attributes['databaseType']=databaseType.decode('palmos')
		self.attributes['creatorID']=creatorID.decode('palmos')
		self.attributes['createdTime']=crackPalmDate(createdTime)
		self.attributes['modifiedTime']=crackPalmDate(modifiedTime)
		self.attributes['backedUpTime']=crackPalmDate(backedUpTime)
		self.attributes['modificationNumber']=modificationNumber
		self.attributes['version']=version
		self.attributes['uid']=uid
		self.attributes['nextRecord']=nextRecord

		self.attributes['flagReset']=bool(getBits(flags,PalmHeaderInfo.flagResetPosition))
		self.attributes['flagResource']=bool(getBits(flags,PalmHeaderInfo.flagResourcePosition))
		self.attributes['flagNewer']=bool(getBits(flags,PalmHeaderInfo.flagNewerPosition))
		self.attributes['flagExcludeFromSync']=bool(getBits(flags,PalmHeaderInfo.flagExcludeFromSyncPosition))
		self.attributes['flagAppInfoDirty']=bool(getBits(flags,PalmHeaderInfo.flagAppInfoDirtyPosition))
		self.attributes['flagReadOnly']=bool(getBits(flags,PalmHeaderInfo.flagReadOnlyPosition))
		self.attributes['flagBackup']=bool(getBits(flags,PalmHeaderInfo.flagBackupPosition))
		self.attributes['flagOpen']=bool(getBits(flags,PalmHeaderInfo.flagOpenPosition))

		return (applicationInformationOffset,sortInformationOffset,numberOfRecords)

	def _headerInfoToByteArray(self,applicationInformationOffset,sortInformationOffset):
		'''
		Get raw data to marshall class.

		This function returns the binary form of the Palm database header.
		You need to copy the bytes returned by this function to the beginning of the 
		Palm database file. The string returned will be calcsize() bytes long.
		'''
		flag=0
		flag=setBits(flag,self.attributes['flagReset'],PalmHeaderInfo.flagResetPosition)
		flag=setBits(flag,self.attributes['flagResource'],PalmHeaderInfo.flagResourcePosition)
		flag=setBits(flag,self.attributes['flagNewer'],PalmHeaderInfo.flagNewerPosition)
		flag=setBits(flag,self.attributes['flagExcludeFromSync'],PalmHeaderInfo.flagExcludeFromSyncPosition)
		flag=setBits(flag,self.attributes['flagAppInfoDirty'],PalmHeaderInfo.flagAppInfoDirtyPosition)
		flag=setBits(flag,self.attributes['flagReadOnly'],PalmHeaderInfo.flagReadOnlyPosition)
		flag=setBits(flag,self.attributes['flagBackup'],PalmHeaderInfo.flagBackupPosition)
		flag=setBits(flag,self.attributes['flagOpen'],PalmHeaderInfo.flagOpenPosition)

		raw = struct.pack(HeaderInfo.PDBHeaderStructString,
			self.attributes['fileName'].encode('palmos'),
			flag,
			self.attributes['version'],
			packPalmDate(self.attributes['createdTime']),
			packPalmDate(self.attributes['modifiedTime']),
			packPalmDate(self.attributes['backedUpTime']),
			self.attributes['modificationNumber'],
			applicationInformationOffset,
			sortInformationOffset,
			self.attributes['databaseType'].encode('palmos'),
			self.attributes['creatorID'].encode('palmos'),
			self.attributes['uid'],
			self.attributes['nextRecord'],
			len(self) # get our record count
			)
		return raw

	def toXML(self):
		returnValue=''
		
		plugin=self._getPlugin()

		PalmHeaderAttributes=returnDictionaryAsXML(self.attributes)
		PalmHeaderAttributes=returnAsXMLItem('palmHeader',PalmHeaderAttributes,escape=False)
		
		returnValue+=plugin.getXMLVersionHeader(self)
		returnValue+=plugin.getXMLFileHeader(self)
		returnValue+=PalmHeaderAttributes
		if self.attributes.has_key('_categoriesObject'):
			returnValue+=self.attributes['_categoriesObject'].toXML()
		if self.attributes.has_key('_applicationInformationObject'):
			returnValue+=self.attributes['_applicationInformationObject'].toXML()
		if self.attributes.has_key('_sortBlockObject'):
			returnValue+=self.attributes['_sortBlockObject'].toXML()
		returnValue+=plugin.getRecordsAsXML(self)
		returnValue+=plugin.getXMLFileFooter(self)
		return returnValue
	def fromXML(self,fileStream):
		plugin=self._getPlugin()
		XMLReaderObject=plugin.getXMLReaderObject(self)
		XMLReaderObject.fromXML(fileStream,self)

	def _palmHeaderFromDOMNode(self,DOMNode):
		headerDict=dictionaryFromXMLDOMNode(DOMNode)
		self.attributes.update(headerDict)
#	 def getAppBlock(self):
# 		return self.appblock and self.appblock or None
#	 def setAppBlock(self, raw):
#		 self.dirty = True
#		 self.appblock = raw

#	 def getSortBlock(self): return self.sortblock and self.sortblock or None
#	 def setSortBlock(self, raw):
#		 self.dirty = True
#		 self.appblock = raw

	# sequence/map API Begins
	def __len__(self):
		return len(self.records)
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
		return newDatabase
	
	def __getitem__(self, index):
		return self.records[index]
	def __setitem__(self, index,record):
		self.records[index]=record
		self.dirty = True
	def __delitem__(self, index):
		del(self.records[index])
		self.dirty = True
	def append(self,record):
		self.records.append(record)
		self.dirty = True
	def insert(self,index,record):
		self.records.insert(index,record)
		self.dirty = True
	def remove(self,record):
		"Remove the first record with the specified ID"
		self.records.remove(record)
		self.dirty = True
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
	
		return offset

	def _getRecordHeader(self,plugin,raw,rawSize,maxRecords,desiredRecord):
		palmHeaderSize = PalmHeaderInfo.PDBHeaderStructSize
		palmRecordEntrySize=plugin.getPalmRecordEntrySize(self)
		
		startingRecordOffset=desiredRecord*palmRecordEntrySize+palmHeaderSize
		endingRecordOffset=startingRecordOffset+palmRecordEntrySize
		
		hstr=raw[startingRecordOffset:endingRecordOffset]

		# make sure we got the data we are looking for
		if (not hstr) or (len(hstr) <> palmRecordEntrySize):
			raise IOError, _("Error: problem reading record entry, size was (%d), size should have been (%d)")%(len(hstr),palmRecordEntrySize)

		return hstr
		
	def _getRecordData(self,plugin,raw,rawSize,maxRecords,desiredRecord):
		hstr=self._getRecordHeader(plugin,raw,rawSize,maxRecords,desiredRecord)

		startOffset=self._parseRecordOffset(hstr)
		if desiredRecord < maxRecords-1:
			endOffset=self._parseRecordOffset(self._getRecordHeader(plugin,raw,rawSize,maxRecords,desiredRecord+1))
		else:
			endOffset=rawSize

		if startOffset > rawSize:
			raise IOError, _("Error: Invalid start offset (%d), off end of database")%(startOffset)

		if endOffset > rawSize:
			raise IOError, _("Error: Invalid end offset (%d), off end of database")%(endOffset)

		if startOffset > endOffset:
			raise IOError, _("Error: Invalid offset pair (%d,%d), start is greater than end.")%(startOffset,endOffset)

		return (hstr,raw[startOffset:endOffset])
		
	def fromByteArray(self, raw, headerOnly = False):
		"""
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
		"""

		# clear all existing records
		self.clear()

		(applicationInformationOffset,sortInformationOffset,numberOfRecords)=self._headerInfoFromByteArray(raw)

		if headerOnly:
			return

		# grab the plugin to create things
		plugin=self._getPlugin()

		# assign some needed variables that were retrieved from the header
		rawSize = len(raw) # length of entire database

		palmHeaderSize = PalmHeaderInfo.PDBHeaderStructSize
		palmRecordEntrySize=plugin.getPalmRecordEntrySize(self)

		#-----BEGIN: INSTANTIATE AND APPEND DATABASE RECORDS / RESOURCES------

		# check to make sure the Palm database is big enough to at least contain the records it says it does
		if palmHeaderSize + palmRecordEntrySize * numberOfRecords > rawSize:
			raise IOError, _("Error: database not big enough to have %d records")%(numberOfRecords)

		# create records for each Palm record
		for desiredRecord in range(numberOfRecords):
			(hstr,dstr)=self._getRecordData(plugin,raw,rawSize,numberOfRecords,desiredRecord)

			# Create an instance of the record
			# recordMaker is either createRecordFromByteArray() or createResourceFromByteArray()
			record = plugin.createPalmDatabaseRecord(self)
			if not record:
				raise ValueError, _("Error: did not receive a PalmRecord back from the createPalmDatabaseRecord call into the plugin.problem reading record")
			# Check for problems
			try:
				# populate the record with the chunk data that it points to
				record.fromByteArray(hstr,dstr)

				# Add to beginning of self.records list because we are going backwards
				self.records.append(record)
			except Exception,e:
				print 'Had some sort of error reading record (',desiredRecord,') [',e,']'
#				traceback.print_exc()
		#-------END: INSTANTIATE AND APPEND DATABASE RECORDS / RESOURCES-------


		# Now take care of the sortinfo and appinfo blocks
		
		# The Order of the major blocks is as follows:
		# Palm DB Header
		# List of Record Header Entries
		# AppInfo block
		# SortInfo block
		# Sequence of DB record data entries

		# +++ FIX THIS +++ have to setup bottomOfAppRecords correctly
		bottomOfAppRecords=self._parseRecordOffset(self._getRecordHeader(plugin,raw,rawSize,numberOfRecords,0))
		# +++ FIX THIS +++ have to setup bottomOfAppRecords correctly

		# Calculate SortInfo block size
		# If no block, then of course size is zero
		# If we have records, then the offset of the first record is the bounds of the sortinfo block because they are on the end
		# Otherwise, the bounds must be the end of the file
		sortinfo_size=0
		if sortInformationOffset: # if there is no SortInfo block, the offset=0
			if numberOfRecords > 0:
				# bottomOfAppRecords is the beginning of the first record's data chunk
				sortinfo_size=bottomOfAppRecords-sortInformationOffset
			else: # if there are no records, then the SortInfo block ends at the end of the database
				sortinfo_size=rawSize-sortInformationOffset

		# Calculate the AppInfo block size
		# If we have a sort block, the offset to that is what bounds the AppInfo block
		# Otherwise, if we have records, then the offset of the first record is what bounds the AppInfo block
		# Finally if none of the previous things are true, then the boundary is the end of the file
		appinfo_size=0
		if applicationInformationOffset: # if there is no AppInfo block, the offset=0
			if sortInformationOffset > 0: # if there is a SortInfo block
				appinfo_size=sortInformationOffset-applicationInformationOffset
			elif numberOfRecords > 0:
				appinfo_size=bottomOfAppRecords-applicationInformationOffset
			else:
				appinfo_size=rawSize-applicationInformationOffset

		if appinfo_size < 0:
			raise IOError, _("Error: bad database header AppInfo Block size < 0 (%d)")%(appinfo_size)

		if sortinfo_size < 0:
			raise IOError, _("Error: bad database header SortInfo Block size < 0 (%d)")%(sortinfo_size)

		if appinfo_size: # if AppInfo block exists
			applicationInfoBlock = raw[applicationInformationOffset:applicationInformationOffset+appinfo_size]
			if len(applicationInfoBlock) != appinfo_size:
				raise IOError, _("Error: failed to read appinfo block")

			categoriesObject=plugin.createCategoriesObject(self)
			if categoriesObject <> None:
				categoriesObject.fromByteArray(applicationInfoBlock)
				self.attributes['_categoriesObject']=categoriesObject
				applicationInfoBlock=applicationInfoBlock[categoriesObject.objectBinarySize():]

				applicationInformationObject=plugin.createApplicationInformationObject(self)
			if applicationInformationObject <> None:
				applicationInformationObject.fromByteArray(applicationInfoBlock)
				self.attributes['_applicationInformationObject']=applicationInformationObject

		if sortinfo_size: # if SortInfo block exists
			sortInfoBlock = raw[sortInformationOffset:sortInformationOffset+sortinfo_size]
			if len(sortInfoBlock) != sortinfo_size:
				raise IOError, _("Error: failed to read sortinfo block")

			sortBlockObject=plugin.createSortBlockObject(self)
			if self.sortBlockObject <> None:
				sortBlockObject.fromByteArray(sortInfoBlock)
				self.attributes['_sortBlockObject']=sortBlockObject

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
		
		# grab the plugin to create things
		plugin=self._getPlugin()

		palmHeaderSize = PalmHeaderInfo.PDBHeaderStructSize

		# first, we need to precalculate the offsets.
		entries_len=plugin.getPalmRecordEntrySize(self)*len(self)
		offset = palmHeaderSize + entries_len + 2  #position following the entries

		if self.attributes.has_key('_applicationInformationObject') or self.attributes.has_key('_categoriesObject'):
			applicationInformationOffset = offset
			if self.attributes.has_key('_categoriesObject'):
				offset += self.attributes['_categoriesObject'].objectBinarySize()
			if self.attributes.has_key('_applicationInformationObject'):
				offset += self.attributes['_applicationInformationObject'].getSize()
		else:
			applicationInformationOffset = 0

		if self.attributes.has_key('_sortBlockObject'):
			sortInformationOffset = offset
			offset += self.attributes['_sortBlockObject'].getSize()
		else:
			sortInformationOffset = 0

		# begin to assemble the string to return (raw); start with database header
		raw=self._headerInfoToByteArray(applicationInformationOffset,sortInformationOffset)

		entries = [] # a list which holds all of the record/resource entries
		record_data = [] # holds record/resource data-chunks
		# +++ REMOVE THIS +++
#		print 'attributes of record'
#		print self[1].attributes
		# +++ REMOVE THIS +++
		# populate the lists...
		for record in self:
			(entryData,recordData)=record.toByteArray(offset)
			entries.append(entryData)
			record_data.append(recordData)
			offset+=len(recordData)

		# add the record/resource entries onto the data to be returned
		for x in entries: 
			raw = raw + x

		raw = raw + '\0\0' # padding?  dunno, it's always there

		# add the AppInfo and/or SortInfo blocks
		if self.attributes.has_key('_categoriesObject'):
			raw += self.attributes['_categoriesObject'].toByteArray()
		if self.attributes.has_key('_applicationInformationObject'):
			raw += self.attributes['_applicationInformationObject'].toByteArray()
		if self.attributes.has_key('_sortBlockObject'):
			raw += self.attributes['_sortBlockObject'].toByteArray()

		# finally, add the record/resource data chunks
		for x in record_data: 
			raw = raw + x

		return raw
	# Load/Save API Ends

if __name__ == "__main__":
	print 'running file'
	a=PalmDatabase()
	print 'finished'
