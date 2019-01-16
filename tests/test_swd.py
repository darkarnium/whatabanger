''' Implements tests for the SWD module. '''

import unittest
import coverage

import whatabanger


class WhatABangerSWDTestCase(unittest.TestCase):
    ''' Implements tests for the SWD module. '''

    def setUp(self):
        ''' Ensure the application is setup for testing. '''
        self.protocol = whatabanger.swd.Protocol()

    def tearDown(self):
        ''' Ensure everything is torn down between tests. '''
        pass

    def test_check_parity(self):
        ''' Ensures parity bit generation works as expected. '''
        # Number of bits set to 1 odd? Parity is 1. Otherwise,
        # it's 0.
        self.assertTrue(whatabanger.swd.check_parity(0, [0, 0]))
        self.assertTrue(whatabanger.swd.check_parity(1, [0, 1]))
        self.assertTrue(whatabanger.swd.check_parity(0, [1, 1]))

    def test__request(self):
        ''' Ensures the request method generates correct packets. '''
        candidate = self.protocol._request()
        desired = [1, 0, 1, 0, 0, 1, 0, 1]
        self.assertEqual(candidate, desired)

    def test_idr(self):
        ''' Ensures the idr method generates correct packets. '''
        candidate = self.protocol.idr()
        desired = [1, 0, 1, 0, 0, 1, 0, 1]
        self.assertEqual(candidate['CMD'], desired)

    def test_rdbuff(self):
        ''' Ensures the rdbuff method generates correct packets. '''
        candidate = self.protocol.rdbuff()
        desired = [1, 0, 1, 1, 1, 1, 0, 1]
        self.assertEqual(candidate['CMD'], desired)

    def test_stat(self):
        ''' Ensures the stat method generates correct packets. '''
        candidate = self.protocol.stat()
        desired = [1, 0, 1, 1, 0, 0, 0, 1]
        self.assertEqual(candidate['CMD'], desired)

    def test_read(self):
        ''' Ensures the read method generates correct packets. '''
        candidate = self.protocol.read()
        desired = [1, 0, 1, 0, 0, 1, 0, 1]
        self.assertEqual(candidate['CMD'], desired)

        candidate = self.protocol.read(addr=0b01)
        desired = [1, 0, 1, 1, 0, 0, 0, 1]
        self.assertEqual(candidate['CMD'], desired)

        candidate = self.protocol.read(apndp=0b1)
        desired = [1, 1, 1, 0, 0, 0, 0, 1]
        self.assertEqual(candidate['CMD'], desired)

    def test_tar(self):
        ''' Ensures the tar method generates correct packets. '''
        candidate = self.protocol.tar(addr=0x20000000)
        desired = [1, 1, 0, 1, 0, 0, 0, 1]
        self.assertEqual(candidate['CMD'], desired)

        # Ensure the request body is valid.
        desired = [
            0, 0, 1, 0, 0, 0, 0, 0,  # ADDRESS (0x20000000)
            0, 0, 0, 0, 0, 0, 0, 0,  #
            0, 0, 0, 0, 0, 0, 0, 0,  #
            0, 0, 0, 0, 0, 0, 0, 0,  #
        ]
        desired.reverse()            # FLIP LSb-to-MSb
        desired.extend([1])          # PARITY
        self.assertEqual(candidate['DATA'], desired)

        # Ensure flags are valid.
        self.assertEqual(candidate['ACK'], True)
        self.assertEqual(candidate['READ'], False)

    def test_drw(self):
        ''' Ensures the drw method generates correct packets. '''
        candidate = self.protocol.drw()
        desired = [1, 1, 1, 1, 1, 0, 0, 1]
        self.assertEqual(candidate['CMD'], desired)

    def test_select(self):
        ''' Ensures the select method generates correct packets. '''
        candidate = self.protocol.select(apbanksel=0b1111)
        desired = [1, 0, 0, 0, 1, 1, 0, 1]
        self.assertEqual(candidate['CMD'], desired)

        # Ensure the request body is valid.
        desired = [
            0, 0, 0, 0, 0, 0, 0, 0,  # APSEL - AHB-AP (0x0)
            0, 0, 0, 0, 0, 0, 0, 0,  # RESERVED
            0, 0, 0, 0, 0, 0, 0, 0,  #
            1, 1, 1, 1,              # APBANKSEL - BANK 0xF (0xF)
            0, 0, 0, 0,              # DPBANKSEL - CTRL/STAT (0x0)
        ]
        desired.reverse()            # FLIP LSb-to-MSb
        desired.extend([0])          # PARITY
        self.assertEqual(candidate['DATA'], desired)

        # Ensure flags are valid.
        self.assertEqual(candidate['ACK'], True)
        self.assertEqual(candidate['READ'], False)

    def test_abort(self):
        ''' Ensures the abort method generates correct packets. '''
        candidate = self.protocol.abort()
        desired = [1, 0, 0, 0, 0, 0, 0, 1]
        self.assertEqual(candidate['CMD'], desired)

        # Ensure the request body is valid.
        desired = [
            0, 0, 0, 0, 0, 0, 0, 0,  # RESERVED
            0, 0, 0, 0, 0, 0, 0, 0,  #
            0, 0, 0, 0, 0, 0, 0, 0,  #
            0, 0, 0,                 #
            1,                       # ORUNERRCLR
            1,                       # WDERRCLR
            1,                       # STKERRCLR
            1,                       # STKCMPCLR
            0,                       # DAPABORT
        ]
        desired.reverse()            # FLIP LSb-to-MSb
        desired.extend([0])          # PARITY

        self.assertEqual(candidate['DATA'], desired)

        # Ensure flags are valid.
        self.assertEqual(candidate['ACK'], True)
        self.assertEqual(candidate['READ'], False)

    def test_ctrl(self):
        ''' Ensures the ctrl method generates correct packets. '''
        candidate = self.protocol.ctrl()
        desired = [1, 0, 0, 1, 0, 1, 0, 1]
        self.assertEqual(candidate['CMD'], desired)

        # Ensure the request body is valid.
        desired = [
            0, 0, 0, 0, 0, 0, 0, 0,  # CSYSPWRUPACK ... RESERVED
            0, 0, 0, 0, 0, 0, 0, 0,  # TURNCNT
            0, 0, 0, 0,              #
            0, 0, 0, 0,              # MASKLANE
            0, 0, 0, 0, 0, 0, 0, 0,  # WDATAERR ... ORUNDETECT
        ]
        desired.reverse()            # FLIP LSb-to-MSb
        desired.extend([0])          # PARITY
        self.assertEqual(candidate['DATA'], desired)

        # Ensure flags are valid.
        self.assertEqual(candidate['ACK'], True)
        self.assertEqual(candidate['READ'], False)
