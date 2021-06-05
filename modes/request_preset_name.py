from modes.standard import Standard
import random
import logging

log = logging.getLogger(__name__)


class RequestPresetName(Standard):
    def __init__(self, helix_usb):
        Standard.__init__(self, helix_usb=helix_usb, name="request_preset_name")
        self.preset_name_data = []

    def start(self):
        log.info('Starting mode')
        self.preset_name_data = []
        data = [0x19, 0x0, 0x0, 0x18, 0x80, 0x10, 0xed, 0x3, 0x0, "XX", 0x0, 0x4, self.helix_usb.maybe_session_no, self.helix_usb.preset_data_packet_double(), 0x0, 0x0, 0x1, 0x0, 0x6,
                0x0, 0x9, 0x0, 0x0, 0x0, 0x83, 0x66, 0xcd, 0x4, 0x4, 0x64, 0x17, 0x65, 0xc0, 0x0, 0x0, 0x0]
        self.helix_usb.endpoint_0x1_out(data)

    def shutdown(self):
        log.info('Shutting down mode')

    def data_in(self, data_in):
        if self.helix_usb.check_keep_alive_response(data_in):
            return False  # don't print incoming message to console

        elif self.helix_usb.my_byte_cmp(left=data_in[23:], right=[0x0, 0x83, 0x66, 0xcd, "XX", "XX", 0x67, 0x0, 0x68, 0x86, 0x6b, 0xcd, 0x0, 0x0, 0x6c, 0xcd], length=16):
            self.helix_usb.log_data_in(data_in)
            for b in data_in[16:]:
                self.preset_name_data.append(b)

            if data_in[1] == 0x0:
                slot_number_idx = 27
                preset_name = ''
                for i in range(slot_number_idx, slot_number_idx + 24):
                    if self.preset_name_data[i] == 0x00:
                        break
                    preset_name += chr(self.preset_name_data[i])

                # log.info("*************************** Preset Name: " + preset_name)
                self.helix_usb.set_preset_name(preset_name)

                # update session no
                self.helix_usb.maybe_session_no = random.choice(range(0x04, 0xff))

                self.helix_usb.switch_mode()

            return True  # print incoming message to console

        else:
            hex_str = ''.join('0x{:x}, '.format(x) for x in data_in)
            log.warning("Unexpected message in mode: " + str(hex_str))
            return True
