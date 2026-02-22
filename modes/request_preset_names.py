from modes.standard import Standard
from out_packet import OutPacket
import logging
import threading
log = logging.getLogger(__name__)


class RequestPresetNames(Standard):
	def __init__(self, helix_usb):
		Standard.__init__(self, helix_usb=helix_usb, name="request_preset_names")
		self.preset_names_data = []
		self.preset_names_stream = []
		self.stream_parse_idx = 0
		self.decoded_preset_names = []
		self.decoded_preset_names_by_index = {}
		self.decoded_preset_names_fallback = []
		self.expected_preset_name_count = 125
		self.idle_watchdog_timer = None
		self.transfer_complete = False
		self.preset_name_placeholder = "<empty>"

	def start(self):
		log.info('Starting mode')
		self.preset_names_data = []
		self.preset_names_stream = []
		self.stream_parse_idx = 0
		self.decoded_preset_names = []
		self.decoded_preset_names_by_index = {}
		self.decoded_preset_names_fallback = []
		self.transfer_complete = False
		self._cancel_idle_watchdog()
		data = [0x1d, 0x0, 0x0, 0x18, 0x1, 0x10, 0xef, 0x3, 0x0, "XX", 0x0, 0xc, 0x38, 0x10, 0x0, 0x0, 0x1, 0x0, 0x2,
				0x0, 0xd, 0x0, 0x0, 0x0, 0x83, 0x66, 0xcd, 0x3, 0xea, 0x64, 0x1, 0x65, 0x82, 0x6b, 0x0, 0x65, 0x2, 0x0,
				0x0, 0x0]
		# data = [0x19, 0x0, 0x0, 0x18, 0x1, 0x10, 0xef, 0x3, 0x0, "XX", 0x0, 0x4, 0x1a, 0x10, 0x0, 0x0, 0x1, 0x0, 0x2, 0x0, 0x9, 0x0, 0x0, 0x0, 0x83, 0x66, 0xcd, 0x3, 0xe9, 0x64, 0x0, 0x65, 0xc0, 0x0, 0x0, 0x0]
		# data = [0x1a, 0x0, 0x0, 0x18, 0x1, 0x10, 0xef, 0x3, 0x0, "XX", 0x0, 0x4, 0x9, 0x10, 0x0, 0x0, 0x1, 0x0, 0x2, 0x0, 0xa, 0x0, 0x0, 0x0, 0x83, 0x66, 0xcd, 0x3, 0xe8, 0x64, 0xcc, 0xfe, 0x65, 0x80, 0x0, 0x0]
		self.helix_usb.endpoint_0x1_out(data, silent=True)
		self._arm_idle_watchdog()

	def shutdown(self):
		log.info('Shutting down mode')
		self._cancel_idle_watchdog()

	def _cancel_idle_watchdog(self):
		if self.idle_watchdog_timer is not None:
			self.idle_watchdog_timer.cancel()
			self.idle_watchdog_timer = None

	def _arm_idle_watchdog(self):
		self._cancel_idle_watchdog()
		self.idle_watchdog_timer = threading.Timer(0.75, self._on_idle_watchdog_timeout)
		self.idle_watchdog_timer.start()

	def _on_idle_watchdog_timeout(self):
		if self.transfer_complete:
			return
		count = self.parse_preset_names(finalize=True)
		log.info('Preset-name request idle timeout reached with %d decoded names; finishing request mode', count)
		self._finish_transfer()

	def _finish_transfer(self):
		if self.transfer_complete:
			return
		self.transfer_complete = True
		self._cancel_idle_watchdog()
		self.parse_preset_names(finalize=True)
		self.decoded_preset_names = self._build_aligned_preset_names()

		self.helix_usb.set_preset_names(self.decoded_preset_names)
		for idx, name in enumerate(self.decoded_preset_names):
			log.info('%d: %s', idx, name)
		log.info('Received preset names: %d', len(self.decoded_preset_names))
		self.helix_usb.switch_mode()

	def _extract_record_preset_index(self, record):
		if len(record) < 9:
			return None

		metadata = record[3:9]
		idx_6b = -1
		idx_6c = -1
		for i, b in enumerate(metadata):
			if b == 0x6b and i + 1 < len(metadata):
				idx_6b = metadata[i + 1]
			elif b == 0x6c and i + 1 < len(metadata):
				idx_6c = metadata[i + 1]

		if idx_6b < 0 or idx_6c < 0:
			return None

		candidate = (idx_6b * 25) + idx_6c
		if 0 <= candidate < self.expected_preset_name_count:
			return candidate
		return None

	def _decoded_name_count(self):
		return len(self.decoded_preset_names_by_index) + len(self.decoded_preset_names_fallback)

	def _build_aligned_preset_names(self):
		aligned = [self.preset_name_placeholder] * self.expected_preset_name_count

		for idx, name in self.decoded_preset_names_by_index.items():
			aligned[idx] = name

		fallback_iter = iter(self.decoded_preset_names_fallback)
		for idx in range(self.expected_preset_name_count):
			if aligned[idx] == self.preset_name_placeholder:
				try:
					aligned[idx] = next(fallback_iter)
				except StopIteration:
					break

		return aligned

	def parse_preset_names(self, finalize=False):
		pattern = [0x81, 0xcd, 0x0]
		record_len = 25  # marker(3) + metadata/name fields up to 16-byte name area

		while True:
			search_limit = len(self.preset_names_stream) - len(pattern) + 1
			if self.stream_parse_idx >= search_limit:
				if not finalize:
					self.stream_parse_idx = max(0, len(self.preset_names_stream) - len(pattern) + 1)
				break

			marker_idx = -1
			for i in range(self.stream_parse_idx, search_limit):
				if self.preset_names_stream[i:i + len(pattern)] == pattern:
					marker_idx = i
					break

			if marker_idx < 0:
				if not finalize:
					self.stream_parse_idx = max(0, len(self.preset_names_stream) - len(pattern) + 1)
				break

			if marker_idx + record_len > len(self.preset_names_stream):
				if not finalize:
					self.stream_parse_idx = marker_idx
				break

			record = self.preset_names_stream[marker_idx:marker_idx + record_len]
			name_bytes = record[9:25]
			name_chars = []
			for b in name_bytes:
				if b == 0x0:
					break
				if 32 <= b <= 126:
					name_chars.append(chr(b))
				else:
					name_chars.append('?')
			decoded_name = ''.join(name_chars)
			preset_idx = self._extract_record_preset_index(record)
			if preset_idx is not None:
				if preset_idx not in self.decoded_preset_names_by_index:
					self.decoded_preset_names_by_index[preset_idx] = decoded_name
			else:
				self.decoded_preset_names_fallback.append(decoded_name)
			self.stream_parse_idx = marker_idx + record_len

		return self._decoded_name_count()

	def _append_name_packet_payload(self, packet):
		self.preset_names_data.append(packet)
		self.preset_names_stream.extend(packet[16:])

	def data_in(self, data_in):
		if self.transfer_complete:
			return False

		if self.helix_usb.check_keep_alive_response(data_in):
			return False  # don't print incoming message to console

		elif self.helix_usb.my_byte_cmp(left=data_in, right=[0x8, 0x1, 0x0, 0x18, 0xef, 0x3, 0x1, 0x10, 0x0, "XX", 0x0, 0x4, "XX", 0x2, 0x0, 0x0, "XX"], length=17):
			# one packet
			self._append_name_packet_payload(data_in)
			out = OutPacket(data=[0x8, 0x0, 0x0, 0x18, 0x1, 0x10, 0xef, 0x3, 0x0, "XX", 0x0, 0x8, 0x38, data_in[9]+9, 0x0, 0x0])
			self.helix_usb.out_packet_to_endpoint_0x1(out, silent=True)
			self._arm_idle_watchdog()
			decoded_count = self.parse_preset_names()
			if decoded_count >= self.expected_preset_name_count:
				log.info('Preset-name request reached expected count (%d), finishing request mode', self.expected_preset_name_count)
				self._finish_transfer()

		elif self.helix_usb.my_byte_cmp(left=data_in, right=["XX", 0x0, 0x0, 0x18, 0xef, 0x3, 0x1, 0x10, 0x0, "XX", 0x0, 0x4, "XX", 0x2, 0x0, 0x0], length=16):
			# packet with payload shape that may be final or intermediate depending on transfer timing
			out = OutPacket(data=[0x8, 0x0, 0x0, 0x18, 0x1, 0x10, 0xef, 0x3, 0x0, "XX", 0x0, 0x8, 0x38, data_in[9] + 9, 0x0, 0x0])
			self.helix_usb.out_packet_to_endpoint_0x1(out, silent=True)

			self._append_name_packet_payload(data_in)
			self._arm_idle_watchdog()
			decoded_count = self.parse_preset_names()
			if decoded_count >= self.expected_preset_name_count:
				log.info('Preset-name request reached expected count (%d), finishing request mode', self.expected_preset_name_count)
				self._finish_transfer()

		else:
			hex_str = ''.join('0x{:x}, '.format(x) for x in data_in)
			log.warning("Unexpected message in mode: " + str(hex_str))

		return True  # print incoming message to console
