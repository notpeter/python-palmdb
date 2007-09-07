from setuptools import setup, find_packages

PalmDBVersion = '1.8.0'

setup(
    name="PalmDB",
    version=PalmDBVersion,
    description="Pure Python library to read/write/modify Palm PDB and PRC format databases.",
    long_description=
    '''
    This module allows access to Palm OS(tm) database files on the desktop 
    in pure Python.
    This version is an almost complete rewrite of the original library to
    use plugins to read/write specific formats. It also uses plugins to
    read/write XML representations of the PDB. Hooks are provided to use
    XSLT conversions to go to application specific formats.
    Really, the only XML conversion that works completely is Palm Progect,
    but a (untested) sample Todo database plugin has been provided.
    Work is continuing, and I hope to provide plugins for the standard
    Palm databases, either written by other people or by myself over time.
    *Any* database will be converted to XML, but the application specific
    data will remain opaque, by providing a plugin you can turn the opaque
    data into something useful.
    ''',
    maintainer="Rick Price",
    maintainer_email="rick_price@users.sourceforge.net",
    url="https://sourceforge.net/projects/pythonpalmdb/",
    license='GNU Library or Lesser General Public License (LGPL)',
    classifiers = [
    'Development Status :: 4 - Beta',
    'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
    'Intended Audience :: Developers',
    'Programming Language :: Python',
    'Topic :: Database',
    'Topic :: Software Development',
    'Operating System :: PalmOS',
    'Environment :: Handhelds/PDA\'s',
    ],
    keywords='PRC,PDB,Palm,database',

    install_requires = ['4Suite_XML'],
    packages = find_packages(),
    test_suite = 'UnitTests.__init__',
    entry_points = {
        'console_scripts': [
            'PDBConvert = PalmDB.PDBConvert:main',
        ],
    },

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
#    install_requires = ['docutils>=0.3'],

#     package_data = {
#         # If any package contains *.txt or *.rst files, include them:
#         '': ['*.txt', '*.rst'],
#         # And include any *.msg files found in the 'hello' package, too:
#         'hello': ['*.msg'],
#}
    zip_safe=True,
    # could also include long_description, download_url, classifiers, etc.
)





# from distutils.core import setup
# import glob
# import os

# PalmDBVersion = '1.6.1'

# # find files that 
# def findExampleFiles(directoryToSearch,extensionList,prefixDirectory):
#     '''Find files that end with the right suffixes, and return in a format suitable for data_files'''
#     result = []
#     for (directory,dirlist,files) in os.walk(directoryToSearch):
#         files=[os.path.join(directory,file) for file in files if os.path.splitext(file)[1] in extensionList]
#         if files:
#             result.append((os.path.join(prefixDirectory,directory),files))
#     return result;

# def createFileList(dataFilesVariable):
#     '''Return the enumeration of the files listed in dataFilesVariable which follows the format required for data_files'''
#     result = []
#     for (directory,files) in dataFilesVariable:
#         result.extend([file for file in files])
#     return result;

# dataFilesExamples=findExampleFiles('examples',['.py','.PRC','.PDB',],os.path.join('share','PalmDB'))
# dataFilesExamples.extend(findExampleFiles('UnitTests',['.py','.PRC','.PDB',],''))

# # Setup list of strings to put in MANIFEST.in
# includeFileList=['*.txt','*.py']
# includeFileList.extend(createFileList(dataFilesExamples))
# includeFileList=['include ' + fileSpec for fileSpec in includeFileList]

# # Overwrite existing MANIFEST.in with our newly generated list
# open('MANIFEST.in','w').write('\n'.join(includeFileList)+'\n')

# setup(name="PalmDB",
#       version=PalmDBVersion,
#       description="Pure Python library to read/write/modify Palm PDB and PRC format databases.",
#       long_description=
#       '''
# This module allows access to Palm OS(tm) database files on the desktop 
# in pure Python. It is as simple as possible without (hopefully) being 
# too simple. As much as possible Python idioms have been used to make
# it easier to use and more versatile.
#       ''',
#       maintainer="Rick Price",
#       maintainer_email="rick_price@users.sourceforge.net",
#       url="https://sourceforge.net/projects/pythonpalmdb/",
#       packages=['PalmDB','PalmDB.Plugins'],
#       data_files=dataFilesExamples,
#       license="Python Software Foundation License",
#       classifiers = [
#           'Development Status :: 4 - Beta',
#           'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
#           'Intended Audience :: Developers',
#           'Programming Language :: Python',
#           'Topic :: Database',
#           'Topic :: Software Development',
#           'Operating System :: PalmOS',
#           'Environment :: Handhelds/PDA\'s',
#           ],
#       keywords='PRC,PDB,Palm,database',
#       )

