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

# This file includes changes made (including better naming, comments and design changes)
# by Mark Edgington, many thanks Mark.


"""
    PRC/PDB file I/O in pure Python.
    XML utilities to make creating XML easier.
"""

__copyright__ = 'Copyright 2006 Rick Price <rick_price@users.sourceforge.net>'

import time
import datetime

import struct

# def plah(toPrint):
#     return 'UTL'+struct.pack('>L',long(toPrint)).encode('HEX')

XMLsuppressFalseOrBlank = False


class simpleRational:
    '''
    Just a simple way to represent rational numbers to print them out as XML.
    '''
    def __init__(self, numerator, denominator):
        self.numerator = numerator
        self.denominator = denominator

    def __repr__(self):
        return 'simpleRational(numerator=%s,denominator=%s)' % (self.numerator, self.denominator)


def getBits(variable, MSBBitIndex, bitCount=1):
    """
    This function is for.... Does ....?
    """
    # MSBBitIndex is zero based

    assert(MSBBitIndex < 32)
    assert(MSBBitIndex >= 0)
    assert(MSBBitIndex >= bitCount-1)
    assert(bitCount != 0)

    shift = MSBBitIndex-bitCount+1
    bitsToMask = pow(2, bitCount)-1
    mask = bitsToMask << shift
    result = variable & mask
    result = result >> shift
    return result


def setBits(variable, value, MSBBitIndex, bitCount=1):
    # MSBBitIndex is zero based
    """
    This function is for.... Does ....?
    """

    assert(MSBBitIndex < 32)
    assert(MSBBitIndex >= 0)
    assert(MSBBitIndex >= bitCount - 1)
    assert(bitCount != 0)

    # MSBBitIndex is zero based
    shift = MSBBitIndex - bitCount + 1
    bitsToMask = pow(2, bitCount) - 1

    # remove any extraneous data from value before we shift mask
    value = value & bitsToMask
    # shift mask into place
    mask = bitsToMask << shift

    # Remove current bit values
    result = variable & ~mask

    # replace them with new values
    value = value & bitsToMask
    value = value << shift
    result = result | value
    return result


def setBooleanAttributeFromBits(dictionary, attributeName, bitStruct, bit):
    dictionary[attributeName] = bool(getBits(bitStruct, bit))


def setBitsFromBooleanAttribute(dictionary, attributeName, bitStruct, bit):
    if dictionary.get(attributeName, False):
        return setBits(bitStruct, 1, bit)
    else:
        return setBits(bitStruct, 0, bit)


PILOT_TIME_DELTA = 2082844800


def crackPalmDate(variable):
    if variable == 0 or variable < PILOT_TIME_DELTA:
        return None
    else:
        return datetime.datetime.fromtimestamp(variable - PILOT_TIME_DELTA)


def packPalmDate(variable):
    if variable is None:
        return 0
    else:
        return int(time.mktime(variable.timetuple()) + PILOT_TIME_DELTA)


def crackPalmDatePacked(variable):
    # Date due field:
    # This field seems to be layed out like this:
    #     year  7 bits (0-128)
    #     month 4 bits (0-16)
    #     day   5 bits (0-32)

    # it would seem that Palm uses 0xffff to mean no date at all
    if variable == 0xffff:
        return None

    year = getBits(variable, 15, 7) + 1904
    return datetime.date(year, getBits(variable, 8, 4), getBits(variable, 4, 5))


def packPalmDatePacked(date):
    if date is None:
        return 0xffff
    returnValue = 0
    returnValue = setBits(returnValue, date.year - 1904, 15, 7)
    returnValue = setBits(returnValue, date.month, 8, 4)
    returnValue = setBits(returnValue, date.day, 4, 5)
    return returnValue

#
# XML Helper Functions
#


def escapeForXML(text):
    return text.replace("&", "&amp;")\
            .replace("<", "&lt;")\
            .replace(">", "&gt;")\
            .replace("'", "&apos;")\
            .replace('"', "&quot;")


def returnObjectAsXML(itemName, item):
    if item is None:
        return ''

    if (item.__class__.__name__ == 'int') or (item.__class__.__name__ == 'long'):
        return returnAttributeAsXML(itemName, 'integer', item)
    if item.__class__.__name__ == 'float':
        return returnAttributeAsXML(itemName, 'real', item)
    if item.__class__.__name__ == 'simpleRational':
        return returnRationalAsXML(itemName, item.numerator, item.denominator)
    if item.__class__.__name__ == 'str' or item.__class__.__name__ == 'unicode':
        return returnAttributeAsXML(itemName, 'string', item)
    if item.__class__.__name__ == 'bool':
        return returnAttributeAsXML(itemName, 'boolean', item)
    if item.__class__.__name__ == 'dict':
        return returnAttributeAsXML(
            itemName, 'dictionary', returnDictionaryAsXML(item), escape=False)
    if item.__class__.__name__ == 'list':
        return returnAsXMLItem(
            itemName, returnAsXMLItem('list', returnSequenceAsXML(item), escape=False), escape=False)
    if item.__class__.__name__ == 'tuple':
        return returnAsXMLItem(
            itemName, returnAsXMLItem('tuple', returnSequenceAsXML(item), escape=False), escape=False)

    if item.__class__.__name__.startswith('date'):
        (year, month, day, hour, minutes, seconds, weekday, yearday, dstAdjustment) = item.timetuple()
        return (
            '<attribute name="%s">'
            '<date year="%d" month="%d" day="%d" hour="%d" minutes="%d" seconds="%d"/>'
            '</attribute>\n') % (itemName, year, month, day, hour, minutes, seconds)

    return returnAttributeAsXML(itemName, 'Unknown-' + item.__class__.__name__, item)


def returnRationalAsXML(itemName, numerator, denominator):
    return (
        '<attribute name="%s"><rational numerator="%d" denominator="%d"/></attribute>\n'
        ) % (itemName, numerator, denominator)


def returnAttributeAsXML(itemName, itemType, item, escape=True):
    if escape:
        itemAsString = escapeForXML(str(item))
    else:
        itemAsString = str(item)

    if len(itemAsString) or not XMLsuppressFalseOrBlank:
        return '<attribute name="%s"><%s value="%s"/></attribute>\n' % (itemName, itemType, itemAsString)
    else:
        return ''


def returnAsXMLItem(itemName, item, escape=True):
    if escape:
        itemAsString = escapeForXML(str(item))
    else:
        itemAsString = str(item)

    if len(itemAsString) or not XMLsuppressFalseOrBlank:
        return '<%s>%s</%s>\n' % (itemName, itemAsString, itemName)
    else:
        return ''


def returnDictionaryAsXML(dictionary):
    returnValue = ''
    for (key, value) in dictionary.items():
        if not key.startswith('_'):
            returnValue += returnObjectAsXML(key, value)
    return returnValue


def returnSequenceAsXML(sequence):
    returnValue = ''
    for value in sequence.__iter__():
        returnValue += returnObjectAsXML('item', value)
    return returnValue


def dictionaryFromXMLDOMNode(XMLDOMNode):
    # if no children; no point in trying
    assert(XMLDOMNode.hasChildNodes())

    returnValue = {}
    for item in XMLDOMNode.childNodes:
        if item.nodeName == 'attribute':
            itemName = item.attributes['name'].value
            for itemChild in item.childNodes:
                itemData = itemFromXMLDOMNode(itemChild)
                returnValue[itemName] = itemData
    return returnValue


def itemFromXMLDOMNode(XMLDOMNode):
    if XMLDOMNode.nodeName == 'integer':
        return int(XMLDOMNode.attributes['value'].value)
    if XMLDOMNode.nodeName == 'real':
        return float(XMLDOMNode.attributes['value'].value)
    if XMLDOMNode.nodeName == 'rational':
        return simpleRational(
            int(XMLDOMNode.attributes['numerator'].value),
            int(XMLDOMNode.attributes['denominator'].value)
        )
    if XMLDOMNode.nodeName == 'string':
        return XMLDOMNode.attributes['value'].value
    if XMLDOMNode.nodeName == 'boolean':
        if XMLDOMNode.attributes['value'].value == 'True':
            return True
        else:
            return False
    if XMLDOMNode.nodeName == 'date':
        year = int(XMLDOMNode.attributes['year'].value)
        month = int(XMLDOMNode.attributes['month'].value)
        day = int(XMLDOMNode.attributes['day'].value)
        hour = int(XMLDOMNode.attributes['hour'].value)
        minutes = int(XMLDOMNode.attributes['minutes'].value)
        seconds = int(XMLDOMNode.attributes['seconds'].value)
        return datetime.datetime(year, month, day, hour, minutes, seconds)
    # +++ FIX THIS +++ Some types missing here
    return None


class StructMap(dict):
    typeConversion = {
        'padbyte': 'x',
        'char': 'c',
        'schar': 'b',
        'uchar': 'B',
        'short': 'h',
        'ushort': 'H',
        'int': 'i',
        'uint': 'I',
        'long': 'l',
        'ulong': 'L',
        'longlong': 'q',
        'ulonglong': 'Q',
        'float': 'f',
        'double': 'd',
        'char[]': 's',
        'void *': 'P'
    }
    byteOrder = {
        'native-native': '@',
        'native-standard': '=',
        'little-endian': '<',
        'big-endian': '>',
        'network': '!',
        'palmos': '>',
    }

    def __init__(self):
        self.conversionList = []
        self.networkOrder = 'native-native'

    def selfNetworkOrder(self, networkOrder):
        self.networkOrder = networkOrder

    def setConversion(self, conversionList):
        '''
        conversionList is a list of tuples that look like (name,type,repeat)
        '''
        self.conversionList = conversionList

    def _getPackString(self):
        # explicitly set network byte order
        packString = self.byteOrder[self.networkOrder]
        # build list of struct parameters
        for conversion in self.conversionList:
            if len(conversion) > 2:
                (name, type, repeat) = conversion
                if repeat > 1:
                    if type != 'char[]':
                        raise ValueError('Can only use a repeat with a char[] type')
                    packString += str(repeat)
            else:
                (name, type) = conversion
            packString += self.typeConversion[type]
        return packString

    def _getParameterNames(self):
        return [conversionTuple[0] for conversionTuple in self.conversionList]

    def fromByteArray(self, byteArray):
        if len(byteArray) < self.getSize():
            raise IOError(
                "Error: raw data passed in to Structmap is too small; required (%d), available (%d)" % (
                    self.getSize(), len(byteArray)
                )
            )

        crackedData = struct.unpack(self._getPackString(), byteArray[:self.getSize()])
        forDictData = list(zip(self._getParameterNames(), crackedData))
        self.clear()
        self.update(forDictData)

    def toByteArray(self):
        packedTuple = tuple([self[item] for item in self._getParameterNames()])
        return struct.pack(self._getPackString(), *packedTuple)

    def getSize(self):
        return struct.calcsize(self._getPackString())

    def updateFromDict(self, dictionary):
        for attribute in self._getParameterNames():
            self[attribute] = dictionary.get(attribute, None)
