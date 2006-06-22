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
