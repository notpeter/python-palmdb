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

import sys
from optparse import OptionParser

def convertPalmApplicationNametoAppID(palmApplicationName):
    pass
def guessPalmAppID(fileName):
    pass
def guessApplicationName(fileName):
    pass

def listSupportAppsCallBack(option, opt, value, parser):
    print 'print list of supported palm apps and their desktop apps'
    sys.exit(2)
def main():
    parser = OptionParser(usage="%prog [options] from.ext to.ext", version="%prog 1.0")

    parser.add_option('-d','--desktopApplication',dest='desktopApplicationName',help='specify desktop application by name',metavar='Application_Name')
    parser.add_option('-p','--palmApplication',dest='palmApplicationName',help='specify palm application by name',metavar='Palm_Application_Name')
    parser.add_option('-l','--listApps',action='callback',help='print out a list of support Palm applications and their corresponding Desktop Applications',callback=listSupportAppsCallBack)
    
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
        

    if options.palmApplicationName:
        palmAppID=convertPalmApplicationNametoAppID(options.palmApplicationName)
    else:
        palmAppID=guessPalmAppID(arguments[Palm])

    if options.desktopApplicationName:
        applicationName=options.palmApplicationName
    else:
        applicationName=guessApplicationName(arguments[Desktop])

    if palmAppID is None:
        parser.error('Cannot determine Palm Creator ID, therefore cannot convert database')

        
    print 'actually do something'    
    # example of how to print out help
#    parser.print_help()

if __name__ == "__main__":
    sys.exit(main())

# if __name__ == "__main__":
#         ProgectDB=PDBFile('lbPG-tutorial.PDB')

#         OutputFile=open('lbPG-tutorial.xml','wb')
#         OutputFile.write(ProgectDB.toXML())
#         OutputFile.close()

#         ProgectDB2=PDBFile('lbPG-tutorial2.PDB',writeBack=True,read=False)

#         # With progect databases, we can't currently figure out the creator ID during load
#         ProgectDB2.setCreatorID('lbPG')
#         InputFile=open('lbPG-tutorial.xml','rb')
#         ProgectDB2.fromXML(InputFile)
#         InputFile.close()

#         print 'before save'
#         ProgectDB2.save()
#         print 'after save'
        
# #        XMLFile=open('test.xml')
# #        print ProgectDB.toXML()
# #         OutputFile=open('test2.xml','w')
# #         OutputFile.write(ProgectDB.toXML())
# #         OutputFile.close()
# #         XMLFile2=open('test2.xml')
# #         ProgectDB.fromXML(XMLFile2)
# #         OutputFile=open('test3.xml','w')
# #         OutputFile.write(ProgectDB.toXML())
# #        x=ProgectDB.toByteArray()
        
