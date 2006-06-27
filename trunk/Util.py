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

import datetime

XMLsuppressFalseOrBlank=False

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

PILOT_TIME_DELTA = 2082844800L
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

    if (item.__class__.__name__ == 'int') or (item.__class__.__name__ == 'long'):
	return returnAttributeAsXML(itemName,'integer',item)
    if item.__class__.__name__ == 'float':
	return returnAttributeAsXML(itemName,'real',item)
    if item.__class__.__name__ == 'str':
	return returnAttributeAsXML(itemName,'string',item)
    if item.__class__.__name__ == 'bool':
	return returnAttributeAsXML(itemName,'boolean',item)
    if item.__class__.__name__ == 'bool':
	return returnAttributeAsXML(itemName,'boolean',item)
    if item.__class__.__name__ == 'dict':
	return returnAttributeAsXML(itemName,'dictionary',returnDictionaryAsXML(item),escape=False)
    if item.__class__.__name__ == 'list':
	return returnAsXMLItem(itemName,returnAsXMLItem('list',returnSequenceAsXML(item),escape=False),escape=False)
    if item.__class__.__name__ == 'tuple':
	return returnAsXMLItem(itemName,returnAsXMLItem('tuple',returnSequenceAsXML(item),escape=False),escape=False)

    if item.__class__.__name__.startswith('date'):
        (year,month,day,hour,minutes,seconds,weekday,yearday,dstAdjustment)=item.timetuple()
        return '<attribute name="%s"><date year="%d" month="%d" day="%d" hour="%d" minutes="%d" seconds="%d"/></attribute>\n'%\
            (itemName,year,month,day,hour,minutes,seconds)

    return returnAttributeAsXML(itemName,'Unknown-'+item.__class__.__name__,item)
    
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

def returnDictionaryAsXML(dictionary):
	returnValue=''
	for (key,value) in dictionary.iteritems():
		if not key.startswith('_'):
			returnValue+=returnObjectAsXML(key,value)
	return returnValue

def returnSequenceAsXML(sequence):
	returnValue=''
	for value in sequence.__iter__():
		returnValue+=returnObjectAsXML('item',value)
	return returnValue

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
	PDBPlugins[type]=PDBFilePluginClass

def getPDBPlugin(CreatorID):
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
