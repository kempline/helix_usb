import sys
from presets import preset_1, preset_2
from formatter import format_1, ieee754_to_rendered_str


def main(args):
	full_packet_data = []
	for i, packet in enumerate(preset_1):
		if i == 1:
			packet = packet[24:]
		else:
			packet = packet[16:]
		for b in packet:
			full_packet_data.append(b)

	pattern = [0xC2, 0x07, 0x00, 0x82]
	indexes = [(i, i + len(pattern)) for i in range(len(full_packet_data)) if full_packet_data[i:i + len(pattern)] == pattern]

	for idx in indexes:
		part = []
		for i in range(0, 35):
			part.append(full_packet_data[idx[0]+i])
		print(part)

	out = ''
	for b in full_packet_data:
		out += str(hex(b) + ', ')
	if out.endswith(', '):
		out = out[:-2]
	out_formatted = format_1(out)

	for i in range(0, 100):
		part = out_formatted[i*8:i*8+8]
		ieee = ieee754_to_rendered_str(part)
		print(part + ': ' + str(ieee))


if __name__ == '__main__':
	main(sys.argv)
