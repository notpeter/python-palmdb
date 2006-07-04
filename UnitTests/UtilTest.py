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
 	def testMultipleBitsOn(self):
 		'''Set Multiple Bit Tests'''
		for bitCount in range(1,32):
			comparisonMask=pow(2,bitCount)-1
			bitsToSet=-1 # Check masking of unwanted bits
			startValue=0
			for MSBBitIndex in range(bitCount-1,32):
				shift=MSBBitIndex-bitCount+1
				testValue=setBits(startValue,bitsToSet,MSBBitIndex,bitCount)
				self.assertEqual(testValue,comparisonMask << shift)
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
	def testMultipleBitsOff(self):
		'''Reset Multiple Bit Tests'''
		for bitCount in range(1,32):
			comparisonMask=pow(2,bitCount)-1
			bitsToSet=0 # Check masking of unwanted bits
			startValue=-1
			for MSBBitIndex in range(bitCount-1,32):
				shift=MSBBitIndex-bitCount+1
				testValue=setBits(startValue,bitsToSet,MSBBitIndex,bitCount)
				self.assertEqual(testValue,~(comparisonMask << shift))
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
 	def testMultipleBits(self):
 		'''Get Multiple Bit Tests'''
		for bitCount in range(1,32):
			comparisonMask=pow(2,bitCount)-1
			for MSBBitIndex in range(bitCount-1,32):
				shift=MSBBitIndex-bitCount+1
				testValue=getBits(comparisonMask<<shift,MSBBitIndex,bitCount)
				self.assertEqual(testValue,comparisonMask)
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

