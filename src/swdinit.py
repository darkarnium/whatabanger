''' A Python SWD initialisation script. Simply sets up an interface. '''

import time
import logging
import binascii
import multiprocessing

import whatabanger


def main():
    ''' A Python SWD initialisation script. Simply sets up an interface. '''
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(process)d - [%(levelname)s] %(message)s',
    )
    log = logging.getLogger()

    # NOTE: Enabling debug logging has an impact on clock jitter!
    log.setLevel(logging.DEBUG)

    # Setup an SWD object to handle building requests.
    log.info("Setting up SWD")
    swd = whatabanger.swd.Protocol()

    # We're using queues to communicate with the main execution process - 
    # which is responsible for doing the actual bit banging. This is in
    # order to (hopefully) reduce clock jitter.
    log.info("Setting up requests queue")
    request = multiprocessing.Queue()
    log.info("Setting up response queue")
    response = multiprocessing.Queue()
    
    # Kick off the bit banger.
    log.info("Setting up bit banger")
    banger = whatabanger.executor.Executor(request, response)
    banger.start()

    # Define a list of messages to send - in order.
    commands = [
        swd.resync(),
        swd.idr(),
        swd.read(addr=0b01),
        swd.abort(),
        swd.read(addr=0b01),
        swd.select(apbanksel=0b1111),    # Select 0xF0 bank on AP0.
        swd.read(addr=0b11, apndp=0b1),  # Read 0xFC from AP0 (IDR).
        swd.read(addr=0b10, apndp=0b1),  # Read 0xF8 from AP0 (ROMTABLE).
    ]

    for command in commands:
        request.put(command)
        data = response.get()

        if data:
            parity = data.pop()
            log.info("Response: %x", whatabanger.helpers.bits_to_bytes(data))

            # Do a quick parity check (TODO: Re-try?)
            if not whatabanger.swd.check_parity(parity, data):
                log.error("Response failed parity check!")

    # DEBUG.
    time.sleep(65535)


if __name__ == '__main__':
    main()
