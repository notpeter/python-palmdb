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

import PalmDB
import PalmDatabase
import PluginManager
import DesktopApplications
from PalmDatabase import PalmHeaderInfo

import sys
from optparse import OptionParser

def guessPalmIDs(filename):
	try:
		PalmDB=PalmDatabase.PalmDatabase()
		fileData=open(filename,'rb').read(PalmHeaderInfo.PDBHeaderStructSize)
		PalmDB.fromByteArray(fileData,headerOnly=True)
		return (PalmDB.getCreatorID(),PalmDB.getTypeID())
	except:
		return None
def guessApplicationName(palmAppID,palmTypeID,filename):
	plugin=PluginManager.getPDBPlugin(palmAppID,palmTypeID)
	if plugin is  None:
		return None
	return plugin.getApplicationNameFromFile(filename)

def listSupportAppsCallBack(option, opt, value, parser):
	print 'print list of supported palm apps and their desktop apps'
	sys.exit(2)
def main():
	plugin=None
	parser = OptionParser(usage="%prog [options] from.ext to.ext", version="%prog 1.0")

	parser.add_option('-d','--desktopApplication',dest='desktopApplicationID',help='specify desktop application by name',metavar='Application_Name')
	parser.add_option('-p','--palmApplicationID',dest='palmApplicationID',help='specify palm application by ID',metavar='Palm_Application_ID')
	parser.add_option('-l','--listApps',action='callback',help='print out a list of supported Palm application IDs and their corresponding Desktop Applications',callback=listSupportAppsCallBack)
	
	options,arguments=parser.parse_args()
	if len(arguments) <> 2:
		parser.error('Incorrect number of arguments')

	Palm=None
	Desktop=None
	if arguments[0].upper().endswith('.PDB'):
		Palm=0
	if arguments[1].upper().endswith('.PDB'):
		Palm=1

	if not arguments[0].upper().endswith('.PDB'):
		Desktop=0
	if not arguments[1].upper().endswith('.PDB'):
		Desktop=1

	if Palm is None:
		parser.error('Can only convert between between a Palm database and a desktop application. You do not seem to have specified a palm database. Palm databases have to end in .pdb to be recognized.')

	if Desktop is None:
		parser.error('Can only convert between between a Palm database and a desktop application. You do not seem to have specified a desktop application file.')


	PalmFilename=arguments[Palm]
	DesktopFilename=arguments[Desktop]
	if options.palmApplicationID:
		plugin=PluginManager.getPDBPluginByPalmApplicationID(options.palmApplicationID)
	else:
		if Palm == 0:
			plugin=PluginManager.getPluginsForFile(PalmFilename,DesktopApplications.READ)
		else:
			plugin=PluginManager.getPluginsForFile(PalmFilename,DesktopApplications.WRITE)
	if not plugin:
		parser.error('Could not determine Palm application type.')
	palmAppID=plugin.getPDBCreatorID()
	palmTypeID=PluginManager.getPDBTypeID()

	if options.desktopApplicationID:
		desktopApplicationID=options.desktopApplicationID
	else:
		if Palm == 0:
			apps=plugin.getSupportedApplicationsForFile(DesktopFilename,DesktopApplications.WRITE)
		else:
			apps=plugin.getSupportedApplicationsForFile(DesktopFilename,DesktopApplications.READ)
		if len(apps) == 0:
			parser.error('Could not determine desktop application type.')
		elif len(apps) > 1:
			parser.error('More than one supported desktop application type for file, please specify.')
		desktopApplicationID=apps[0]

	if Palm == 0:
		print 'Converting ',PalmFilename,' to ', DesktopFilename
	else:
		print 'Converting ',DesktopFilename, ' to ',PalmFilename
		
#     print 'Desktop Filename is',DesktopFilename
#     print 'palm app id is',palmAppID
#     print 'From XML XSLT is[',FromXMLXSLT,']'
#     print 'To XML XSLT is[',ToXMLXSLT,']'
#     print 'GZIP Result is',GZIPResult

#     print 'actually do something'

	PalmDB=PalmDatabase.PalmDatabase()
	if Palm == 0:
		desktopFile=open(DesktopFilename,'wb')
		plugin.readPalmDBFromFile(PalmDB,PalmFilename)
		plugin.saveToApplicationFile(PalmDB,desktopApplicationID,desktopFile)
	else:
		desktopFile=open(DesktopFilename,'rb')
		plugin.loadFromApplicationFile(PalmDB,desktopApplicationID,desktopFile)
		plugin.writePalmDBToFile(PalmDB,PalmFilename)

if __name__ == "__main__":
	sys.exit(main())
