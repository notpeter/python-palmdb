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
import datetime
import PalmDB.Plugins.BasePlugin

from PalmDB.Util import getBits
from PalmDB.Util import setBits
from PalmDB.Util import returnDictionaryAsXML
from PalmDB.Util import dictionaryFromXMLDOMNode
from PalmDB.Util import returnObjectAsXML
from PalmDB.Util import returnAsXMLItem
from PalmDB.Util import simpleRational

class ProgectPlugin(PalmDB.Plugins.BasePlugin.BasePDBFilePlugin):
	def getPDBCreatorID(self):
		return 'lbPG'

	def createPalmDatabaseRecord(self,PalmDatabaseObject):
            return ProgectRecord()

	def getRecordsAsXML(self,PalmDatabaseObject):
		recordsXML=''
		# Iterate over records and create XML, kind of a pain because the data is stored as a list
		# but is really a hierarchy, so we have to do ugly stuff.

		# first record is some garbage record, I can't remember what it is for
		# but real records are it's child so lastLevel starts at 1
		lastLevel=1
		lastHasNext=1
		thisLevel=1
		openLevel=0
		recordNumber=1
		for record in PalmDatabaseObject[1:]:
			if not lastHasNext:
				for i in range(lastLevel-record.attributes['_level']-1,-1,-1):
					recordsXML+='</children>'
					recordsXML+='</%s>'%record.getRecordXMLName()
					openLevel-=1

			recordsXML+='<%s>'%(record.getRecordXMLName())
			recordsXML+=record.toXML()
			if record.attributes['_hasChild']:
				recordsXML+='<children>'
				openLevel+=1
			else:
				recordsXML+='</%s>'%record.getRecordXMLName()

			lastLevel=record.attributes['_level']
			lastHasNext=record.attributes['_hasNext']
			thisLevel=record.attributes['_level']
			recordNumber+=1

		if not lastHasNext:
			for i in range(thisLevel-1):
				recordsXML+='</children>'
				recordsXML+='</%s>'%record.getRecordXMLName()
				openLevel-=1
		return recordsXML
	def getXMLReaderObject(self,PalmDatabaseObject):
		return ProgectPalmDBXMLReaderObject()
	
class ProgectPalmDBXMLReaderObject(PalmDB.Plugins.BasePlugin.GeneralPalmDBXMLReaderObject):
	def __init__(self):
		self.previousPalmRecords={}
		self.currentPalmRecord=None
		self.currentHierarchyLevel=0
	def parse_START_ELEMENT_ProgectDataRecord(self,events,node,palmDatabaseObject):
		# Set _hasNext
		try:
			self.previousPalmRecords[self.currentHierarchyLevel].attributes['_hasNext']=True
		except KeyError:
			pass

		plugin=palmDatabaseObject._getPlugin()
		self.currentPalmRecord=plugin.createPalmDatabaseRecord(palmDatabaseObject)
		self.currentPalmRecord.fromDOMNode(node)

		self.currentPalmRecord.attributes['_level']=self.currentHierarchyLevel
		self.previousPalmRecords[self.currentHierarchyLevel]=self.currentPalmRecord

		# Set _hasPrev
		if self.previousPalmRecords.get(self.currentHierarchyLevel,None):
			self.currentPalmRecord.attributes['_hasPrevious']=True
		
		palmDatabaseObject.append(self.currentPalmRecord)

	def parse_START_ELEMENT_recordAttributes(self,events,node,palmDatabaseObject):
		events.expandNode(node)
		self.currentPalmRecord.recordAttributesFromDOMNode(node)

	def parse_START_ELEMENT_children(self,events,node,palmDatabaseObject):
		self.previousPalmRecords[self.currentHierarchyLevel].attributes['_hasChild']=True

		self.currentHierarchyLevel+=1
		# since we are starting a level, there cannot be a previous item at our level
		try:
			del(self.previousPalmRecords[self.currentHierarchyLevel])
		except KeyError:
			pass
		
	def parse_END_ELEMENT_children(self,events,node,palmDatabaseObject):
		self.currentHierarchyLevel-=1

def crackProgectDate(variable):
	# Date due field:
    	# This field seems to be layed out like this:
    	#     year  7 bits (0-128)
    	#     month 4 bits (0-16)
    	#     day   5 bits (0-32)
	year = getBits(variable,15,7)
	if year <> 0:
		year += 1904
	else:
		return None

	return datetime.date(year,getBits(variable,8,4),getBits(variable,4,5))

def packProgectDate(year,date):
	returnValue=0
	returnValue=setBits(date.year-1904,returnValue,15,7)
	returnValue=setBits(date.month,returnValue,8,4)
	returnValue=setBits(date.day,returnValue,4,5)
	return returnValue

# Progect Record Information
class PRI:
    # 8 bits for level
    # 8 bits for: (hasNext,hasChild, opened,hasPrev) and 4 bits for reserved
    # 16 bits for: 
    # 1 bit each - (hasStartDate,hasPred,hasDuration,hasDueDate,hasToDo,hasNote,hasLink);
    # 5 bits - itemType; 
    # 1 bit each (hasXB,newTask,newFormat,nextFormat)
    TaskAttrTypeStructString = '>HH'
    TaskAttrTypeStructSize=struct.calcsize(TaskAttrTypeStructString)

    # 8 bits for priority
    # 8 bits for completed
    # 16 bits for dueDate;
    TaskStandardFieldStructString = '>BBH' # the first H is padding...
    TaskStandardFieldStructSize=struct.calcsize(TaskStandardFieldStructString)

    # 16 bits for size
    XBFieldsStructString = '>H'
    XBFieldsStructSize=struct.calcsize(XBFieldsStructString)

    # ItemType defines
    PROGRESS_TYPE=0
    NUMERIC_TYPE=1
    ACTION_TYPE=2
    INFORMATIVE_TYPE=3
    EXTENDED_TYPE=4
    LINK_TYPE=5
    INVALID_TYPE=6

    typeTextNames={
        PROGRESS_TYPE:u'PROGRESS_TYPE',
        NUMERIC_TYPE:u'NUMERIC_PROGRESS_TYPE',
        ACTION_TYPE:u'ACTION_TYPE',
        INFORMATIVE_TYPE:u'INFORMATION_TYPE',
        EXTENDED_TYPE:u'EXTENDED_TYPE',
        LINK_TYPE:u'LINK_TYPE',
        INVALID_TYPE:u'INVALID_TYPE',
        }
    
class ProgectRecord(PalmDB.Plugins.BasePlugin.DataRecord):
    '''
    This class encapsulates a Palm application record.

    Comparison and hashing are done by ID; thus, the id value 
    *may not be changed* once the object is created. You need to call
    fromByteArray() and getRaw() to set the raw data.
    '''
    def __init__(self):
        PalmDB.Plugins.BasePlugin.DataRecord.__init__(self)

	self.clear()
        
    def clear(self):
        self.attributes.clear()
        self.attributes['_level']=0
        self.attributes['_hasNext']=False
    	self.attributes['_hasChild']=False
    	self.attributes['opened']=False
    	self.attributes['_hasPrevious']=False

        self.attributes['description']=''
        self.attributes['note']=''

        self.extraBlockRecordList=[]
	    
    def getRecordXMLName(self):
	    return 'ProgectDataRecord'

    def toXML(self):
        attributesAsXML=returnDictionaryAsXML(self.attributes)
        for extraBlock in self.extraBlockRecordList:
            attributesAsXML+=extraBlock.toXML()
	return returnAsXMLItem('recordAttributes',attributesAsXML,escape=False)
    def recordAttributesFromDOMNode(self,DOMNode):
	    # self.clear() can't use clear because of the order that things are called
	    # should not matter anyway, we creat a new object for each row
	    attributesDict=dictionaryFromXMLDOMNode(DOMNode)
	    self.attributes.update(attributesDict)
    def fromDOMNode(self,DOMNode):
	    pass
    
    def fromByteArray(self,hstr,dstr):
        self._crackRecordHeader(hstr)

        if len(dstr) < PRI.TaskAttrTypeStructSize:
            raise IOError, "Error: raw data passed in is too small; required (%d), available (%d)"%(PRI.TaskAttrTypeStructSize,len(dstr))

        
        (taskAttrType, taskFormatType)= \
            struct.unpack(PRI.TaskAttrTypeStructString,dstr[:PRI.TaskAttrTypeStructSize])

        # setup AttrType bits, level was handled above
        self.attributes['_level']=getBits( taskAttrType, 15, 8 )
        self.attributes['_hasNext']=bool(getBits( taskAttrType, 7 ))
        self.attributes['_hasChild']=bool(getBits( taskAttrType, 6 ))
        self.attributes['opened']=bool(getBits( taskAttrType, 5 ))
        self.attributes['_hasPrev']=bool(getBits( taskAttrType, 4 ))
    

        # TaskFormatType values
        self.attributes['_hasStartDate']=bool(getBits( taskFormatType, 15 ))
    	self.attributes['_hasPred']=bool(getBits( taskFormatType, 14 ))
        self.attributes['_hasDuration']=bool(getBits( taskFormatType, 13 ))
        self.attributes['_hasDueDate']=bool(getBits( taskFormatType, 12 ))
        self.attributes['hasToDo']=bool(getBits( taskFormatType, 11 ))
        self.attributes['_hasNote']=bool(getBits( taskFormatType, 10 ))
        self.attributes['hasLink']=bool(getBits( taskFormatType, 9 ))

        itemType=getBits( taskFormatType, 8, 5 )
        self.attributes['itemType']=PRI.typeTextNames[itemType]
        self.attributes['_hasXB']=bool(getBits( taskFormatType, 3 ))
        self.attributes['_newTask']=bool(getBits( taskFormatType, 2 ))
        self.attributes['_newFormat']=bool(getBits( taskFormatType, 1 ))
        self.attributes['_nextFormat']=bool(getBits( taskFormatType, 0 ))
	    
        if self.attributes['_hasXB']:
            self.fromByteArrayTaskXBRecords(dstr[PRI.TaskAttrTypeStructSize:])
            # XBSize will always be two more than the size variable, to account for the variable
            self.XBSize+=2
            self.fromByteArrayTaskStandardFields(dstr[PRI.TaskAttrTypeStructSize+self.XBSize:])
        else:
            self.fromByteArrayTaskStandardFields(dstr[PRI.TaskAttrTypeStructSize:])
    
    def fromByteArrayTaskXBRecords( self, dstr ):
        (self.XBSize,)=struct.unpack(PRI.XBFieldsStructString,dstr[:PRI.XBFieldsStructSize])

        xbRecordFactory=ExtraBlockRecordFactory()
        xbRaw=dstr[PRI.XBFieldsStructSize:PRI.XBFieldsStructSize+self.XBSize]
        while len(xbRaw):
            (xbRecord,xbRecordSize)=xbRecordFactory.fromByteArray(xbRaw)
            self.extraBlockRecordList.append(xbRecord)
            xbRaw=xbRaw[xbRecordSize:]

    def fromByteArrayTaskStandardFields( self, dstr ):
        # we don't currently handle links
        if self.attributes['hasLink']:
            self.attributes['description']='Links Not Supported'
            self.attributes['note']='Links Not Supported'
            return

        ( priority,completed,dueDate )= struct.unpack( PRI.TaskStandardFieldStructString, dstr[:PRI.TaskStandardFieldStructSize] )
        # now correct dueDate field
        self.attributes['dueDate']=crackProgectDate(dueDate)
        if (priority == 0) or (priority == 6):
            self.attributes['priority']='None'
        else:
            self.attributes['priority']=simpleRational(priority,5)

        if self.attributes['itemType'] == 'ACTION_TYPE':
            self.attributes['completed']=bool(completed)
        if self.attributes['itemType'] == 'PROGRESS_TYPE':
            self.attributes['completed']=simpleRational(completed,10)

        text=dstr[PRI.TaskStandardFieldStructSize:]
        self.attributes['description']=text.split('\0')[0]
        self.attributes['note']=text.split('\0')[1]



class ExtraBlockNULL(object):
    def fromByteArray( self, raw ):
	self.raw=raw
    def __repr__( self ):
       return 'ExtraBlockNULL(raw="%s")'%self.raw
    def toXML(self):
        return ''

class ExtraBlockLinkToDo(object):
    def fromByteArray( self, raw ):
	self.raw=raw
    def __repr__( self ):
       return 'ExtraBlockLinkToDo(raw="%s")'%self.raw
    def toXML(self):
        return returnObjectAsXML('linkToDo',self.raw)

class ExtraBlockLinkLinkMaster(object):
    def fromByteArray( self, raw ):
	self.raw=raw
    def __repr__( self ):
       return 'ExtraBlockLinkLinkMaster(raw="%s")'%self.raw
    def toXML(self):
        return returnObjectAsXML('linkLinkMaster',self.raw)

class ExtraBlockIcon(object):
    def fromByteArray( self, raw ):
        (self.icon,)=struct.unpack(">H", raw)
    def __repr__( self ):
       return 'ExtraBlockIcon(icon=%d)'%self.icon
    def toXML(self):
        return returnObjectAsXML('icon',self.icon)

class ExtraBlockNumeric(object):
    def fromByteArray( self, raw ):
        (self.limit,self.actual)=struct.unpack(">HH",raw)
    def __repr__( self ):
       return 'ExtraBlockNumeric(limit=%d,actual=%d)'%(self.limit,self.actual)
    def toXML(self):
       returnValue=returnObjectAsXML('completed',simpleRational(self.actual,self.limit))
       return returnValue

class ExtraBlockUnknown(object):
    def fromByteArray( self, raw ):
	self.raw=raw
    def __repr__( self ):
       return 'ExtraBlockUnknown(raw="%s")'%self.raw
    def toXML(self):
        return returnObjectAsXML('extraBlockUnknown',self.raw)


class ExtraBlockRecordFactory( object ):
    def __init__(self):
        self.__packString = '>BBBB'
        self.__packSize = struct.calcsize( self.__packString )

        self.Extra_NULL=0 # sentinel for block tail, must be subkey is zero.
        self.Extra_Description=1 # currently not used.
        self.Extra_Note=2 # currently not used.
        self.Extra_Link_ToDo=20
        self.Extra_Link_LinkMaster=21
        self.Extra_Icon=50
        self.Extra_Numeric=51 # for numeric type

    def fromByteArray( self, raw ):
        '''
        Set raw data to marshall class.
        '''
        if len(raw) < self.__packSize:
            raise IOError, "Error: raw data passed in is too small; required (%d), available (%d)"%(self.__packSize,len(raw))

        (type,subKey,reserve1,size)= \
            struct.unpack( self.__packString, raw[:self.__packSize] )
        body=raw[self.__packSize:self.__packSize+size]
        if type == self.Extra_NULL:
            newRecord=ExtraBlockNULL()
        elif type == self.Extra_Link_ToDo:
            newRecord=ExtraBlockLinkToDo()
        elif type == self.Extra_Link_LinkMaster:
            newRecord=ExtraBlockLinkLinkMaster()
        elif type == self.Extra_Icon:
            newRecord=ExtraBlockIcon()
        elif type == self.Extra_Numeric:
            newRecord=ExtraBlockNumeric()
        else:
            newRecord=ExtraBlockUnknown()

        newRecord.fromByteArray(body)
	return (newRecord,self.__packSize+size)
