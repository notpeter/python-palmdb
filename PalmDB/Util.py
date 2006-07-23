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
# 	return 'UTL'+struct.pack('>L',long(toPrint)).encode('HEX')

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

def setBooleanAttributeFromBits(dictionary,attributeName,bitStruct,bit):
    dictionary[attributeName]=bool(getBits( bitStruct, bit ))
def setBitsFromBooleanAttribute(dictionary,attributeName,bitStruct,bit):
    if dictionary.get(attributeName,False):
        return setBits(bitStruct,1,bit)
    else:
        return setBits(bitStruct,0,bit)

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
    if item.__class__.__name__ == 'str' or item.__class__.__name__ == 'unicode':
	return returnAttributeAsXML(itemName,'string',item)
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


def dictionaryFromXMLDOMNode(XMLDOMNode):
    # if no children; no point in trying
    assert(XMLDOMNode.hasChildNodes())

    returnValue={}
    for item in XMLDOMNode.childNodes:
        if item.nodeName == 'attribute':
            itemName=item.attributes['name'].value
            for itemChild in item.childNodes:
                itemData=itemFromXMLDOMNode(itemChild)
                returnValue[itemName]=itemData
    return returnValue

def itemFromXMLDOMNode(XMLDOMNode):
    if XMLDOMNode.nodeName == 'integer':
        return int(XMLDOMNode.attributes['value'].value)
    if XMLDOMNode.nodeName == 'real':
        return float(XMLDOMNode.attributes['value'].value)
    if XMLDOMNode.nodeName == 'rational':
        return simpleRational(int(XMLDOMNode.attributes['numerator'].value),int(XMLDOMNode.attributes['denominator'].value))
    if XMLDOMNode.nodeName == 'string':
        return XMLDOMNode.attributes['value'].value
    if XMLDOMNode.nodeName == 'boolean':
        if XMLDOMNode.attributes['value'].value == 'True':
            return True
        else:
            return False
    if XMLDOMNode.nodeName == 'date':
        year=int(XMLDOMNode.attributes['year'].value)
        month=int(XMLDOMNode.attributes['month'].value)
        day=int(XMLDOMNode.attributes['day'].value)
        hour=int(XMLDOMNode.attributes['hour'].value)
        minutes=int(XMLDOMNode.attributes['minutes'].value)
        seconds=int(XMLDOMNode.attributes['seconds'].value)
        return datetime.datetime(year,month,day,hour,minutes,seconds)
    # +++ FIX THIS +++ Some types missing here
    return None

class StructMap:
    typeConversion={
        'padbyte':'x',
        'char':'c',
        'schar':'b',
        'uchar':'B',
        'short':'h',
        'ushort':'H',
        'int':'i',
        'uint':'I',
        'long':'l',
        'ulong':'L',
        'longlong':'q',
        'ulonglong':'Q',
        'float':'f',
        'double':'d',
        'char[]':'s',
        'void *':'P'
        }
    byteOrder={
        'native-native':'@',
        'native-standard':'=',
        'little-endian':'<',
        'big-endian':'>',
        'network':'!'
        }
    def __init__(self):
        self.conversionList=[]
        self.data={}
        self.networkOrder='native-native'
    def selfNetworkOrder(self,networkOrder):
        self.networkOrder=networkOrder
    def setConversion(self,conversionList):
        '''
        conversionList is a list of tuples that look like (repeat,name,type)
        '''
        self.conversionList=conversionList
    def _getPackString(self):
        # explicitly set network byte order
        packString=self.byteOrder[self.networkOrder]
        # build list of struct parameters
        for conversion in self.conversionList:
            (repeat,name,type)=conversion
            if repeat > 1:
                packString+=str(repeat)
            packString+=self.conversionList[type]
    
    def _getParameterNames(self):
        return [paramName for (repeat,paramName,type) in self.conversionList]
    def crackByteArray(self,byteArray):
        crackedData=struct.unpack(self._getPackString(),byteArray)
        forDictData=zip(self._getParameterNames(),crackedData)
        self.data.clear()
        self.data.update(forDictData)
    def packByteArray(self):
        packedTuple=tuple([self.data[item] for item in self._getParameterNames()])
        return struct.pack(self._getPackString,*packedTuple)
    def __len__(self):
        return struct.calcsize(_getPackString())

    # map API Begins
    def __getitem__(self, index):
        return self.data[index]
    def __setitem__(self, index,record):
        self.data[index]=record
    def __delitem__(self, index):
        del(self.data[index])
    def __contains__(self,record):
        return self.data.__contains__(record)
    # Sequence/map API Ends
