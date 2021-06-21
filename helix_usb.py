import sys
import signal
import usb.core
import usb.util
import threading
import time
from utils.usb_monitor import UsbMonitor
import struct
import binascii
from utils.formatter import ca_splitter
from utils.simple_filter import EmptySlotInfo
from excel_logger import ExcelLogger
import logging
import copy
import getopt
from modes.connect import Connect
from modes.reconfigure_x1 import ReconfigureX1
from modes.standard import Standard
from modes.request_preset import RequestPreset
from modes.request_preset_names import RequestPresetNames
from modes.request_preset_name import RequestPresetName
log = logging.getLogger(__name__)


class HelixUsb:
	GET_STRING_VENDOR = 0x01
	GET_STRING_PRODUCT = 0x02
	GET_STRING_SERIAL = 0x03

	GET_STRING_APP = 0x04
	GET_STRING_VERSION = 0x05
	GET_STRING_CPU_ID = 0x06
	GET_STRING_MAC_ADDR = 0x07
	GET_STRING_VMGR = 0x08
	GET_STRING_VDEF = 0x09
	GET_STRING_UNDEFINED = 0x0a

	ON = 0x01
	OFF = 0x00

	LED_COLORS = [
		'off', 'white', 'red', 'dark_orange', 'light_orange', 'yellow', 'green', 'turquoise', 'blue', 'violet',
		'pink', 'auto_color']

	UI_MODES = ['Stomp Mode', 'Scroll Mode', 'Preset Mode', 'Snapshot Mode']

	FOOT_SWITCH_FUNCTIONS = \
		["Tap/Tuner", "Stomp3", "PresetUp", "PresetDown", "SnapshotUp", "SnapshotDown", "AllBypass", "ToggleExp"]

	FOOT_SWITCHES = {
		"FS3": 0x61,
		"FS4": 0x62,
		"FS5": 0x63
	}

	VIEWS = {
		194: "Play View",
		195: "Edit View"
	}

	MIDI_CC = {
		"EmulateFS1": 49,
		"EmulateFS2": 50,
		"EmulateFS3": 51,
		"EmulateFS4": 52,
		"EmulateFS5": 53
	}

	def __init__(self):

		self.preset_no = 0
		self.current_snapshot = 9
		self.current_preset_no = -1

		self.usb_device = None
		self.active_configuration = None
		self.interface = None
		self.interface_2_1 = None
		self.interface_3_1 = None
		self.interface_4 = None
		self.endpoint_0x1_bulk_out = None
		self.endpoint_0x81_bulk_in = None
		self.endpoint_0x2_bulk_out = None
		self.endpoint_0x82_bulk_in = None
		self.endpoint_0x3_isochronous_out = None
		self.endpoint_0x83_isochronous_in = None

		self.usb_io_exception_cb = self.on_usb_io_exception

		self.maybe_session_no = 0x1a
		self.preset_data_double_cnt = [0x1e, 0x00]

		self.stop_threads = False
		self.x81_reader = None

		self.stop_communication = False
		self.stop_x80x10_communication = False

		self.x80x10_keep_alive_thread = None
		self.x1x10_keep_alive_thread = None
		self.x2x10_keep_alive_thread = None

		self.x1x10_cnt = 0x2
		self.x2x10_cnt = 0x2
		self.x80x10_cnt = 0x2

		self.expecting_x80_x10_response = False
		self.expecting_x1_x10_response = False
		self.expecting_x2_x10_response = False

		self.last_x80_x10_keep_alive_out = time.time()
		self.last_x2_x10_keep_alive_out = time.time()
		self.last_x1_x10_keep_alive_out = time.time()

		self.session_quadruple = [0xf4, 0x1e, 0x00, 0x00]

		self.active_mode = None
		self.connected = False
		self.reconfigured_x1 = False
		self.got_preset_name = False
		self.got_preset = False
		self.got_preset_names = False

		self.preset_name = ''
		self.preset_name_change_cb_fct_list = list()
		self.preset_no_change_cb_fct_list = list()

		self.slot_data = []
		for i in range(0, 16):
			si = EmptySlotInfo()
			si.slot_no = i
			self.slot_data.append(si)
		self.slot_data_change_cb_fct_list = list()
		self.snapshot_change_cb_fct_list = list()

		self.excel_logger = None

		self.preset_change_cnt = 0

		# Modes
		self.request_preset_mode = RequestPreset(self)

	def set_excel_logger(self, excel_log_path):
		if excel_log_path:
			self.excel_logger = ExcelLogger(excel_log_path)
		else:
			self.excel_logger = None

	def switch_callback(self, id, val):
		log.info('switch: ' + str(id) + ', value: ' + str(val))
		if val == 0:
			return

	def switch_hold_callback(self, id):
		log.info('switch hold: ' + str(id))

	def switch_double_click_callback(self, id):
		log.info('switch double clicked: ' + str(id))

	def pedal_callback(self, id, val):
		log.info('pedal: ' + str(id) + ' moved: ' + str(val))

	def on_serial_exception(self, exc):
		if self.serial_interface is not None:
			self.open_fbv.stop()
			self.serial_interface.close()

	def register_snapshot_change_cb_fct(self, p_cb_fct):
		if p_cb_fct is not None:
			self.snapshot_change_cb_fct_list.append(p_cb_fct)

	def register_preset_name_change_cb_fct(self, p_cb_fct):
		if p_cb_fct is not None:
			self.preset_name_change_cb_fct_list.append(p_cb_fct)

	def register_preset_no_change_cb_fct(self, p_cb_fct):
		if p_cb_fct is not None:
			self.preset_no_change_cb_fct_list.append(p_cb_fct)

	def register_slot_data_change_cb_fct(self, p_cb_fct):
		if p_cb_fct is not None:
			self.slot_data_change_cb_fct_list.append(p_cb_fct)

	def set_preset_name(self, name):
		self.got_preset_name = True
		self.preset_name = name
		for cb_fct in self.preset_name_change_cb_fct_list:
			cb_fct(self.preset_name)

	def set_slot_info(self, slot_info_list):

		if len(slot_info_list) != 16:
			log.error('Wrong size for slot info - expected 16 slots, CHECK PRESET - resetting to all empty')
			self.slot_data = []
			for i in range(0, 16):
				si = EmptySlotInfo()
				si.slot_no = i
				self.slot_data.append(si)
			return

		for i in range(0, 16):
			if self.slot_data[i] == slot_info_list[i]:
				pass
			else:
				for cb_fct in self.slot_data_change_cb_fct_list:
					cb_fct(i, slot_info_list[i])
		self.slot_data = slot_info_list

	def set_snapshot(self, current_snapshot):
		self.current_snapshot = current_snapshot
		for cb_fct in self.snapshot_change_cb_fct_list:
			cb_fct(self.current_snapshot)

	def increase_session_quadruple_x11(self):
		self.session_quadruple[0] += 0x11
		if self.session_quadruple[0] > 0xff:
			self.session_quadruple[0] %= 0x100
			self.session_quadruple[1] += 0x1
			if self.session_quadruple[1] > 0xff:
				self.session_quadruple[1] %= 0x100
				self.session_quadruple[2] += 0x1
				if self.session_quadruple[2] > 0xff:
					self.session_quadruple[2] %= 0x100
					self.session_quadruple[3] += 0x1

	def check_keep_alive_response(self, data):
		# x1 keep alive response from device
		if self.my_byte_cmp(left=data, right=[0x8, 0x0, 0x0, 0x18, 0xef, 0x3, 0x1, 0x10, 0x0, "XX", 0x0, 0x10, "XX", 0x2, 0x0, 0x0], length=16):
			self.expecting_x1_x10_response = False
			return True

		# x2 keep alive response from device
		elif self.my_byte_cmp(left=data, right=[0x8, 0x0, 0x0, 0x18, 0xf0, 0x3, 0x2, 0x10, 0x0, "XX", 0x0, 0x10, "XX", 0x2, 0x0, 0x0], length=16):
			self.expecting_x2_x10_response = False
			return True

		# x80 keep alive response from device
		elif self.my_byte_cmp(left=data, right=[0x8, 0x0, 0x0, 0x18, 0xed, 0x3, 0x80, 0x10, 0x0, "XX", 0x0, 0x10, "XX", "XX", "XX", "XX"], length=16):
			self.expecting_x80_x10_response = False
			return True

		return False

	def config(self, usb_device):
		self.usb_device = usb_device

		if self.usb_device is None:
			log.error('Device not found')
			return 1
		# self.usb_device.set_configuration()

		self.active_configuration = self.usb_device.get_active_configuration()
		self.interface = self.active_configuration[(0, 0)]

		if self.usb_device.is_kernel_driver_active(0):
			log.info("Detaching kernel driver")
			self.usb_device.detach_kernel_driver(0)

		for endpoint in self.interface:
			desc = str(endpoint)
			if "ENDPOINT 0x1: Bulk OUT" in desc:
				self.endpoint_0x1_bulk_out = endpoint
			elif "ENDPOINT 0x81: Bulk IN" in desc:
				self.endpoint_0x81_bulk_in = endpoint

		try:
			self.interface_4 = self.active_configuration[(4, 0)]
			for endpoint in self.interface_4:
				desc = str(endpoint)
				if "ENDPOINT 0x2: Bulk OUT" in desc:
					self.endpoint_0x2_bulk_out = endpoint
				elif "ENDPOINT 0x82: Bulk IN" in desc:
					self.endpoint_0x82_bulk_in = endpoint
		except usb.core.USBError as e:
			log.error('While trying to claim interface')

		try:
			self.interface_2_1 = self.active_configuration[(2, 1)]
			for endpoint in self.interface_2_1:
				desc = str(endpoint)
				if "ENDPOINT 0x3: Isochronous OUT" in desc:
					self.endpoint_0x3_isochronous_out = endpoint
		except usb.core.USBError as e:
			log.error('While trying to claim interface')

		try:
			self.interface_3_1 = self.active_configuration[(3, 1)]
			for endpoint in self.interface_3_1:
				desc = str(endpoint)
				if "ENDPOINT 0x83: Isochronous IN" in desc:
					self.endpoint_0x83_isochronous_in = endpoint
		except usb.core.USBError as e:
			log.error('While trying to claim interface')

		self.x81_reader = threading.Thread(target=self.endpoint_listener, args=('0x81', self.endpoint_0x81_bulk_in))

		return 0

	def begin(self):
		self.stop_threads = False
		for request_string_id in [self.GET_STRING_VENDOR, self.GET_STRING_PRODUCT, self.GET_STRING_SERIAL,
								  self.GET_STRING_APP, self.GET_STRING_VERSION, self.GET_STRING_CPU_ID,
								  self.GET_STRING_MAC_ADDR, self.GET_STRING_VMGR, self.GET_STRING_VDEF,
								  self.GET_STRING_UNDEFINED, self.GET_STRING_VENDOR]:
			try:
				tst = usb.util.get_string(self.usb_device, request_string_id, langid=0x0409)
				log.info(tst)
			except usb.core.USBError as e:
				log.warning("Caught exception while trying to get string (" + str(request_string_id) + "): " + str(e))
				pass

		# very important for usb.control.clear_feature to work
		try:
			usb.util.claim_interface(self.usb_device, self.interface)
		except usb.core.USBError as e:
			log.error('While trying to claim interface')

		try:
			usb.util.claim_interface(self.usb_device, self.interface_3_1)
		except usb.core.USBError as e:
			log.error('While trying to claim interface 3.1, error: ' + str(e))

		'''
		If you receive a libusb exception (USBError: [Errno 2] Entity not found) here,
		it might be the case that the operating system has already taken control of the
		midi device. You can try to unplug the usb cable, start this script and plug
		the cable in again. Usually, this script is faster than the OS and you can
		run it...
		'''
		usb.control.clear_feature(
			dev=self.usb_device, feature=usb.control.ENDPOINT_HALT, recipient=self.endpoint_0x1_bulk_out)
		usb.control.clear_feature(
			dev=self.usb_device, feature=usb.control.ENDPOINT_HALT, recipient=self.endpoint_0x81_bulk_in)

		self.x81_reader.start()

	def on_usb_io_exception(self, exc):
		return

	def on_serial_exception(self, exc):
		return

	def parse_preset(self):
		all_data = list()
		for packet in self.preset_data:
			# hex_str = ''.join('0x{:x}, '.format(x) for x in packet)
			# all_presets += hex_str
			for b in packet[16:]:
				all_data.append(b)

		str_rep_hex = ''.join('{:02x}'.format(x) for x in all_data)
		# print(str_rep_hex)
		ca_splitter(str_rep_hex)

	def next_preset_data_packet_double(self):
		next_preset_data_packet_double = self.preset_data_double_cnt
		self.preset_data_double_cnt[0] += 1
		if self.preset_data_double_cnt[0] > 0xff:
			self.preset_data_double_cnt[0] = 0
			self.preset_data_double_cnt[1] += 1

		if self.preset_data_double_cnt[1] > 0xff:
			self.preset_data_double_cnt[1] = 0
		return next_preset_data_packet_double

	def preset_data_packet_double(self):
		return self.preset_data_double_cnt

	def next_x80x10_packet_no(self):
		next_no = self.x80x10_cnt
		self.x80x10_cnt += 1
		if self.x80x10_cnt > 0xFF:
			self.x80x10_cnt = 0
		# self.x80x10_cnt %= 0xFF
		# log.info("x80x10: " + str(next_no))
		return next_no

	def x80x10_keep_alive_thread_fct(self, start_delay):
		log.info("Starting x80x10_keep_alive_thread, delay is: " + str(start_delay))
		time.sleep(start_delay)

		t = threading.currentThread()

		if start_delay < 1.04:
			preset_data_packet_double = self.preset_data_packet_double()
			self.endpoint_0x1_out(
				[0x8, 0x0, 0x0, 0x18, 0x80, 0x10, 0xed, 0x3, 0x0, "XX", 0x0, 0x10, self.maybe_session_no, preset_data_packet_double[0], preset_data_packet_double[1], 0x0],
				silent=True
			)
			self.expecting_x80_x10_response = True
			self.last_x80_x10_keep_alive_out = time.time()

		while getattr(t, "do_run", True):

			while self.last_x80_x10_keep_alive_out + 1.04 > time.time():
				time.sleep(0.05)
				# log.info('Delayed x80_x10_ timer')
			# if self.awaiting_preset_name_data is False and self.awaiting_preset_data is False:
			if self.expecting_x80_x10_response:
				log.error('No x80x10 response!')

			preset_data_packet_double = self.preset_data_packet_double()
			self.endpoint_0x1_out(
				[0x8, 0x0, 0x0, 0x18, 0x80, 0x10, 0xed, 0x3, 0x0, "XX", 0x0, 0x10, self.maybe_session_no, preset_data_packet_double[0], preset_data_packet_double[1], 0x0],
				silent=True
			)
			self.expecting_x80_x10_response = True
			time.sleep(1.04)
		log.info("Finished x80x10_keep_alive_thread")

	def next_x1x10_packet_no(self):
		next_no = self.x1x10_cnt
		self.x1x10_cnt += 1
		if self.x1x10_cnt > 0xFF:
			self.x1x10_cnt = 0
		# self.x1x10_cnt %= 0xFF
		return next_no

	def x1x10_keep_alive_thread_fct(self, start_delay):
		log.info("Starting x1x10_keep_alive_thread, delay is: " + str(start_delay))
		time.sleep(start_delay)
		while self.stop_communication is False:
			if self.expecting_x1_x10_response:
				log.error('No x1x10 response!')

			self.endpoint_0x1_out(
				[0x8, 0x0, 0x0, 0x18, 0x1, 0x10, 0xef, 0x3, 0x0, "XX", 0x0, 0x8, 0x72, 0x1e, 0x0, 0x0],
				silent=True)
			self.expecting_x1_x10_response = True
			time.sleep(1.04)

	def next_x2x10_packet_no(self):
		next_no = self.x2x10_cnt
		self.x2x10_cnt += 1
		if self.x2x10_cnt > 0xFF:
			self.x2x10_cnt = 0
		# self.x2x10_cnt %= 0xFF
		return next_no

	def x2x10_keep_alive_thread_fct(self, start_delay):
		log.info("Starting x2x10_keep_alive_thread, delay is: " + str(start_delay))
		time.sleep(start_delay)

		t = threading.currentThread()

		if start_delay < 1.04:
			self.endpoint_0x1_out(
				[0x8, 0x0, 0x0, 0x18, 0x2, 0x10, 0xf0, 0x3, 0x0, "XX", 0x0, 0x10, 0x9, 0x10, 0x0, 0x0],
				silent=True)
			self.expecting_x2_x10_response = True
			self.last_x2_x10_keep_alive_out = time.time()

		while getattr(t, "do_run", True):

			while self.last_x2_x10_keep_alive_out + 1.04 > time.time():
				time.sleep(0.05)

			if self.expecting_x2_x10_response:
				log.error('No x2x10 response!')

			self.endpoint_0x1_out(
				[0x8, 0x0, 0x0, 0x18, 0x2, 0x10, 0xf0, 0x3, 0x0, "XX", 0x0, 0x10, 0x9, 0x10, 0x0, 0x0],
				silent=True)
			self.expecting_x2_x10_response = True
			time.sleep(1.04)
		log.info("Finished x2x10_keep_alive_thread")

	def start_x1x10_keep_alive_thread(self, delay=0.0):
		self.x1x10_keep_alive_thread = threading.Thread(target=self.x1x10_keep_alive_thread_fct, args=(delay,))
		self.x1x10_keep_alive_thread.start()

	def start_x2x10_keep_alive_thread(self, delay=0.0):
		self.x2x10_keep_alive_thread = threading.Thread(target=self.x2x10_keep_alive_thread_fct, args=(delay,))
		self.x2x10_keep_alive_thread.start()

	def start_x80x10_keep_alive_thread(self, delay=1.0):
		if self.x80x10_keep_alive_thread is not None:
			return
		self.stop_x80x10_communication = False
		self.x80x10_keep_alive_thread = threading.Thread(target=self.x80x10_keep_alive_thread_fct, args=(delay,))
		self.x80x10_keep_alive_thread.start()

	def start_keep_alive_messages(self, delay_x80x10=0.3, delay_x1x10=0.3, delayx2_x10=0.7):

		if self.x80x10_keep_alive_thread is not None:
			return

		self.stop_communication = False
		self.stop_x80x10_communication = False

		self.x80x10_keep_alive_thread = threading.Thread(target=self.x80x10_keep_alive_thread_fct, args=(delay_x80x10,))
		self.x1x10_keep_alive_thread = threading.Thread(target=self.x1x10_keep_alive_thread_fct, args=(delay_x1x10,))
		self.x2x10_keep_alive_thread = threading.Thread(target=self.x2x10_keep_alive_thread_fct, args=(delayx2_x10,))

		self.x80x10_keep_alive_thread.start()
		self.x1x10_keep_alive_thread.start()
		self.x2x10_keep_alive_thread.start()

	def switch_mode(self, mode_name="Standard"):
		if self.active_mode is not None:
			self.active_mode.shutdown()

		if mode_name == "Standard":
			'''
			self.connected = False
			self.reconfigured_x1 = False
			self.got_preset_name = False
			self.got_preset = False
			self.got_preset_names = False
			'''
			if self.connected is False:
				self.active_mode = Connect(self)
				self.active_mode.start()
			elif self.connected is True and self.reconfigured_x1 is False:
				self.active_mode = ReconfigureX1(self)
				self.active_mode.start()
			elif self.reconfigured_x1 is True and self.got_preset_name is False:
				self.active_mode = RequestPresetName(self)
				self.active_mode.start()
			elif self.got_preset_name is True and self.got_preset is False:
				self.active_mode = self.request_preset_mode
				self.active_mode.start()
			elif self.got_preset is True and self.got_preset_names is False:
				self.active_mode = RequestPresetNames(self)
				self.active_mode.start()
			else:
				self.active_mode = Standard(self, name="standard")
				self.active_mode.start()
		elif mode_name == "Connect":
			self.active_mode = Connect(self)
			self.active_mode.start()
		elif mode_name == "ReconfigureX1":
			self.active_mode = ReconfigureX1(self)
			self.active_mode.start()
		elif mode_name == "RequestPreset":
			self.active_mode = RequestPreset(self)
			self.active_mode.start()
		elif mode_name == "RequestPresetNames":
			self.active_mode = RequestPresetNames(self)
			self.active_mode.start()
		elif mode_name == "RequestPresetName":
			self.active_mode = RequestPresetName(self)
			self.active_mode.start()
		elif mode_name == "Standard":
			self.active_mode = Standard(self, name="standard")
			self.active_mode.start()
		else:
			log.error('Unknown mode: ' + mode_name)

	def endpoint_listener(self, description, endpoint):

		log.info('Started ' + description + ' thread')
		while self.stop_threads is False:
			try:
				data = endpoint.read(size_or_buffer=endpoint.wMaxPacketSize, timeout=0)
				self.data_in(description, data)
			except ValueError as _:
				pass
			except usb.core.USBError as e:
				if self.usb_io_exception_cb is not None:
					self.usb_io_exception_cb(str(e))
		log.info('Stopped thread reading endpoint data!')
		# self.x81_reader = threading.Thread(target=self.endpoint_listener, args=())

	@staticmethod
	def my_byte_cmp(left, right, length=-1):
		if length == -1:
			length = min(len(left), len(right))

		if len(left) < length:
			return False
		if len(right) < length:
			return False

		for i in range(0, length):
			if left[i] == 'XX' or right[i] == 'XX':
				continue
			if left[i] != right[i]:
				return False
				break

		return True

	@staticmethod
	def ieee754_to_rendered_str(val):
		value = struct.unpack('>f', binascii.unhexlify(val))
		rounded_val = round(value[0], 2) * 10
		return rounded_val

	def log_data_in(self, data):
		if data[6] not in [0x1, 0x2, 0x80]:
			return
		hex_str = ''.join('0x{:x}, '.format(x) for x in data)
		str_rep_hex = ''.join('{:02x}'.format(x) for x in data)
		# str_rep = str_rep_hex.decode("hex")
		if hex_str.endswith(', '):
			hex_str = hex_str[:-2]
		log.info('\t\t' + hex_str)
		# log.info('\t\t' + str_rep)


	def log_data_out(self, data):
		if data[4] not in [0x1, 0x2, 0x80]:
			return

		hex_str = ''.join('0x{:x}, '.format(x) for x in data)
		if hex_str.endswith(', '):
			hex_str = hex_str[:-2]
		log.info(hex_str)

	def out_packet_to_endpoint_0x1(self, out_packet, silent=False):
		data_to_send = copy.deepcopy(out_packet.data)
		if out_packet.delay == 0.0:
			self.endpoint_0x1_out(data_to_send, silent)
		else:
			threading.Timer(out_packet.delay, self.endpoint_0x1_out, [data_to_send]).start()

	def endpoint_0x1_out(self, data, silent=False):

		if data[9] == "XX":
			if data[4] == 0x1:
				data[9] = self.next_x1x10_packet_no()
			elif data[4] == 0x2:
				data[9] = self.next_x2x10_packet_no()
			elif data[4] == 0x80:
				data[9] = self.next_x80x10_packet_no()
		if not silent:
			self.log_data_out(data)
			# hex_str = ''.join('{:02x} '.format(x) for x in out_data)
		if self.excel_logger:
			self.excel_logger.log(data)
		if data[4] == 0x1:
			self.last_x1_x10_keep_alive_out = time.time()
		elif data[4] == 0x2:
			self.last_x2_x10_keep_alive_out = time.time()
		elif data[4] == 0x80:
			self.last_x80_x10_keep_alive_out = time.time()

		self.endpoint_0x1_bulk_out.write(data)

	def data_in(self, endpoint_id, data):
		if endpoint_id == '0x81':
			if self.excel_logger:
				self.excel_logger.log(data)
			try:
				print_to_console = self.active_mode.data_in(data)
				# if print_to_console:
				# 	self.log_data_in(data)

			except IndexError as _:
				pass

	def usb_device_found_cb(self, usb_descriptor):
		log.info('Found: ' + str(usb_descriptor))
		if usb_descriptor.device_id in ['0e41:4246', '0e41:5055']:
			if 0 == self.config(usb_descriptor.device):
				self.begin()
				self.switch_mode(mode_name="Connect")
			else:
				log.error('While trying to configure the OpenKpaUsb instance')
				return

	def usb_device_lost_cb(self, usb_descriptor):
		# print('Lost: 4
		# ' + str(usb_descriptor))
		if usb_descriptor.device_id == '133e:0001':
			log.warn('Lost connection to KPA - going to stop all used threads!')
			self.stop_threads = True

		elif usb_descriptor.device_id in ['0e41:4246', '0e41:5055']:
			# find connected open_fbv instance
			for open_fbv in self.open_fbvs:
				fbv_usb_descriptor = UsbMonitor.device_to_usb_descriptor(open_fbv.io_interface.usb_device)
				if fbv_usb_descriptor == usb_descriptor:
					open_fbv.stop()
					self.open_fbvs.remove(open_fbv)
					log.info('Removed FBV instance')


	def set_midi_cc(self, switch_no, cc):
		if switch_no not in [0, 1, 2]:
			log.error("switch_no must be either 0, 1 or 2")
			return
		      # 0x21, 0x0, 0x0, 0x18, 0x03, 0x10, 0xed, 0x3, 0x0, 0x4a, 0x0, 0x4, 0xb0, 0x1c, 0x0, 0x0, 0x1, 0x0, 0x6, 0x0, 0x11, 0x0, 0x0, 0x0, 0x83, 0x66, 0xcd, 0x3, 0xf2, 0x64, 0x44, 0x65, 0x84, 0x18, 0x6            , 0x4d, 0x2, 0x1c, 0x2, 0x51, 0x33, 0x00, 0x00, 0x00   0x51 = i[39]
		data = [0x21, 0x0, 0x0, 0x18, 0x80, 0x10, 0xed, 0x3, 0x0, "XX", 0x0, 0x4, 0x42, 0x1b, 0x0, 0x0, 0x1, 0x0, 0x6, 0x0, 0x11, 0x0, 0x0, 0x0, 0x83, 0x66, 0xcd, 0x3, 0xf3, 0x64, 0x44, 0x65, 0x84, 0x18, 0x6 + switch_no, 0x4d, 0x1, 0x1c, 0x2, 0x51, 0x2, 0x0, 0x0, 0x0]
		data = [0x21, 0x0, 0x0, 0x18, 0x80, 0x10, 0xed, 0x3, 0x0, "XX", 0x0, 0x4, 0xb0, 0x1c, 0x0, 0x0, 0x1, 0x0, 0x6, 0x0, 0x11, 0x0, 0x0, 0x0, 0x83, 0x66, 0xcd, 0x3, 0xf2, 0x64, 0x44, 0x65, 0x84, 0x18, 0x6 + switch_no, 0x4d, 0x2, 0x1c, 0x2, 0x51, 0x33, 0x0, 0x0, 0x0]

		try:
			data[40] = int(cc)
			self.endpoint_0x1_out(data)
		except ValueError:
			log.error('Given midi channel is no integer: ' + str(midi_channel))
			return

	def set_midi_channel(self, switch_no, midi_channel):
		if switch_no not in [0, 1, 2]:
			log.error("switch_no must be either 0, 1 or 2")
			return

		data = [0x21, 0x0, 0x0, 0x18, 0x80, 0x10, 0xed, 0x3, 0x0, "XX", 0x0, 0x4, 0x42, 0x1b, 0x0, 0x0, 0x1, 0x0, 0x6, 0x0, 0x11, 0x0, 0x0, 0x0, 0x83, 0x66, 0xcd, 0x3, 0xf3, 0x64, 0x44, 0x65, 0x84, 0x18, 0x6 + switch_no, 0x4d, 0x1, 0x1c, 0x1, 0x51, 0x1, 0x0, 0x0, 0x0]

		try:
			data[40] = int(midi_channel)
			self.endpoint_0x1_out(data)
		except ValueError:
			log.error('Given midi channel is no integer: ' + str(midi_channel))
			return

	def set_custom_foot_switch_function(self, switch_no, function_code):
		if switch_no not in [0, 1, 2]:
			log.error("switch_no must be either 0, 1 or 2")
			return
		try:
			function_code = int(function_code)
			if function_code == 5:
				# Hotkey
				data = [0x1d, 0x0, 0x0, 0x18, 0x80, 0x10, 0xed, 0x3, 0x0, "XX", 0x0, 0x4, 0x87, 0x1b, 0x0, 0x0, 0x1, 0x0, 0x6, 0x0, 0xd, 0x0, 0x0, 0x0, 0x83, 0x66, 0xcd, 0x3, 0xf6, 0x64, 0x43, 0x65, 0x82, 0x18, 0x6 + switch_no, 0x4d, 0x2, 0x0, 0x0, 0x0]
			else:
				data = [0x1d, 0x0, 0x0, 0x18, 0x80, 0x10, 0xed, 0x3, 0x0, "XX", 0x0, 0x4, 0x42, 0x27, 0x0, 0x0, 0x1, 0x0, 0x6, 0x0, 0xd, 0x0, 0x0, 0x0, 0x83, 0x66, 0xcd, 0x4, 0x43, 0x64, 0x43, 0x65, 0x82, 0x18, 0x6 + switch_no, 0x4d, 0x0, 0x0, 0x0, 0x0]
				data[36] = function_code
			self.endpoint_0x1_out(data)
		except ValueError:
			log.error('Given function_codeis no integer: ' + str(function_code))
			return

	def set_color(self, switch_no, color_id):
		if switch_no not in [0, 1, 2]:
			log.error("switch_no must be either 0, 1 or 2")
			return

		alt_cnt = 0xa6  # it's a legacy variable

		data = [0x1d, 0x0, 0x0, 0x18, 0x80, 0x10, 0xed, 0x3, 0x0, "XX", 0x0, 0x4, self.session_quadruple[0], self.session_quadruple[1], self.session_quadruple[2], self.session_quadruple[3], 0x1, 0x0, 0x6, 0x0, 0xd, 0x0, 0x0, 0x0, 0x83, 0x66, 0xcd, alt_cnt, 0xf0, 0x64, 0x3d, 0x65, 0x82, 0x66, switch_no, 0x42, color_id, 0x0, 0x7f, 0x0]
		self.endpoint_0x1_out(data)

	def set_label(self, switch_no, text):
		if switch_no not in [0, 1, 2]:
			log.error("switch_no must be either 0, 1 or 2")
			return

		msg_size_byte = 0x1e + len(text)
		length_byte = 0xa1 + len(text)
		second_length_byte = msg_size_byte - 0x10

		data = [msg_size_byte, 0x0, 0x0, 0x18, 0x80, 0x10, 0xed, 0x3, 0x0, "XX", 0x0, 0x4, self.session_quadruple[0], self.session_quadruple[1], self.session_quadruple[2], self.session_quadruple[3], 0x1, 0x0, 0x6, 0x0, second_length_byte, 0x0, 0x0, 0x0, 0x83, 0x66, 0xcd, 0x3, 0xf0, 0x64, 0x3b, 0x65, 0x82, 0x66, switch_no, 0x6d, length_byte]
		for character in text:
			data.append(ord(character))

		while len(data) < msg_size_byte + 9 + 2:
			data.append(0x0)

		self.endpoint_0x1_out(data)

	def highlight_slot(self, slot_no):
		data = [0x1d, 0x0, 0x0, 0x18, 0x80, 0x10, 0xed, 0x3, 0x0, "XX", 0x0, 0x4, 0x44, 0x26, 0x0, 0x0, 0x1, 0x0, 0x6, 0x0, 0xd, 0x0, 0x0, 0x0, 0x83, 0x66, 0xcd, 0x4, 0x34, 0x64, 0x4e, 0x65, 0x82, 0x62, 0x1, 0x1a, 0x0, 0x0, 0x0, 0x0]

		try:
			data[34] = int(slot_no)
			self.endpoint_0x1_out(data)
		except ValueError:
			log.error('Given function_code is no integer: ' + str(slot_no))
			return

	def set_fs_function(self, foot_switch_name, function_name):

		try:
			foot_switch_id = self.FOOT_SWITCHES[foot_switch_name]
		except KeyError:
			log.error("Unknown foot switch with name: " + foot_switch_name)
			return

		try:
			foot_switch_function_id = self.FOOT_SWITCH_FUNCTIONS.index(function_name)
		except ValueError:
			log.error("Unknown foot switch function with name: " + function_name)
			return

		log.info(foot_switch_name + ": setting foot switch function to: " + function_name)
		data = [0x1d, 0x0, 0x0, 0x18, 0x80, 0x10, 0xed, 0x3, 0x0, "XX", 0x0, 0x4, 0xc6, 0x1e, 0x0, 0x0, 0x1, 0x0, 0x6, 0x0, 0xd, 0x0, 0x0, 0x0, 0x83, 0x66, 0xcd, 0x4, 0x4, 0x64, 0x19, 0x65, 0x82, 0x76, foot_switch_id, 0x77, foot_switch_function_id, 0x0, 0x0, 0x0]
		self.endpoint_0x1_out(data)

	def set_preset_label_be_careful(self, prog_no, text):
		msg_size_byte = 0x20 + len(text)
		length_byte = 0xa1 + len(text)
		second_length_byte = msg_size_byte - 0x10
		data = [msg_size_byte, 0x0, 0x0, 0x18, 0x1, 0x10, 0xef, 0x3, 0x0, "XX", 0x0, 0x4, 0x77, 0x1e, 0x0, 0x0, 0x1, 0x0, 0x2, 0x0, second_length_byte, 0x0, 0x0, 0x0, 0x83, 0x66, 0xcd, 0x3, 0xed, 0x64, 0x6, 0x65, 0x83, 0x6b, 0x0, 0x6c, prog_no, 0x6d, length_byte]

		for character in text:
			data.append(ord(character))

		while len(data) < msg_size_byte + 9 + 2:
			data.append(0x0)

		self.endpoint_0x1_out(data)

	def on_preset_name_update(self, preset_name):
		log.info("*************************** Preset Name: " + preset_name)

	def on_slot_update(self, slot_no, slot_info):
		log.info('Slot ' + str(slot_no) + ' change: ' + slot_info.to_string())

	def on_snapshot_change(self, current_snapshot):
		log.info('Snapshot change to: ' + str(current_snapshot))

	def set_preset(self, preset_no):
		self.current_preset_no = preset_no
		for cb_fct in self.preset_no_change_cb_fct_list:
			cb_fct(self.current_preset_no)

	def on_preset_change(self, preset_no):
		self.preset_change_cnt += 1
		log.info("******************** PRESET switch no: " + str(self.preset_change_cnt) +" to: " + str(preset_no))
		self.preset_no = preset_no

	def signal_handler(self, sig, frame):
		if self.excel_logger:
			self.excel_logger.save()


def print_usage(p_b_exit=True):
	print()
	print()
	print("Usage: %s [args]" % sys.argv[0])
	print()
	print("args:")
	print('\t-x: dumps session data to given xlsx file (Excel format)')
	print()
	print("switches:")
	print('\t-h: prints this text')
	print()

	if p_b_exit is True:
		sys.exit(1)


def main(argv):
	logging.basicConfig(
		level='INFO',
		format="%(asctime)s - %(levelname)s - %(message)s (%(name)s)",
		datefmt="%Y-%m-%d %H:%M:%S")

	excel_log_path = None
	try:
		opts, args = getopt.getopt(argv[1:], 'x:h', [])
		for opt, arg in opts:
			if opt in '-h':
				print_usage()
			elif opt in '-x':
				excel_log_path = arg
			else:
				print_usage()
	except getopt.GetoptError as e:
		log.error("While trying to parse command line arguments: " + str(e))
		print_usage()

	helix_usb = HelixUsb()
	helix_usb.set_excel_logger(excel_log_path)
	helix_usb.register_preset_name_change_cb_fct(helix_usb.on_preset_name_update)
	helix_usb.register_slot_data_change_cb_fct(helix_usb.on_slot_update)
	helix_usb.register_snapshot_change_cb_fct(helix_usb.on_snapshot_change)
	helix_usb.register_preset_no_change_cb_fct(helix_usb.on_preset_change)

	signal.signal(signal.SIGINT, helix_usb.signal_handler)

	# only report Line6 Helix devices
	usb_monitor = UsbMonitor(['0e41:4246', '0e41:5055'])

	usb_monitor.register_device_found_cb(helix_usb.usb_device_found_cb)
	usb_monitor.register_device_lost_cb(helix_usb.usb_device_lost_cb)
	usb_monitor.start()

	while True:

		try:
			python_version = int(sys.version_info[0])
			if python_version <= 2:
				text = raw_input("command: ")
			else:
				text = input("command: ")
			text = text.rstrip()
			tokens = text.split(' ')
			if len(tokens) == 1:
				try:
					if text == "save":
						helix_usb.excel_logger.save()
					else:
						text = int(text)
						if text == 0:
							helix_usb.switch_mode("RequestPresetName")
						elif text == 1:
							helix_usb.switch_mode("RequestPreset")
						elif text == 2:
							helix_usb.switch_mode("RequestPresetNames")
						else:
							log.warning('Unknown command id: ' + str(text))
				except ValueError:
					log.error('Invalid value - only integer values allowed')
					continue
			elif len(tokens) == 2:
				try:
					switch_id = int(tokens[0])
				except ValueError:
					log.error('Invalid value - only integer values allowed')
					continue
				if switch_id in [11, 12, 13]:
					if tokens[1] in HelixUsb.LED_COLORS:
						color_id = HelixUsb.LED_COLORS.index(tokens[1])
						helix_usb.set_color(switch_id - 11, color_id)
				elif switch_id in [21, 22, 23]:
					helix_usb.set_label(switch_id - 21, tokens[1])
				elif switch_id in [31, 32, 33]:
					helix_usb.set_midi_channel(switch_id - 31, tokens[1])
				elif switch_id in [41, 42, 43]:
					helix_usb.set_midi_cc(switch_id - 41, tokens[1])
				elif switch_id in [51, 52, 53]:
					helix_usb.set_custom_foot_switch_function(switch_id - 51, tokens[1])
				elif switch_id in [63, 64, 65]:
					if switch_id == 63:
						helix_usb.set_fs_function("FS3", tokens[1])
					if switch_id == 64:
						helix_usb.set_fs_function("FS4", tokens[1])
					if switch_id == 65:
						helix_usb.set_fs_function("FS5", tokens[1])
				elif switch_id in [18]:
					helix_usb.highlight_slot(tokens[1])
				elif switch_id in [19]:
					helix_usb.set_preset_label_be_careful(tokens[1])

		except KeyboardInterrupt as _:
			usb_monitor.request_terminate = True
			helix_usb.stop_threads = True
			return 0


if __name__ == '__main__':
	main(sys.argv)
