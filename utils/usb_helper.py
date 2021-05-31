
# There are additional values within the USB Midi data. It seems the Midi messages are first padded to have mod 3 size.
# 0x00's will be added for this. Next, either a 0x14, 0x15 or 0x16 is printed in front of every triple value segment.
# I called these bytes Padding Signaling Bytes PBS.
# If the original Midi message still has enough values (more or equal to three) a 0x14 is added. If one byte must
# be added for padding (remaining size of original Midi message == 2) a 0x16 (yes 0x16, no typo) is added. If two
# bytes must be added for padding (remaining size of original Midi message == 1) a 0x15 is added.
#
# Sometimes there seems to be a PSB of 0x17 being used in string values. Here, the padding seems to add 0x00s before
# the 0xF7 value rather than afterwards. Example (0x2E is a '.'):
# ... 0x2E 0x2E 0x17 0x2E 0x00 0xF7 => padding with PSB 0x17
# ... 0x2E 0x2E 0x14 0x2E 0xF7 0x00 => padding with PSB 0x14
# don't know the advantage yet
#
# Further, concatenated messages are split 64 byte chunks (or smaller => last chunk) in order to not exceed the
# USB endpoint transfer limit.
''
# Example: remove USB flags
# 0x14, 0xF0, 0x00, 0x20, 0x14, 0x33, 0x02, 0x7F, 0x14, 0x47, 0x00, 0x00, 0x14, 0x00, 0x0C, 0x1A, 0x16, 0x40, 0xF7, 0x00
# Read every mod % 3 == 0 position (0, 3, 6, 9, 12, ...) and check if there is one of the Padding Signaling Bytes.
# If this is the case, don't copy those values to the output data. Depending on the PSB value remove former added 0x00
# (not implemented yet - could be an improvement!)
# 0xF0, 0x00, 0x20, 0x33, 0x02, 0x7F, 0x47, 0x00, 0x00, 0x00, 0x0C, 0x1A, 0x40, 0xF7, 0x00
# Because the last PSB had a value of 0x16 one 0x00 byte was added for padding. We could remove this
#
# Example: add USB flags
# 0xF0, 0x00, 0x20, 0x33, 0x02, 0x7F, 0x47, 0x00, 0x00, 0x00, 0x0C, 0x1A, 0x40, 0xF7
# get the length of input data = 14
# add 0x00's until there is a length that fulfills mod % 3 == 0. This is a length of 15 in this case.
# Go to the input data and take groups of 3 bytes: 0xF0, 0x00, 0x20
# if d == [0xF7, 0x00, 0x00] => append a PSB 0x15 since we padded two bytes
# elif d[1:3] == [0xF7, 0x00] => append a PSB 0x16 since we padded one byte
# else: append a PSB 0x14
# and of course, add the three bytes afterwards


class UsbHelper:
	def __init__(self):
		pass

	@staticmethod
	def remove_usb_flags(data_in):
		pos_in_data_in = 0
		data_out = []
		for d in data_in:
			if pos_in_data_in % 4 == 0:
				if d not in [0x14, 0x15, 0x16, 0x17]:
					return data_in
				pos_in_data_in += 1
				continue
			data_out.append(d)
			pos_in_data_in += 1
		return data_out

	@staticmethod
	def remove_usb_flags_and_split(data_in):

		pos_in_data_in = 0
		data_out = []
		for d in data_in:
			if pos_in_data_in % 4 == 0:
				if d not in [0x14, 0x15, 0x16, 0x17]:
					return 1, data_in, []
				pos_in_data_in += 1
				continue
			data_out.append(d)
			pos_in_data_in += 1

		idx_f0 = data_out.index(0xF0)
		idx_f7 = data_out.index(0xF7)
		split_messages = []
		while idx_f0 != -1 and idx_f7 != -1:
			split_messages.append(data_out[idx_f0:idx_f7 + 1])
			try:
				idx_f0 = data_out.index(0xF0, idx_f7 + 1)
			except ValueError:
				idx_f0 = -1
			try:
				idx_f7 = data_out.index(0xF7, idx_f7 + 1)
			except ValueError:
				idx_f7 = -1

		remaining_part = []
		if idx_f0 != -1 and idx_f7 == -1:
			# remaining parts in data_in
			remaining_part = UsbHelper.add_usb_flags(data_out[idx_f0:])
		return 0, split_messages, remaining_part

	@staticmethod
	def add_usb_flags(data_in):
		length = len(data_in)
		padding = length % 3
		if padding == 0:
			pass
		elif padding == 1:
			data_in.append(0x00)
			data_in.append(0x00)
		elif padding == 2:
			data_in.append(0x00)
		elif padding == 3:
			pass

		data_out = []
		for i in range(0, len(data_in), 3):
			d = data_in[i:i+3]
			if d == [0xF7, 0x00, 0x00]:
				data_out.append(0x15)
			elif d[1:3] == [0xF7, 0x00]:
				data_out.append(0x16)
			else:
				data_out.append(0x14)
			for x in d:
				data_out.append(x)

		return data_out

	@staticmethod
	def add_flags_and_join(messages_in):
		data_out = []
		for msg in messages_in:
			data_out += UsbHelper.add_usb_flags(msg)
		return data_out


def main():
	import sys
	try:
		while True:
			ch = sys.stdin.read(1)
			if ch == '\n':
				sys.exit(0)

			try:
				cmd = int(ch)
			except ValueError as e:
				cmd = 0

			if cmd == 0:
				print("0")
			elif cmd == 1:
				print("1")
			elif cmd == 2:
				print("2")
			else:
				print('Unknown command: ' + ch)
	except KeyboardInterrupt:
		sys.exit(0)

	while len(data) > 0:
		sub = data[:64]
		print(sub)
		data = data[64:]

	input_data = [0x14, 0xF0, 0x00, 0x20, 0x14, 0x33, 0x02, 0x7F, 0x14, 0x06, 0x00, 0x00, 0x14, 0x00, 0x01, 0x04, 0x14, 0x03, 0x00, 0x00, 0x14, 0x00, 0x00, 0x00, 0x15, 0xF7, 0x00, 0x00, 0x14, 0xF0, 0x00, 0x20, 0x14, 0x33, 0x02, 0x7F, 0x14, 0x06, 0x00, 0x00, 0x14, 0x00, 0x01, 0x04, 0x14, 0x01, 0x00, 0x00, 0x14, 0x00, 0x00, 0x00, 0x15, 0xF7, 0x00, 0x00, 0x14, 0xF0, 0x00, 0x20, 0x14, 0x33, 0x02, 0x7F]
	input_data2 = [0x14, 0x06, 0x00, 0x00, 0x14, 0x00, 0x01, 0x04, 0x14, 0x00, 0x00, 0x00, 0x14, 0x00, 0x00, 0x01, 0x15, 0xF7, 0x00, 0x00]
	# input_data = [0x14, 0xF0, 0x00, 0x20, 0x14, 0x33, 0x02, 0x7F, 0x14, 0x06, 0x00, 0x00, 0x14, 0x00, 0x06, 0x20, 0x14, 0x00, 0x00, 0x00, 0x14, 0x00, 0x00, 0x07, 0x14, 0x00, 0x00, 0x00, 0x14, 0x00, 0x09, 0x00, 0x14, 0x00, 0x00, 0x0F, 0x14, 0x64, 0x00, 0x00, 0x14, 0x00, 0x00, 0x14, 0x14, 0x00, 0x00, 0x00, 0x14, 0x00, 0x32, 0x00, 0x14, 0x00, 0x00, 0x00, 0x16, 0x32, 0xF7, 0x00]
	# input_data = [0x14, 0xF0, 0x00, 0x20, 0x14, 0x33, 0x02, 0x7F, 0x14, 0x47, 0x00, 0x00, 0x14, 0x00, 0x0C, 0x1A, 0x16, 0x40, 0xF7, 0x00]

	messages, remaining_part = UsbHelper.remove_usb_flags_and_split(input_data)

	for d in [0x14, 0x06, 0x00, 0x00, 0x14, 0x00, 0x01, 0x04, 0x14, 0x00, 0x00, 0x00, 0x14, 0x00, 0x00, 0x01, 0x15, 0xF7, 0x00, 0x00]:
		remaining_part.append(d)

	messages2, remaining_part = UsbHelper.remove_usb_flags_and_split(remaining_part)

	msgs = messages + messages2


	joint_msgs = UsbHelper.add_flags_and_join(msgs)
	bla = joint_msgs[:64]
	if input_data == bla:
		print('Equal!')
	else:
		print('NOT Equal!')

	bla2 = joint_msgs[64:]
	if input_data2 == bla2:
		print('Equal!')
	else:
		print('NOT Equal!')

	input_without_usb = UsbHelper.remove_usb_flags(input_data)
	input_with_usb = UsbHelper.add_usb_flags(input_without_usb)

	print(input_data)
	print(input_with_usb)

	if input_data == input_with_usb:
		print('Equal!')
	else:
		print('NOT Equal!')


if __name__ == '__main__':
	main()
