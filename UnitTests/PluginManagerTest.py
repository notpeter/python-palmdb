import unittest

from PalmDB.PluginManager import *
import PalmDB.Plugins.BasePlugin

class TestPDBPlugin(PalmDB.Plugins.BasePlugin.BasePDBFilePlugin):
	def getPDBCreatorID(self):
		return 'TeSt'

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
		self.assertEquals(getPDBPluginByType(None,None),basePlugin)
 	def testRegisterTestPluginNone(self):
 		'''Attempt to register test plugin'''
		plugin=TestPDBPlugin()
		registerPDBPlugin(plugin)
		self.assertEquals(getPDBPluginByType(plugin.getPDBCreatorID(),plugin.getPDBTypeID()),plugin)
 	def testDeRegisterTestPluginNone(self):
 		'''Attempt to de-register test plugin'''
		plugin=TestPDBPlugin()
		
		registerPDBPlugin(plugin)
		self.assertEquals(getPDBPluginByType(plugin.getPDBCreatorID(),plugin.getPDBTypeID()),plugin)

		deRegisterPDBPlugin(plugin)
		# make sure it's gone
 		self.assertRaises(KeyError,deRegisterPDBPlugin,plugin)
		
if __name__ == "__main__":
	unittest.main()

	def getPDBCreatorID(self):
#		raise NotImplementedError
		return 'Unknown'
	def getPDBTypeID(self):
