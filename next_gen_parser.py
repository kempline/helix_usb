# data = "94870a000b84000305a54e6f74650006ce0007100c07c20cc30ea1000dc210040fc3870a010b85000105a74368726f6d650006ce0003000b07c208010cc30ea1000dc210040fc3870a020b85000105ac446f75626c652054616e6b0006ce00ff2d0007c308060cc30ea1000dc210040fc3870a030b85000105ad566f6c756d6520506564616c0006cdff8007c308070cc30ea1000dc210040fc3"\
data = "91870a000b84000305aa434320546f67676c650006ce0007100c07c20cc20ea84372756e63683e000dc310060fc3"



class FootSwitchChild:
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


def extract_footswitch_sections(data):
    begin = data.index('0895')
    assert(begin >= 0)
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
        if (data[peek_cursor] & 0xF0) == 0x90 and data[peek_cursor+1] == 0x87:
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
            footswitch_sections_idx.append((begin, end+1))
            begin = -1
            end = -1
    if begin > -1:
        footswitch_sections_idx.append((begin, len(data)))

    footswitch_sections_data = []
    for section in footswitch_sections_idx:
        footswitch_sections_data.append(data[section[0]:section[1]])

    return footswitch_sections_data


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


preset_data = preset_data_list[86]
print(preset_data)
fs_info_data = extract_footswitch_sections(preset_data)

for data in fs_info_data:
    print(data)
    fsi = FootSwitchInfo(data, debug=True)
    print(fsi)


for i, preset_data in enumerate(preset_data_list):
    bank = int(i / 3) + 1
    num = i % 3 + 1
    letter = chr(64 + num)
    print('Preset {}{} ({}): '.format(bank, letter, i))
    fs_info_data = extract_footswitch_sections(preset_data)
    for j, data in enumerate(fs_info_data):
        fsi = FootSwitchInfo(data, debug=False)
        for child in fsi.children:
            print("S{}: {}, {}, {}".format(j+1, child.label[:-1], child.custom_label[:-1], child.led_color))
