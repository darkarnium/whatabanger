''' Provides a very rudimentary SWD protocol implementation. '''

from whatabanger import helpers

# Define known SWD Responses.
SWD_ACK_OK = 0x1
SWD_ACK_WAIT = 0x2
SWD_ACK_FAULT = 0x4

# Define known SWD commands.
SWD_CMD_JTAG_TO_SWD = [0x79, 0xE7]


def check_parity(parity, data):
    ''' Implements an SWD parity check. '''
    if calculate_parity(data) == parity:
        return True
    else:
        return False


def calculate_parity(data):
    ''' Implements a parity bit 'generator'. '''
    cnt = data.count(1)
    if cnt % 2 == 0:
        return 0b0
    else:
        return 0b1


class Protocol(object):
    ''' Provides a very rudimentary SWD protocol implementation. '''

    def _request(self, apndp=0b0, rnw=0b1, addr=0b00):
        ''' Constructs an SWD Request. '''
        request = 0b0
        if addr > 3:
            raise Exception("Address can only be two bits")

        # Parity is constructed based on the number of HIGH (1) bits in the
        # APnDP APnDP, RnW, and A[2:3] fields.
        bitcount = 0
        bitcount += 1 if(rnw == 0b1) else 0
        bitcount += 1 if(apndp == 0b1) else 0

        # Look-up SHOULD be quickest here.
        if addr > 0b0:
            bitcount += 1 if addr == 0b01 else 0
            bitcount += 1 if addr == 0b10 else 0
            bitcount += 2 if addr == 0b11 else 0

        # Parity here is a PITA, as we need to check bitcount in a number
        # of fields.
        if bitcount % 2 == 0:
            parity = 0b0
        else:
            parity = 0b1

        # Construct the SWD Request header.
        request |= 0b1          # Start Bit
        request |= apndp << 1   # APnDP Bit
        request |= rnw << 2     # RnW Bit
        request |= addr << 3    # Address
        request |= parity << 5  # Parity
        request |= 0b0 << 6     # Stop Bit
        request |= 0b1 << 7     # Park Bit

        # Convert to a list of bits before returning.
        return helpers.to_bit_list([request], bitflip=True)

    def read(self, addr=0b00, apndp=0b0):
        ''' Wrapper for constructing SWD READ packets. '''
        data = None
        request = []
        request.extend(self._request(addr=addr, apndp=apndp))

        # ACK and READ is required, so make sure both flags are set.
        return {'CMD': request, 'DATA': data, 'ACK': True, 'READ': True}

    def idr(self):
        ''' Returns an SWD DP IDR request packet. '''
        return self.read(addr=0b00)

    def rdbuff(self):
        ''' Returns an SWD RDBUFF request packet. '''
        return self.read(addr=0b11)

    def resync(self):
        ''' Returns an SWD 'reset' sequence. '''
        data = None
        request = []
        request.extend([0b1] * 50)
        request.extend(helpers.to_bit_list(SWD_CMD_JTAG_TO_SWD, bitflip=True))
        request.extend([0b1] * 50)
        request.extend([0b0] * 2)

        # No ACK or READ required after a resync.
        return {'CMD': request, 'DATA': data, 'ACK': False, 'READ': False}

    def drw(self):
        ''' Returns an SWD DRW READ packet (WRITE unsupported right now). '''
        sequence = []
        sequence.extend(self._request(addr=0b11, rnw=0b1, apndp=0b1))

        # ACK and READ is required, so make sure both flags are set.
        return  {'CMD': sequence, 'DATA': None, 'ACK': True, 'READ': True}

    def tar(self, addr=0b00000000000000000000000000000000):
        ''' Returns an SWD TAR write packet. '''
        sequence = []
        sequence.extend(self._request(addr=0b01, rnw=0b0, apndp=0b1))

        # Construct the TAR request.
        data = []
        data.extend(helpers.to_bit_list([addr], 32))  # ADDR
        data.reverse()

        # Parity always trails.
        data.append(calculate_parity(data))

        # ACK is required, as is data, so make sure those fields are set.
        return  {'CMD': sequence, 'DATA': data, 'ACK': True, 'READ': False}

    def select(self, apsel=0b00000000, apbanksel=0b0000, dpbanksel=0b0000, apndp=0b0):
        ''' Returns an SWD SELECT request packet. '''
        sequence = []
        sequence.extend(self._request(addr=0b10, rnw=0b0, apndp=apndp))

        # Construct the SELECT request.
        data = []
        data.extend(helpers.to_bit_list([apsel]))         # APSEL.
        data.extend([0b0] * 16)                           # RESERVED.
        data.extend(helpers.to_bit_list([apbanksel], 4))  # APBANKSEL.
        data.extend(helpers.to_bit_list([dpbanksel], 4))  # DPBANKSEL.
        data.reverse()                                    # Bitflip (MSb/LSb)

        # Parity always trails.
        data.append(calculate_parity(data))

        # ACK is required, as is data, so make sure those fields are set.
        return  {'CMD': sequence, 'DATA': data, 'ACK': True, 'READ': False}

    def abort(self):
        ''' Returns an SWD ABORT request packet. '''
        sequence = []
        sequence.extend(self._request(addr=0b00, rnw=0b0))

        # Reserved to 0b0 * N. Clear all, no DAPABORT.
        data = [0b0] * 27
        data.extend([0b1])  # ORUNERRCLR
        data.extend([0b1])  # WDERRCLR
        data.extend([0b1])  # STKERRCLR
        data.extend([0b1])  # STKCMPCLR
        data.extend([0b0])  # DAPABORT
        data.reverse()      # Bitflip (MSb/LSb)

        # Parity always trails.
        data.append(calculate_parity(data))

        # ACK is required, as is data, so make sure those fields are set.
        return  {'CMD': sequence, 'DATA': data, 'ACK': True, 'READ': False}

    def stat(self):
        ''' Returns an SWD CTRL/STAT READ request packet. '''
        sequence = []
        sequence.extend(self._request(addr=0b01))

        # ACK is required.
        return  {'CMD': sequence, 'DATA': None, 'ACK': True, 'READ': True}

    def ctrl(self, cdbgpweupreq=0b0, csyspwrupreq=0b0):
        ''' Returns an SWD CTRL/STAT WRITE request packet. '''
        sequence = []
        sequence.extend(self._request(addr=0b01, rnw=0b0))

        # Set only required CTRL fields.
        data = []
        data.extend([0b0])           # CSYSPWRUPACK
        data.extend([csyspwrupreq])  # CSYSPWRUPREQ
        data.extend([0b0])           # CDBGPWRUPACK
        data.extend([cdbgpweupreq])  # CDBGPWRUPREQ
        data.extend([0b0])           # CDBGSTACK
        data.extend([0b0])           # CDBGSTREQ
        data.extend([0b0])           # RESERVED
        data.extend([0b0])           #
        data.extend([0b0] * 12)      # TRNCNT
        data.extend([0b0] * 4)       # MASKLANE
        data.extend([0b0])           # WDATAERR
        data.extend([0b0])           # READOK
        data.extend([0b0])           # STICKYERR
        data.extend([0b0])           # STICKYCMP
        data.extend([0b0])           # TRNMODE
        data.extend([0b0])           #
        data.extend([0b0])           # STICKYORUN
        data.extend([0b0])           # ORUNDETECT
        data.reverse()               # Bitflip (MSb/LSb)

        # Parity always trails.
        data.append(calculate_parity(data))

        # ACK is required, as is data, so make sure those fields are set.
        return  {'CMD': sequence, 'DATA': data, 'ACK': True, 'READ': False}
