from out_packet import OutPacket
import logging
log = logging.getLogger(__name__)


class Standard:
	def __init__(self, helix_usb, name):
		self.helix_usb = helix_usb
		self.name = name

	def start(self):
		log.info('Starting mode')

	def shutdown(self):
		log.info('Shutting down mode')

	def data_in(self, data):
		# LED COLOR CHANGE
		if self.helix_usb.my_byte_cmp(left=data, right=["XX", 0x0, 0x0, 0x18, 0xed, 0x3, 0x80, 0x10, 0x0, "XX", 0x0, 0x4, "XX", "XX", "XX", "XX"], length=16):
			self.helix_usb.increase_session_quadruple_x11()
			out = OutPacket(data=[0x8, 0x0, 0x0, 0x18, 0x80, 0x10, 0xed, 0x3, 0x0, "XX", 0x0, 0x8, self.helix_usb.session_quadruple[0], self.helix_usb.session_quadruple[1], self.helix_usb.session_quadruple[2], self.helix_usb.session_quadruple[3]],
					  delay=0.0)
			self.helix_usb.out_packet_to_endpoint_0x1(out)

		elif self.helix_usb.my_byte_cmp(left=data, right=[0x17, 0x0, 0x0, 0x18, 0xf0, 0x3, 0x2, 0x10, 0x0, "XX", 0x0, 0x4, 0x9, 0x2, 0x0, 0x0], length=16):
			out = OutPacket(data=[0x8, 0x0, 0x0, 0x18, 0x2, 0x10, 0xf0, 0x3, 0x0, "XX", 0x0, 0x8, 0x74, 0x77, 0x0, 0x0],
					  delay=0.01)
			self.helix_usb.out_packet_to_endpoint_0x1(out)


		# VIEW CHANGE
		elif self.helix_usb.my_byte_cmp(left=data, right=[0x23, 0x0, 0x0, 0x18, 0xf0, 0x3, 0x2, 0x10, 0x0, "XX", 0x0, 0x4, 0x9, 0x2, 0x0, 0x0, 0x0, 0x0, 0x4, 0x0, 0x13, 0x0, 0x0, 0x0, 0x82, 0x69, 0x16, 0x6a, 0x84, 0x52, 0x0, 0x44, 0x9, 0x79, 0x19, 0x6a, 0x82, 0x76, 0xcd, 0x0, 0x13, 0x77], length=42):
			view_id = data[42]
			try:
				view_name = self.helix_usb.VIEWS[view_id]
				log.info("UI changed to: " + view_name)
			except KeyError:
				log.info("Error while trying to get view name, id is: " + str(view_id))

		# UI MODE CHANGE
		elif self.helix_usb.my_byte_cmp(left=data, right=[0x23, 0x0, 0x0, 0x18, 0xf0, 0x3, 0x2, 0x10, 0x0, "XX", 0x0, 0x4, 0x9, 0x2, 0x0, 0x0, 0x0, 0x0, 0x4, 0x0, 0x13, 0x0, 0x0, 0x0, 0x82, 0x69, 0x16, 0x6a, 0x84, 0x52, 0x0, 0x44, 0x9, 0x79, 0x19, 0x6a, 0x82, 0x76, 0xcd, 0x0, 0x15, 0x77], length=42):
			mode_idx = data[42]
			if 0 <= mode_idx < 4:
				mode_name = self.helix_usb.UI_MODES[mode_idx]
				log.info("UI mode changed to: " + mode_name)
			else:
				log.info("Error while trying to get UI mode name, unknown mode_idx: " + str(mode_idx))

		# SLOT CHANGE
		elif self.helix_usb.my_byte_cmp(left=data, right=[0x21, 0x0, 0x0, 0x18, 0xf0, 0x3, 0x2, 0x10, 0x0, "XX", 0x0, 0x4, 0x9, 0x2, 0x0, 0x0, 0x0, 0x0, 0x4, 0x0, 0x11, 0x0, 0x0, 0x0, 0x82, 0x69, 0x27, 0x6a, 0x84, 0x52, 0x1, 0x44, 0x3, 0x79, 0x13, 0x6a, 0x82, 0x62], length=38):
			slot_id = data[38]
			log.info("Selected slot id changed to: " + str(slot_id))

		# PRESET SWITCH
		# if self.helix_usb.my_byte_cmp(left=data, right=[0x23, 0x0, 0x0, 0x18, 0xf0, 0x3, 0x2, 0x10, 0x0, "XX", 0x0, 0x4, 0x9, 0x2, 0x0, 0x0, 0x0, 0x0, 0x4, 0x0, 0x13, 0x0, 0x0, 0x0, 0x82, 0x69, 0x16, 0x6a, 0x84, 0x52, 0x0, 0x44, 0x9, 0x79, 0x19, 0x6a, 0x82, 0x76, 0xcd, 0x0, 0x1c, 0x77, "XX", 0x42], length=44):
		elif self.helix_usb.my_byte_cmp(left=data, right=[0x21, 0x0, 0x0, 0x18, 0xf0, 0x3, 0x2, 0x10, 0x0, "XX", 0x0, 0x4, 0x9, 0x2, 0x0, 0x0, 0x0, 0x0, 0x4, 0x0, 0x11, 0x0, 0x0, 0x0, 0x82, 0x69, "XX", 0x6a, 0x84, 0x52, 0x1, 0x44, 0x1, 0x79, "XX", 0x6a, 0x82, 0x6b, 0x0, 0x6c], length=30):

			hex_str = ''.join('0x{:x}, '.format(x) for x in data)
			log.warning("Unexpected message in mode: " + str(hex_str))

			self.helix_usb.set_preset(data[40])
			self.helix_usb.got_preset_name = False
			self.helix_usb.got_preset = False
			self.helix_usb.switch_mode()
			out = OutPacket(data=[0x8, 0x0, 0x0, 0x18, 0x2, 0x10, 0xf0, 0x3, 0x0, "XX", 0x0, 0x8, 0x74, 0x77, 0x0, 0x0],
							delay=0.01)
			self.helix_usb.out_packet_to_endpoint_0x1(out)

		elif self.helix_usb.my_byte_cmp(left=data, right=[0x21, 0x0, 0x0, 0x18, 0xf0, 0x3, 0x2, 0x10, 0x0, "XX", 0x0, 0x4, 0x9, 0x2, 0x0, 0x0, 0x0, 0x0, 0x4, 0x0, 0x11, 0x0, 0x0, 0x0, 0x82, 0x69, 0x27, 0x6a, 0x84, 0x52, 0x1, 0x44, 0x3, 0x79, 0x13, 0x6a, 0x82, 0x62], length=38):
			# self.helix_usb.set_preset(data[40])
			# log.info("******************** PRESET: " + str(self.helix_usb.preset_no))
			self.helix_usb.got_preset_name = False
			self.helix_usb.got_preset = False
			self.helix_usb.switch_mode()
			out = OutPacket(data=[0x8, 0x0, 0x0, 0x18, 0x2, 0x10, 0xf0, 0x3, 0x0, "XX", 0x0, 0x8, 0x74, 0x77, 0x0, 0x0],
							delay=0.01)
			self.helix_usb.out_packet_to_endpoint_0x1(out, silent=True)

		elif self.helix_usb.check_keep_alive_response(data):
			return False  # don't print incoming message to console

		else:
			hex_str = ''.join('0x{:x}, '.format(x) for x in data)
			log.warning("Unexpected message in mode: " + str(hex_str))

		return True  # print incoming message to console