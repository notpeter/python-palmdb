#!/usr/bin/env python
#
# Example of assembling all available unit tests into one suite. This usually
# varies greatly from one project to the next, so the code shown below will not
# be incorporated into the 'unittest' module. Instead, modify it for your own
# purposes.
#
# $Id: alltests.py,v 1.3 2001/03/12 11:52:56 purcell Exp $

import unittest

from .UtilTest import *
from .PluginManagerTest import *


class ModuleTestCase(unittest.TestCase):
    def setUp(self):
        None

    def tearDown(self):
        None

    def testSetBits(self):
        assert (1 == 1)

    def testSetBits2(self):
        assert (1 == 1)


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
