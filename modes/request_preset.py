from modes.standard import Standard
import random
from modules import modules
from utils.formatter import format_1
from utils.simple_filter import slot_splitter_2
import logging
log = logging.getLogger(__name__)


class RequestPreset(Standard):
	def __init__(self, helix_usb):
		Standard.__init__(self, helix_usb=helix_usb, name="request_preset")
		self.preset_data = []
		self.data_requests_packages_or_whatever = []
		self.num_received_1f = 0

	def start(self):
		log.info('Starting mode')
		self.preset_data = []
		self.num_received_1f = 0
		next_packet_no = self.helix_usb.next_preset_data_packet_no()

		data = [0x19, 0x0, 0x0, 0x18, 0x80, 0x10, 0xed, 0x3, 0x0, "XX", 0x0, 0xc, self.helix_usb.maybe_session_no, next_packet_no, 0x0, 0x0, 0x1, 0x0, 0x6, 0x0, 0x9, 0x0, 0x0, 0x0, 0x83, 0x66, 0xcd, 0x3, 0xeb, 0x64, 0x16, 0x65, 0xc0, 0x0, 0x0, 0x0]
		self.helix_usb.endpoint_0x1_out(data, silent=True)
		self.data_requests_packages_or_whatever = range(0x10, 0x1a)

	def shutdown(self):
		log.info('Shutting down mode')

	def data_in(self, data_in):

		if self.helix_usb.check_keep_alive_response(data_in):
			return False  # don't print incoming message to console

		if data_in[6] != 0x80:
			hex_str = ''.join('0x{:x}, '.format(x) for x in data_in)
			log.error("Unexpected package while trying to read preset data: " + str(hex_str))
			return True  # print incoming message to console

		if self.helix_usb.my_byte_cmp(left=data_in, right=["XX", "XX", 0x0, 0x18, 0xed, 0x3, 0x80, 0x10, 0x0, "XX", 0x0, 0x4, "XX", "XX", 0x0, 0x0], length=16):
			# self.helix_usb.log_data_in(data_in)
			reply_here = True
			if len(self.preset_data) == 0:
				reply_here = False

			for b in data_in[16:]:
				self.preset_data.append(b)

			if reply_here is False:
				log.info('Skipping reply for first data packet')
				return True  # print incoming message to console

			if data_in[1] == 0x0:
				self.helix_usb.maybe_session_no = random.choice(range(0x04, 0xff))

				data_out = [0x8, 0x0, 0x0, 0x18, 0x80, 0x10, 0xed, 0x3, 0x0, "XX", 0x0, 0x8, self.helix_usb.maybe_session_no, self.helix_usb.preset_data_packet_no()-1, 0x0, 0x0]
				self.helix_usb.endpoint_0x1_out(data_out, silent=True)

				# update session no
				self.helix_usb.maybe_session_no = random.choice(range(0x04, 0xff))

				# data_out = [0x1b, 0x0, 0x0, 0x18, 0x80, 0x10, 0xed, 0x3, 0x0, "XX", 0x0, 0x4, 0x4d, 0x1a, 0x0, 0x0, 0x1, 0x0, 0x6, 0x0, 0xb, 0x0, 0x0, 0x0, 0x83, 0x66, 0xcd, 0x3, 0xec, 0x64, 0x18, 0x65, 0x81, 0x76, 0xe, 0x0]
				# self.helix_usb.endpoint_0x1_out(data_out)

				# log.info("GOT PRESET DATA")
				str_out = ''
				for b in self.preset_data:
					str_out += hex(b) + ", "
				str_out = str_out[:-2]
				nice_str = format_1(str_out)
				slot_data = slot_splitter_2(nice_str)
				# print(str_out)
				# print(nice_str)
				self.helix_usb.set_slot_info(slot_data)

				# splitter for the labels: 87 0A 00 0B 84 00 03 05 A9
				# active snapshot information:
				if '860600070208' in nice_str and self.helix_usb.current_snapshot != 1:
					self.helix_usb.set_snapshot(1)
				elif '860601070208' in nice_str and self.helix_usb.current_snapshot != 2:
					self.helix_usb.set_snapshot(2)
				elif '860602070208' in nice_str and self.helix_usb.current_snapshot != 3:
					self.helix_usb.set_snapshot(3)

				# 1:
				# 2: 860601070208
				# 2: 860602070208

				'''
				if slot_data is not None:
					for slot in slot_data:
						if slot.module_id == "14c0":
							log.info("No module")
							continue
						try:
							desc = modules[slot.module_id]
							log.info(str(desc) + ', params: ' + str(slot.params))
						except KeyError:
							log.info('Unknown module with id: ' + str(slot.module_id))
				'''
				self.helix_usb.got_preset = True
				self.helix_usb.switch_mode()

				return True  # print incoming message to console
			else:
				next_packet_no = self.helix_usb.next_preset_data_packet_no()
				data_out = [0x8, 0x0, 0x0, 0x18, 0x80, 0x10, 0xed, 0x3, 0x0, "XX", 0x0, 0x8, self.helix_usb.maybe_session_no, next_packet_no, 0x0, 0x0]
				self.helix_usb.endpoint_0x1_out(data_out, silent=True)
		else:
			hex_str = ''.join('0x{:x}, '.format(x) for x in data_in)
			log.warning("Unexpected message in mode: " + str(hex_str))
		return True
		'''
		elif self.helix_usb.my_byte_cmp(left=data_in, right=[0x1f, 0x0, 0x0, 0x18, 0xed, 0x3, 0x80, 0x10, 0x0, "XX", 0x0, 0x4, "XX", "XX", 0x0, 0x0], length=16):
			if self.num_received_1f == 0:
				self.num_received_1f += 1
				data_out = [0x1b, 0x0, 0x0, 0x18, 0x80, 0x10, 0xed, 0x3, 0x0, "XX", 0x0, 0xc, 0x64, 0x1a, 0x0, 0x0, 0x1, 0x0, 0x6, 0x0, 0xb, 0x0, 0x0, 0x0, 0x83, 0x66, 0xcd, 0x3, 0xed, 0x64, 0x18, 0x65, 0x81, 0x76, 0x49, 0x0]
				self.helix_usb.endpoint_0x1_out(data_out)
			elif self.num_received_1f == 1:
				self.num_received_1f += 1
				data_out = [0x8, 0x0, 0x0, 0x18, 0x80, 0x10, 0xed, 0x3, 0x0, "XX", 0x0, 0x8, self.helix_usb.maybe_session_no, self.helix_usb.preset_data_packet_no()-1, 0x0, 0x0]
				self.helix_usb.endpoint_0x1_out(data_out)
				log.info("GOT PRESET DATA")
				str_out = ''
				for b in self.preset_data:
					str_out += hex(b) + ", "
				str_out = str_out[:-2]
				nice_str = format_1(str_out)
				slot_data = slot_splitter_2(nice_str)

				if slot_data is not None:
					for slot in slot_data:
						if slot.module_id == "14c0":
							log.info("No module")
							continue
						try:
							desc = modules[slot.module_id]
							log.info(str(desc) + ', params: ' + str(slot.params))
						except KeyError:
							log.info('Unknown module with id: ' + str(slot.module_id))

				self.helix_usb.got_preset = True
				self.helix_usb.switch_mode()
			else:
				log.error("Too many 0x1f messages received")
				self.helix_usb.switch_mode()
		'''

