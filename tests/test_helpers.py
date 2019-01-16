''' Implements tests for the Helpers module. '''

import unittest
import coverage

import whatabanger


class WhatABangerHelpersTestCase(unittest.TestCase):
    ''' Implements tests for the Helpers module. '''

    def setUp(self):
        ''' Ensure the application is setup for testing. '''
        pass

    def tearDown(self):
        ''' Ensure everything is torn down between tests. '''
        pass

    def test_to_bit_list(self):
        ''' Ensures integer to bit-list conversion works as expected. '''
        # Input should be REVERSED (MSb to LSb).
        candidate = whatabanger.helpers.to_bit_list([0b10000101], bitflip=True)
        desired = [1, 0, 1, 0, 0, 0, 0, 1]
        self.assertEqual(candidate, desired)

        candidate = whatabanger.helpers.to_bit_list([0b1], bitflip=True)
        desired = [1, 0, 0, 0, 0, 0, 0, 0]
        self.assertEqual(candidate, desired)

        # Input should NOT be REVERSED (MSb to LSb).
        candidate = whatabanger.helpers.to_bit_list([0b10100001])
        desired = [1, 0, 1, 0, 0, 0, 0, 1]
        self.assertEqual(candidate, desired)

        candidate = whatabanger.helpers.to_bit_list([0b1])
        desired = [0, 0, 0, 0, 0, 0, 0, 1]
        self.assertEqual(candidate, desired)

    def test_bits_to_bytes(self):
        ''' Ensutes the bits to bytes conversion works as expected. '''
        # Input should be REVERSED (MSb to LSb).
        self.assertEqual(
            whatabanger.helpers.bits_to_bytes([1, 0, 0, 0, 0, 0, 0, 0]),
            0x1,
        )
        self.assertEqual(
            whatabanger.helpers.bits_to_bytes([1, 1, 1, 1, 1, 1, 1, 1]),
            0xFF,
        )
        self.assertEqual(
            whatabanger.helpers.bits_to_bytes([0, 0, 0, 0, 0, 0, 0, 1]),
            0x80,
        )
