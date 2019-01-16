# What-A-Banger

This repository contains a rudimentary SWD implementation in Python using an
FT2232H for interfacing with the target device. This was developed as part of
research into an STM32F103x device, which lead to a requirement to 'properly'
understand the SWD protocol.

### Scripts

Although What-A-Banger is intended to be used to interact with devices
supporting SWD in a flexible manner, a few example scripts have been
provided.

* `apwalk.py`
** Attempts to enumerate all APs connected to a compatible SWD DAP.
* `swdinit.py`
** An SWD initialisation script. Simply sets up an interface.
* `sramread.py`
** Attempts to read STM32F103x SRAM (`0x20000000` -> `0x40000000`).

### Testing

Tox has been used for testing. Please ensure that tox is installed before
attempting to run!

To run all tests, simply execute the following from this directory:

```
tox
```

### More Information

For more information on SWD, see:

* http://www.kernelpicnic.net/2018/12/29/Messing-with-SWD-Part-I.html
