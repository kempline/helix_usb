from utils.formatter import format_1, ieee754_to_rendered_str


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
        self.label = '--'
        self.custom_label = '--'
        self.led_color = -1
        self.parameter_a = []
        self.parameter_b = []
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
                    print("until_end triggered")
                    start = cursor
                    cursor = len(data)
                    value = data[start:cursor]
                    beauty_str = ''.join('{:02x}'.format(x) for x in value)
                    print(beauty_str)

                    num_params = value[2]
                    params, bytes_processed = self.read_params(num_params, value[7:])
                    self.parameter_b = params

                else:
                    raise ValueError("Unknown field type")

                setattr(self, field_name, value)
                self._log_field(marker, field_name, value)

            self._dbg(cursor, f"Finished child #{child_index}")


def extract_slot_sections(data):
    begin = data.index('8215')
    assert(begin >= 0)
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
        if (data[peek_cursor] & 0xF0) == 0x80 and data[peek_cursor+1] == 0x13:
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


file_path = "./ideas/20260226_all_data.txt"

preset_data_list = []

try:
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            preset_data_list.append(line.rstrip("\n"))

    print("Datei erfolgreich eingelesen.")
    print(f"Anzahl Zeilen: {len(preset_data_list)}")

except FileNotFoundError:
    print(f"Datei nicht gefunden: {file_path}")
except Exception as e:
    print(f"Fehler beim Einlesen der Datei: {e}")


preset_data = preset_data_list[56]
print(preset_data)
fs_info_data = extract_slot_sections(preset_data)


for data in fs_info_data:
    print(data)
    fsi = SlotInfo(data, debug=True)
    print(fsi.parameter_a)
    print(fsi.parameter_b)
    print(fsi)


for i, preset_data in enumerate(preset_data_list):
    bank = int(i / 3) + 1
    num = i % 3 + 1
    letter = chr(64 + num)
    print('Preset {}{} ({}): '.format(bank, letter, i))
    fs_info_data = extract_slot_sections(preset_data)
    for j, data in enumerate(fs_info_data):
        fsi = SlotInfo(data, debug=False)
        print(fsi.parameter_a)
        print(fsi.parameter_b)
        # for child in fsi.children:
        #    print("S{}: {}, {}, {}".format(j+1, child.label[:-1], child.custom_label[:-1], child.led_color))
