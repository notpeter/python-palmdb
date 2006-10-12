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


class PalmToDoPlugin(PalmDB.Plugins.BasePlugin.BasePDBFilePlugin):
	def getPDBCreatorID(self):
		return 'todo'
	def getPalmApplicationName(self):
		return 'PalmToDo'
	def getApplicationNameFromFile(self,filename):
		# return tuple (ApplicationName,XSLT,GZIPResult)
		if filename.upper().endswith('.XML'):
			return 'NativeXML'
		if filename.upper().endswith('.XML.GZ'):
			return 'NativeXMLGZ'
		return None

	def createPalmDatabaseRecord(self,PalmDatabaseObject):
		return PalmToDoRecord()

class PalmToDoRecord(PalmDB.Plugins.BasePlugin.DataRecord):
	'''
		This class encapsulates a Palm ToDo application record.
	'''
	def __init__(self):
		PalmDB.Plugins.BasePlugin.DataRecord.__init__(self)
		self.taskHeader=StructMap()
		self.taskHeader.selfNetworkOrder('palmos')
		# +++ FIX THIS +++
		# you will need to set these according to the task header
		self.taskHeader.setConversion([('dueDate','ulong'),('priority','uchar'),])
		# +++ FIX THIS +++
	
		self.clear()

	def clear(self):
		self.attributes.clear()
		# +++ FIX THIS ++++
		# you will need to set default values here for the task attributes
		self.attributes['dueDate']=None
		self.attributes['priority']=0
		self.attributes['completed']=False
		# +++ FIX THIS ++++

		self.attributes['description']=''
		self.attributes['note']=''

	def getRecordXMLName(self):
		return 'ToDoDataRecord'

	
	def _crackPayload(self,dstr):
#		self.attributes['debug_payload']=dstr.encode('HEX')

		# tell the StructMap to crack the data for us
		self.taskHeader.fromByteArray(dstr)

		# copy the data from the structmap
		self.attributes['dueDate']=crackPalmDatePacked(self.taskHeader['dueDate'])
		# evidently *completed* is the leftmost bit in priority
		setBooleanAttributeFromBits(self.attributes,'completed',self.taskHeader['priority'],7)
		self.attributes['priority']=getBits(self.taskHeader['priority'],6,7)

		# find the part of the data that will be our description and note
		descriptionNoteString=dstr[self.taskHeader.getSize():]
		# now we assume that the string _will_ end in a zero, this should break apart the strings for us
		(description,note)=descriptionNoteString.split('\0')[:2]
		# now set in our attributes
		self.attributes['description']=description.decode('palmos')
		self.attributes['note']=note.decode('palmos')
	
	
	def _packPayload(self):
		# copy the data to the structmap
		self.taskHeader['dueDate']=packPalmDatePacked(self.attributes['dueDate'])
		# set the priority and completed in one statement
		self.taskHeader['priority']=setBitsFromBooleanAttribute(self.attributes,'completed',self.taskHeader['priority'],7)

		dstr=self.taskHeader.toByteArray()
		dstr+=self.attributes['description'].encode('palmos')+'\0'
		dstr+=self.attributes['note'].encode('palmos')+'\0'
		return dstr
