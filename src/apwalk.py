''' Attempts to enumerate all APs connected to a compatible SWD DAP. '''

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
    ''' Attempts to enumerate all APs connected to a compatible SWD DAP. '''
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
        swd.read(addr=0b01),
    ]

    # For each possible AP address, reset the line, and try to query the AP
    # IDR.
    apsel = 0b0

    while apsel <= 0b11111111:
        for command in setup:
            request.put(command)
            _handle_parity(response.get())

        # On the first query, also grab the DP IDR too.
        if apsel == 0b0:
            log.info("Querying for DP IDR")
            request.put(swd.idr())
            data = response.get()
            _handle_parity(data)

            # Print our 'friendly' display of DP IDR info.
            log.info(
                "-> DP IDR 0x%x",
                whatabanger.helpers.bits_to_bytes(data[0:31])
            )
            for key, val in whatabanger.helpers.decode_dp_idr(data).items():
                log.info("-> DP %s: %s", key, val)

        # Select the AP, and the 0xF0 bank.
        log.info("Querying for AP 0x%02x IDR", apsel)
        request.put(swd.select(apsel=apsel, apbanksel=0b1111))
        _handle_parity(response.get())

        # Read 0xFC from the AP (IDR).
        request.put(swd.read(addr=0b11, apndp=0b1))
        _handle_parity(response.get())

        # Read the contents of RDBUFF to get the real value - this is due
        # to the first read needing to be thrown away, per ARM DDI.
        request.put(swd.rdbuff())
        data = response.get()
        _handle_parity(data)

        # Print our 'friendly' display of AP IDR info.
        if whatabanger.helpers.bits_to_bytes(data[0:31]) != 0:
            log.info(
                "-> AP IDR 0x%x",
                whatabanger.helpers.bits_to_bytes(data[0:31])
            )
            for key, val in whatabanger.helpers.decode_ap_idr(data).items():
                log.info("-> AP %s: %s", key, val)

        # Read 0xF8 from the AP (ROMTABLE).
        request.put(swd.read(addr=0b10, apndp=0b1))
        _handle_parity(response.get())
        
        # Read the contents of RDBUFF to get the real value - this is due
        # to the first read needing to be thrown away, per ARM DDI.
        request.put(swd.rdbuff())
        data = response.get()
        _handle_parity(data)

        # Print the ROMTABLE base.
        if whatabanger.helpers.decode_baseaddr(data) != 0:
            log.info(
                "-> AP ROMTABLE 0x%x",
                whatabanger.helpers.decode_baseaddr(data)
            )

        # Next!
        apsel += 0b1


if __name__ == '__main__':
    main()
