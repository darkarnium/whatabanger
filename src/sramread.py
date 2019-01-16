''' Attempts to read STM32F103x SRAM (0x20000000 -> 0x40000000). '''

import time
import logging
import binascii
import multiprocessing

import whatabanger


def _handle_parity(data):
    ''' Raise an exception on parity failure. '''
    if data:
        parity = data.pop()
        if not whatabanger.swd.check_parity(parity, data):
            raise Exception("Response failed parity check!")


def main():
    ''' A Python SWD initialisation script. Simply sets up an interface. '''
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(process)d - [%(levelname)s] %(message)s',
    )
    log = logging.getLogger()

    # NOTE: Enabling debug logging has an impact on clock jitter!
    # log.setLevel(logging.DEBUG)

    # Setup an SWD object to handle building requests.
    log.info("Setting up SWD")
    swd = whatabanger.swd.Protocol()

    # We're using queues to communicate with the main execution process - 
    # which is responsible for doing the actual bit banging. This is in
    # order to (hopefully) reduce clock jitter.
    log.debug("Setting up requests queue")
    request = multiprocessing.Queue()
    log.debug("Setting up response queue")
    response = multiprocessing.Queue()
    
    # Kick off the bit banger.
    log.debug("Setting up bit banger")
    banger = whatabanger.executor.Executor(request, response)
    banger.start()

    # Define a list of messages to send - in order.
    setup = [
        swd.resync(),
        swd.idr(),
        swd.abort(),
    ]

    # Ensure the interface is setup.
    for command in setup:
        request.put(command)
        _handle_parity(response.get())

    # Attempt to extract all SRAM.
    addr = 0x20000000
    contents = []
    while addr <= 0x40000000:
        request.put(swd.tar(addr=addr))
        _handle_parity(response.get())

        # Initiate a READ via DRW - which will use the address we just wrote
        # to the TAR register.
        request.put(swd.drw())
        _handle_parity(response.get())

        # Read the contents of RDBUFF to get the real value - this is due to
        # the first read needing to be thrown away, per ARM DDI.
        request.put(swd.rdbuff())
        data = response.get()
        _handle_parity(data)

        # Log and add to contents.
        contents.extend(data)
        log.info(
            "-> 0x%x :: 0x%x ",
            addr,
            whatabanger.helpers.bits_to_bytes(data)
        )

        # Next!
        addr += 0x4

if __name__ == '__main__':
    main()
