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

"""

__copyright__ = 'Copyright 2006 Rick Price <rick_price@users.sourceforge.net>'

import DesktopApplications
import Plugins.BasePlugin

basePlugin=Plugins.BasePlugin.BasePDBFilePlugin()

# +++ READ THIS +++ Plugins need to implement the interface in Plugins.BasePlugin.BasePDBFilePlugin
PDBPlugins={}
PDBApplicationIDS={}
def registerPDBPlugin(PDBFilePluginClass):
	global PDBPlugins
	global PDBApplicationIDS

	creator=PDBFilePluginClass.getPDBCreatorID()
	type=PDBFilePluginClass.getPDBTypeID()
	palmApplicationID=PDBFilePluginClass.getPalmApplicationNameID()

	PDBPlugins[(creator,type)]=PDBFilePluginClass
	PDBApplicationIDS[palmApplicationID]=PDBFilePluginClass

def deRegisterPDBPlugin(PDBFilePluginClass):
	global PDBPlugins
	global PDBApplicationIDS

	creator=PDBFilePluginClass.getPDBCreatorID()
	type=PDBFilePluginClass.getPDBTypeID()
	palmApplicationID=PDBFilePluginClass.getPalmApplicationNameID()

	del(PDBPlugins[(creator,type)])
	del(PalmApplicationIDS[palmApplicationID])

def getPDBPluginByType(CreatorID,TypeID):
	# if we cannot find an appropriate plugin, default to one that can handle any type
	return PDBPlugins.get((CreatorID,TypeID),basePlugin)

def getPDBPluginByPalmApplicationID(palmApplicationID):
	return PalmApplicationIDS[palmApplicationID]

def getPluginsForFile(filename,readOrWrite):
	if filename.upper().endswith('.PDB'):
		if readOrWrite == DesktopApplications.READ:
			file=open(filename,'rb')
			palmIDS=guessPalmIDSFromFileObject(file)
			plugin=getPDBPlugin(*palmIDS)
			return [plugin]
		else:
			# without a file, we have no way of knowing what type of Palm Application it is
			return []
	else:
		pluginList=[]
		# So it does not seem to be a PDB file, we will have to ask each plugin if they know anything about the file
		for pluginIDS,plugin in PDBPlugins.iteritems():
			retval=plugin.getSupportedApplicationsForFile(filename,readOrWrite)
			if retval:
				pluginList.append(plugin)
		return pluginList

def guessPalmIDSFromFileObject(fileObject):
	PalmDB=PalmDatabase.PalmDatabase()
	if fileObject.tell() <> 0:
		fileObject.seek(0)
	fileData=fileObject.read(PalmHeaderInfo.PDBHeaderStructSize)
	PalmDB.fromByteArray(fileData,headerOnly=True)
	return (PalmDB.getCreatorID(),PalmDB.getTypeID())

#
#--------- Register Standard Plugins that come with Library ---------
#

import Plugins.ProgectPlugin
import Plugins.PalmToDoPlugin
#import StandardNotepadPDBPlugin

registerPDBPlugin(Plugins.ProgectPlugin.ProgectPlugin())
#registerPDBPlugin(Plugins.PalmToDoPlugin.PalmToDoPlugin())
#registerPDBPlugin(StandardNotepadPDBPlugin.plugin)
