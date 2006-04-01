#
#  $Id: PalmDB.py,v 1.11 2005/12/13 03:12:12 rprice Exp $
#
#  Copyright 2004 Rick price <rick_price@users.sourceforge.net>
#
#  This file may be used in accordance with the Python Software License 2.3.4 or any later version.
#
#  This code was based on code written by Rob Tillotson <rob@pyrite.org>, but has been heavily
#  modified.


"""PRC/PDB file I/O in pure Python.

    This module allows access to Palm OS(tm) database files on the desktop 
    in pure Python. It is as simple as possible without (hopefully) being 
    too simple. As much as possible Python idioms have been used to make
    it easier to use and more versatile.
"""

__version__ = '$Id: PalmDB.py,v 1.11 2005/12/13 03:12:12 rprice Exp $'

__copyright__ = 'Copyright 2004 Rick Price <rick_price@users.sourceforge.net>'

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

import sys, os, stat, struct

PI_RESOURCE_ENT_SIZE = 10
PI_RECORD_ENT_SIZE = 8

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

# you need to pass the AppBlock into this class in the constructor
class Categories(dict):
    '''
    This class encapsulates Palm Categories.

    Currently renaming categories or adding/deleting categories is not supported.
    As of this writing, you may only have 16 categories, and this code us unable
    to handle anything other than that.
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
            'flagReset': 0,
            'flagResource': 0,
            'flagNewer': 0,
            'flagExcludeFromSync': 0,
            'flagAppInfoDirty': 0,
            'flagReadOnly': 0,
            'flagBackup': 0,
            'flagOpen': 0,
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
            'createDate': ctime - PILOT_TIME_DELTA,
            'modifyDate': mtime - PILOT_TIME_DELTA,
            'backupDate': btime - PILOT_TIME_DELTA,
            'modnum': mnum,
            'version': ver,
            'flagReset': flags & flagReset,
            'flagResource': flags & flagResource,
            'flagNewer': flags & flagNewer,
            'flagExcludeFromSync': flags & flagExcludeFromSync,
            'flagAppInfoDirty': flags & flagAppInfoDirty,
            'flagReadOnly': flags & flagReadOnly,
            'flagBackup': flags & flagBackup,
            'flagOpen': flags & flagOpen,
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

def filterForRecordsByCategory(records,category=None):
    '''
    This function lets you filter a list of records by category.

    When passed a list of records, and the appropriate category it will
    return a list of records that match the criteria.
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
    map(lambda x : x.attr & ~attrDirty,records)

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
        return 'PRecord(attr=' + str(self.attr) + ',id='+str(self.id)+',category='+str(self.category)+',raw=\''+self.raw+'\')'

    def __cmp__(self, obj):
        if type(obj) == type(0):
            return cmp(self.id, obj)
        else:
            return cmp(self.id, obj.id)

    def __hash__(self):
        return self.id

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

    def __cmp__(self, obj):
        if type(obj) == type(()):
            return cmp( (self.type, self.id), obj)
        else:
            return cmp( (self.type, self.id), (obj.type, obj.id) )

    def __repr__(self):
        return 'PResource(type=\'' + self.type + '\',id='+str(self.id)+',raw=\''+self.raw+'\')'

    def __hash__(self):
        return hash((self.type, self.id))

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
        self.dirty = 0
        # if allow_zero_ids is 1, then this prc behaves appropriately
        # for a desktop database.  That is, it never attempts to assign
        # an ID, and lets new records be inserted with an ID of zero.
        self.allow_zero_ids = 0

    def getAppBlock(self): return self.appblock and self.appblock or None
    def setAppBlock(self, raw):
        self.dirty = 1
        self.appblock = raw

    def getSortBlock(self): return self.sortblock and self.sortblock or None
    def setSortBlock(self, raw):
        self.dirty = 1
        self.appblock = raw

    def getPalmDBInfo(self): return self.palmDBInfo
    def setPalmDBInfo(self, info):
        self.dirty = 1
        self.palmDBInfo=info

    def getRecords(self):
        return self.records
    def setRecords(self,records):
        self.records = records
        self.dirty = 1

    # sequence/map API Begins
    def __len__(self): return len(self.records)
    def __getitem__(self, index):
        return self.records[index]
    def __setitem__(self, i,record):
        self.records[index]=record
        self.dirty = 1
    def __delitem__(self, index):
        del(self.records[index])
        self.dirty = 1
    def clear(self):
        self.records = []
        self.dirty = 1
    def append(self,record):
        self.records.append(record)
        self.dirty = 1
    def insert(self,index,record):
        self.records.insert(index,record)
        self.dirty = 1
    def remove(self,record):
        self.records.remove(record)
        self.dirty = 1
    def index(self,record):
        return self.records.index(record)
    def __contains__in(self,record):
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



    def addRecordFromByteArray( self, hstr):
        '''
        This function parses out a record entry
        and returns the physical offset of the record data
        Note that "deleted" records are NOT added and return 0
        '''
        (offset, auid) = struct.unpack('>ll', hstr)
        attr = (auid & 0xff000000) >> 24
        uid = auid & 0x00ffffff

        # debugging:
        # print 'offset', offset, 'Attr', attr2string(attr), 'UID', uid

        # don't add deleted records... I have only seen these once!
        if attr & attrDeleted:
            return (0,0);
        
        return (offset, self.recordFactory(attr & 0xf0, uid, attr & 0x0f))


    def addResourceFromByteArray( self, hstr):
        '''
        This function parses out a resource entry
        and returns the physical offset of the resource data
        '''
        (typ, id, offset) = struct.unpack('>4shl', hstr)
        return (offset, self.recordFactory(typ, id)) 

        
    def fromByteArray(self, raw, headerOnly = False):
        '''
        This function initializes the class with the Palm database data.

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
        self.palmDBInfo = PalmDatabaseInfo()

        palmHeaderSize = self.palmDBInfo.calcsize()

        self.palmDBInfo.setRaw(raw)  

        if headerOnly:
            return

        rsrc = self.palmDBInfo['flagResource']
        numrec = self.palmDBInfo['numrec']
        appinfo_offset = self.palmDBInfo['appinfo_offset']
        sortinfo_offset = self.palmDBInfo['sortinfo_offset']
        rawsize = len(raw)

        # debugging
        # print 'Scanning PDB of size', rawsize
        # print 'AppInfo at', appinfo_offset
        # print 'SortInfo at', sortinfo_offset
        # print 'Found', numrec, 'records'

        if self.recordFactory == None:
            if rsrc: 
                self.setDatabaseRecordFactory(defaultResourceFactory)
            else: 
                self.setDatabaseRecordFactory(defaultRecordFactory)

        if rsrc: 
            s = PI_RESOURCE_ENT_SIZE
            recordMaker = PalmDatabase.addResourceFromByteArray
        else: 
            s = PI_RECORD_ENT_SIZE
            recordMaker = PalmDatabase.addRecordFromByteArray

        first_offset = 0        # need this to find the sort/app info blocks

        # next two maintain state for the loop
        prev_offset = 0         # track the offset of the previous block
        prev_record = None      # track the previous record

        # loop over the block index
        for pos in range( palmHeaderSize, palmHeaderSize + s * numrec, s):
            hstr = raw[pos:pos+s]
            if not hstr or len(hstr) < s:
                raise IOError, _("problem reading record entry")

            # Create an instance of the record
            (offset, record) = recordMaker( self, hstr)

            if record:
                if offset > rawsize:
                    raise IOError, _("Invalid offset, off end of database")

                if first_offset == 0:
                    first_offset = offset

                if prev_record:
                    if offset < prev_offset:
                        raise IOError, _("Invalid offset, less than previous offset")
                    prev_record.setRaw( raw[ prev_offset:offset])
                    self.records.append( prev_record)
                    prev_offset = offset 

                prev_record = record

        # Make sure we set the data and append for the last record
        if prev_record:
            prev_record.setRaw( raw[ prev_offset:rawsize])
            self.records.append( prev_record)

        if first_offset == 0:
            first_offset = rawsize 

        if sortinfo_offset:
            sortinfo_size = first_offset - sortinfo_offset
            first_offset = sortinfo_offset
        else:
            sortinfo_size = 0

        if appinfo_offset:
            appinfo_size = first_offset - appinfo_offset
            first_offset = appinfo_offset
        else:
            appinfo_size = 0

        if appinfo_size < 0 or sortinfo_size < 0:
            raise IOError, _("bad database header (appinfo_size or sortinfo_size < 0)")

        if appinfo_size:
            self.appblock = raw[appinfo_offset:appinfo_offset+appinfo_size]
            if len(self.appblock) != appinfo_size:
                raise IOError, _("failed to read appinfo block")

        if sortinfo_size:
            self.sortblock = raw[sortinfo_offset:sortinfo_offset+sortinfo_size]
            if len(self.sortblock) != sortinfo_size:
                raise IOError, _("failed to read sortinfo block")

    def toByteArray(self):
        '''
        This function returns the data for the complete Palm database.

        For example:
        x = PalmDB.PalmDatabase()
        f = open('palmdb.pdb', 'wb')
        f.write(x.toByteArray())
        f.close()       
        '''
        palmHeaderSize = self.palmDBInfo.calcsize()
        rsrc = self.palmDBInfo['flagResource']

        # first, we need to precalculate the offsets.
        if rsrc:
            entries_len = 10 * len(self.records)
        else: 
            entries_len = 8 * len(self.records)

        off = palmHeaderSize + entries_len + 2
        if self.appblock:
            appinfo_offset = off
            off = off + len(self.appblock)
        else:
            appinfo_offset = 0

        if self.sortblock:
            sortinfo_offset = off
            off = off + len(self.sortblock)
        else:
            sortinfo_offset = 0

        rec_offsets = []
        for x in self.records:
            rec_offsets.append(off)
            off = off + len(x.getRaw())

        self.palmDBInfo['appinfo_offset']=appinfo_offset
        self.palmDBInfo['sortinfo_offset']=sortinfo_offset
        self.palmDBInfo['numrec']=len(self.records)

        raw = self.palmDBInfo.getRaw()

        entries = []
        record_data = []
        for x, off in map(None, self.records, rec_offsets):
            if rsrc:
                record_data.append(x.getRaw())
                entries.append(struct.pack('>4shl', x.type, x.id, off))
            else:
                record_data.append(x.getRaw())
                a = ((x.attr | x.category) << 24) | x.id
                entries.append(struct.pack('>ll', off, a))

        for x in entries: 
            raw = raw + x

        raw = raw + '\0\0' # padding?  dunno, it's always there.

        if self.appblock: raw = raw + self.appblock
        if self.sortblock: raw = raw + self.sortblock

        for x in record_data: 
            raw = raw + x

        return raw
    # Load/Save API Ends

class File(PalmDatabase):
    def __init__(self, name=None, factory=None,read=1, write=0):
        PalmDatabase.__init__(self)
        self.filename = name
        self.writeback = write
        self.isopen = 0
        if factory <> None:
            self.setDatabaseRecordFactory(factory)

        if read:
            self.load(name)
        self.isopen = 1

    def close(self):
        if self.writeback and self.dirty:
            self.save(self.filename)
        self.isopen = 0

    def __del__(self):
        if self.isopen: 
            self.close()

    def load(self, fileName):
        '''
        Open fileName and load the Palm database file contents.
        '''
        f = open(fileName, 'rb')
        data = f.read()
        self.fromByteArray(data)
        f.close()

    def save(self, fileName):
        '''
        Open fileName and save the Palm database to the open file.
        '''
        f = open(fileName, 'wb')
        f.write(self.toByteArray())
        f.close()
