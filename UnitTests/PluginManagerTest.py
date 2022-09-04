import unittest

from PalmDB.PluginManager import *
import PalmDB.Plugins.BasePlugin

class TestPDBPlugin(PalmDB.Plugins.BasePlugin.BasePDBFilePlugin):
	def getPDBCreatorID(self):
		return 'TeSt'
	def getPDBTypeID(self):
		return 'DaTa'

class PluginManagerTestCase(unittest.TestCase):
	def tearDown(self):
		try:
			plugin=TestPDBPlugin()
			deRegisterPDBPlugin(plugin)
		except:
			None
	def testRegisterNone(self):
		'''Attempt to register None as a plugin'''
		self.assertRaises(AttributeError,registerPDBPlugin,None)
	def testGetPluginNone(self):
		'''Attempt to get plugin for a non-existent type'''
		self.assertEqual(getPDBPluginByType(None,None),basePlugin)
	def testRegisterTestPluginNone(self):
		'''Attempt to register test plugin'''
		plugin=TestPDBPlugin()
		registerPDBPlugin(plugin)
		self.assertEqual(getPDBPluginByType(plugin.getPDBCreatorID(),plugin.getPDBTypeID()),plugin)
	def testDeRegisterTestPluginNone(self):
		'''Attempt to de-register test plugin'''
		plugin=TestPDBPlugin()
		
		registerPDBPlugin(plugin)
		self.assertEqual(getPDBPluginByType(plugin.getPDBCreatorID(),plugin.getPDBTypeID()),plugin)

		deRegisterPDBPlugin(plugin)
		# make sure it's gone
		self.assertRaises(KeyError,deRegisterPDBPlugin,plugin)
		
if __name__ == "__main__":
	unittest.main()
