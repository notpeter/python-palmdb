from distutils.core import setup
import glob
import os

PalmDBVersion = '1.5.1'

# find files that 
def findExampleFiles(directoryToSearch,extensionList,prefixDirectory):
    '''Find files that end with the right suffixes, and return in a format suitable for data_files'''
    result = []
    for (directory,dirlist,files) in os.walk(directoryToSearch):
        files=[os.path.join(directory,file) for file in files if os.path.splitext(file)[1] in extensionList]
        if files:
            result.append((os.path.join(prefixDirectory,directory),files))
    return result;

def createFileList(dataFilesVariable):
    '''Return the enumeration of the files listed in dataFilesVariable which follows the format required for data_files'''
    result = []
    for (directory,files) in dataFilesVariable:
        result.extend([file for file in files])
    return result;

dataFilesExamples=findExampleFiles('examples',['.py','.PRC','.PDB',],os.path.join('share','PalmDB'))

# Setup list of strings to put in MANIFEST.in
includeFileList=['*.txt']
includeFileList.extend(createFileList(dataFilesExamples))
includeFileList=['include ' + fileSpec for fileSpec in includeFileList]

# Overwrite existing MANIFEST.in with our newly generated list
open('MANIFEST.in','w').write('\n'.join(includeFileList)+'\n')

setup(name="PalmDB",
      version=PalmDBVersion,
      description="Pure Python library to read/write/modify Palm PDB and PRC format databases.",
      long_description=
      '''
This module allows access to Palm OS(tm) database files on the desktop 
in pure Python. It is as simple as possible without (hopefully) being 
too simple. As much as possible Python idioms have been used to make
it easier to use and more versatile.
      ''',
      maintainer="Rick Price",
      maintainer_email="rick_price@users.sourceforge.net",
      url="https://sourceforge.net/projects/pythonpalmdb/",
      py_modules=["PalmDB"],
      data_files=dataFilesExamples,
      license="Python Software Foundation License",
      classifiers = [
          'Development Status :: 4 - Beta',
          'License :: OSI Approved :: Python Software Foundation License',
          'Intended Audience :: Developers',
          'Programming Language :: Python',
          'Topic :: Database',
          'Topic :: Software Development',
          'Operating System :: PalmOS',
          'Environment :: Handhelds/PDA\'s',
          ],
      keywords='PRC,PDB,Palm,database',
      )

