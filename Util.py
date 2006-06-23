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

    XML utilities to make creating XML easier.
"""

__version__ = '$Id: PalmDB.py,v 1.11 2005/12/13 03:12:12 rprice Exp $'

__copyright__ = 'Copyright 2006 Rick Price <rick_price@users.sourceforge.net>'

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

def setBits(variable,value,MSBBitIndex,bitCount=1):
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
