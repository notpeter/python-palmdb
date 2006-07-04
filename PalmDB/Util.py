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

__copyright__ = 'Copyright 2006 Rick Price <rick_price@users.sourceforge.net>'

import time
import datetime

import struct

# def plah(toPrint):
# 	return 'UTL'+struct.pack('>l',long(toPrint)).encode('HEX')

XMLsuppressFalseOrBlank=False

class simpleRational:
    '''
    Just a simple way to represent rational numbers to print them out as XML.
    '''
    def __init__(self,numerator,denominator):
        self.numerator=numerator
        self.denominator=denominator
        
def getBits(variable,MSBBitIndex,bitCount=1):
    """
    This function is for.... Does ....?
    """
    # MSBBitIndex is zero based

    assert(MSBBitIndex < 32)
    assert(MSBBitIndex >= 0)
    assert(MSBBitIndex >= bitCount-1)
    assert(bitCount <> 0)
    
    shift=MSBBitIndex-bitCount+1
    bitsToMask=pow(2,bitCount)-1
    mask=bitsToMask<<shift
    result=variable & mask
    result=result>>shift
    return result

def setBits(variable,value,MSBBitIndex,bitCount=1):
    # MSBBitIndex is zero based
    """
    This function is for.... Does ....?
    """

    assert(MSBBitIndex < 32)
    assert(MSBBitIndex >= 0)
    assert(MSBBitIndex >= bitCount-1)
    assert(bitCount <> 0)

    # MSBBitIndex is zero based
    shift=MSBBitIndex-bitCount+1
    bitsToMask=pow(2,bitCount)-1

    # remove any extraneous data from value before we shift mask
    value=value&bitsToMask
    # shift mask into place
    mask=bitsToMask<<shift

    # Remove current bit values
    result=variable & ~mask

    # replace them with new values
    value=value&bitsToMask
    value=value<<shift
    result=result|value
    return result

PILOT_TIME_DELTA = 2082844800L
def crackPalmDate(variable):
        if variable == 0:
            return None
        else:
            return datetime.datetime.fromtimestamp(variable-PILOT_TIME_DELTA)

def packPalmDate(variable):
	if variable == None:
		return 0
	else:
		return int(time.mktime(variable.timetuple())+PILOT_TIME_DELTA)

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
    if item.__class__.__name__ == 'simpleRational':
	return returnRationalAsXML(itemName,item.numerator,item.denominator)
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
