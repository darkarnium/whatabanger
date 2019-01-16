'''
Provides an executor - responsible for banging data onto and off of the wire -
which is intended to be run in a separate process. This also handles timing
and has been built to use queues to try and reduce clock jitter.
 '''

import time
import logging
import multiprocessing

from whatabanger import swd
from whatabanger import helpers

from struct import pack
from struct import unpack
from operator import xor
from pyftdi.gpio import GpioController 


class Executor(multiprocessing.Process):
    '''
    Provides an executor - responsible for banging data onto and off of the
    wire - which is intended to be run in a separate process. This also
    handles timing and has been built to use queues to try and reduce clock
    jitter.
    '''

    def __init__(self, req, res, swclk=0x01, swdio=0x02, clock=0.001):
        ''' Ensure a logger is setup, and access to the GPIO is possible. '''
        super(Executor, self).__init__()
        self.log = logging.getLogger(__name__)

        # The intial state is everything pulled LOW.
        self.state = 0x0

        # Ensure the work queue is accessible - this is used for the parent
        # to push request to bang onto the wire.
        self._in = req
        self._out = res

        # Defaults are:
        #     Pin D0 - 0x01 - OUT (TCK)
        #     Pin D1 - 0x02 - OUT (TDI / TDO)
        self.swclk = swclk
        self.swdio = swdio

        # Setup the clock interval. This isn't the cycle time, but half the
        # target cycle time.
        self.clock = clock

        # Setup the interface.
        self.gpio = GpioController()
        self.log.debug("Setting up FT2232 for GPIO")
        self.gpio.open_from_url(url='ftdi://0x0403:0x6010/1', direction=0xFF)

        # Set the initial GPIO state.
        self.log.debug("Setting the initial GPIO state to %s", self.state)
        self.gpio.write_port(self.state)

    def _write_bits(self, bits):
        ''' Write bits onto the wire (Master to Target) communication. '''
        self.log.debug("Starting banging bits (%s)", bits)

        # First, ensure the GPIO is set to OUT.
        self.gpio.set_direction(self.swdio, self.swdio)

        for bit in bits:
            # Pull the clock HIGH.
            self.state |= self.swclk
            self.gpio.write_port(self.state)
            time.sleep(self.clock)

            # Check whether we need to write a HIGH or LOW for the bit to be
            # transmitted (where HIGH is 1).
            if bit == 1:
                self.state |= self.swdio
            else:
                self.state &= ~self.swdio

            # Send data via SWDIO on the FALLING-edge of the clock.
            self.state &= ~self.swclk
            self.gpio.write_port(self.state)
            time.sleep(self.clock)

        # If there's not a Logic Analyser connected, determining when all
        # data has been sent is a pain. Thus, this.
        self.log.debug("Finished banging bits")

    def _read_bits(self, count):
        ''' Reads N bits from the wire (Target to Master) communication. '''
        self.log.debug("Reading %s bits", count)

        # First, ensure that the SWDIO pin is set to IN, rather than OUT, and
        # leave it the fuck alone.
        self.gpio.set_direction(self.swdio, 0x0)

        result = []
        for _ in range(count):
            # Data will be banged onto the wire by the target device on the
            # RISING edge.
            self.state |= self.swclk
            self.gpio.write_port(self.state)

            # Finally, read the state of SWDIO to determine the value sent by
            # the target.
            if(self.gpio.read() & self.swdio) == self.swdio:
                result.append(1)
            else:
                result.append(0)

            # Sleep and then drive the clock LOW to complete the cycle.
            time.sleep(self.clock)
            self.state &= ~self.swclk
            self.gpio.write_port(self.state)
            time.sleep(self.clock)

        self.log.debug("Read %s", result)
        return result

    def _write_clock(self):
        ''' 'Write' a clock cycle without sending any data. '''
        # Pull the clock HIGH.
        self.state |= self.swclk
        self.gpio.write_port(self.state)
        time.sleep(self.clock)

        # Pull the clock LOW.
        self.state &= ~self.swclk
        self.gpio.write_port(self.state)
        time.sleep(self.clock)

    def _check_ack(self):
        ''' Convenience method to handle ACKs. '''
        # TODO: Handle SWD_ACK_WAIT.
        ack = helpers.bits_to_bytes(self._read_bits(3))
        if ack != swd.SWD_ACK_OK:
            raise Exception("SWD ACK response was NOT OK")

    def run(self):
        ''' Starts clocking SWCLK, and banging bits onto SWDIO as needed. '''
        self.log.info("Bit banger clock and monitor started")
        while True:
            # Ensure data is sent, if there is anything in the queue.
            if self._in.qsize() > 0:
                request = self._in.get()
                result = []

                # Write the request, and read results - if required.
                self._write_bits(request['CMD'])
                if request['ACK']:
                    # 'Turn-round' so the target can control SWDIO.
                    self._write_clock()
                    self._check_ack()

                    # Reading data and writing data are mutually exclusive in
                    # a single operation - with the exception of ACKs - so
                    # we don't allow both.
                    if request['DATA']:
                        # 'Turn-round' so the host can again control SWDIO.
                        self._write_clock()
                        self._write_bits(request['DATA'])
                    elif request['READ']:
                        # 32-bits for the payload, plus the parity, and then
                        # 'turn-round' again to return control of SWDIO to
                        # the host.
                        result = self._read_bits(33)
                        self._read_bits(1)

                    # Complete the operation by clocking out 8 more rising
                    # edges.
                    self._write_bits([0b0] * 8)

                # A result is always sent back to the main thread, even if
                # empty. This allows it to confirm requests were serviced.
                self._out.put(result)
            else:
                # If no data is pending send, make sure we still drive the
                # clock.
                self._write_clock()
