from setuptools import setup, find_packages

PalmDBVersion = '1.8.1'

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
    read/write XML representations of the PDB. The default format is XML, but
    it is possible to read/write other formats. If there is no plugin for the
    database type you are converting, a basic one will be used. Currently
    the plugins include Progect, Progect Project List and Palm TODO.
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

    install_requires = [],
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
