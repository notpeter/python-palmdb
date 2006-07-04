import unittest

import struct
from PalmDB.Util import *

def plah(toPrint):
	return struct.pack('>l',toPrint).encode('HEX')
	
class UtilSetBitsTestCase(unittest.TestCase):
 	def testSingleBitsBitToLow(self):
 		'''Set Single Bit Tests - Bit too low'''
 		originalValue=0
 		bitsToSet=0
 		MSBBitIndex=-1
 		self.assertRaises(AssertionError,setBits,originalValue,bitsToSet,MSBBitIndex)
 	def testSingleBitsOn(self):
 		'''Set Single Bit Tests'''
 		comparisonMask=1
 		startValue=0
 		bitsToSet=1
 		for MSBBitIndex in range(32):
 			testValue=setBits(startValue,bitsToSet,MSBBitIndex)
 			self.assertEqual(testValue,comparisonMask << MSBBitIndex)
	def testSingleBitsOff(self):
		'''Reset Single Bit Tests'''
                bitCount=1
		startValue=-1 # all bits set
                originalMask=pow(2,bitCount)-1
		bitsToSet=0
		for MSBBitIndex in range(32):
			comparisonMask=originalMask<<MSBBitIndex
			testValue=setBits(startValue,bitsToSet,MSBBitIndex)
			self.assertEqual(testValue,startValue&~comparisonMask)
	def testSingleBitsBitToHigh(self):
		'''Set Single Bit Tests - Bit too high'''
		originalValue=0
		bitsToSet=0
		MSBBitIndex=33
		self.assertRaises(AssertionError,setBits,originalValue,bitsToSet,MSBBitIndex)
 	def testSetBitsAskForNoBits(self):
 		'''Set Bit Tests - No bits requested'''
 		originalValue=0
 		MSBBitIndex=1
 		bitsToSet=0
 		bitCount=0
 		self.assertRaises(AssertionError,setBits,originalValue,bitsToSet,MSBBitIndex,bitCount)

 	def testSetBitsAskForTooManyBits(self):
 		'''Set Bit Tests - Too many bits'''
 		originalValue=0
 		bitsToSet=0
 		for MSBBitIndex in range(32):
 			bitCount=MSBBitIndex+2
 			self.assertRaises(AssertionError,setBits,originalValue,bitsToSet,MSBBitIndex,bitCount)
 	def testSetBitsAskForJustEnoughBits(self):
 		'''Set Bit Tests - Just enough bits; should exception if problem'''
 		originalValue=0
 		bitsToSet=0
 		for MSBBitIndex in range(32):
 			bitCount=MSBBitIndex+1
 			setBits(originalValue,bitsToSet,MSBBitIndex,bitCount)


class UtilGetBitsTestCase(unittest.TestCase):
	def testSingleBitsBitToLow(self):
		'''Get Single Bit Tests - Bit too low'''
		originalValue=0
		MSBBitIndex=-1
		self.assertRaises(AssertionError,getBits,originalValue,MSBBitIndex)
	def testSingleBits(self):
		'''Get Single Bit Tests'''
		comparisonMask=1
		for MSBBitIndex in range(32):
			returnValue=getBits(comparisonMask<<MSBBitIndex,MSBBitIndex)
			self.assertEqual(returnValue,1)
	def testSingleBitsBitToHigh(self):
		'''Get Single Bit Tests - Bit too high'''
		originalValue=0
		MSBBitIndex=33
		self.assertRaises(AssertionError,getBits,originalValue,MSBBitIndex)

	def testGetBitsAskForNoBits(self):
		'''Get Bit Tests - No bits requested'''
		originalValue=0
		MSBBitIndex=1
		bitCount=0
		self.assertRaises(AssertionError,getBits,originalValue,MSBBitIndex,bitCount)

	def testGetBitsAskForTooManyBits(self):
		'''Get Bit Tests - Too many bits requested'''
		originalValue=0
		for MSBBitIndex in range(32):
			bitCount=MSBBitIndex+2
			self.assertRaises(AssertionError,getBits,originalValue,MSBBitIndex,bitCount)
	def testGetBitsAskForJustEnoughBits(self):
		'''Get Bit Tests - Just enough bits requested; should assert if problem'''
		originalValue=0
		for MSBBitIndex in range(32):
			bitCount=MSBBitIndex+1
			getBits(originalValue,MSBBitIndex,bitCount)

if __name__ == "__main__":
	unittest.main()

