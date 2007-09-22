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

from PalmDB.Util import setBooleanAttributeFromBits
from PalmDB.Util import setBitsFromBooleanAttribute
from PalmDB.Util import getBits

from PalmDB.Util import packPalmDatePacked
from PalmDB.Util import crackPalmDatePacked
from PalmDB.Util import StructMap


class ProgectProjectListPlugin(PalmDB.Plugins.BasePlugin.BasePDBFilePlugin):
	def getPluginID(self):
		return 'PROGECT_PROJECT_LIST'
	def getPDBCreatorID(self):
		return 'lbPG'
	def getPDBTypeID(self):
		return 'META'
	def getDefaultDesktopApplicationID(self):
		return 'PDESK_PROJECT_LIST_XML'
	def getSupportedDesktopApplications(self,readOrWrite):
		return ['PDESK_PROJECT_LIST_XML']
	def getSupportedApplicationsForFile(self,filename,readOrWrite):
		if filename.upper() == 'LBPG-PROJECT_META_DATA.XML':
			return ['PDESK_PROJECT_LIST_XML']
		return []
	def createPalmDatabaseRecord(self,PalmDatabaseObject):
		return ProgectProjectRecord()
	def getXMLReaderObject(self,PalmDatabaseObject):
		return ProgectProjectListXMLReaderObject()

class ProgectProjectListXMLReaderObject(PalmDB.Plugins.BasePlugin.GeneralPalmDBXMLReaderObject):
	def parse_START_ELEMENT_ProgectProjectDataRecord(self,events,node,palmDatabaseObject):
		events.expandNode(node)
		plugin=palmDatabaseObject._getPlugin()
		palmRecord=plugin.createPalmDatabaseRecord(palmDatabaseObject)
		palmRecord.fromDOMNode(node)
		palmDatabaseObject.append(palmRecord)

class ProgectProjectRecord(PalmDB.Plugins.BasePlugin.DataRecord):
	'''
		This class encapsulates a Progect project list record.
	'''
	def __init__(self):
		PalmDB.Plugins.BasePlugin.DataRecord.__init__(self)
		self.taskHeader=StructMap()
		self.taskHeader.selfNetworkOrder('palmos')
		self.taskHeader.setConversion([('cardNumber','ushort'),('lastSentinelValue','ushort'),('databaseName','char[]',32)])
	
		self.clear()

	def clear(self):
		self.attributes.clear()
		self.attributes['cardNumber']=0
		self.attributes['lastSentinelValue']=0
		self.attributes['databaseName']=False
		self.attributes['note']=''

	def getRecordXMLName(self):
		return 'ProgectProjectDataRecord'

	
	def _crackPayload(self,dstr):
#		self.attributes['debug_payload']=dstr.encode('HEX')

		# tell the StructMap to crack the data for us
		self.taskHeader.fromByteArray(dstr)

		# copy the data from the structmap
		self.attributes['cardNumber']=self.taskHeader['cardNumber']
		self.attributes['lastSentinelValue']=self.taskHeader['lastSentinelValue']
		(databaseName,)=self.taskHeader['databaseName'].split('\0')[:1]
		self.attributes['databaseName']=databaseName.decode('palmos')

		# find the part of the data that will be our note
		noteString=dstr[self.taskHeader.getSize():]
		# now we assume that the string _will_ end in a zero, this should break apart the strings for us
		(note,)=noteString.split('\0')[:1]
		# now set in our attributes
		self.attributes['note']=note.decode('palmos')

	def _packPayload(self):
		# copy the data to the structmap
		self.taskHeader['cardNumber']=self.attributes['cardNumber']
		self.taskHeader['lastSentinelValue']=self.attributes['lastSentinelValue']
		self.taskHeader['databaseName']=self.attributes['databaseName'].encode('palmos')

		dstr=self.taskHeader.toByteArray()
		dstr+=self.attributes['note'].encode('palmos')+'\0'
		return dstr
