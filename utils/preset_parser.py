from utils.formatter import ieee754_to_rendered_str
import sys
from modules import modules


class SlotInfo:
    FIELD_MAP_00 = {
        0x13: ("slot_type", "byte"),
        0x14: ("unknown_1_x82", "byte"),
        0x05: ("unknown_2_x01", "byte"),
        0x07: ("parameter", "until_end")
    }

    FIELD_MAP_01 = {
        0x13: ("slot_type", "byte"),
        0x14: ("unknown_1_x82", "byte"),
        0x06: ("unknown_2_x01", "byte"),
        0x07: ("parameter", "until_end")
    }

    FIELD_MAP_02 = {
        0x13: ("slot_type", "byte"),
        0x14: ("unknown_1_x83", "byte"),
        0x0e: ("unknown_2_x02", "byte"),
        0x05: ("unknown_3", "raw3"),
        0x02: ("unknown_4_x00", "byte"),
        0x03: ("unknown_5_x00", "byte"),
        0x04: ("unknown_6_x90", "byte"),
        0x0f: ("unknown_7_x84", "byte"),
        0x08: ("unknown_8", "raw3"),
        0x0d: ("unknown_9_x08", "byte"),
        0x0a: ("unknown_10_xc3", "byte"),
        0x07: ("parameter", "until_end")
    }

    FIELD_MAP_03 = {
        0x13: ("slot_type", "byte"),
        0x14: ("unknown_1_x83", "byte"),
        0x10: ("unknown_2_x02", "byte"),
        0x06: ("unknown_3", "byte"),
        0x07: ("parameter", "until_end")
    }

    FIELD_MAP = {
        0x13: ("slot_type", "byte"),
        # (00 - Input Upper chain, 01 Output upper chain, 02 Input Lower chain, 03 Output lower chain, 08 No Slot, 06 standard slot, 07 Looper )
        0x1c: ("unknown_1_x02", ("until_marker", [0x18])),
        # 0x14: ("unknown_1_x85", ("until_marker", [0x1c])),
        0x14: ("unknown_1_x85", "byte"),
        0x18: ("unknown_2_x83", "byte"),
        0x17: ("dual_slot", "bool"),
        0x19: ("amp_effect_slot_a", ("until_marker", [0x1a])),
        0x1a: ("amp_effect_slot_b", ("until_marker", [0x09])),
        0x09: ("unknown_3_xc3", "byte"),
        0x0a: ("enabled", "bool"),
        0x0b: ("info_slot_a", ("until_marker", [0x0c, 0x83])),
        0x0c: ("info_slot_b", "until_end")
    }

    FIELD_MAP_LOOPER = {
        0x13: ("slot_type", "byte"),
        # (00 - Input Upper chain, 01 Output upper chain, 02 Input Lower chain, 03 Output lower chain, 08 No Slot, 06 standard slot, 07 Looper )
        # 0x1c: ("unknown_1_x02", ("until_marker", [0x18])),
        0x14: ("unknown_1_x84", "byte"),

        0x08: ("unknown_2_x83", ("until_marker", [0x0a])),
        0x01: ("dual_slot", "bool"),
        0x09: ("amp_effect_slot_a", "byte"),
        0x0a: ("enabled", "bool"),
        0x07: ("info_slot", "until_end")
    }

    def __init__(self, hex_string: str, debug=False):
        self.raw = hex_string
        self.debug = debug
        self.parameter_a = []
        self.parameter_b = []
        self.amp_effect_slot_a = b'\xff'
        self.amp_effect_slot_b = b'\xff'
        self._parse()

    # --------------------------------------------------
    # DEBUG HELPERS
    # --------------------------------------------------

    def _dbg(self, cursor, msg):
        if not self.debug:
            return

        context = 30
        start = max(0, cursor - context)
        end = min(len(self.raw), cursor + context)

        snippet = self.raw[start:end].hex(" ")
        pointer = "   " * (cursor - start) + "^^"

        print(f"\n[pos={cursor:03}] {msg}")
        print(snippet)
        print(pointer)

    def _log_field(self, marker, name, value):
        if not self.debug:
            return
        print(f"    Parsed {hex(marker)} → {name} = {value}")

    @staticmethod
    def read_params(num_params, byte_data):

        data = ''.join('{:02x}'.format(x) for x in byte_data)
        bytes_read = 0
        params = list()
        # print(data)

        while len(params) < num_params:
            if data.startswith('c2'):
                # boolean false
                params.append(False)
                data = data[2:]
                bytes_read += 2
            elif data.startswith('c3'):
                # boolean true
                bytes_read += 2
                data = data[2:]
                params.append(True)
            elif data.startswith('ca'):
                # float value
                value = data[2:10]
                ieee_val = ieee754_to_rendered_str(value)
                data = data[10:]
                bytes_read += 10
                params.append(ieee_val)

            else:
                # should be a simple integer/index
                param = int(data[0], 16) * 16 + int(data[1], 16)
                data = data[2:]
                bytes_read += 2
                params.append(param)
                '''
                simple_int_value = data_stream[0:2]
                params.append(simple_int_value)
                data_stream = data_stream[2:]
                '''
        if data.startswith('1bda'):
            # binary data - used in IRs. I spent some time understanding the code so I implemented it here
            val1 = data[4:6]
            val2 = data[6:8]
            size_of_data = int(data[4:6], 16) * 16 + int(data[6:8], 16)
            data = data[8:]
            bytes_read += 8
            # assert (len(data) > size_of_data * 2)
            param = data[:size_of_data * 2]
            params.append(param)
            bytes_read += size_of_data * 2

        return params, bytes_read

    def id_to_names(self):
        readable_name_a = readable_name_b = ''
        if self.amp_effect_slot_a != b'\xff':
            beauty_str = ''.join('{:02x}'.format(x) for x in self.amp_effect_slot_a)
            try:
                readable_name_a = modules[beauty_str]
            except KeyError as _:
                readable_name_a = ["NOT FOUND IN MODULES {}".format(beauty_str), '']
        if self.amp_effect_slot_b != b'\xff':
            beauty_str = ''.join('{:02x}'.format(x) for x in self.amp_effect_slot_b)
            try:
                readable_name_b = modules[beauty_str]
            except KeyError as _:
                readable_name_b = ["NOT FOUND IN MODULES {}".format(beauty_str), '']
        return [readable_name_a, readable_name_b]

    # --------------------------------------------------
    # PARSER
    # --------------------------------------------------

    def _parse(self):
        data = self.raw
        cursor = 0

        active_field_map = self.FIELD_MAP
        # ---- HEADER ----
        header = data[cursor]
        self._dbg(cursor, f"Reading header {hex(header)}")
        cursor += 1

        if (header & 0xF0) != 0x80:
            raise ValueError("Invalid header")

        child_count = header & 0x0F
        print(f"\n== Slot type {child_count} ==") if self.debug else None

        # ---- CHILDREN ----
        for child_index in range(child_count):

            self._dbg(cursor, f"Entering child #{child_index}")

            while cursor < len(data):

                marker = data[cursor]
                self._dbg(cursor, f"Reading marker {hex(marker)}")
                cursor += 1

                if marker not in active_field_map:
                    raise ValueError(f"Unknown marker {hex(marker)}")

                field_name, field_type = active_field_map[marker]

                # ---- TYPE HANDLING ----

                if field_type == "byte":
                    value = data[cursor]
                    cursor += 1
                    if field_name == 'slot_type':
                        if value == 0x00:
                            active_field_map = self.FIELD_MAP_00
                        elif value == 0x01:
                            active_field_map = self.FIELD_MAP_01
                        elif value == 0x02:
                            active_field_map = self.FIELD_MAP_02
                        elif value == 0x03:
                            active_field_map = self.FIELD_MAP_03
                        elif value == 0x07:
                            active_field_map = self.FIELD_MAP_LOOPER

                elif field_type == "bool":
                    raw = data[cursor]
                    cursor += 1

                    if raw == 0xC2:
                        value = True
                    elif raw == 0xC3:
                        value = False
                    else:
                        raise ValueError("Invalid bool encoding")

                elif field_type == "string":
                    length_byte = data[cursor]
                    cursor += 1

                    # strlen = length_byte & 0x0F
                    # Length of the values are stored in one byte.
                    # a5 => 5 characters, a0 => 10 characters, aa => 11 characters and so on.
                    # I don't know yet, wie 0xaf is not used for 16 characters but one example with 16 chars
                    # used 0xb0 => 16 characters as coding. Maybe 0xaf should not be part of a message??
                    # thus, the values of 0xa0 needs to subtracted from MSB
                    strlen = (length_byte & 0xF0) - 0xA0 + (length_byte & 0x0F)
                    raw_bytes = data[cursor:cursor+strlen]
                    cursor += strlen

                    if cursor < len(data) and data[cursor] == 0x00:
                        cursor += 1

                    value = raw_bytes.decode("ascii", errors="ignore")

                elif isinstance(field_type, tuple) and field_type[0] == "until_marker":
                    stop_marker = field_type[1]
                    start = cursor

                    self._dbg(cursor, "Scanning for stop condition (marker + bool)")

                    while cursor < len(data) - 0:
                        stop_condition_valid = True
                        for i in range(0, len(stop_marker)):
                            try:
                                l = data[cursor+i]
                                r = stop_marker[i]
                                if data[cursor + i] != stop_marker[i]:
                                    stop_condition_valid = False
                            except Exception as _:
                                pass
                        if stop_condition_valid:
                            self._dbg(cursor, "Stop condition found")
                            break
                        cursor += 1

                    value = data[start:cursor]
                    if field_name == "info_slot_a":
                        num_params = value[2]
                        params, bytes_processed = self.read_params(num_params, value[7:])
                        self.parameter_a = params
                    if field_name == "info_slot_b":
                        num_params = value[2]
                        params, bytes_processed = self.read_params(num_params, value[7:])
                        self.parameter_b = params


                elif field_type == "raw3":
                    value = data[cursor:cursor + 3]
                    cursor += 3

                elif field_type == "until_end":
                    start = cursor
                    cursor = len(data)
                    value = data[start:cursor]
                    # beauty_str = ''.join('{:02x}'.format(x) for x in value)

                    num_params = value[2]
                    params, bytes_processed = self.read_params(num_params, value[7:])
                    self.parameter_b = params

                else:
                    raise ValueError("Unknown field type")

                setattr(self, field_name, value)
                self._log_field(marker, field_name, value)

            self._dbg(cursor, f"Finished child #{child_index}")


class FootSwitchChild:
    LED_COLORS = [
        'off', 'white', 'red', 'dark_orange', 'light_orange', 'yellow', 'green', 'turquoise', 'blue', 'violet',
        'pink', 'auto_color']

    """
    Represents one 0x87 child block.
    Fields are assigned dynamically as attributes.
    """

    FIELD_MAP = {
        0x0A: ("index", "byte"),
        0x0B: ("config", "raw3"),
        0x05: ("label", "string"),
        0x06: ("data_blob", ("until_marker_bool", 0x07)),
        0x07: ("enabled", "bool"),
        0x08: ("optional_param", "byte"), # In very (very) rare cases, such as:
        0x02: ("optional_param", "byte"), # 91870a000b87000205a6426f6f73740006ce0007100c07c2
        0x09: ("optional_param", "raw5"), # 0806020009831c001d0729c20cc20ea1000dc210000fc2c0
        0x29: ("optional_param", "bool"), # we see those 4 parameters
        0x0C: ("state", "bool"),
        0x0E: ("custom_label", "string"),
        0x0D: ("flag1", "bool"),
        0x10: ("led_color", "byte"),
        0x0F: ("flag2", "bool"),
    }

    def __init__(self):
        self.label = '--'
        self.custom_label = '--'
        self.led_color = -1


class FootSwitchInfo:

    def __init__(self, hex_string: str, debug=False):
        self.raw = hex_string
        self.children = []
        self.debug = debug
        self._parse()

    # --------------------------------------------------
    # DEBUG HELPERS
    # --------------------------------------------------

    def _dbg(self, cursor, msg):
        if not self.debug:
            return

        context = 10
        start = max(0, cursor - context)
        end = min(len(self.raw), cursor + context)

        snippet = self.raw[start:end].hex(" ")
        pointer = "   " * (cursor - start) + "^^"

        print(f"\n[pos={cursor:03}] {msg}")
        print(snippet)
        print(pointer)

    def _log_field(self, marker, name, value):
        if not self.debug:
            return
        print(f"    Parsed {hex(marker)} → {name} = {value}")

    # --------------------------------------------------
    # PARSER
    # --------------------------------------------------

    def _parse(self):
        data = self.raw
        cursor = 0

        # ---- HEADER ----
        header = data[cursor]
        self._dbg(cursor, f"Reading header {hex(header)}")
        cursor += 1

        if data[0] == 0xc0:
            child = FootSwitchChild()
            self.children.append(child)
            return

        if (header & 0xF0) != 0x90:
            raise ValueError("Invalid header")

        child_count = header & 0x0F
        print(f"\n== Expecting {child_count} children ==") if self.debug else None

        # ---- CHILDREN ----
        for child_index in range(child_count):

            if data[cursor] != 0x87:
                raise ValueError("Expected child marker 0x87")

            self._dbg(cursor, f"Entering child #{child_index}")
            cursor += 1

            child = FootSwitchChild()

            while cursor < len(data):

                if data[cursor] == 0x87:
                    self._dbg(cursor, "Next child detected")
                    break

                marker = data[cursor]
                self._dbg(cursor, f"Reading marker {hex(marker)}")
                cursor += 1

                if marker not in FootSwitchChild.FIELD_MAP:
                    raise ValueError(f"Unknown marker {hex(marker)}")

                field_name, field_type = FootSwitchChild.FIELD_MAP[marker]

                # ---- TYPE HANDLING ----

                if field_type == "byte":
                    value = data[cursor]
                    cursor += 1
                    # in very (very) rare cases I found an addition byte with value 0x00 which seems to be useless.
                    # correct example:
                    # 9187 -    0a 00
                    # 		    0b 840003
                    # 		    05 a5 4e6f746500
                    # wrong example:
                    # 9187 -    0a 0000                 <-- see additional 0x00
                    # 		    0b 840003
                    # 		    05 a5 4e6f746500
                    # we need to jump over this byte in oder to make the structure fit again.
                    if marker == 0x0a and data[cursor] == 0x00:
                        cursor += 1

                elif field_type == "raw3":
                    value = data[cursor:cursor+3]
                    cursor += 3

                elif field_type == "raw5":
                    value = data[cursor:cursor+5]
                    cursor += 5

                elif field_type == "bool":
                    raw = data[cursor]
                    cursor += 1

                    if raw == 0xC2:
                        value = True
                    elif raw == 0xC3:
                        value = False
                    else:
                        raise ValueError("Invalid bool encoding")

                elif field_type == "string":
                    length_byte = data[cursor]
                    cursor += 1

                    # strlen = length_byte & 0x0F
                    # Length of the values are stored in one byte.
                    # a5 => 5 characters, a0 => 10 characters, aa => 11 characters and so on.
                    # I don't know yet, wie 0xaf is not used for 16 characters but one example with 16 chars
                    # used 0xb0 => 16 characters as coding. Maybe 0xaf should not be part of a message??
                    # thus, the values of 0xa0 needs to subtracted from MSB
                    strlen = (length_byte & 0xF0) - 0xA0 + (length_byte & 0x0F)
                    raw_bytes = data[cursor:cursor+strlen]
                    cursor += strlen

                    if cursor < len(data) and data[cursor] == 0x00:
                        cursor += 1

                    value = raw_bytes.decode("ascii", errors="ignore")

                elif isinstance(field_type, tuple) and field_type[0] == "until_marker_bool":
                    stop_marker = field_type[1]
                    start = cursor

                    self._dbg(cursor, "Scanning for stop condition (marker + bool)")

                    while cursor < len(data) - 1:
                        if (
                            data[cursor] == stop_marker and
                            data[cursor + 1] in (0xC2, 0xC3)
                        ):
                            self._dbg(cursor, "Stop condition found")
                            break
                        cursor += 1

                    value = data[start:cursor]

                else:
                    raise ValueError("Unknown field type")

                setattr(child, field_name, value)
                self._log_field(marker, field_name, value)

            self.children.append(child)
            self._dbg(cursor, f"Finished child #{child_index}")


class HxPreset:
    def __init__(self, data_in: str, preset_no=-1, preset_name=''):
        self.data_in = data_in
        self.switch_info = []
        self.slot_info = []
        self.preset_no = preset_no
        self.preset_name = preset_name
        self._parse()

    def _parse(self):
        self.switch_info = []
        self.slot_info = []

        # switch infos
        fs_info_data = self.extract_footswitch_sections(self.data_in)

        for data in fs_info_data:
            switch_info = FootSwitchInfo(data, debug=False)
            self.switch_info.append(switch_info)
            # print(switch_info)

        # slot infos
        slot_data = self.extract_slot_sections(self.data_in)

        for data in slot_data:
            slot_info = SlotInfo(data, debug=False)
            self.slot_info.append(slot_info)
            # print(slot_info.parameter_a)
            # print(slot_info.parameter_b)

    @staticmethod
    def extract_footswitch_sections(data):
        begin = data.index('0895')
        assert (begin >= 0)
        data = data[begin + 4:]
        end = data.index('049a')
        assert (end >= 0)
        data = data[:end]
        data = bytes.fromhex(data)
        # look for 9187, 9287, 9387 and so on
        footswitch_sections_idx = []
        cursor = 0
        begin = -1
        end = -1

        # divide into 5 switch information
        for peek_cursor in range(0, len(data)):
            # print("{:x} {:x}".format(data[peek_cursor], data[peek_cursor+1]))
            if (data[peek_cursor] & 0xF0) == 0x90 and data[peek_cursor + 1] == 0x87:
                # begin of a new footswitch info section
                if begin != -1:
                    footswitch_sections_idx.append((begin, peek_cursor))
                    begin = -1
                    end = -1
                begin = peek_cursor
            elif data[peek_cursor] == 0xc0:
                # empty slot
                if begin != -1:
                    footswitch_sections_idx.append((begin, peek_cursor))
                begin = end = peek_cursor
                footswitch_sections_idx.append((begin, end + 1))
                begin = -1
                end = -1
        if begin > -1:
            footswitch_sections_idx.append((begin, len(data)))

        footswitch_sections_data = []
        for section in footswitch_sections_idx:
            footswitch_sections_data.append(data[section[0]:section[1]])

        return footswitch_sections_data

    @staticmethod
    def extract_slot_sections(data):
        begin = data.index('8215')
        assert (begin >= 0)
        data = data[begin + 14:]
        end = data.index('0895')
        assert (end >= 0)
        data = data[:end]
        data = bytes.fromhex(data)
        # look for 9187, 9287, 9387 and so on
        slot_sections_idx = []
        cursor = 0
        begin = -1
        end = -1

        # divide into 5 switch information
        for peek_cursor in range(0, len(data)):
            # print("{:x} {:x}".format(data[peek_cursor], data[peek_cursor+1]))
            if (data[peek_cursor] & 0xF0) == 0x80 and data[peek_cursor + 1] == 0x13:
                # begin of a new footswitch info section
                if begin != -1:
                    slot_sections_idx.append((begin, peek_cursor))
                    begin = -1
                    end = -1
                begin = peek_cursor
        if begin > -1:
            slot_sections_idx.append((begin, len(data)))

        slot_sections_data = []
        for section in slot_sections_idx:
            slot_sections_data.append(data[section[0]:section[1]])

        return slot_sections_data

    def to_string(self):

        slots_idx = [1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15, 16, 17, 18]

        bank = int(self.preset_no / 3) + 1
        num = self.preset_no % 3 + 1
        letter = chr(64 + num)
        print("---------------------------------------------------------------------------")
        print('Preset {}{} ({}): {}'.format(bank, letter, self.preset_no, self.preset_name))
        print("---------------------------------------------------------------------------")

        print("Slots: ")
        for slot_idx in slots_idx:
            module_name_info = self.slot_info[slot_idx].id_to_names()
            beauty_str = ''
            if module_name_info[0] == '' and module_name_info[1] == '':
                beauty_str += '[{}]: -'.format(slot_idx)
            elif module_name_info[0] != '':
                beauty_str = '[{}]: {}'.format(slot_idx, module_name_info[0][1].replace(' (mono)', '').replace(' (stereo)', ''))
                beauty_str += ' ({})'.format(module_name_info[0][0])

            if module_name_info[1] != '':
                beauty_str += ', {}'.format(module_name_info[1][1].replace(' (mono)', '').replace(' (stereo)', ''))
                beauty_str += ' ({})'.format(module_name_info[1][0])

            print(beauty_str)

        print("")
        print("Switches: ")
        for i in range(0, 5):
            for j, child in enumerate(self.switch_info[i].children):
                if j == 0:
                    print('[{}]: '.format(i + 1), end='')
                else:
                    print('     ', end='')
                print('{}, {}, {}'.format(child.label, child.custom_label,
                                                FootSwitchChild.LED_COLORS[child.led_color]))

def main(args):
    file_path = "../ideas/20260226_all_data.txt"

    preset_data_list = []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                preset_data_list.append(line.rstrip("\n"))

        print("File successfully imported.")
        print(f"Number of lines: {len(preset_data_list)}")

    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"Error reading the file: {e}")

    preset_data = preset_data_list[0]
    hx_preset = HxPreset(preset_data)
    # hx_preset.to_string()

    for i, preset_data in enumerate(preset_data_list):
        hx_preset = HxPreset(preset_data, preset_no=i)
        hx_preset.to_string()

if __name__ == '__main__':
    main(sys.argv)