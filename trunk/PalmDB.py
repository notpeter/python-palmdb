Have to break this file into a few pieces:

XML utilities
Base plugin code
Main body code (IE PalmDB.py that holds just the basics and __main__)
File derivative code?
Plugins directory
PDB processing code


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

def getBits(variable,MSBBitIndex,bitCount=1):
    """
    This function is for.... Does ....?
    """
    # MSBBitIndex is zero based
    shift=MSBBitIndex-bitCount+1
    bitsToMask=pow(2,bitCount)-1
    mask=bitsToMask<<shift
    result=variable & mask
    result=result>>shift
    return result

def setBits(value,variable,MSBBitIndex,bitCount=1):
	# MSBBitIndex is zero based

	# +++ FIX THIS +++ this needs to be implemented
	pass

def crackPalmDate(variable):
        if variable == 0:
            return None
        else:
            return datetime.datetime.fromtimestamp(variable-PILOT_TIME_DELTA)

def packPalmDate(variable):
        return time.mktime(variable.timetuple())+PILOT_TIME_DELTA

#
# XML Helper Functions
#
def escapeForXML(text):
        return text.replace(u"&", u"&amp;")\
               .replace(u"<", u"&lt;")\
               .replace(u">", u"&gt;")\
               .replace(u"'", u"&apos;")\
               .replace(u'"', u"&quot;")

def returnObjectAsXML(itemName,item):
    if item == None:
	return ''

    if item.__class__.__name__ == 'int':
	return returnAttributeAsXML(itemName,'integer',item)
    if item.__class__.__name__ == 'float':
	return returnAttributeAsXML(itemName,'real',item)
    if item.__class__.__name__ == 'str':
	return returnAttributeAsXML(itemName,'string',item)
    if item.__class__.__name__ == 'bool':
	return returnAttributeAsXML(itemName,'boolean',item)
    if item.__class__.__name__.startswith('date'):
        (year,month,day,hour,minutes,seconds,weekday,yearday,dstAdjustment)=item.timetuple()
        return '<attribute name="%s"><date year="%d" month="%d" day="%d" hour="%d" minutes="%d" seconds="%d"/></attribute>\n'%\
            (itemName,year,month,day,hour,minutes,seconds)

    return returnAttributeAsXML(itemName,'unknownType',item)
    
def returnRationalAsXML(itemName,numerator,denominator):
    return '<attribute name="%s"><rational numerator="%d" denominator="%d"/></attribute>\n'%(itemName,numerator,denominator)

def returnAttributeAsXML(itemName,itemType,item,escape=True):
    if escape:
        itemAsString=escapeForXML(str(item))
    else:
        itemAsString=str(item)

    if len(itemAsString) or not XMLsuppressFalseOrBlank:
        return '<attribute name="%s"><%s value="%s"/></attribute>\n'%(itemName,itemType,itemAsString)
    else:
        return ''

def returnAsXMLItem(itemName,item,escape=True):
    if escape:
        itemAsString=escapeForXML(str(item))
    else:
        itemAsString=str(item)

    if len(itemAsString) or not XMLsuppressFalseOrBlank:
        return '<%s>%s</%s>\n'%(itemName,itemAsString,itemName)
    else:
        return ''


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

# you need to pass the AppBlock into this class in the constructor
class Categories(dict):
    '''
    This class encapsulates Palm Categories.

    Currently renaming categories or adding/deleting categories is not supported.
    As of this writing, you may only have 16 categories, and this code us unable
    to handle anything other than that.
    
    This class is not used by any other class in this module. Its only purpose
    is if you want to extract category data from the AppInfo block (provided
    that it contains category data...)
    '''
    def __init__(self,raw=None):
        '''
        To initialize the class with the categories from a database, pass it 
        calcsize() bytes from the beginning of the application info block.
        Doing so will probably be easier if we can make calcsize a class variable
        so here is the current recommended way of doing it.
        x = PalmDB.Categories()
        x.SetRaw(applicationInfoBlock[:x.calcsize())
        '''

        self.__packString = '!H'+('16s'*16)+('B'*16)+'B'+'x'
        if raw <> None:
            self.setRaw(raw)

    def setRaw(self,raw):
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

    def getRaw(self):
        '''
        Get raw data to marshal class

        This function returns the binary form of the categories used in a Palm database.
        You need to copy the bytes returned by this function to the beginning of the 
        application info block. The string returned will be calcsize() bytes long.
        '''
	return struct.pack(self.__packString,*([self.renamedCategories]+self.categoryLabels+self.categoryUniqIDs+[self.lastUniqID]))

    def getXML(self):
        returnValue=''
        for key in self.keys():
            returnValue+=returnAsXMLItem('category',returnObjectAsXML('CategoryID',key)+returnObjectAsXML('CategoryName',self[key]),escape=False)
        return returnAsXMLItem('palmCategories',returnValue,escape=False)

    def calcsize(self):
        '''
        Return the packed structure size of the Palm category information.
        '''
        return struct.calcsize(self.__packString)

    def getTestData(self):
        '''
        Return some data suitable for testing.
        '''
        a =  map(lambda x : 'Test String' + str(x) ,range(16))
        b = range(16)
        return struct.pack(self.__packString,*([0]+a+b+[15]))

# +++ FIX THIS +++
# perhaps numrec, nextrec and a few more like that should be *magic* where they pick up their
# values from the parent PalmDatabase on the fly
# +++ FIX THIS +++

class PalmDatabaseInfo(dict):
    '''
    This class encapsulates information from the Palm database header.

    To initialize the class with the Database header, pass it calcsize() 
    bytes from the beginning of the file. Doing so will probably be easier
    if we can make calcsize a class variable so here is the current
    recommended way of doing it.
    x = PalmDB.PalmDatabaseInfo()
    x.SetRaw(rawData[:x.calcsize())
    
    All times (i.e. modifyDate, backupDate, createDate) are the number of
    seconds since the epoch (Jan. 1, 1970, 12AM).
    '''
    def __init__(self,raw=None):
        '''
        Initialize class.

        To initialize the class with the Database header, pass it calcsize() 
        bytes from the beginning of the file. Doing so will probably be easier
        if we can make calcsize a class variable so here is the current
        recommended way of doing it.
        x = PalmDB.PalmDatabaseInfo()
        x.SetRaw(rawData[:x.calcsize())
        '''
        self.__packString='>32shhLLLlll4s4sllh'
        self.clear()
        if raw <> None:
            self.setRaw(raw)
        else:
            self.clear()

    def clear(self):
        '''
        Reset all class data to the defaults.
        '''
        dict.clear(self)
        self.update({
            'name': '',
            'type': 'DATA',
            'creator': '    ',
            'createDate': 0,
            'modifyDate': 0,
            'backupDate': 0,
            'modnum': 0,
            'version': 0,
            'flagReset': False,
            'flagResource': False,
            'flagNewer': False,
            'flagExcludeFromSync': False,
            'flagAppInfoDirty': False,
            'flagReadOnly': False,
            'flagBackup': False,
            'flagOpen': False,
            'more': 0,
            'index': 0,
            'uid' : 0,
            'nextrec' : 0,
            'numrec' : 0,
            })

    def calcsize(self):
        '''
        Return the packed structure size of the Palm Database header.
        '''
        return struct.calcsize(self.__packString)

    def getTestData(self):
        '''
        Return some data suitable for testing.
        !!!Warning!!! destroys any current data in class.
        '''
        self.clear()
        return self.getRaw()

    def _updateNumberOfRecords(self,parentDbObject):
        """
        Takes a PalmDatabase instance as the argument, and updates the
        number-of-records field of the this PalmDatabaseInfo class instance.
        """
        
        numberOfRecords = len(parentDbObject)
        self['numrec'] = numberOfRecords

    def setRaw(self,raw):
        '''
        Set raw data to marshall class.

        To initialize the class with the Database header, pass it calcsize() 
        bytes from the beginning of the file. Doing so will probably be easier
        if we can make calcsize a class variable so here is the current
        recommended way of doing it.
        x = PalmDB.PalmDatabaseInfo()
        x.SetRaw(rawData)
        '''
        requiredBytes = self.calcsize()

        if len(raw) < requiredBytes: raise ValueError, _("Too little data passed in.")

        (name, flags, ver, ctime, mtime, btime, mnum, appinfo_offset, sortinfo_offset,
            typ, creator, uid, nextrec, numrec) \
            = struct.unpack(self.__packString, raw[:requiredBytes])

        if nextrec or appinfo_offset < 0 or sortinfo_offset < 0 or numrec < 0:
            raise ValueError, _("Invalid database header.")
        mydata = {
            'name': name.split('\0')[0],
            'type': typ,
            'creator': creator,
            'createDate': ctime,
            'modifyDate': mtime,
            'backupDate': btime,
            'modnum': mnum,
            'version': ver,
            'flagReset': bool(flags & flagReset),
            'flagResource': bool(flags & flagResource),
            'flagNewer': bool(flags & flagNewer),
            'flagExcludeFromSync': bool(flags & flagExcludeFromSync),
            'flagAppInfoDirty': bool(flags & flagAppInfoDirty),
            'flagReadOnly': bool(flags & flagReadOnly),
            'flagBackup': bool(flags & flagBackup),
            'flagOpen': bool(flags & flagOpen),
            'appinfo_offset' : appinfo_offset,
            'sortinfo_offset': sortinfo_offset,
            'more': 0,
            'index': 0,
            'uid' : uid,
            'nextrec' : nextrec,
            'numrec' : numrec,
         }

        self.update( mydata)

    def getRaw(self):
        '''
        Get raw data to marshall class.

        This function returns the binary form of the Palm database header.
        You need to copy the bytes returned by this function to the beginning of the 
        Palm database file. The string returned will be calcsize() bytes long.
        '''
        flg = 0
        if self['flagResource']: flg = flg | flagResource
        if self['flagReadOnly']: flg = flg | flagReadOnly
        if self['flagAppInfoDirty']: flg = flg | flagAppInfoDirty
        if self['flagBackup']: flg = flg | flagBackup
        if self['flagOpen']: flg = flg | flagOpen
        if self['flagNewer']: flg = flg | flagNewer
        if self['flagReset']: flg = flg | flagReset
        if self['flagExcludeFromSync']: flg = flg | flagExcludeFromSync
        raw = struct.pack(self.__packString,
            self['name'],
            flg,
            self['version'],
            self['createDate']+PILOT_TIME_DELTA,
            self['modifyDate']+PILOT_TIME_DELTA,
            self['backupDate']+PILOT_TIME_DELTA,
            self['modnum'],
            self['appinfo_offset'],
            self['sortinfo_offset'],
            self['type'],
            self['creator'],
            self['uid'],
            self['nextrec'],
            self['numrec'])
        return raw

    def getXML(self):
        returnValue=''

        returnValue+=returnObjectAsXML('reset',self['flagReset'])
        returnValue+=returnObjectAsXML('resource',self['flagResource'])
        returnValue+=returnObjectAsXML('newer',self['flagNewer'])
        returnValue+=returnObjectAsXML('excludeFromSync',self['flagExcludeFromSync'])
        returnValue+=returnObjectAsXML('appInfoDirty',self['flagAppInfoDirty'])
        returnValue+=returnObjectAsXML('readOnly',self['flagReadOnly'])
        returnValue+=returnObjectAsXML('backup',self['flagBackup'])
        returnValue+=returnObjectAsXML('open',self['flagOpen'])
        if len(returnValue):
            returnValue=returnAsXMLItem('PalmDatabaseFlags',returnValue,escape=False)

        returnValue+=returnObjectAsXML('databaseName',self['name'])
        returnValue+=returnObjectAsXML('type',self['type'])
        returnValue+=returnObjectAsXML('creatorID',self['creator'])
        returnValue+=returnObjectAsXML('creationdate',crackPalmDate(self['createDate']))
        returnValue+=returnObjectAsXML('modificationDate',crackPalmDate(self['modifyDate']))
        returnValue+=returnObjectAsXML('backupDate',crackPalmDate(self['backupDate']))
        returnValue+=returnObjectAsXML('modificationNumber',self['modnum'])
        returnValue+=returnObjectAsXML('version',self['version'])
     
        return returnAsXMLItem('palmHeaderInfo',returnValue,escape=False)

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

def defaultRecordFactory(attributes,id,category):
    '''
    Default factory function for creating records.

    This function is the default factory used by PalmDatabase to create new records.
    attributes are the record attributes like (deleted,dirty, etc), id is the resource id, 
    category is the category of the record. The PalmDatabase code will call setRaw() on
    this object to set the raw data, and getRaw() to retrieve the raw data.
    '''
    return PRecord(attributes,id,category)

class PRecord:
    '''
    This class encapsulates a Palm application record.

    Comparison and hashing are done by ID; thus, the id value 
    *may not be changed* once the object is created. You need to call
    setRaw() and getRaw() to set the raw data.
    '''
    def __init__(self, attr=0, id=0, category=0):
        self.id = id
        self.attr = attr
        self.category = category
        self.raw=''

    def __repr__(self):
        return "PRecord(attr=" + str(self.attr) + ",id=" + str(self.id) + ",category=" + str(self.category) + ",raw=" + repr(self.raw) + ")"

    # removing __cmp__() and __hash__() allows one to do things like
    # database.remove(recordObj) and have the first occurance of that object
    # removed -- otherwise only the id variable is considered, which is
    # not of much use in the case where all id's are the same.  If it is
    # desired to remove by id, a custom function should be made to do this.

    def setRaw(self,raw):
        '''
        Set raw data to marshall class.
        '''
        self.raw = raw

    def getRaw(self):
        '''
        Get raw data to marshal class
        '''
        return self.raw

    def getRecordAttributesAsXML(self,categories):
        returnValue =self.getCategoryAsXML(categories)
        returnValue+=self.getIDAsXML()
        returnValue+=self.getAttrBitsAsXML()
        return returnValue

    def getCategoryAsXML(self,categories):
        return returnObjectAsXML('PalmCategory',categories[self.category])

    def getIDAsXML(self):
        return returnObjectAsXML('PalmID',self.id)

    def getAttrBitsAsXML(self):
        '''
        Get record attributes as XML records
        '''
        returnValue=''
        deleted=bool(getBits(self.attr,3))
        dirty=bool(getBits(self.attr,2))
        busy=bool(getBits(self.attr,1))
        secret=bool(getBits(self.attr,0))
        
        if deleted:
            returnValue+=returnObjectAsXML('deleted',deleted)
        if dirty:
            returnValue+=returnObjectAsXML('dirty',dirty)
        if busy:
            returnValue+=returnObjectAsXML('busy',busy)
        if secret:
            returnValue+=returnObjectAsXML('secret',secret)

        if len(returnValue):
            returnValue=returnAsXMLItem('palmRecordAttributes',returnValue,escape=False)
        return returnValue

def filterForResourcesByTypeID(records,type=None,id=None):
    '''
    This function lets you filter a list of resources by type and/or id.

    When passed a list of resources, and the appropriate filter it will
    return a list of resources that match the criteria.
    '''
    return filter(lambda x : (type == None or x.type == type) and (id == None or x.id == id), records)

def defaultResourceFactory(type,id):
    '''
    Default factory function for creating resources.

    This function is the default factory used by PalmDatabase to create new resource
    records. Type is the 4 letter resource type, id is the resource id.  The PalmDatabase
    code will call setRaw() on this object to set the raw data, and getRaw() to retrieve the
    raw data.
    '''
    return PResource(type,id)

class PResource:
    '''
    This class encapsulates a Palm resource record.
    '''
    def __init__(self, type='    ', id=0):
        self.id = id
        self.type = type
        self.raw=''

    def __repr__(self):
        return "PResource(type='" + self.type + "',id=" + str(self.id) + ",raw=" + repr(self.raw) + ")"

# see in PRecord object for why this is commented out
##    def __cmp__(self, obj):
##        if type(obj) == type(()):
##            return cmp( (self.type, self.id), obj)
##        else:
##            return cmp( (self.type, self.id), (obj.type, obj.id) )
##
##    def __hash__(self):
##        return hash((self.type, self.id))

    def setRaw(self,raw):
        '''
        Set raw data to marshall class.
        '''
        self.raw = raw

    def getRaw(self):
        '''
        Get raw data to marshal class
        '''
        return self.raw

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
        self.recordFactory = None
        self.records = []
        self.appblock = ''
        self.sortblock = ''
        self.palmDBInfo = PalmDatabaseInfo()
        self.dirty = False

    def getAppBlock(self): return self.appblock and self.appblock or None
    def setAppBlock(self, raw):
        self.dirty = True
        self.appblock = raw

    def getSortBlock(self): return self.sortblock and self.sortblock or None
    def setSortBlock(self, raw):
        self.dirty = True
        self.appblock = raw

    def getPalmDBInfo(self): return self.palmDBInfo
    def setPalmDBInfo(self, info):
        self.dirty = True
        self.palmDBInfo=info

    def getRecords(self):
        return self.records
    def setRecords(self,records):
        self.records = records
        self.dirty = True

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
    def setDatabaseRecordFactory(self,factory):
        '''
        This function sets the function to be used to create new records.

        When you call this function with something other than None, it will
        use the function you have provided to create new records when it
        reads the database. The function you have passed in will be called to
        with either 3 or 4 parameters depending on whether the database is a
        PDB or PRC database.

        For a PRC database the function will be called with 3 parameters:
        Factory(type,id,raw). The type is the 4 character type of the resource,
        the id is the id of the resource, and raw is the raw resource data.

        For a PDB database the function will be called with 4 parameters:
        Factory(attributes,id,category,raw). The attributes are the record
        attributes (dirty,deleted,etc), the id is the record ID, the category is
        the record category and raw is the raw record data.

        The function is expected to return an object which has at least the
        interfaces exposed by PResource or PRecord depending on the type of the
        database.

        Calling setRecordFactory() with None as the parameter returns the behaviour
        to the default.

        For example:
        def myFactory(type,id,raw):
            return MyPResource(type,id,raw)
        
        x = PalmDB.PalmDatabase()
        x.setRecordFactory(myFactory)
        f = open('palmdb.pdb','r')
        data = f.read()
        x.fromByteArray(data)
        f.close()
        '''
        self.recordFactory = factory

    def createRecordFromByteArray(self, hstr):
        '''
        This function parses out a record entry from the corresponding segment
        of binary data taken from the PDB file (hstr), and returns a tuple
        containing the physical offset of the record data, and a record
        object populated with the record-entry information.
        
        Note that "deleted" records are NOT processed and return 0
        '''
        
        (offset, auid) = struct.unpack('>ll', hstr)
        attr = (auid & 0xff000000) >> 24
        uid = auid & 0x00ffffff
        attributes = attr & 0xf0
        category  = attr & 0x0f

        # debugging:
        # print 'offset', offset, 'Attr', attr2string(attr), 'UID', uid

        # don't add deleted records... I have only seen these once!
        if attr & attrDeleted:
            return (0,0);
        newRecordObject = self.recordFactory(attributes, uid, category)
        return (offset, newRecordObject)
        
    def createResourceFromByteArray(self, hstr):
        '''
        This function parses out a resource entry from the corresponding segment
        of binary data taken from the PDB file (hstr), and returns a tuple
        containing the physical offset of the resource data, and a resource
        object populated with the resource-entry information.
        '''

        (resourceType, id, offset) = struct.unpack('>4shl', hstr)
        # if createResourceFromByteArray is called, it is assumed that
        # self.recordFactory is actually assigned to a resource factory
        newResourceObject = self.recordFactory(resourceType, id)
        return (offset, newResourceObject) 
        
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
        if info[ 'creator'] == 'Gtkr':
            ...
        '''

        # clear all existing records
        self.clear()

        # instantiate and initialize database header
        self.palmDBInfo = PalmDatabaseInfo()
        palmHeaderSize = self.palmDBInfo.calcsize()
        self.palmDBInfo.setRaw(raw)  

        if headerOnly:
            return

        # assign some needed variables that were retrieved from the header
        rsrc = self.palmDBInfo['flagResource'] # is this a resource database?
        numrec = self.palmDBInfo['numrec'] # number of records
        appinfo_offset = self.palmDBInfo['appinfo_offset'] # offset location of AppInfo block
        sortinfo_offset = self.palmDBInfo['sortinfo_offset'] # offset location of SortInfo block
        rawsize = len(raw) # length of entire database

        # debugging
#        print 'Debug: Scanning PDB of size', rawsize
#        print 'Debug: AppInfo at', appinfo_offset
#        print 'Debug: SortInfo at', sortinfo_offset
#        print 'Debug: Found', numrec, 'records'
#        print 'Debug: Palm Header Size %d'%(palmHeaderSize)

        #-----BEGIN: INSTANTIATE AND APPEND DATABASE RECORDS / RESOURCES------

        if self.recordFactory == None:
            if rsrc: # if this is a resource database
                self.setDatabaseRecordFactory(defaultResourceFactory)
            else: 
                self.setDatabaseRecordFactory(defaultRecordFactory)

        if rsrc: 
            s = RESOURCE_ENTRY_SIZE
            recordMaker = PalmDatabase.createResourceFromByteArray
#            print "Debug: resource type"
        else: 
            s = RECORD_ENTRY_SIZE
            recordMaker = PalmDatabase.createRecordFromByteArray
#            print "Debug: record type"

        first_offset = 0        # need this to find the sort/app info blocks

        # next two maintain state for the loop
        prev_offset = rawsize    # track the offset of the previous block, but we are going backwards to simplify the algorithm

	# check to make sure the Palm database is big enough to at least contain the records it says it does
        if palmHeaderSize + s * numrec > rawsize:
            raise IOError, _("Error: database not big enough to have %d records")%(numrec)

#        print "Debug: Header size (%d), Number of records (%d)"%(s,numrec)
        # create records for each Palm record
        # have to use -1 as the final number, because range never reaches it, it always stops before it
        for count in range(numrec-1,-1,-1):
#            print "Debug: count (%d)"%(count)
            startingRecordOffset=count*s+palmHeaderSize
            # we have to offset by one because we have to skip the Palm header
            endingRecordOffset = (count+1)*s + palmHeaderSize
            
            # extract the raw data for the current record/resource entry
            hstr=raw[startingRecordOffset:endingRecordOffset]

#            print "Debug: using range of %d to %d"%(startingRecordOffset,endingRecordOffset)
            # make sure we got the data we are looking for
            if (not hstr) or (len(hstr) <> s):
                raise IOError, _("Error: problem reading record entry, size was (%d), size should have been (%d)")%(len(hstr),s)

            # Create an instance of the record
            # recordMaker is either createRecordFromByteArray() or createResourceFromByteArray()
            (offset, record) = recordMaker( self, hstr)
#            print "Debug: offset (%d) record (%s)"%(offset,record)

            # Check for problems
            if record:
                if offset > rawsize:
                    raise IOError, _("Error: Invalid offset (%d), off end of database")%(offset)

                if offset > prev_offset:
                        raise IOError, _("Error: Invalid offset (%d), greater than previous offset (records being processed in reverse order)")%(offset)

                # populate the record with the chunk data that it points to
                record.setRaw( raw[offset:prev_offset])

                # Add to beginning of self.records list because we are going backwards
                self.records.insert(0,record)
                prev_offset = offset 
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
        if sortinfo_offset: # if there is no SortInfo block, the offset=0
            if numrec > 0:
                # prev_offset is the beginning of the first record's data chunk
                sortinfo_size=prev_offset-sortinfo_offsets
            else: # if there are no records, then the SortInfo block ends at the end of the database
                sortinfo_size=rawsize-sortinfo_offset

        # Calculate the AppInfo block size
        # If we have a sort block, the offset to that is what bounds the AppInfo block
        # Otherwise, if we have records, then the offset of the first record is what bounds the AppInfo block
        # Finally if none of the previous things are true, then the boundary is the end of the file
        appinfo_size=0
        if appinfo_offset: # if there is no AppInfo block, the offset=0
            if sortinfo_offset > 0: # if there is a SortInfo block
                appinfo_size=sortinfo_offset-appinfo_offset
            elif numrec > 0:
                appinfo_size=prev_offset-appinfo_offset
            else:
                appinfo_size=rawsize-appinfo_offset

        if appinfo_size < 0:
            raise IOError, _("Error: bad database header AppInfo Block size < 0 (%d)")%(appinfo_size)

        if sortinfo_size < 0:
            raise IOError, _("Error: bad database header SortInfo Block size < 0 (%d)")%(sortinfo_size)

        if appinfo_size: # if AppInfo block exists
            self.appblock = raw[appinfo_offset:appinfo_offset+appinfo_size]
            if len(self.appblock) != appinfo_size:
                raise IOError, _("Error: failed to read appinfo block")

        if sortinfo_size: # if SortInfo block exists
            self.sortblock = raw[sortinfo_offset:sortinfo_offset+sortinfo_size]
            if len(self.sortblock) != sortinfo_size:
                raise IOError, _("Error: failed to read sortinfo block")

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
        
        palmHeaderSize = self.palmDBInfo.calcsize()
        rsrc = self.palmDBInfo['flagResource']

        # first, we need to precalculate the offsets.
        if rsrc:
            entries_len = RESOURCE_ENTRY_SIZE * len(self.records)
        else: 
            entries_len = RECORD_ENTRY_SIZE * len(self.records)

        offset = palmHeaderSize + entries_len + 2  #position following the entries
        if self.appblock:
            appinfo_offset = offset
            offset = offset + len(self.appblock)
        else:
            appinfo_offset = 0

        if self.sortblock:
            sortinfo_offset = offset
            offset = offset + len(self.sortblock)
        else:
            sortinfo_offset = 0

        # make list containing offsets for record/resource data-chunk locations
        rec_offsets = []
        for x in self.records:
            rec_offsets.append(offset)
            offset = offset + len(x.getRaw())

        self.palmDBInfo['appinfo_offset']=appinfo_offset
        self.palmDBInfo['sortinfo_offset']=sortinfo_offset
        self.palmDBInfo['numrec']=len(self.records)

        # begin to assemble the string to return (raw); start with database header
        raw = self.palmDBInfo.getRaw()

        entries = [] # a list which holds all of the record/resource entries
        record_data = [] # holds record/resource data-chunks
        # populate the lists...
        for x, offset in map(None, self.records, rec_offsets):
            if rsrc:
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

class File(PalmDatabase):
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

