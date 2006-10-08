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

import Plugins.BasePlugin

basePlugin=Plugins.BasePlugin.BasePDBFilePlugin()

# +++ READ THIS +++ Plugins need to implement the interface in Plugins.BasePlugin.BasePDBFilePlugin
PDBPlugins={}
PalmApplications={}
def registerPDBPlugin(PDBFilePluginClass):
	type=PDBFilePluginClass.getPDBCreatorID()
	PDBPlugins[type]=PDBFilePluginClass
	PalmApplications[type]=PDBFilePluginClass.getPalmApplicationName()
def deRegisterPDBPlugin(PDBFilePluginClass):
	type=PDBFilePluginClass.getPDBCreatorID()
	del(PDBPlugins[type])
	del(PalmApplications[type])

def getPDBPlugin(CreatorID):
        # if we cannot find an appropriate plugin, default to one that can handle any type
	return PDBPlugins.get(CreatorID,basePlugin)
def getPalmApplicationName(CreatorID):
        # if we cannot find an appropriate plugin, default to one that can handle any type
	return PalmApplications.get(CreatorID,None)
def getCreatorIDFromApplicationName(applicationName):
	reverseDictionary={}
	(keys,values)=zip(*PalmApplications.items())
	reverseDictionary.update(zip(values,keys))
	return reverseDictionary.get(applicationName,None)

def PalmApplicationName(CreatorID):
        # if we cannot find an appropriate plugin, default to one that can handle any type
	return PalmApplications.get(CreatorID,None)

#
#--------- Register Standard Plugins that come with Library ---------
#

import Plugins.ProgectPlugin
import Plugins.PalmToDoPlugin
#import StandardNotepadPDBPlugin

registerPDBPlugin(Plugins.ProgectPlugin.ProgectPlugin())
registerPDBPlugin(Plugins.PalmToDoPlugin.PalmToDoPlugin())
#registerPDBPlugin(StandardNotepadPDBPlugin.plugin)
