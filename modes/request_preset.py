from modes.standard import Standard
import random
from modules import modules
from utils.formatter import format_1
from utils.simple_filter import slot_splitter_2
import logging
import threading
log = logging.getLogger(__name__)


class RequestPreset(Standard):
	def __init__(self, helix_usb):
		Standard.__init__(self, helix_usb=helix_usb, name="request_preset")
		self.preset_data = []
		self.data_requests_packages_or_whatever = []
		self.num_received_1f = 0
		self.request_preset_session_id = 0xf4
		self.in_transfer = False
		self.wait_for_next_packet_timer = None

	def start(self):
		log.info('Starting mode')
		self.preset_data = []
		self.num_received_1f = 0
		next_packet_double = self.helix_usb.preset_data_packet_double()

		data = [0x19, 0x0, 0x0, 0x18, 0x80, 0x10, 0xed, 0x3, 0x0, "XX", 0x0, 0xc, self.helix_usb.maybe_session_no, next_packet_double[0], next_packet_double[1], 0x0, 0x1, 0x0, 0x6, 0x0, 0x9, 0x0, 0x0, 0x0, 0x83, 0x66, 0xcd, 0x3, self.request_preset_session_id, 0x64, 0x16, 0x65, 0xc0, 0x0, 0x0, 0x0]
		self.helix_usb.endpoint_0x1_out(data, silent=True)

		self.data_requests_packages_or_whatever = range(0x10, 0x1a)
		self.request_preset_session_id += 2
		if self.request_preset_session_id > 0xff:
			self.request_preset_session_id -= 0xff
		self.in_transfer = False
		self.wait_for_next_packet_timer = None

	def shutdown(self):
		log.info('Shutting down mode')

	def parse_preset_data(self):
		self.helix_usb.maybe_session_no = random.choice(range(0x04, 0xff))

		# preset_data_packet_double = self.helix_usb.preset_data_packet_double()
		# data_out = [0x8, 0x0, 0x0, 0x18, 0x80, 0x10, 0xed, 0x3, 0x0, "XX", 0x0, 0x8, self.helix_usb.maybe_session_no, preset_data_packet_double[0], preset_data_packet_double[1], 0x0]
		# self.helix_usb.endpoint_0x1_out(data_out, silent=True)

		log.info("GOT PRESET DATA, length is: " + str(len(self.preset_data)))
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

		self.helix_usb.got_preset = True
		self.helix_usb.switch_mode()

		return True  # print incoming message to console

	def data_in(self, data_in):

		# if not self.in_transfer:
		# 	if self.helix_usb.check_keep_alive_response(data_in):
		# 		return False  # don't print incoming message to console

		if data_in[6] != 0x80:
			hex_str = ''.join('0x{:x}, '.format(x) for x in data_in)
			log.error("Unexpected package while trying to read preset data: " + str(hex_str))
			return True  # print incoming message to console

		if self.helix_usb.my_byte_cmp(left=data_in, right=["XX", "XX", 0x0, 0x18, 0xed, 0x3, 0x80, 0x10, 0x0, "XX", 0x0, 0x4, "XX", "XX", 0x0, 0x0], length=16):
			if self.wait_for_next_packet_timer is not None:
				self.wait_for_next_packet_timer.cancel()
				self.wait_for_next_packet_timer = None

			self.in_transfer = False

			reply_here = True
			if len(self.preset_data) == 0:
				reply_here = False

			for b in data_in[16:]:
				self.preset_data.append(b)

			if reply_here is False:
				log.info('Skipping reply for first data packet')
				return True  # print incoming message to console

			if data_in[1] != 2:
				next_packet_double_no = self.helix_usb.next_preset_data_packet_double()
			else:
				next_packet_double_no = self.helix_usb.preset_data_packet_double()
			data_out = [0x8, 0x0, 0x0, 0x18, 0x80, 0x10, 0xed, 0x3, 0x0, "XX", 0x0, 0x8, self.helix_usb.maybe_session_no, next_packet_double_no[0], next_packet_double_no[1], 0x0]
			self.helix_usb.endpoint_0x1_out(data_out, silent=True)
			return True
															 0x8, 0x0, 0x0, 0x18, 0xed, 0x3, 0x80, 0x10, 0x0, 0x32, 0x0, 0x10, 0x6f, 0x2, 0x0, 0x0
		elif self.helix_usb.my_byte_cmp(left=data_in, right=[0x8, 0x0, 0x0, 0x18, 0xed, 0x3, 0x80, 0x10, 0x0, "XX", 0x0, 0x8, "XX", "XX", 0x0, 0x0], length=16):

			# Either we received a pending keep-alive signal or a message marking the end of the transmission.
			# Since both message look similar (or even identical) we start a quick time. If no other message is
			# received within a certain time, we shutdown the mode

			self.wait_for_next_packet_timer = threading.Timer(0.02, self.parse_preset_data)
			self.wait_for_next_packet_timer.start()

			preset_data_packet_double = self.helix_usb.preset_data_packet_double()
			data_out = [0x8, 0x0, 0x0, 0x18, 0x80, 0x10, 0xed, 0x3, 0x0, "XX", 0x0, 0x8, self.helix_usb.maybe_session_no, preset_data_packet_double[0], preset_data_packet_double[1], 0x0]
			self.helix_usb.endpoint_0x1_out(data_out, silent=True)

			return True  # print incoming message to console

		else:
			hex_str = ''.join('0x{:x}, '.format(x) for x in data_in)
			log.warning("Unexpected message in mode: " + str(hex_str))
		return True
