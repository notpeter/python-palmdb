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
from PalmDB.Util import setBooleanAttributeFromBits
from PalmDB.Util import setBitsFromBooleanAttribute
from PalmDB.Util import returnDictionaryAsXML
from PalmDB.Util import dictionaryFromXMLDOMNode
from PalmDB.Util import returnObjectAsXML
from PalmDB.Util import returnAsXMLItem
from PalmDB.Util import simpleRational
from PalmDB.Util import StructMap

# Load XSLT templates
from ProgectXSLT_GanttProject import XSLT_GanttProject_ToDesktop
from ProgectXSLT_GanttProject import XSLT_GanttProject_FromDesktop


XSLT_NativeXML_ToDesktop=\
'''
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
<xsl:template match="@*|node()">
<xsl:copy>
<xsl:apply-templates select="@*|node()"/>
</xsl:copy>
</xsl:template>
<xsl:template match="@id"/>
</xsl:stylesheet>
'''
XSLT_NativeXML_FromDesktop=XSLT_NativeXML_ToDesktop

XSLT_NativeXMLGZ_ToDesktop=XSLT_NativeXML_ToDesktop
XSLT_NativeXMLGZ_FromDesktop=XSLT_NativeXML_FromDesktop

# PDesk reads/writes the data raw for now...
XSLT_PDeskXML_ToDesktop=None
XSLT_PDeskXML_FromDesktop=None

XSLT_OMNIOutliner_ToDesktop=''
XSLT_OMNIOutliner_FromDesktop=''

class ProgectPrefsObject(StructMap):
	def __init__(self):
		StructMap.__init__(self)
		self.selfNetworkOrder('palmos')
		self.setConversion([\
			('format','uchar'),
			('reserved','uchar'),
			('hideDoneTasks','uchar'),
			('displayDueDates','uchar'),
			('displayPriorities','uchar'),
			('displayYear','uchar'),
			('useFatherStatus','uchar'),
			('autoSyncToDo','uchar'),
			('flatHideDone','uchar'),
			('flatDated','uchar'),
			('flatMinPriority','uchar'),
			('flatOr','uchar'),
			('flatMin','uchar'),
			('boldMinPriority','uchar'),
			('boldMinDays','uchar'),
			('strikeDoneTasks','uchar'),
			('hideDoneProgress','uchar'),
			('junk_TaskAttrType','ushort'),
			('junk_TaskFormatType','ushort'),
			('junk_priority','uchar'),
			('junk_completed','uchar'),
			('junk_dueDate','ushort'),
			('junk_description','uint'),
			('junk_note','uint'),
			('sortType','ushort'),
			('flatDateLimit','uchar'),
			('completionDate','uchar'),
			('flatCategories','ushort'),
			('wordWrapLines','uchar'),
			('drawTreeLines','uchar'),
			('completedGroup','uchar'),
			])
			
class ProgectAppInfoObject(PalmDB.Plugins.BasePlugin.applicationInformationObject):
	def __init__(self):
		self.progectPrefsObject=ProgectPrefsObject()
	def getSize(self):
	    return self.progectPrefsObject.getSize()
	def fromByteArray(self,dstr):
		self.progectPrefsObject.fromByteArray(dstr)
	def toByteArray(self):
		return self.progectPrefsObject.toByteArray()
	
	def toXML(self):
		attributesAsXML=returnDictionaryAsXML(self.progectPrefsObject)
		return returnAsXMLItem('applicationBlock',attributesAsXML,escape=False)
	def fromDOMNode(self,DOMNode):
		attributes=dictionaryFromXMLDOMNode(DOMNode)
		self.progectPrefsObject.update(attributes)


class ProgectPlugin(PalmDB.Plugins.BasePlugin.BasePDBFilePlugin):
	def getPDBCreatorID(self):
		return 'lbPG'
	def getPalmApplicationName(self):
		return 'Progect'
	def getApplicationNameFromFile(self,filename):
		# return tuple (ApplicationName,XSLT,GZIPResult)
		if filename.upper().endswith('.XML'):
			return 'NativeXML'
		if filename.upper().endswith('.XML.GZ'):
			return 'NativeXMLGZ'
		if filename.upper().endswith('.GAN'):
			return 'GanttProject'
		return None

	def createApplicationInformationObject(self,PalmDatabaseObject):
		return ProgectAppInfoObject()

	def getXSLTText(self,application,type):
		# have to create global vars with XSLT text
		XSLTEval='XSLT_%s_%s'%(application,type)
		try:
			xslt = eval(XSLTEval)
			return xslt
		except Exception, e:
			return None

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
		# +++ REMOVE THIS +++
#		print 'first real Progect record'
#		print PalmDatabaseObject[1].attributes
		# +++ REMOVE THIS +++
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
		self.currentHierarchyLevel=1
	def parse_START_DOCUMENT(self,events,node,palmDatabaseObject):
		PalmDB.Plugins.BasePlugin.GeneralPalmDBXMLReaderObject.parse_START_DOCUMENT(self,events,node,palmDatabaseObject)
		# add in a empty record, since Progect databases always have an empty record at the beginning
		ProgectFirstRecord=ProgectRecord()
		ProgectFirstRecord._setProgectFirstRecordProperties()
		palmDatabaseObject.append(ProgectFirstRecord)
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

def packProgectDate(date):
	if date == None:
		return 0
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

    # Setup ItemType defines
    PROGRESS_TYPE=0
    NUMERIC_TYPE=1
    ACTION_TYPE=2
    INFORMATIVE_TYPE=3
    EXTENDED_TYPE=4
    LINK_TYPE=5
    INVALID_TYPE=6
    # Setup ItemType text names
    typeTextNames={
        PROGRESS_TYPE:u'PROGRESS_TYPE',
        NUMERIC_TYPE:u'NUMERIC_PROGRESS_TYPE',
        ACTION_TYPE:u'ACTION_TYPE',
        INFORMATIVE_TYPE:u'INFORMATION_TYPE',
        EXTENDED_TYPE:u'EXTENDED_TYPE',
        LINK_TYPE:u'LINK_TYPE',
        INVALID_TYPE:u'INVALID_TYPE',
        }
    # Setup reverse ItemType text names
    reverseTypeTextNames={}
    (keys,values)=zip(*typeTextNames.items())
    reverseTypeTextNames.update(zip(values,keys))
    
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
	    
    def _setProgectFirstRecordProperties(self):
	    self.attributes={'itemType': u'PROGRESS_TYPE','_hasDuration': False,'hasLink': False, '_hasDueDate': True,
			     'dueDate': None, '_hasNext': False, 'uid': 1638401, 'category': 0, 'priority': 'None',
			     'busy': False, 'opened': True, '_hasPrevious': False, '_newFormat': True, 'note': u'',
			     'deleted': False, 'secret': False, '_nextFormat': False, 'description': u'', '_hasNote': False,
			     '_hasChild': True, 'completed': simpleRational(numerator=0,denominator=10), '_hasXB': False,
			     '_newTask': True, 'hasToDo': False, '_level': 0, '_hasPrev': False, 'dirty': True,
			     '_hasPred': False, '_hasStartDate': False}	    
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

	    # set _hasXB
	    if self.attributes['itemType'] == 'NUMERIC_PROGRESS_TYPE':
		    self.attributes['_hasXB']=True
	    for testFor in ['icon','linkToDo','linkLinkMaster']:
		    if self.attributes.has_key(testFor):
			    self.attributes['_hasXB']=True
			    break
	    # set some static flags
	    self.attributes['_nextFormat']=True
	    self.attributes['_newFormat']=True
	    self.attributes['_newTask']=False
	    # Some of these may need to be setup
	    # _hasStartdate
	    # _hasPred
	    # _hasNote
	    # _hasDueDate
	    # _hasNext
	    # _hasDuration
	    # _hasPrevious
	    # _hasChild
	    # _level

    def fromDOMNode(self,DOMNode):
	    pass
    
    def _crackPayload(self,dstr):
        if len(dstr) < PRI.TaskAttrTypeStructSize:
            raise IOError, "Error: raw data passed in is too small; required (%d), available (%d)"%(PRI.TaskAttrTypeStructSize,len(dstr))

        (taskAttrType, taskFormatType)= \
            struct.unpack(PRI.TaskAttrTypeStructString,dstr[:PRI.TaskAttrTypeStructSize])

        # setup AttrType bits
        self.attributes['_level']=getBits( taskAttrType, 15, 8 )
        setBooleanAttributeFromBits(self.attributes,'_hasNext',taskAttrType,7)
        setBooleanAttributeFromBits(self.attributes,'_hasChild',taskAttrType,6)
        setBooleanAttributeFromBits(self.attributes,'opened',taskAttrType,5)
        setBooleanAttributeFromBits(self.attributes,'_hasPrev',taskAttrType,4)

        # TaskFormatType values
        setBooleanAttributeFromBits(self.attributes,'_hasStartDate',taskFormatType,15)
    	setBooleanAttributeFromBits(self.attributes,'_hasPred',taskFormatType,14)
        setBooleanAttributeFromBits(self.attributes,'_hasDuration',taskFormatType,13)
        setBooleanAttributeFromBits(self.attributes,'_hasDueDate',taskFormatType,12)
        setBooleanAttributeFromBits(self.attributes,'hasToDo',taskFormatType,11)
        setBooleanAttributeFromBits(self.attributes,'_hasNote',taskFormatType,10)
        setBooleanAttributeFromBits(self.attributes,'hasLink',taskFormatType,9)

        itemType=getBits( taskFormatType, 8, 5 )
        self.attributes['itemType']=PRI.typeTextNames[itemType]
        setBooleanAttributeFromBits(self.attributes,'_hasXB',taskFormatType,3)
        setBooleanAttributeFromBits(self.attributes,'_newTask',taskFormatType,2)
        setBooleanAttributeFromBits(self.attributes,'_newFormat',taskFormatType,1)
        setBooleanAttributeFromBits(self.attributes,'_nextFormat',taskFormatType,0)
	    
        if self.attributes['_hasXB']:
            XBSize=self.fromByteArrayTaskXBRecords(dstr[PRI.TaskAttrTypeStructSize:])
            # XB Offset will always be two more than the size variable, to account for the variable embedded in the structure
            self.fromByteArrayTaskStandardFields(dstr[PRI.TaskAttrTypeStructSize+2+XBSize:])
        else:
            self.fromByteArrayTaskStandardFields(dstr[PRI.TaskAttrTypeStructSize:])
    def _packPayload(self):
        dstr=''

	XBRecordsData=self.toByteArrayTaskXBRecords()

        # setup AttrType bits
	taskAttrType=0
        taskAttrType=setBits(taskAttrType,self.attributes['_level'],15,8)
        taskAttrType=setBitsFromBooleanAttribute(self.attributes,'_hasNext',taskAttrType,7)
        taskAttrType=setBitsFromBooleanAttribute(self.attributes,'_hasChild',taskAttrType,6)
        taskAttrType=setBitsFromBooleanAttribute(self.attributes,'opened',taskAttrType,5)
        taskAttrType=setBitsFromBooleanAttribute(self.attributes,'_hasPrev',taskAttrType,4)

        # TaskFormatType values
	taskFormatType=0
        taskFormatType=setBitsFromBooleanAttribute(self.attributes,'_hasStartDate',taskFormatType,15)
    	taskFormatType=setBitsFromBooleanAttribute(self.attributes,'_hasPred',taskFormatType,14)
        taskFormatType=setBitsFromBooleanAttribute(self.attributes,'_hasDuration',taskFormatType,13)
        taskFormatType=setBitsFromBooleanAttribute(self.attributes,'_hasDueDate',taskFormatType,12)
        taskFormatType=setBitsFromBooleanAttribute(self.attributes,'hasToDo',taskFormatType,11)
        taskFormatType=setBitsFromBooleanAttribute(self.attributes,'_hasNote',taskFormatType,10)
        taskFormatType=setBitsFromBooleanAttribute(self.attributes,'hasLink',taskFormatType,9)

	itemType=PRI.reverseTypeTextNames[self.attributes['itemType']]
	taskFormatType=setBits(taskFormatType,itemType,8,5)

	if len(XBRecordsData):
		taskFormatType=setBits(taskFormatType,1,3)
	else:
		taskFormatType=setBits(taskFormatType,0,3)

        taskFormatType=setBitsFromBooleanAttribute(self.attributes,'_newTask',taskFormatType,2)
        taskFormatType=setBitsFromBooleanAttribute(self.attributes,'_newFormat',taskFormatType,1)
        taskFormatType=setBitsFromBooleanAttribute(self.attributes,'_nextFormat',taskFormatType,0)

	# Pack header information
	dstr+=struct.pack(PRI.TaskAttrTypeStructString,taskAttrType,taskFormatType)

	dstr+=XBRecordsData
	dstr+=self.toByteArrayTaskStandardFields()
	return dstr
    def fromByteArrayTaskXBRecords( self, dstr ):
	    xbFactory=ExtraBlockRecordFactory()
	    (XBSize,self.extraBlockRecordList)=xbFactory.fromByteArray(dstr)
	    return XBSize
    def toByteArrayTaskXBRecords(self):
        # first build up our XBRecordList, this may be lossy since we will only create
	# XBRecords that are logical for the record type, and Progect keeps extrablocks
	# around if you change the type of a task.
	# This should be fixed (so that we don't lose the information) when we create the
	# new Progect file format.
        XBRecordList=[]
	if self.attributes.get('icon',False):
		XBRecordList.append(ExtraBlockIcon(self.attributes['icon']))
		
        if self.attributes['itemType'] == 'NUMERIC_PROGRESS_TYPE':
		XBRecordList.append(ExtraBlockNumeric(self.attributes.get('completed',simpleRational(0,1))))

        if self.attributes.get('linkToDo',False):
		XBRecordList.append(ExtraBlockLinkToDo(self.attributes['linkToDo']))

        if self.attributes.get('linkLinkMaster',False):
		XBRecordList.append(ExtraBlockLinkLinkMaster(self.attributes['linkLinkMaster']))

#+++ FIX THIS +++ Need to pull in more items here

	# if no XB Records, then just return an empty string
	if len(XBRecordList) == 0:
		return ''
	
	xbFactory=ExtraBlockRecordFactory()
	dstr=xbFactory.toByteArray(XBRecordList)
	return dstr
    def fromByteArrayTaskStandardFields( self, dstr ):
        # we don't currently handle links
        if self.attributes['hasLink']:
	    print 'dropping link record....'
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
        self.attributes['description']=text.split('\0')[0].decode('palmos')
        self.attributes['note']=text.split('\0')[1].decode('palmos')
    def toByteArrayTaskStandardFields( self):
        dstr=''

        # now correct dueDate field
	dueDate=packProgectDate(self.attributes.get('dueDate',None))
	if self.attributes['priority']=='None':
		priority=6
	else:
		priority=self.attributes['priority'].numerator

	completed=0
        if self.attributes['itemType'] == 'ACTION_TYPE':
		if self.attributes['completed']:
			completed=10
		else:
			completed=0
        if self.attributes['itemType'] == 'PROGRESS_TYPE':
		completed=self.attributes['completed'].numerator

	dstr+=struct.pack(PRI.TaskStandardFieldStructString,priority,completed,dueDate)
	dstr+=self.attributes['description'].encode('palmos')+'\0'
	dstr+=self.attributes['note'].encode('palmos')+'\0'
	return dstr
class ExtraBlockNULL(object):
    def fromByteArray( self, raw ):
	self.raw=raw
    def toByteArray(self):
        return self.raw
    def __repr__( self ):
       return 'ExtraBlockNULL(raw="%s")'%self.raw
    def toXML(self):
        return ''

class ExtraBlockLinkToDo(object):
    def fromByteArray( self, raw ):
	self.raw=raw
    def toByteArray(self):
        return self.raw
    def __repr__( self ):
       return 'ExtraBlockLinkToDo(raw="%s")'%self.raw
    def toXML(self):
        return returnObjectAsXML('linkToDo',self.raw)

class ExtraBlockLinkLinkMaster(object):
    def fromByteArray( self, raw ):
	self.raw=raw
    def toByteArray(self):
        return self.raw
    def __repr__( self ):
       return 'ExtraBlockLinkLinkMaster(raw="%s")'%self.raw
    def toXML(self):
        return returnObjectAsXML('linkLinkMaster',self.raw)

class ExtraBlockIcon(object):
    def __init__(self,icon=0):
	    self.icon=icon
    def fromByteArray( self, raw ):
        (self.icon,)=struct.unpack(">H", raw)
    def toByteArray( self ):
        return struct.pack(">H", self.icon)
    def __repr__( self ):
       return 'ExtraBlockIcon(icon=%d)'%self.icon
    def toXML(self):
        return returnObjectAsXML('icon',self.icon)

class ExtraBlockNumeric(object):
    def __init__(self,rational=simpleRational(1,1)):
	    self.actual=rational.numerator
	    self.limit=rational.denominator
    def fromByteArray( self, raw ):
        (self.limit,self.actual)=struct.unpack(">HH",raw)
    def toByteArray( self ):
        return struct.pack(">HH",self.limit,self.actual)
    def __repr__( self ):
       return 'ExtraBlockNumeric(limit=%d,actual=%d)'%(self.limit,self.actual)
    def toXML(self):
       returnValue=returnObjectAsXML('completed',simpleRational(self.actual,self.limit))
       return returnValue

class ExtraBlockUnknown(object):
    def fromByteArray( self, raw ):
	self.raw=raw
    def toByteArray(self):
        return self.raw
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

    def fromByteArray( self, dstr ):
        extraBlockRecordList=[]
        (self.XBSize,)=struct.unpack(PRI.XBFieldsStructString,dstr[:PRI.XBFieldsStructSize])

        xbRecordFactory=ExtraBlockRecordFactory()
        xbRaw=dstr[PRI.XBFieldsStructSize:PRI.XBFieldsStructSize+self.XBSize]
        while len(xbRaw):
            (xbRecord,xbRecordSize)=self.recordFromByteArray(xbRaw)
            extraBlockRecordList.append(xbRecord)
            xbRaw=xbRaw[xbRecordSize:]

	return (self.XBSize,extraBlockRecordList)
    def toByteArray(self,extraBlockRecordList):
        dstr=''
	recordDstr=''

	for xbRecord in extraBlockRecordList:
		recordDstr+=self.recordToByteArray(xbRecord)

	size=len(recordDstr)
        dstr+=struct.pack(PRI.XBFieldsStructString,size)
	dstr+=recordDstr
	return dstr
    def recordFromByteArray( self, raw ):
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
    def recordToByteArray( self, xbRecord ):
        dstr=''
	
        if xbRecord.__class__.__name__ == 'ExtraBlockNULL':
		type=self.Extra_NULL
        if xbRecord.__class__.__name__ == 'ExtraBlockLinkToDo':
		type=self.Extra_Link_ToDo
        if xbRecord.__class__.__name__ == 'ExtraBlockLinkLinkMaster':
		type=self.Extra_Link_LinkMaster
        if xbRecord.__class__.__name__ == 'ExtraBlockIcon':
		type=self.Extra_Icon
        if xbRecord.__class__.__name__ == 'ExtraBlockNumeric':
		type=self.Extra_Numeric
	# toss unknown records, we aren't really setup to handle them yet
		
	recordDstr=xbRecord.toByteArray()
	size=len(recordDstr)
	subKey=0   # currently not used
	reserve1=0 # Currently not used
	dstr+=struct.pack(self.__packString,type,subKey,reserve1,size)
	dstr+=recordDstr
	return dstr
