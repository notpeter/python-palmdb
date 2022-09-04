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

import codecs
import struct
from xml.dom import pulldom
#from Ft.Xml.Xslt import Transform
import io

from PalmDB.Util import getBits
from PalmDB.Util import setBits
from PalmDB.Util import returnDictionaryAsXML
from PalmDB.Util import returnAsXMLItem
from PalmDB.Util import returnObjectAsXML
from PalmDB.Util import dictionaryFromXMLDOMNode

from PalmDB.DesktopApplications import getDesktopApplicationNameFromID
from PalmDB.DesktopApplications import READ
from PalmDB.DesktopApplications import WRITE
from functools import reduce

RESOURCE_ENTRY_SIZE = 10  # size of a resource entry
RECORD_ENTRY_SIZE = 8 # size of a record entry


class BasePDBFilePlugin:
#+++ READ THIS +++ This HAS to be redefined in child classes otherwise things won't work
	def getPluginID(self):
		return 'DEFAULT_PLUGIN'
#+++ READ THIS +++ This HAS to be redefined in child classes otherwise things won't work
	def getPDBFormatName(self):
		return 'Unknown PDB Format'
#+++ READ THIS +++ This HAS to be redefined in child classes otherwise things won't work
	def getDefaultDesktopApplicationID(self):
		return 'PALMDB_XML'
	#+++ READ THIS +++ This HAS to be redefined in child classes otherwise things won't work
	def getPDBCreatorID(self):
#		raise NotImplementedError
		return 'Unknown'
	def getPDBTypeID(self):
	#+++ READ THIS +++ This MAY need to be redefined in child classes
		return 'DATA'
	#+++ READ THIS +++ This HAS to be redefined in child classes otherwise things won't work
	def getSupportedDesktopApplications(self,readOrWrite):
		return ['PALMDB_XML']
	#+++ READ THIS +++ This HAS to be redefined in child classes otherwise things won't work
	def getSupportedApplicationsForFile(self,filename,readOrWrite):
		# return tuple (ApplicationName,XSLT,GZIPResult)
		if filename.upper().endswith('.XML'):
			return ['PALMDB_XML']
		return []



	def loadFromApplicationFile(self,PalmDB,applicationID,filename):
		if applicationID not in self.getSupportedDesktopApplications(READ):
			raise NotImplementedError('This plugin does not support [%s; %s]'%(applicationID,getDesktopApplicationNameFromID(applicationID)))
		desktopData=self.unpackXMLFromFile(applicationID,filename)
		PalmDB.setCreatorID(self.getPDBCreatorID())
		PalmDB.setTypeID(self.getPDBTypeID())
		PalmDB.fromXML(io.StringIO(desktopData))
	def saveToApplicationFile(self,PalmDB,applicationID,filename):
		if applicationID not in self.getSupportedDesktopApplications(WRITE):
			raise NotImplementedError('This plugin does not support [%s; %s]'%(applicationID,getDesktopApplicationNameFromID(applicationID)))
		desktopData=PalmDB.toXML()
		self.packXMLIntoFile(applicationID,filename,desktopData)

	def unpackXMLFromFile(self,applicationID,filename):
		# +++ READ THIS +++ You should not be trying to decode the XML, it has to be a stream of bytes, the XML parser needs to do the decoding.
		XMLData=open(filename,'rb').read()
		return XMLData
	def packXMLIntoFile(self,applicationID,filename,XMLData):
		XMLData=codecs.open(filename,'w','utf8').write(XMLData)

	def readPalmDBFromFile(self,PalmDB,filename):
		palmData=open(filename,'rb').read()
		PalmDB.fromByteArray(palmData)
	def writePalmDBToFile(self,PalmDB,filename):
		PalmDB.setFilename(filename)
		palmData=PalmDB.toByteArray()
		open(filename,'wb').write(palmData)

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
		return '<?xml version="1.0" encoding="UTF-8"?>'
	def getXMLFileHeader(self,PalmDatabaseObject):
		return '<palmDatabase type="%s">'%PalmDatabaseObject.getCreatorID()
	def getXMLFileFooter(self,PalmDatabaseObject):
		return '</palmDatabase>'
	def getRecordsAsXML(self,PalmDatabaseObject):
		recordsXML=''
		for record in PalmDatabaseObject:
			recordsXML+=record.toXML()
		recordsXML=returnAsXMLItem('PalmRecordList',recordsXML,escape=False)
		return recordsXML
	def getXMLReaderObject(self,PalmDatabaseObject):
		return GeneralPalmDBXMLReaderObject()

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
		# +++ READ THIS +++ This has to be implemented in a child class
		raise NotImplementedError
		return 'PalmRecord'
	def toXML(self):
		attributesAsXML=returnDictionaryAsXML(self.attributes)
		return returnAsXMLItem(self.getRecordXMLName(),attributesAsXML,escape=False)
	def fromDOMNode(self,DOMNode):
		self.attributes=dictionaryFromXMLDOMNode(DOMNode)

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
		return 'palmDataRecord'

	def _crackRecordHeader(self,hstr):
		(offset, bits) = struct.unpack('>ll', hstr)

		attributes=getBits(bits,31,4)
		category=getBits(bits,27,4)
		uid=getBits(bits,23,24)
	
		self.attributes['uid']=uid
		self.attributes['category']=category
		self._crackAttributeBits(attributes)

	def _packRecordHeader(self,offset):
		uid=self.attributes['uid']
		category=self.attributes['category']
		attributes=self._packAttributeBits()

		bits=setBits(0,attributes,31,4)
		bits=setBits(bits,category,27,4)
		bits=setBits(bits,uid,23,24)
		return struct.pack('>LL',offset,bits)
	
	def _crackAttributeBits(self,attr):
		self.attributes['deleted']=bool(getBits(attr,3))
		self.attributes['dirty']=bool(getBits(attr,2))
		self.attributes['busy']=bool(getBits(attr,1))
		self.attributes['secret']=bool(getBits(attr,0))
	def _packAttributeBits(self):
		returnValue=setBits(0,self.attributes['deleted'],3)
		returnValue=setBits(returnValue,self.attributes['dirty'],2)
		returnValue=setBits(returnValue,self.attributes['busy'],1)
		returnValue=setBits(returnValue,self.attributes['secret'],0)
		return returnValue
	def getCategory(self):
		return self.attributes['category']

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
		return 'palmResourceRecord'

	def getResourceType(self):
		return self.attributes['resourceType']
	def getResourceID(self):
		return self.attributes['id']

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


	typedef struct AppInfoTag {
	UInt16	renamedCategories;
	Char	categoryLabels [dmRecNumCategories] [dmCategoryLength];
	UInt8	categoryUniqIDs[dmRecNumCategories];
	UInt8	lastUniqID;	// Uniq IDs generated by the device are between
							// 0 - 127.  Those from the PC are 128 - 255.
	UInt8	padding;
	} AppInfoType;
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

		renamedCategories=struct.unpack('!H',raw[0:2])[0]
		categoryLabels=list(struct.unpack('16s'*16,raw[2:258]))
		# Strip off the trailing zeroes
		categoryLabels=[x.split('\0')[0] for x in categoryLabels]
		# decode Palm charset
		categoryLabels=[x.decode('palmos') for x in categoryLabels]
		# Get category ID's
		categoryUniqIDs=list(struct.unpack('B'*16,raw[258:274]))
		lastUniqID=struct.unpack('B',raw[274])[0]
		# build category list, use name as key, number as value
		categories=list(zip(categoryLabels,categoryUniqIDs))
	
		# get rid of categories that are empty, because empty strings are false
		categories=[x for x in categories if x[0]]
	
		tempDict=dict(categories)
	
		# update ourselves with the new categories
		self.clear()
		self.update(tempDict)

		# Return list of labels for indexing with record categories.
		return categoryLabels

	def toByteArray(self):
		'''
		Get raw data to marshal class

		This function returns the binary form of the categories used in a Palm database.
		You need to copy the bytes returned by this function to the beginning of the 
		application info block. The string returned will be calcsize() bytes long.
		'''
		# +++ FIX THIS +++, this is just plain old broken
		renamedCategories=0
		(categoryLabels,categoryUniqIDs)=list(zip(*list(self.items())))
		lastUniqID=reduce(max,categoryUniqIDs)
		categoryLabels=list(categoryLabels)
		categoryUniqIDs=list(categoryUniqIDs)
	
		# have to convert unicode strings to palmos format
		categoryLabels=[x.encode('palmos') for x in categoryLabels]
		
		# have to add in dummy data now
		dummyCount=16-len(categoryLabels)
		categoryLabels.extend(['']*dummyCount)
		categoryUniqIDs.extend(list(range(lastUniqID+1,lastUniqID+dummyCount+1)))
		lastUniqID=lastUniqID+dummyCount-1
		# +++ CHECK THIS +++
		# this is completely untested, and should be assumed to be broken
		#	raise NotImplementedError
		# +++ CHECK THIS +++
		return struct.pack(self.__packString,*([renamedCategories]+categoryLabels+categoryUniqIDs+[lastUniqID]))

	def toXML(self):
		return returnAsXMLItem('palmCategories',returnDictionaryAsXML(self),escape=False)

	def fromDOMNode(self,DOMNode):
		self.clear()
		categoriesDict=dictionaryFromXMLDOMNode(DOMNode)
		self.update(categoriesDict)
	def __setitem__(self,key,value):
		dict.__setitem__(key,value)
		self._reverseLookup[value]=key
	def __delitem__(self,key):
		# delete reverse lookup
		del(self._reverseLookup[self[key]])
		dict.__delitem__(key)
	def update(self,dictionary):
		dict.update(self,dictionary)
		# now update the reverse lookup
		(keys,values)=list(zip(*list(dictionary.items())))
		self._reverseLookup.update(list(zip(values,keys)))
	def reverseLookup(self,value):
		return self._reverseLookup[value]

class applicationInformationObject:
	def __init__(self):
		self.attributes={}
		self.attributes['payload']=''
	def getSize(self):
		return len(self.attributes.get('payload','').decode('HEX'))

	def fromByteArray(self,dstr):
		self.attributes['payload']=dstr.encode('HEX')

	def toByteArray(self):
		return self.attributes.get('payload','').decode('HEX')
	
	def toXML(self):
		attributesAsXML=returnDictionaryAsXML(self.attributes)
		return returnAsXMLItem('applicationBlock',attributesAsXML,escape=False)
	def fromDOMNode(self,DOMNode):
		self.attributes=dictionaryFromXMLDOMNode(DOMNode)

class sortBlockObject:
	def __init__(self):
		self.attributes={}
		self.attributes['payload']=''
	def getSize(self):
		return len(self.attributes.get('payload','').decode('HEX'))

	def fromByteArray(self,dstr):
		self.attributes['payload']=dstr.encode('HEX')

	def toByteArray(self):
		return self.attributes.get('payload','').decode('HEX')
	
	def toXML(self):
		attributesAsXML=returnDictionaryAsXML(self.attributes)
		return returnAsXMLItem('sortBlock',attributesAsXML,escape=False)
	def fromDOMNode(self,DOMNode):
		self.attributes=dictionaryFromXMLDOMNode(DOMNode)

class BaseXMLReaderObject:
	def fromXML(self,fileStream,palmDatabaseObject):
		# IE call functions with names like 'parse_START_ELEMENT' and 'parse_END_ELEMENT'; the names are defined in
		# xml.dom.pulldom at the top of the source file.
		events = pulldom.parse(fileStream)
		for (event, node) in events:
			parseMethod=getattr(self, "parse_%s"%event,None)
			if parseMethod:
				parseMethod(events,node,palmDatabaseObject)

class GenericXMLReaderObject(BaseXMLReaderObject):
	def _callParseMethod(self,events,node,palmDatabaseObject,type):
		parseMethod=getattr(self, "parse_%s_%s"%(type,node.nodeName),None)
		if parseMethod:
			parseMethod(events,node,palmDatabaseObject)
	def parse_START_ELEMENT(self,events,node,palmDatabaseObject):
		self._callParseMethod(events,node,palmDatabaseObject,'START_ELEMENT')
	def parse_END_ELEMENT(self,events,node,palmDatabaseObject):
		self._callParseMethod(events,node,palmDatabaseObject,'END_ELEMENT')
		
class GeneralPalmDBXMLReaderObject(GenericXMLReaderObject):
	def parse_START_DOCUMENT(self,events,node,palmDatabaseObject):
		palmDatabaseObject.clear()
	def parse_START_ELEMENT_palmDatabase(self,events,node,palmDatabaseObject):
		# Set creatorID from header
		palmDatabaseObject.setCreatorID(node.attributes['type'].value)
	def parse_START_ELEMENT_palmHeader(self,events,node,palmDatabaseObject):
		events.expandNode(node)
		palmDatabaseObject._palmHeaderFromDOMNode(node)
	def parse_START_ELEMENT_palmCategories(self,events,node,palmDatabaseObject):
		events.expandNode(node)
		plugin=palmDatabaseObject._getPlugin()
		categoriesObject=plugin.createCategoriesObject(palmDatabaseObject)
		categoriesObject.fromDOMNode(node)
		palmDatabaseObject.setCategoriesObject(categoriesObject)
	def parse_START_ELEMENT_applicationBlock(self,events,node,palmDatabaseObject):
		events.expandNode(node)
		plugin=palmDatabaseObject._getPlugin()
		applicationInformationObject=plugin.createApplicationInformationObject(palmDatabaseObject)
		applicationInformationObject.fromDOMNode(node)
		palmDatabaseObject.setApplicationInformationObject(applicationInformationObject)
	def parse_START_ELEMENT_sortBlock(self,events,node,palmDatabaseObject):
		events.expandNode(node)
		plugin=palmDatabaseObject._getPlugin()
		sortBlockObject=plugin.createSortBlockObject(palmDatabaseObject)
		sortBlockObject.fromDOMNode(node)
		palmDatabaseObject.setSortBlockObject(sortBlockObject)
	def parse_START_ELEMENT_palmDataRecord(self,events,node,palmDatabaseObject):
		events.expandNode(node)
		plugin=palmDatabaseObject._getPlugin()
		palmRecord=plugin.createPalmDatabaseRecord(palmDatabaseObject)
		palmRecord.fromDOMNode(node)
		palmDatabaseObject.append(palmRecord)
	def parse_START_ELEMENT_palmResourceRecord(self,events,node,palmDatabaseObject):
		events.expandNode(node)
		plugin=palmDatabaseObject._getPlugin()
		palmRecord=plugin.createPalmDatabaseRecord(palmDatabaseObject)
		palmRecord.fromDOMNode(node)
		palmDatabaseObject.append(palmRecord)
