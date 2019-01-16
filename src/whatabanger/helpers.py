''' Provides helpers for working with bits and bytes. '''

# Provides a quick list of JDEC JEP106 designer IDs.
JDEC_JEP106 = {
    571: 'ARM (0x23B)'
}


def to_bit_list(entries, width=8, bitflip=False):
    ''' Convert interger list to a list of bits. '''
    result = []

    # TODO: Do this without string formatting.
    fmt = '{{0:0{}b}}'.format(width)
    for entry in entries:
        for bit in list(fmt.format(entry)):
            result.append(1 if bit == '1' else 0)

    # Flip LSb to MSb, if requested.
    if bitflip:
        result.reverse()

    return result

def bits_to_bytes(data):
    ''' Convert a list of bits to bytes - also flips LSb to MSb. '''
    result = 0x0
    for idx, bit in enumerate(data):
        result |= bit << idx

    return result

def decode_dp_idr(data):
    ''' Attempts to decode a DP IDR  - provided as an LSB list. '''
    if len(data) != 32:
        raise Exception("A DP IDR payload should be 32-bits long")

    # Decode the version to something readable.
    if bits_to_bytes(data[12:16]) == 0:
        version = 'Reserved'
    elif bits_to_bytes(data[12:16]) == 1:
        version = 'DPv1'
    elif bits_to_bytes(data[12:16]) == 2:
        version = 'DPv2'
    else:
        version = 'Unknown'

    # Decode MINDP to something grokable.
    if bits_to_bytes([data[16]]) == 0:
        mindp = 'Yes'
    elif bits_to_bytes([data[16]]) == 1:
        mindp = 'No'
    else:
        mindp = 'Unknown'

    # Attempt to lookup the Designer.
    try:
        designer = JDEC_JEP106[bits_to_bytes(data[1:12])]
    except KeyError:
        designer = 'Unknown (0x{:0x})'.format(bits_to_bytes(data[1:12]))

    # Fields per section 2.3.5 of ARM IHI0031C.
    return {
        'Designer': designer,
        'Revision': '0x{:0x}'.format(bits_to_bytes(data[28:32])),
        'Version': version,
        'Part Number': '0x{:0x}'.format(bits_to_bytes(data[20:28])),
        'Minimal Debug Port Implemented': mindp,
    }


def decode_ap_idr(data):
    ''' Attempts to decode an AP IDR  - provided as an LSB list. '''
    if len(data) != 32:
        raise Exception("A AP IDR payload should be 32-bits long")

    # Decode the class to something readable.
    if data[16] == 0b1:
        klass = 'Memory AP (MEM-AP)'
    else:
        klass = 'No Defined Class (0x{:0x})'.format(
            bits_to_bytes(data[13:17])
        )

    # Fields per section 6.3.1 of ARM IHI0031C.
    return {
        'Revision': '0x{:0x}'.format(bits_to_bytes(data[28:32])),
        'JEP106 Identity': '0x{:0x}'.format(bits_to_bytes(data[17:24])),
        'JEP106 Continuation': '0x{:0x}'.format(bits_to_bytes(data[24:28])),
        'AP Identification (Type)': '0x{:0x}'.format(bits_to_bytes(data[0:4])),
        'AP Identification (Variant)': '0x{:0x}'.format(bits_to_bytes(data[4:8])),
        'Class': klass,
    }

def decode_baseaddr(data):
    ''' Attempts to 'decode' a ROM table address - provided as an LSB list. '''
    if len(data) != 32:
        raise Exception("A BASE payload should be 32-bits long")

    # Append 0x0000 to the end, per section 7.6.1 of ARM IHI0031C.
    addr = []
    addr.extend([0b0] * 12)
    addr.extend(data[12:])

    return bits_to_bytes(addr)
