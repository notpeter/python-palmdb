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

__copyright__ = 'Copyright 2006 Rick Price <rick_price@users.sourceforge.net>'

import struct
import Util

RESOURCE_ENTRY_SIZE = 10  # size of a resource entry
RECORD_ENTRY_SIZE = 8 # size of a record entry

class BasePDBFilePlugin:
	#+++ FIX THIS +++ This HAS to be redefined in child classes otherwise things won't work
	def getPDBCreatorID(self):
		return None

	def createCategoriesObject(self,PalmDatabaseObject):
		return CategoriesObject()

	def createApplicationInformationObject(self,PalmDatabaseObject):
		return applicationInformationObject()

	def createSortBlockObject(self,PalmDatabaseObject):
		return sortBlockObject()

	def getPalmRecordEntrySize(self,PalmDatabaseObject):
	    if PalmDatabaseObject.isResourceDatabase():
            	return RESOURCE_ENTRY_SIZE
            else: 
           	return RECORD_ENTRY_SIZE

	def createPalmDatabaseRecord(self,PalmDatabaseObject):
	    if PalmDatabaseObject.isResourceDatabase():
                return ResourceRecord()
            else: 
		return DataRecord()

	def getXMLVersionHeader(self,PalmDatabaseObject):
		return '<?xml version="1.0" encoding="ISO-8859-1"?>'
	def getXMLFileHeader(self,PalmDatabaseObject):
		return '<palmDatabase type="%s">'%PalmDatabaseObject.getCreatorID()
	def getXMLFileFooter(self,PalmDatabaseObject):
		return '</palmDatabase>'
	def getRecordsAsXML(self,PalmDatabaseObject):
		recordsXML=''
		for record in PalmDatabaseObject:
			recordsXML+=record.toXML()
		recordsXML=Util.returnAsXMLItem('PalmRecordList',recordsXML,escape=False)
		return recordsXML
	
class BaseRecord:
    def __init__(self):
	    self.attributes={}
	    self.attributes['payload']=''

    def fromByteArray(self,hstr,dstr):
	    self._crackRecordHeader(hstr)
	    self._crackPayload(dstr)
    def toByteArray(self,offset):
	    return (self._packRecordHeader(offset),self._packPayload())

    def _crackRecordHeader(self,hstr):
	    # +++ READ THIS +++ This has to be implemented in a child class
	    raise NotImplementedError
    def _crackPayload(self,dstr):
	    self.attributes['payload']=dstr.encode('HEX')
    def _packPayload(self):
	    return self.attributes['payload'].decode('HEX')

    def getRecordXMLName(self):
	    return 'PalmRecord'
    def toXML(self):
	    attributesAsXML=Util.returnDictionaryAsXML(self.attributes)
	    return Util.returnAsXMLItem(self.getRecordXMLName(),attributesAsXML,escape=False)
	    
class DataRecord(BaseRecord):
    '''
    This class encapsulates a Palm application record.

    Comparison and hashing are done by ID; thus, the id value 
    *may not be changed* once the object is created. You need to call
    fromByteArray() and getRaw() to set the raw data.
    '''
    def __init__(self):
	    BaseRecord.__init__(self)
	    self.attributes['category']=0
	    self.attributes['uid']=0
	    self._crackAttributeBits(0)

    def getRecordXMLName(self):
	    return 'PalmDataRecord'

    def _crackRecordHeader(self,hstr):
        (offset, bits) = struct.unpack('>ll', hstr)
	
        attributes=Util.getBits(bits,31,4)
	category=Util.getBits(bits,27,4)
	uid=Util.getBits(bits,23,24)
	
	self.attributes['uid']=uid
	self.attributes['category']=category
	self._crackAttributeBits(attributes)

    def _packRecordHeader(self,offset):
	uid=self.attributes['uid']
	category=self.attributes['category']
	attributes=self._packAttributeBits()

	bits=Util.setBits(0,attributes,31,4)
	bits=Util.setBits(bits,category,27,4)
	bits=Util.setBits(bits,uid,23,24)
        return struct.pack('>ll',offset,bits)
	
    def _crackAttributeBits(self,attr):
        self.attributes['deleted']=bool(Util.getBits(attr,3))
        self.attributes['dirty']=bool(Util.getBits(attr,2))
        self.attributes['busy']=bool(Util.getBits(attr,1))
        self.attributes['secret']=bool(Util.getBits(attr,0))
    def _packAttributeBits(self):
        returnValue=Util.setBits(0,self.attributes['deleted'],3)
        returnValue=Util.setBits(returnValue,self.attributes['dirty'],2)
        returnValue=Util.setBits(returnValue,self.attributes['busy'],1)
        returnValue=Util.setBits(returnValue,self.attributes['secret'],0)
	return returnValue
	    
class ResourceRecord(BaseRecord):
    '''
    This class encapsulates a Palm resource record.
    '''
    def __init__(self):
	    BaseRecord.__init__(self)
	    self.attributes['id']=0
	    self.attributes['resourceType']='    '

    def _crackRecordHeader(self,hstr):
        (resourceType, id, offset) = struct.unpack('>4shl', hstr)
	self.attributes['id']=id
	self.attributes['resourceType']=type
    def _packRecordHeader(self,offset):
        return struct.pack('>4shl', self.attributes['resourceType'],self.attributes['id'],offset)

    def getRecordXMLName(self):
	    return 'PalmResourceRecord'

# you need to pass the AppBlock into this class in the constructor
class CategoriesObject(dict):
    '''
    This class encapsulates Palm Categories.

    Currently renaming categories or adding/deleting categories is not supported.
    As of this writing, you may only have 16 categories, and this code us unable
    to handle anything other than that.
    
    This class is not used by any other class in this module. Its only purpose
    is if you want to extract category data from the AppInfo block (provided
    that it contains category data...)
    '''
    def __init__(self):
        '''
        To initialize the class with the categories from a database, pass it 
        calcsize() bytes from the beginning of the application info block.
        Doing so will probably be easier if we can make calcsize a class variable
        so here is the current recommended way of doing it.
        x = PalmDB.Categories()
        x.SetRaw(applicationInfoBlock[:x.calcsize())
        '''
        self.__packString = '!H'+('16s'*16)+('B'*16)+'B'+'x'
	self._reverseLookup={}
    def objectBinarySize(self):
	    # Return the packed structure size of the Palm category information.
	    return struct.calcsize(self.__packString)

    def fromByteArray(self,raw):
        '''
        Set raw data to marshall class.

        To initialize the class with the categories from a database, pass it 
        calcsize() bytes from the beginning of the application info block.
        Doing so will probably be easier if we can make calcsize a class variable
        so here is the current recommended way of doing it.
        x = PalmDB.Categories()
        x.SetRaw(applicationInfoBlock)
        '''

	self.renamedCategories=struct.unpack('!H',raw[0:2])[0]
	self.categoryLabels=list(struct.unpack('16s'*16,raw[2:258]))
	# Strip off the trailing zeroes
	self.categoryLabels=map(lambda x : x.split('\0')[0],self.categoryLabels)
	self.categoryUniqIDs=list(struct.unpack('B'*16,raw[258:274]))
	self.lastUniqID=struct.unpack('B',raw[274])[0]
	
	# build category list
	categories=zip(range(16),self.categoryLabels)

	# get rid of categories that are empty, because empty strings are false
	categories=filter(lambda x : x[1],categories)
	tempDict=dict(categories)

	# update ourselves with the new categories
	self.clear()
	self.update(tempDict)

    def toByteArray(self):
        '''
        Get raw data to marshal class

        This function returns the binary form of the categories used in a Palm database.
        You need to copy the bytes returned by this function to the beginning of the 
        application info block. The string returned will be calcsize() bytes long.
        '''
	return struct.pack(self.__packString,*([self.renamedCategories]+self.categoryLabels+self.categoryUniqIDs+[self.lastUniqID]))

    def toXML(self):
        returnValue=''
        for key in self.keys():
            returnValue+=Util.returnAsXMLItem('category',Util.returnObjectAsXML('CategoryID',key)+Util.returnObjectAsXML('CategoryName',self[key]),escape=False)
	return Util.returnAsXMLItem('palmCategories',returnValue,escape=False)

    def __setitem__(self,key,value):
	    dict.__setitem__(key,value)
	    self.reverseLookup[value]=key
    def __delitem__(self,key):
	    # delete reverse lookup
	    del(self.reverseLookup[self[key]])
	    dict.__delitem__(key)
    def reverseLookup(self,value):
	    return self.reverseLookup[value]

class applicationInformationObject:
	def __init__(self):
		self.attributes={}
		self.attributes['payload']=''
	def __len__(self):
	    return len(self.attributes.get('payload','').decode('HEX'))

	def fromByteArray(self,dstr):
		self.attributes['payload']=dstr.encode('HEX')

	def toByteArray(self,dstr):
		return self.attributes.get('payload','').decode('HEX')
	
	def toXML(self):
		attributesAsXML=Util.returnDictionaryAsXML(self.attributes)
		return Util.returnAsXMLItem('applicationBlock',attributesAsXML,escape=False)

class sortBlockObject:
	def __init__(self):
		self.attributes={}
		self.attributes['payload']=''
	def __len__(self):
	    return len(self.attributes.get('payload','').decode('HEX'))

	def fromByteArray(self,dstr):
		self.attributes['payload']=dstr.encode('HEX')

	def toByteArray(self,dstr):
		return self.attributes.get('payload','').decode('HEX')
	
	def toXML(self):
		attributesAsXML=Util.returnDictionaryAsXML(self.attributes)
		return Util.returnAsXMLItem('sortBlock',attributesAsXML,escape=False)

