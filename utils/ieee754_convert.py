import struct
import binascii
import sys


def format_1(p_input):
    parts = p_input.split(', ')
    parts_without_0x = list()
    for part in parts:
        a = part.replace('0x', '')
        b = a.zfill(2)
        parts_without_0x.append(b)

    output = ''
    for p in parts_without_0x:
        output += p
    # print(output)
    return output


def ieee754_to_rendered_str(val):
    value = struct.unpack('>f', binascii.unhexlify(val))
    rounded_val = round(value[0], 4)
    return rounded_val


def main(args):
    for i in range(1, len(args)):
        value = args[i]
        if '0x' in value:
            value = format_1(value)
        else:
            value = value.replace(' ', '')
        if len(value) != 8:
            print(args[i] + ' => Length must be 8 characters. Example: "3ca3d70a" or "0x3c, 0xa3, 0xd7, 0x0a"')
            continue
        converted_value = ieee754_to_rendered_str(value)
        print(args[i] + ' => ' + str(converted_value))


if __name__ == '__main__':
    main(sys.argv)
