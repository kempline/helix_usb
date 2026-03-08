import sys
import csv
import re

from utils.formatter import format_1, ieee754_to_rendered_str
from modules import modules


class FsInfoEntry:
    def __init__(self):
        self.command_label = 'not_set'
        self.custom_label = 'not_set'
        self.led_color_id = 0


class FsInfo:
    LED_COLORS = [
        'off', 'white', 'red', 'dark_orange', 'light_orange', 'yellow', 'green', 'turquoise', 'blue', 'violet',
        'pink', 'auto_color']

    def __init__(self, no=-1):
        self.footswitch_no = no
        self.command_list = []

    def to_string(self):
        if len(self.command_list) == 0:
            return str("{}:{} (cmd), {} (custom), LED: {}".format(self.footswitch_no,
                                                                  "none", "none", FsInfo.LED_COLORS[0]))
        return_str = ''
        for cmd in self.command_list:
            if return_str != '':
                return_str += '\n\t'
            return_str += str("{}:{} (cmd), {} (custom), LED: {}".format(
            self.footswitch_no, cmd.command_label, cmd.custom_label, FsInfo.LED_COLORS[cmd.led_color_id]))
        return return_str


class SlotInfo:
    def __init__(self):
        self.slot_no = 0
        self.on_off_state = 0

    def __eq__(self, other):
        if isinstance(other, SlotInfo) is False:
            return False
        if other.slot_no != self.slot_no or \
            other.on_off_state != self.on_off_state:
            return False
        return True

    def category(self):
        return None

    def to_string(self):
        return "SlotInfo to_string - not implemented in abstract class SlotInfo"


class EmptySlotInfo(SlotInfo):
    def __init__(self):
        SlotInfo.__init__(self)
        self.module_id = '14c0'

    def __eq__(self, other):
        if isinstance(other, EmptySlotInfo) is False:
            return False
        if other.slot_no != self.slot_no or \
            other.on_off_state != self.on_off_state or \
            other.module_id != self.module_id:
            return False
        return True

    def category(self):
        return None

    def to_string(self):
        # return '\'Standard Module: ' + self.module_id + ' - ' + str(self.params)
        return str(self.slot_no) + ':<empty>'


class IoSlotInfo(SlotInfo):
    def __init__(self):
        SlotInfo.__init__(self)
        self.module_id = -1
        self.params = []

    def __eq__(self, other):
        if not isinstance(other, IoSlotInfo):
            return False
        if other.slot_no != self.slot_no or \
            other.on_off_state != self.on_off_state or \
            other.module_id != self.module_id or \
            other.params != self.params:
            return False
        return True

    def category(self):
        return None

    def to_string(self):
        desc = 'unknown'
        if self.module_id == '0014':
            desc = 'top row in (left)'
        elif self.module_id == '0114':
            desc = 'top row out (right)'
        elif self.module_id == '0214':
            desc = 'bottom row in (left)'
        elif self.module_id == '0314':
            desc = 'bottom row out (right)'
        return str(self.slot_no) + ':I/O-Slot - ' + desc + ' (' + str(self.params) + ')'


class StandardSlotInfo(SlotInfo):
    def __init__(self):
        SlotInfo.__init__(self)
        self.module_id = ''
        self.params = []

    def __eq__(self, other):
        if isinstance(other, StandardSlotInfo) is False:
            return False
        if other.slot_no != self.slot_no or \
            other.on_off_state != self.on_off_state or \
            other.module_id != self.module_id or \
            other.params != self.params:
            return False
        return True

    def category(self):
        try:
            description = modules[self.module_id]
            return description[0]
        except KeyError:
            print("ERROR: can't find module in modules: " + str(self.module_id))
            return None

    def to_string(self):
        # return '\'Standard Module: ' + self.module_id + ' - ' + str(self.params)
        try:
            description = modules[self.module_id]
            return str(self.slot_no) + ":" + description[0] + ' (' + description[1] + ')'  + str(self.params)
        except KeyError:
            print("ERROR: can't find module in modules: " + str(self.module_id))
            return str(self.slot_no) + ':NO MATCH FOR ' + self.module_id


class CabsDualSlotInfo(SlotInfo):
    def __init__(self):
        SlotInfo.__init__(self)
        self.cab1_id = ''
        self.cab2_id = ''
        self.cab1_params = []
        self.cab2_params = []

    def __eq__(self, other):
        if isinstance(other, CabsDualSlotInfo) is False:
            return False
        if other.cab1_id != self.cab2_id:
            return False
        if other.cab2_id != self.cab2_id:
            return False
        return True

    def category(self):
        return "Cab"

    def to_string(self):
        return '\'Cab1: ' + self.cab1_id + ', Cab2: ' + self.cab2_id + ' - Cab1: ' + str(self.cab1_params) + ', Cab2: ' + str(self.cab2_params)
        # return str(self.module_id)


class AmpCabSlotInfo(SlotInfo):
    def __init__(self):
        SlotInfo.__init__(self)
        self.amp_id = ''
        self.cab_id = ''
        self.amp_params = []
        self.cab_params = []

    def __eq__(self, other):
        if isinstance(other, AmpCabSlotInfo) is False:
            return False
        if other.amp_id != self.amp_id:
            return False
        if other.cab_id != self.cab_id:
            return False
        return True

    def category(self):
        return "Amp+Cab"

    def to_string(self):
        try:
            amp_description = modules[self.amp_id]
            cab_description = modules[self.cab_id]
            return str(self.slot_no) + ":Amp+Cab (" + amp_description[1] + str(self.amp_params) + ' + ' + cab_description[1]  + str(self.cab_params) + ')'
        except KeyError:
            print("ERROR: can't find module in modules: " + str(self.module_id))
            return str(self.slot_no) + ':NO MATCH FOR Amp: ' + self.amp_id + ', Cab: ' + self.cab_id

        # return '\'Amp: ' + self.amp_id + ', Cab: ' + self.amp_id + ' - Amp-Parameter: ' + str(self.amp_params) + ', Cab-Parameter: ' + str(self.cab_params)
        return str(self.amp_id + '1a' + self.cab_id)

'''
def slot_splitter(val):
    slots = val.split('8213')
    if len(slots) > 1:
        slots = slots[1:]
    for i, slot in enumerate(slots):
        if i != 3:
           continue
        # print(str(i) + ': ' + slot)
        values = slot.split('ca')
        effect_id = None
        for value in values:
            if len(value) == 8:
                ieee_val = ieee754_to_rendered_str(value)
                # print(ieee_val)
            else:
                try:
                    idx = value.index('1aff09')
                    
                    # print("\'", end="")
                    # for i in range(idx-4, idx):
                    #     print(value[i], end='')
                    # print()
                    #
                    print('\'' + value[idx-4:idx])
                    return
                except ValueError as _e:
                    pass
    print("No slot id found: " + value)
'''
'''
def parse_parameter(data_stream):
    params = []
    while len(data_stream) >= 4:
        if data_stream.startswith('ca'):
            # ieee754 representation
            hex_value_string = data_stream[2:10]
            data_stream = data_stream[10:]
            floating_point_rep = ieee754_to_rendered_str(hex_value_string)
            params.append(floating_point_rep)

        elif data_stream.startswith('c2'):
            data_stream = data_stream[2:]
            params.append('Opt 1')
            pass
        elif data_stream.startswith('c3'):
            data_stream = data_stream[2:]
            params.append('Opt 2')
            pass
        elif data_stream.startswith('06c2'):
            # maybe we reached the end here?
            data_stream = data_stream[4:]
        else:
            simple_int_value = data_stream[0:2]
            params.append(simple_int_value)
            data_stream = data_stream[2:]
    return params

'''
'''
def parse_amp_and_cab_slot(slot_data):

    try:
        idx = slot_data.index('09120a')
    except ValueError:
        return None

    slot_info = AmpCabSlotInfo()
    ac_data = slot_data[16:idx]

    # special case for Amp Line 6 Doom Guitar Line 6 Original which has the id 1a (and 1a is also the splitter between
    # amp and cab)
    if ac_data.startswith('1a1a') and len(ac_data) == 6:
        ac_parts = ['1a', ac_data[4:6]]
    else:
        ac_parts = ac_data.split('1a')
    if len(ac_parts) != 2:
        print("ERROR: parts for amp+cab modules have unexpected length")
        return None
    slot_info.amp_id = ac_parts[0]
    slot_info.cab_id = ac_parts[1]
    try:
        idx_of_param_start = slot_data.index('ca')
        values_containing_data = slot_data[idx_of_param_start:]
    except ValueError:
        pass

    if len(values_containing_data) == 0:
        print("ERROR: No range containing data in slot: " + str(slot_idx))
        return None

    try:
        idx_amp_cab_parameter_sep = values_containing_data.index('0c83020603050496')
        amp_params_stream = values_containing_data[:idx_amp_cab_parameter_sep]
        cab_params_stream = values_containing_data[idx_amp_cab_parameter_sep + 16:]
        amp_params = parse_parameter(amp_params_stream)
        cab_params = parse_parameter(cab_params_stream)
        slot_info.amp_params = amp_params
        slot_info.cab_params = cab_params
        return slot_info
    except ValueError:
        print("ERROR: No amp/cab parameter separator found in slot data")
        return None
'''
'''
def parse_dual_cab_slot(slot_data):

    try:
        idx = slot_data.index('09100ac')
    except ValueError:
        return None

    slot_info = CabsDualSlotInfo()
    ac_data = slot_data[16:idx]

    
    # try:
    #     idx_od_cd = ac_data.index('cd')
    #     ac_data_tmp = ac_data[0:idx_od_cd]
    #     ac_data_tmp += ac_data[idx_od_cd + 4:]
    #     ac_data = ac_data_tmp
    # except ValueError:
    #     pass
    
    # print(slot_data)

    if ac_data.startswith('1a1a') and len(ac_data) == 6:
        ac_parts = ['1a', ac_data[4:6]]
    else:
        ac_parts = ac_data.split('1a')
    if len(ac_parts) != 2:
        print("ERROR: parts for amp+cab modules have unexpected length")
        return None
    slot_info.cab1_id = ac_parts[0]
    slot_info.cab2_id = ac_parts[1]

    try:
        idx_of_param_start = slot_data.index('ca')
        values_containing_data = slot_data[idx_of_param_start:]
    except ValueError:
        pass

    if len(values_containing_data) == 0:
        print("ERROR: No range containing data in slot: " + str(0))
        return None

    try:
        idx_amp_cab_parameter_sep = values_containing_data.index('0c83020603050496')
        cab1_params_stream = values_containing_data[:idx_amp_cab_parameter_sep]
        cab2_params_stream = values_containing_data[idx_amp_cab_parameter_sep + 16:]
        cab1_params = parse_parameter(cab1_params_stream)
        cab2_params = parse_parameter(cab2_params_stream)
        slot_info.cab1_params = cab1_params
        slot_info.cab2_params = cab2_params
        return slot_info
    except ValueError:
        print("ERROR: No amp/cab parameter separator found in slot data")
        return None
'''
'''
def parse_standard_module_slot(slot_data):
    try:
        idx = slot_data.index('1aff09')
        # -----------------------------------------------------------------
        # Standard module
        # -----------------------------------------------------------------
        if idx < 4:
            # print("ERROR: Can't read module id: " + str(slot_data))
            print("ERROR: Can't read module id")
            return None

        slot_info = StandardSlotInfo()
        ac_data = slot_data[16:idx]

        on_off_state = slot_data[idx + 11]
        if on_off_state == '3':
            slot_info.on_off_state = 1
        elif on_off_state == '2':
            slot_info.on_off_state = 0
        else:
            print("ERROR: Unexpected slot on/off state")

        # remove 19
        slot_info.module_id = ac_data

        # find end tag in slot data
        try:
            idx_end_tag = slot_data.index('0c83020003000490')

            if idx_end_tag < idx:
                print("ERROR: Unexpected value for end tag index: " + str(idx_end_tag))
                return None
            values_containing_data = slot_data[idx + 28:idx_end_tag]
            params = parse_parameter(values_containing_data)
            slot_info.params = params
        except ValueError:
            idx = -1
        return slot_info

    except ValueError:
        return None
'''
'''
def slot_splitter_2(val):
    import re

    pattern = r'(?=(?:82|83)13)'
    matches = [m.start() for m in re.finditer(pattern, val)]

    slots = []
    for i in range(len(matches)):
        start = matches[i] + 4
        end = matches[i + 1] if i + 1 < len(matches) else len(val)
        slots.append(val[start:end])

    
    # data = bytes.fromhex(val)

    # slots = []
    # i = 0

    # while i < len(data) - 1:
    #     if (data[i] in (0x82, 0x83)) and data[i + 1] == 0x13:
    #         start = i
    #         # nächstes Vorkommen suchen
    #         j = i + 2
    #         while j < len(data) - 1:
    #             if (data[j] in (0x82, 0x83)) and data[j + 1] == 0x13:
    #                 break
    #             j += 1
    #         slots.append(data[start:j])
    #         i = j
    #     else:
    #         i += 1

    # slots = val.split('8213')

    # find first slot starting with either 06 or 08
    slot_1_idx = -1
    for i, slot in enumerate(slots):
        if slot.startswith('06') or slot.startswith('08'):
        # if slot[2] in (0x06, 0x08):
            slot_1_idx = i
            break

    if slot_1_idx == -1:
        print("ERROR: No slot 1 found in preset data")
        return

    if slot_1_idx == 0:
        print("ERROR: Slot 1 index is 0 - there can't be a Chain 1 IN slot")
        return

    # remove slots we don't understand or we don't need
    slots = slots[slot_1_idx-1:]
    slots = slots[0:20]
    # we must have 20 slots now

    if len(slots) != 20:
        print("ERROR: Expected exactly 20 slots here, got: " + str(len(slots)))
        return

    if slots[0].startswith('00') is False:
        print("ERROR: Expected slot 0 (Chain 1 Input) to start with 00")
    if slots[9].startswith('01') is False:
        print("ERROR: Expected slot 9 (Chain 1 Master) to start with 00")
    if slots[10].startswith('02') is False:
        print("ERROR: Expected slot 10 (Chain 2 Input) to start with 00")
    if slots[19].startswith('03') is False:
        print("ERROR: Expected slot 19 (Chain 2 Master) to start with 00")

    assignable_slots = [1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15, 16, 17, 18]

    for slot_idx in assignable_slots:
        if (slots[slot_idx].startswith('06') or slots[slot_idx].startswith('08')) is False:
            print("ERROR: Expected slot " + str(slot_idx) + " to start with 06 or 08")

    slot_infos = []
    for slot_idx in assignable_slots:
        if len(slots) <= slot_idx:
            continue
        slot_data = slots[slot_idx]
        if slot_data == '0814c0':
            # print(str(slot_idx) + ' is empty')
            empty_slot_info = EmptySlotInfo()
            empty_slot_info.slot_no = slot_idx
            slot_infos.append(empty_slot_info)
            continue
        # print(slot_data)
        slot_info = parse_standard_module_slot(slot_data)
        if slot_info is None:
            slot_info = parse_amp_and_cab_slot(slot_data)

        if slot_info is None:
            slot_info = parse_dual_cab_slot(slot_data)
            if slot_info is None:
                print("ERROR: Cannot read slot info: " + str(slot_idx))
                continue

        slot_info.slot_no = slot_idx
        slot_infos.append(slot_info)
    return slot_infos
'''

def my_byte_cmp(left, right, length):
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


def slot_extract(data):
    # slots begin at 16dc0014
    parts = data.split('16dc0014')
    assert(len(parts) == 2)

    slot_part_with_tail = parts[1]

    parts = slot_part_with_tail.split('118408cc97')
    assert (len(parts) == 2)
    slots, bytes_read = slot_reader(parts[0])
    return slots


def read_params(num_params, data):
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
        assert (len(data) > size_of_data*2)
        param = data[:size_of_data*2]
        params.append(param)
        bytes_read += size_of_data*2

    return params, bytes_read


def slot_0_reader(data):
    bytes_read = 0
    num_params = int(data[17], 16)
    bytes_read += 18
    params, bytes_read_in = read_params(num_params, data[18:])
    bytes_read += bytes_read_in

    slot = IoSlotInfo()
    slot.params = params
    return slot, bytes_read


def slot_2_reader(data):
    '''
    Unfortunately just a look-up for the next slot.
    Was unable to understand the structure yet
    :param data:
    :return:
    '''
    idx_8213 = 100000
    idx_8313 = 100000
    try:
        idx_8213 = data.index('8213')
        idx_8313 = data.index('8313')
    except ValueError as _:
        pass

    slot = IoSlotInfo()
    return slot, min(idx_8213, idx_8313)


def slot_3_reader(data):
    '''
    Unfortunately just a look-up for potential parameter start
    Was unable to understand the structure yet
    :param data:
    :return:
    '''
    bytes_read = 0
    num_params = int(data[21], 16)
    bytes_read += 22

    params, bytes_read_in = read_params(num_params, data[22:])
    bytes_read += bytes_read_in

    slot = IoSlotInfo()
    slot.params = params
    return slot, bytes_read


def amp_cab_reader(data):
    bytes_read = 0
    slot_info_start_idx = data.index('85188317') + 8
    bytes_read += slot_info_start_idx

    # jump over the next 2 values (either c2 or c3)
    bytes_read += 2

    type_marker = data[bytes_read:].index('19')
    assert (type_marker == 0)
    type_start_idx = type_marker + 2
    type_end_idx = data[bytes_read:].index('09')
    type_amp_and_cab = data[bytes_read + type_start_idx: bytes_read + type_end_idx]
    type_amp_cab_split = type_amp_and_cab.split('1a')
    assert(len(type_amp_cab_split) == 2)

    bytes_read += (
            1 +  # 19
            len(type_amp_cab_split[0]) +
            1 + # 1a
            len(type_amp_cab_split[1])
    )
    # On/Off state
    # jump over next 6 characters - no glue what they do
    bytes_read += 6

    slot_on_off = data[bytes_read:]
    if slot_on_off[2] == 'c' and slot_on_off[3] == '2':
        slot_on_off = False
    elif slot_on_off[2] == 'c' and slot_on_off[3] == '3':
        slot_on_off = True

    bytes_read += 4

    # look for 0b83 - AMP
    data_next = data[bytes_read:]
    assert (data_next.startswith('0b83'))

    # jump over the next 6 values
    bytes_read += 6

    num_params = int(data[bytes_read], 16) * 16 + int(data[bytes_read + 1], 16)
    bytes_read += 2

    # jump over the next 8 values
    bytes_read += 8

    data_next = data[bytes_read:]
    params_amp, bytes_read_in = read_params(num_params, data[bytes_read:])
    bytes_read += bytes_read_in

    # look for 0c83 - CAB
    data_next = data[bytes_read:]
    assert (data_next.startswith('0c83'))

    # jump over the next 6 values
    bytes_read += 6

    num_params = int(data[bytes_read], 16) * 16 + int(data[bytes_read + 1], 16)
    bytes_read += 2

    # jump over the next 8 values
    bytes_read += 8

    data_next = data[bytes_read:]
    params_cab, bytes_read_in = read_params(num_params, data[bytes_read:])
    bytes_read += bytes_read_in

    data_next = data[bytes_read:]

    slot = AmpCabSlotInfo()
    slot.on_off_state = slot_on_off
    slot.amp_id = type_amp_cab_split[0]
    slot.cab_id = type_amp_cab_split[1]
    slot.amp_params = params_amp
    slot.cab_params = params_cab

    # slot.module_id = type
    return slot, bytes_read

def user_slot_reader(data):
    bytes_read = 0

    slot_info_start_idx = data.index('85188317')
    bytes_read += (slot_info_start_idx + 8)
    # local_data_front = data
    # local_data_front = local_data_front[slot_info_start_idx:]

    if data[bytes_read:].startswith('c319'):
        # Amp + Cab'
        return amp_cab_reader(data)


    type_marker = data[bytes_read:].index('c219')
    assert(type_marker == 0)

    type_start_idx = type_marker + 4
    type_end_idx = data[bytes_read:].index('09')

    type = data[bytes_read+type_start_idx : bytes_read+type_end_idx]
    type_split = type.split('1a')

    bytes_read += 4  # c219
    bytes_read += len(type_split[0])
    bytes_read += 2  # 1a
    bytes_read += len(type_split[1]) # always ff in standard slots

    # jump over next 4 characters - no glue what they do
    bytes_read += 4

    slot_on_off = data[bytes_read:]
    if slot_on_off[2] == 'c' and slot_on_off[3] == '2':
        slot_on_off = False
    elif slot_on_off[2] == 'c' and slot_on_off[3] == '3':
        slot_on_off = True

    bytes_read += 4

    # jump over the next 6 values
    bytes_read += 6

    num_params = int(data[bytes_read], 16) * 16 + int(data[bytes_read+1], 16)
    bytes_read += 2

    # jump over the next 8 values
    bytes_read += 8

    params, bytes_read_in = read_params(num_params, data[bytes_read:])
    bytes_read += bytes_read_in

    # description = modules[type]
    # print(description + params)

    # expecting end of slot '0c83020003000490'
    if type_split[0] not in ['cc95', 'cc96']: # impulse responses don't have such an ending tag
        sdfg = data[bytes_read:]
        assert(data[bytes_read:].startswith('0c83020003000490'))
        bytes_read += 16

    slot = StandardSlotInfo()
    slot.on_off_state = slot_on_off
    slot.params = params
    slot.module_id = type_split[0]
    return slot, bytes_read

def slot_reader(data):
    bytes_read = 0
    slots = list()
    local_data_front = data

    while len(local_data_front) > 0:

        if not (local_data_front.startswith('8213') or local_data_front.startswith('8313')):
            print("ERROR: Slot should start with 8213 or 8313")
            return None, 0

        bytes_read += 4
        local_data_front = data[bytes_read:]

        if local_data_front.startswith('00'):
            slot, bytes_read_in = slot_0_reader(local_data_front[8:])
            slot.slot_no = len(slots)
            slot.module_id = local_data_front[0] + local_data_front[1] + '14'
            slots.append(slot)
            bytes_read += 8
            bytes_read += bytes_read_in
            local_data_front = data[bytes_read:]
        elif local_data_front.startswith('01'):
            slot, bytes_read_in = slot_0_reader(local_data_front[8:])
            slot.module_id = local_data_front[0] + local_data_front[1] + '14'
            slot.slot_no = len(slots)
            slots.append(slot)
            bytes_read += 8
            bytes_read += bytes_read_in
            local_data_front = data[bytes_read:]
        elif local_data_front.startswith('02'):
            slot, bytes_read_in = slot_2_reader(local_data_front[8:])
            slot.module_id = local_data_front[0] + local_data_front[1] + '14'
            slot.slot_no = len(slots)
            slots.append(slot)
            bytes_read += 8
            bytes_read += bytes_read_in
            local_data_front = data[bytes_read:]
        elif local_data_front.startswith('03'):
            slot, bytes_read_in = slot_3_reader(local_data_front[8:])
            slot.module_id = local_data_front[0] + local_data_front[1] + '14'
            slot.slot_no = len(slots)
            slots.append(slot)
            bytes_read += 8
            bytes_read += bytes_read_in
            local_data_front = data[bytes_read:]
        elif local_data_front.startswith('06'):
            # Standard-Slot
            slot, bytes_read_in = user_slot_reader(local_data_front[2:])
            slot.slot_no = len(slots)
            slots.append(slot)
            bytes_read += 2
            bytes_read += bytes_read_in
            local_data_front = data[bytes_read:]
        elif local_data_front.startswith('08'):
            # empty slot
            slot = EmptySlotInfo()
            slot.slot_no = len(slots)
            slots.append(slot)
            bytes_read += 6
            local_data_front = data[bytes_read:]
        '''
        elif local_data_front.startswith('06'):
            # Amplifier
            slot, bytes_read_in = user_slot_reader(local_data_front[12:])
            slots.append(slot)
            bytes_read += 12
            bytes_read += bytes_read_in
            local_data_front = data[bytes_read:]
        '''


    return slots, bytes_read


def fs_info_extract(data):
    fs_info_list = []

    begin = data.index('0895') # was 07020895
    char_processed = begin + 4
    assert (begin > 0)

    while data[char_processed:].startswith('c0'):
        # slot empty
        fs_info_list.append(FsInfo(len(fs_info_list) + 1))
        char_processed += 2
        if len(fs_info_list) == 5:
            return fs_info_list

    while len(data[char_processed:]) > 0:
        fs_start = data[char_processed:]
        processed_local = 0
        match_fs_start_tag = re.search(r"9.87", fs_start)
        fs_info = FsInfo(no=len(fs_info_list) + 1)

        if data[char_processed:].startswith('c0'):
            fs_info_list.append(FsInfo(len(fs_info_list) + 1))
            processed_local += 2  # c0

        elif len(match_fs_start_tag.regs) == 1:
            assert match_fs_start_tag.start() == 0
            processed_local += 4
            features_of_switch = int(fs_start[1], 16)
            for i in range(features_of_switch):
                search_area = fs_start[processed_local:processed_local+200]

                match_size_txt1 = re.search(r"05[ab].", search_area)
                assert len(match_size_txt1.regs) == 1
                num_char_txt1 = search_area[match_size_txt1.start() : match_size_txt1.end()]
                assert len(num_char_txt1) == 4
                num_letters_for_label = int(num_char_txt1[3], 16)
                idx_txt1 = match_size_txt1.end()
                txt_1 = search_area[idx_txt1: idx_txt1 + num_letters_for_label * 2]
                txt_1 = txt_1[:-2]  # remove last character - seems to be a newline of something.
                bytes_data = bytes.fromhex(txt_1)
                command_string = bytes_data.decode('ascii')

                match_size_txt2 = re.search(r"0ea.", search_area)
                assert len(match_size_txt2.regs) == 1
                num_char_txt2 = search_area[match_size_txt2.start(): match_size_txt2.end()]
                assert len(num_char_txt2) == 4
                num_letters_for_custom_label = int(num_char_txt2[3], 16)
                idx_txt2 = match_size_txt2.end()
                txt_2 = search_area[idx_txt2: idx_txt2 + num_letters_for_custom_label * 2]
                txt_2 = txt_2[:-2]  # remove last character - seems to be a newline of something.
                bytes_data = bytes.fromhex(txt_2)
                custom_label_string = bytes_data.decode('ascii')

                match_led_color = re.search(r"00.0fc.", search_area)
                assert len(match_led_color.regs) == 1
                led_color_part = search_area[match_led_color.start(): match_led_color.end()]
                assert len(led_color_part) == 7
                led_color = int(led_color_part[2], 16)

                processed_local += match_led_color.end()
                # expecting a 0x87 at the end
                if i + 1 < features_of_switch:
                    ind_x_87 = search_area[match_led_color.end():].index('87')
                    assert (ind_x_87 == 0)
                    processed_local += 2  # 0x87

                fs_info_entry = FsInfoEntry()
                fs_info_entry.custom_label = custom_label_string
                fs_info_entry.command_label = command_string
                fs_info_entry.led_color_id = led_color
                if fs_info_entry.command_label == 'Preset ':
                    # Special case: Custom-LED color set but Preset Switch: Always RED
                    fs_info_entry.led_color_id = 0x02

                fs_info.command_list.append(fs_info_entry)

                '''

                front = fs_start[processed_local:]
                processed_local += 15
                num_letters_for_label = int(fs_start[processed_local], 16)
                processed_local += 1

                txt_1 = fs_start[processed_local : processed_local + num_letters_for_label * 2]
                txt_1 = txt_1[:-2] # remove last character - seems to be a newline of something.
                bytes_data = bytes.fromhex(txt_1)
                command_string = bytes_data.decode('ascii')
                # print(command_string)
                processed_local += num_letters_for_label * 2


                # custom_label
                # jump over the next 23 characters
                processed_local += 23
                num_letters_for_custom_label = int(fs_start[processed_local], 16)
                processed_local += 1
                txt_2 = fs_start[processed_local: processed_local + num_letters_for_custom_label * 2]
                txt_2 = txt_2[:-2] # remove last character - seems to be a newline of something.
                bytes_data = bytes.fromhex(txt_2)
                custom_label_string = bytes_data.decode('ascii')
                processed_local += num_letters_for_custom_label * 2
                # print(custom_label_string)

                front = fs_start[processed_local:]

                # led color
                # jump over the next 6 characters
                processed_local += 7
                led_color = int(fs_start[processed_local], 16)
                processed_local += 1

                # find index of a0
                ind_0f = fs_start[processed_local:].index('0f')
                assert(ind_0f == 0)
                processed_local += ind_0f
                processed_local += 2  # 0f
                processed_local += 2  # c2 or c3

                # expecting a 0x87 at the end
                if i+1<features_of_switch:
                    ind_x_87 = fs_start[processed_local:].index('87')
                    assert (ind_x_87 == 0)
                    processed_local += 2  # 0x87
                '''
            fs_info_list.append(fs_info)


        else:
            print("ERROR: Unexpected structure in footswitich info!!!")
            return None

        char_processed += processed_local
        if len(fs_info_list) == 5:
            return fs_info_list
    '''
    parts = data.split('84000305')
    # assert (len(parts) == 6)
    if len(parts) > 0:
        parts = parts[1:]

    fs_info_list = []
    for fs in parts:
        my_idx = 0
        no_letters_for_label = int(fs[1], 16)
        my_idx += 2
        txt_1 = fs[my_idx:my_idx + no_letters_for_label * 2]
        my_idx += no_letters_for_label * 2
        txt_1 = txt_1.replace('00', '20')
        bytes_data = bytes.fromhex(txt_1)
        command_string = bytes_data.decode('ascii')
        # print(ascii_string)

        my_idx += 22  # fixed pattern
        no_letters_for_label = int(fs[my_idx + 1], 16)
        my_idx += 2

        txt_2 = fs[my_idx:my_idx + no_letters_for_label * 2]
        my_idx += no_letters_for_label * 2
        txt_2 = txt_2.replace('00', '20')
        bytes_data = bytes.fromhex(txt_2)
        custom_string = bytes_data.decode('ascii')
        # print(ascii_string)

        my_idx += 6  # fixed pattern
        led_color = int(fs[my_idx + 1], 16)
        # print("{} - color: {}".format(ascii_string, led_color))

        fs_info = FsInfo(no=len(fs_info_list))
        fs_info.custom_label = custom_string
        fs_info.command_label = command_string
        fs_info.led_color_id = led_color
        if fs_info.command_label == 'Preset ':
            # Special case: Custom-LED color set but Preset Switch: Always RED
            fs_info.led_color_id = 0x02

        fs_info_list.append(fs_info)

    return fs_info_list
    '''

def fs_info_extract_ex(data):
    fs_info_list = []

    begin = data.index('0895')  # was 07020895
    char_processed = begin + 4
    assert (begin > 0)

    while data[char_processed:].startswith('c0'):
        # slot empty
        fs_info_list.append(FsInfo(len(fs_info_list) + 1))
        char_processed += 2
        if len(fs_info_list) == 5:
            return fs_info_list

    while len(data[char_processed:]) > 0:
        fs_start = data[char_processed:]
        processed_local = 0
        match_fs_start_tag = re.search(r"9.87", fs_start)
        fs_info = FsInfo(no=len(fs_info_list) + 1)

        if data[char_processed:].startswith('c0'):
            fs_info_list.append(FsInfo(len(fs_info_list) + 1))
            processed_local += 2  # c0

        elif len(match_fs_start_tag.regs) == 1:
            assert match_fs_start_tag.start() == 0
            processed_local += 4
            features_of_switch = int(fs_start[1], 16)
            for i in range(features_of_switch):
                search_area = fs_start[processed_local:processed_local + 200]

                idx_0a = search_area.index('0a')
                if idx_0a > -1:
                    param_0a = search_area[idx_0a+2: idx_0a+4]
                    search_area = search_area[4:]

                idx_0b = search_area.index('0b')
                if idx_0a > -1:
                    param_0b = search_area[idx_0b + 2: idx_0a + 8]
                    search_area = search_area[8:]
                idx_05 = search_area.index('05')
                if idx_05 > -1:
                    len_text = int(search_area[idx_05+3], 16)
                    param_05 = search_area[idx_05 + 4: idx_05 + 4 + len_text*2]
                    param_05 = param_05[:-2]
                    bytes_data = bytes.fromhex(param_05)
                    command_string = bytes_data.decode('ascii')
                    search_area = search_area[4 + len_text * 2:]
                idx_06 = search_area.index('06')
                if idx_06 > -1:
                    param_6b = search_area[idx_06 + 2: idx_06 + 12]
                    search_area = search_area[12:]
                idx_07 = search_area.index('07')
                if idx_07 > -1:
                    param_07 = search_area[idx_07 + 2: idx_07 + 4]
                    search_area = search_area[4:]

                # idx_08 = search_area.index('08')
                # search_area = search_area[4:]
                idx_0c = search_area.index('0c')
                if idx_0c > -1:
                    param_0c = search_area[idx_0c + 2: idx_0c + 4]
                    search_area = search_area[4:]
                idx_0e = search_area.index('0e')
                if idx_0e > -1:
                    len_text = int(search_area[idx_0e + 3], 16)
                    param_05 = search_area[idx_0e + 4: idx_0e + 4 + len_text * 2]
                    param_05 = param_05[:-2]
                    bytes_data = bytes.fromhex(param_05)
                    custom_string = bytes_data.decode('ascii')
                    search_area = search_area[4 + len_text * 2:]
                search_area = search_area[4:]
                idx_0d = search_area.index('0d')
                if idx_0d > -1:
                    param_0d = search_area[idx_0d + 2: idx_0d + 4]
                    search_area = search_area[4:]
                idx_10 = search_area.index('10')
                if idx_10 > -1:
                    param_10 = search_area[idx_10 + 2: idx_10 + 4]
                    search_area = search_area[4:]
                idx_0f = search_area.index('0f')
                if idx_0f > -1:
                    param_0f = search_area[idx_0f + 2: idx_0f + 4]
                    search_area = search_area[4:]

                fs_info_entry = FsInfoEntry()
                fs_info_entry.custom_label = custom_string
                fs_info_entry.command_label = command_string
                fs_info_entry.led_color_id = int(param_10, 16)
                if fs_info_entry.command_label == 'Preset ':
                    # Special case: Custom-LED color set but Preset Switch: Always RED
                    fs_info_entry.led_color_id = 0x02

                fs_info.command_list.append(fs_info_entry)

            fs_info_list.append(fs_info)

        else:
            print("ERROR: Unexpected structure in footswitich info!!!")
            return None

        char_processed += processed_local
        if len(fs_info_list) == 5:
            return fs_info_list

def main(args):

    file_list = {
        "amps_cabs": "all_amps_PLUS_cabs_in_slot_3_all_other_slots_empty",
        "amps": "all_amps_in_slot_3_all_other_slots_empty",
        "cabs": "all_cabs_in_slot_3_all_other_slots_empty",
        "delays": "all_delays_in_slot_3_all_other_slots_empty",
        "drives": "all_drives_in_slot_3_all_other_slots_empty_ERROR_switching_to_Clathorn_Drive",
        "dynamics": "all_dynamics_in_slot_3_all_other_slots_empty",
        "eqs": "all_eqs_in_slot_3_all_other_slots_empty",
        "filters": "all_filter_in_slot_3_all_other_slots_empty",
        "looper": "all_loopers_in_slot_3_all_other_slots_empty",
        "mods2": "all_modulationsV2_in_slot_3_all_other_slots_empty",
        "mods": "all_modulations_in_slot_3_all_other_slots_empty",
        "pitchs": "all_pitch_synths_in_slot_3_all_other_slots_empty",
        "preamps": "all_preamps_in_slot_3_all_other_slots_empty",
        "reverbs": "all_reverbs_in_slot_3_all_other_slots_empty",
        "send_return": "all_send_return_in_slot_3_all_other_slots_empty",
        "vol_pan": "all_vol_pan_in_slot_3_all_other_slots_empty",
        "wahs": "all_wahs_in_slot_3_all_other_slots_empty",
        "slot6": "switching_mod_slot6_PitchRingMod_to_AmRingMod",
        "slot5": "switching_rvb_slot5_from_Ganymede_to_Searchlights",
        "eqs_stereo": "all_eqsSTEREO_in_slot_3_all_other_slots_empty",
        "mods_stereo": "all_modulationsSTEREO_in_slot_3_all_other_slots_empty",
        "reverbs_stereo": "all_reverbsSTEREO_in_slot_3_all_other_slots_empty",
        "bass_amps": "all_BASSamps_in_slot_3_all_other_slots_empty",
        "mic_preamp": "all_MIC_JUST_ONE_preamps_in_slot_3_all_other_slots_empty",
        "bass_amps_cabs": "all_BASSamps_PLUS_cabs_in_slot_3_all_other_slots_empty",
        "bass_preamps": "all_BASSpreamps_in_slot_3_all_other_slots_empty",
        "delays_legacy": "all_delaysLEGACY_in_slot_3_all_other_slots_empty",
        "delays_stereo": "all_delaysSTEREO_in_slot_3_all_other_slots_empty",
        "drives_legacy": "all_drivesLEGACY_in_slot_3_all_other_slots_empty",
        "drives_stereo": "all_drivesSTEREO_in_slot_3_all_other_slots_empty",
        "dynamics_legacy": "all_dynamicsLEGACY_in_slot_3_all_other_slots_empty",
        "dynamics_stereo": "all_dynamicsSTEREO_in_slot_3_all_other_slots_empty",
        "filter_legacy": "all_filterLEGACY_in_slot_3_all_other_slots_empty",
        "filter_stereo": "all_filterSTEREO_in_slot_3_all_other_slots_empty",
        "wahs_stereo": "all_wahsSTEREO_in_slot_3_all_other_slots_empty",
        "mods_legacy": "all_modulationsLEGACY_in_slot_3_all_other_slots_empty",
        "pitch_synths_legacy": "all_pitch_synthsLEGACY_in_slot_3_all_other_slots_empty",
        "pitch_synths_stereo": "all_pitch_synthsSTEREO_in_slot_3_all_other_slots_empty",
        "reverbs_legacy": "all_reverbsLEGACY_in_slot_3_all_other_slots_empty",
        "send_return_stereo": "all_send_returnSTEREO_in_slot_3_all_other_slots_empty",
        "vol_pan_stereo": "all_vol_panSTEREO_in_slot_3_all_other_slots_empty",
        "cabs_dual": "all_cabsDUAL_in_slot_3_all_other_slots_empty"
    }

    last_session_id = [0x00, 0x00]
    preset_data = ''

    receiving_mode = False
    # for entry in file_list:
    with open('../doc/' + file_list["slot5"] + '.csv') as csv_file:
        # print(entry)
        csv_reader = csv.reader(csv_file, delimiter=';')
        line_count = 0
        display_message_key = '0A070B85000105'
        for row in csv_reader:
            data = row[4]
            if data == '':
                continue
            if data.endswith(', '):
                data = data[:-2]
            data_int = [int(x, 16) for x in data.split(', ')]

            if data_int[0] != 0x08 and receiving_mode is False:
                preset_data = ''
                continue

            if my_byte_cmp(data_int, ["XX", 0x1, 0x0, 0x18, 0xed, 0x3, 0x80, 0x10, 0x0, "XX", 0x0, 0x4], 12) or my_byte_cmp(data_int, ["XX", 0x0, 0x0, 0x18, 0xed, 0x3, 0x80, 0x10, 0x0, "XX", 0x0, 0x4], 12):
                if data_int[0] == 0x08:
                    receiving_mode = True

                hex_string = format_1(data)
                if len(hex_string) > 32:
                    hex_string = hex_string[32:]
                preset_data += hex_string
                # print(hex_string)
                if data_int[0] != 0x08 and data_int[1] != 0x01:
                    receiving_mode = False
                    # print(preset_data)
                    # get current display message
                    try:
                        idx_display_msg = preset_data.index(display_message_key)
                        idx_display_msg += len(display_message_key)
                        for i in range(1, 25):
                            if preset_data[i] == '00':
                                break
                            display_msg += preset_data[i]
                    except ValueError:
                        display_msg = 'NOT FOUND!'

                    slot_infos = slot_splitter_2(preset_data)
                    if slot_infos is None:
                        continue
                    for slot in slot_infos:
                        print(slot.to_string())
                    # if slot_infos[2] is not None:
                    #    print(slot_infos[2].to_string())

                    preset_data = ''
                    # print('FINISHED')

            line_count += 1


if __name__ == '__main__':

    # 17c - New Preset
    # data = "000084288f0b00008366cd03f6670068da0b84a96c362d68656c697800da00303d000000600000000f03000011030000bc0300008e0400007e050000ab0500003e000000b1050000840b0000840b000089078324a45033330023ce0380000025b276332e37312d33322d6731303339363631000082150016dc0014821300148205010783020303030493c2cac2400000ca3f0000008213061485188317c219771aff09010ac30b83020703070497cac214666603ca3d1ba5e0ca3e4cccd0ca3f800000ca40c00000ca40c000000c830200030004908213061485188317c219cd01d81aff09010ac20b83020403040494ca3e999998ca0000000006c20c830200030004908213061485188317c219cd012b1aff09010ac30b83020d030d049d00ca41100001ca00000000ca3f00000000cac10fffffca00000000ca3f000000ca3e4cccd0ca00000000ca00000000ca3f800000ca3f0000000c830200030004908213061485188317c319cd01f41a4009120ac30b830211031104dc0011ca3dccccd0ca3f000000ca3ed70a3cca3f000000ca3e800000ca3f6e147cca3e800000ca3f400000c2c2c2c3ca3f000000ca3f000000ca3f00000002c20c83020603050496ca40000000ca42480000ca4684d000ca00000000ca00000000068213061485188317c2195b1aff09080ac30b83020b030a049bca3f4cccccca3eccccccca3f000000ca3f800000ca3e999998ca00000000ca42c80000ca460b1000c206c30c830200030004908213061485188317c219ccf01aff09080ac30b83020703060497ca3f000000ca3dccccd0ca430f0000ca4592e000ca3eccccccca00000000c20c8302000300049082130814c082130814c0821301148206010783020203020492ca3f000000ca40a9999a82130214830e82050007830200030004900f8408cd01010d000ac30783020303030493ca3f000000ca3f000000c212c282130814c082130814c082130814c082130814c082130814c082130814c082130814c082130814c08213031483108206000783020003000490118408cc970d000ac30783020603060496ca00000000ca3f000000ca00000000ca3f000000c2ca0000000012c201c003820702089591870a000b85000105ab4475616c2050697463680006ce003200ff07c308030cc20ea1000dc210000fc292870a000b85000105aa50696e6720506f6e670006ce0006ff0007c308050cc20ea1000dc210000fc2870a010b85000105a84368616d6265720006ce00ff2d0007c308060cc20ea1000dc210000fc291870a000b85000105ad5363726970742050686173650006cd040d07c208020cc20ea1000dc210000fc2c0c0049ac0c0c0c0c0c0c0c0c09682000501890009010402ca0000000003ca3f8000000400050506831c001d0429c207000dc282000401890009010402ca0000000003ca3f8000000400050406831c001d0629c207000dc282000301890009010402c203c30400050406831c001d0829c207000dc282000201890009010402c203c30400050406831c001d0929c207000dc282000101890009010402ca0000000003ca3f8000000400050406831c001d0029c207000dc282000001890009010402c203c30400050406831c001d0a29c207000dc20282009dd10000d10000d10000d10000d10000d10000d10000d10000d10000d10000d10000d10000d10000019d97cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc00058f10ca42f000002d002ecabdccccd02fcabdccccd0300031c332003300340035003600370038c21e00cc8600068262041a000a8606000700080609140a938800c3019b930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc2970000000000000002dc004093c200c293c201ca3f00000093c202c393c203c293c204ca3f00000093c205ca3ee6666893c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c003dc001492c2c292c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c204ab534e415053484f542031000ec205ca42f000000c008800c3019b930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc2970000000000000002dc004093c200c293c201ca3f00000093c202c393c203c293c204ca3f00000093c205ca3ee6666893c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c003dc001492c2c292c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c204ab534e415053484f542032000ec205ca42f000000c008800c3019b930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc2970000000000000002dc004093c200c293c201ca3f00000093c202c393c203c293c204ca3f00000093c205ca3ee6666893c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c003dc001492c2c292c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c204ab534e415053484f542033000ec205ca42f000000c000ddc0014c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c0"
    # slots = slot_extract(data)

    file_path = "../ideas/20260226_all_data.txt"

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

    # slots = slot_extract(preset_data_list[68])

    fs_info_list = fs_info_extract_ex(preset_data_list[0])

    for i, preset_data in enumerate(preset_data_list):
        bank = int(i / 3) + 1
        num =  i % 3 + 1
        letter = chr(64 + num)
        if i<100:
            continue

        print('Preset {}{} ({}): '.format(bank, letter, i+1))
        slots = slot_extract(preset_data)
        for slot in slots:
            print(slot.to_string())
        print()

    for i, preset_data in enumerate(preset_data_list):
        fs_info_list = fs_info_extract(preset_data)

        print('Preset {}: '.format(i+1))
        for fs_info in fs_info_list:
            print(fs_info.to_string())
        print()
    print(preset_data_list[:5])

    # 01B
    data = "00006828731000008366cd03f4670068da1068a96c362d68656c697800da00303d00000060000000140300001603000001040000e2040000d2050000ff0500003e00000005060000f00b0000f00b00008a078324a45033330023ce0380000025b276332e37312d33322d6731303339363631000082150016dc0014821300148205010783020303030493c3cac2400000ca3f0000008213061485188317c219cd010a1aff09010ac20b83020503050495ca3f800000ca43eb0000ca4516f000ca3f800000ca000000000c830200030004908213061485188317c219cc811aff09010ac20b83020b030b049bca00000000ca00000000ca00000000ca00000000ca3fb33330ca3fc00000ca00000000ca00000000ca00000000ca00000000ca000000000c830200030004908213061485188317c219651aff09010ac30b83020303030493ca00000000ca3f800000ca3f2b85200c830200030004908313061c011485188317c2190a1aff09110ac30b83020c030c049cca3f266666ca3d8f5c30ca3f000000ca3f4cccccca3f4cccccca3f400000ca3eccccccca3d23d700ca3f000000ca3f000000ca3e800000ca3f0000000c8302000300049082130814c08313061c021485188317c219cc961aff09140ac30b8302050305049501ca419f3333ca469d0800ca3f800000cac19000001bda00213633663539356262366466633337363937323134323865363134633461356237008213061485188317c219501aff09080ac30b83020703060497ca3e999998ca3d8f5c30ca00000000ca0000000006c2c20c830200030004908213061485188317c219ccfe1aff091d0ac30b83020203020492ca00000000ca000000000c83020003000490821301148206010783020203020492ca3f800000ca0000000082130214830e82050007830200030004900f8408cd01010d000ac30783020303030493ca3f000000ca3f000000c212c282130814c082130814c082130814c082130814c082130814c082130814c082130814c082130814c08213031483108206000783020003000490118408cc970d000ac30783020603060496ca00000000ca3f000000cac2700000ca3f000000c2ca0000000012c201c003820702089591870a000b84000305a75072657365740006ce0007100c07c20cc20ea6436c65616e000dc310060fc391870a000b84000305a54e6f74650006ce0007100c07c20cc20ea6536f6c6f3e000dc310040fc391870a000b84000305a54e6f74650006ce0007100c07c20cc30ea7426e64486c70000dc310080fc391870a000b84000305a9536e617073686f740006ce0007100c07c20cc30ea1000dc210000fc292870a000b84000305a54e6f74650006ce0007100c07c20cc30ea1000dc210000fc2870a010b85000105a74368726f6d650006ce0003000b07c208010cc30ea1000dc210000fc2049ac09182000001890001010402ca0000000003ca3f8000000400050106831c001d0029c207000dc2c0c0c0c0c0c095820005018a0008010502c003c00402050109ccff0acdff000bc30c0082000401890008011c02ca0000000003ca3e1999980400050706831c001d0229c207000dc282000301890008010702cac270000003cac19000000400050606831c001d0429c207000dc282000201890008011c02ca3f26666603ca3f7333340400050406831c001d0029c207000dc282000101890008011c02ca3f40000003ca3f6666660400050406831c001d0529c207000dc2c00282009dd10012d10000d10000d10000d10000d10000d1000ed10005d10005d1000fd10005d10000d10000019d97cc12cc04cc45cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc0ecc02cc00cc00cc00cc00cc0097cc05cc04cc24cc01cc00cc00cc0097cc05cc04cc0bcc7fcc01cc00cc0097cc0fcc00cc01cc00cc00cc00cc0097cc05cc04cc09cc7fcc01cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc00058f10ca42ee1c192d002ecabdccccd02fcabdccccd0300031c332003300340035003600370038c21e00cc8600068262041a000a8606000705080509140a938800c3019b9300c297000445000000009307c297000424010000009308c29700040b7f0100009309c29700000100000000930ac2970004097f010000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc2970000000000000002dc004093c200ca3f80000093c201ca3f40000093c202ca3f26666693c203cac190000093c204ca0000000093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c003dc001492c2c292c2c292c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c204ab46656e64657220444c58000ec305ca42ee1c190c008800c3019b9300c297000445010000009307c2970004247f0000009308c29700040b7f0100009309c29700000100000000930ac2970004097f010000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc2970000000000000002dc004093c200ca3f80000093c201ca3f40000093c202ca3f26666693c203cac190000093c204ca0000000093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c003dc001492c2c292c2c292c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c204ab44756573656e62657267000ec305ca42ee1c190c008800c3019b9300c297000445020000009307c2970004247f0000009308c29700040b7f0100009309c29700000100000000930ac2970004097f010000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc2970000000000000002dc004093c200ca3f80000093c201ca3f40000093c202ca3ecccccc93c203cac190000093c204ca0000000093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c003dc001492c2c292c2c292c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c204ab46656e64657220444c58000ec305ca42ee1c190c000ddc0014c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c30cdc0080da0021363366353935626236646663333736393732313432386536313463346135623700da0021643534656536386230666634363261356263323862646631343434393936393900da0021313832613037343837623234356261663864613431393965323732646162623400da0021326338323536313363336132303765616635306332333937343133306562656600da0021653238373934663664373361663039643764633735396661663862323333353100da0021323337306533366662306661313965376331666637633064303663376538356200da0021633034323635316131373365303039373833633933616432666532343037623800da0021623531623761313163353331363833643433326261646432633064373839336300da0021623762353037323032613137333835393436366465336332313039336338636600da0021393065363133623261356238313532323663383861613935383437363964346200da0021346635613566336538653464376539343861303665303666306438366139396200da0021386337666266656263633966303262316539373639623530346632333361653900da0021313432306232373039616438343330626233316263353438376261356631346100da0021363366353935626236646663333736393732313432386536313463346135623700da0021313035393238653236663637613962636336356361353137663934396237316100da0021333630326664636365663836663534643231373930666239623634646236386400da0021343463343166303936363832656562346266316266653430393637303039316200da0021396138326161653265663634313833353063613436353065383533363936303000da0021386339386231393365343062313035316132383333313431356239303932643100da0021653565656362396535333165383430353866363635626366393837666236363000da0021653230633239643264353732356534623038613535623738666530663165616300da0021363130383330636336386630363230643538623037343137356534383039393500da0021623362343338363535386639343535373761326534633138376166653639366100da0021623766613563396239333463336166383136386331303837373130396263656100da0021333431663732613663323936333232333765643264306133353566316438623200da0021326332346164333064616136613834386239366232643065373133313561383600a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a10065"
    # 01A
    # data = "00007e00890b00008366cd03f6670068da0b7ea96c362d68656c697800da00303d00000060000000da020000dc020000220400009404000084050000b10500003e000000b70500007e0b00007e0b000089078324a45033330023ce0380000025b276332e37312d33322d6731303339363631000082150216dc0014821300148205010783020303030493c3cac2400000ca3f0000008213061485188317c219cd010a1aff09010ac20b83020503050495ca3f800000ca43eb0000ca4516f000ca3f800000ca000000000c830200030004908213061485188317c219771aff09010ac30b83020703070497cac214666603ca3d1ba5e0ca3e4cccd0ca3f800000ca40e00000ca40c000000c830200030004908213061485188317c3192a1a3609120ac30b83020c030c049cca3eccccccca3ec7ae14ca3f333334ca3f147ae0ca3e800000ca3f4cccccca3f800000ca3f000000ca3f000000ca3ea8f5c4ca3f19999aca3f0000000c83020603050496ca40400000ca42a00000ca45fa0000ca00000000ca000000000582130814c082130814c08213061485188317c219cd01ee1aff09080ac30b83020903080499ca3e570a40ca00000000ca3db851f0ca3eccccccca3e051eb8ca00000000ca42dc0000ca45bb8000c20c830200030004908213061485188317c219cd01051aff09010ac30b83020203020492ca3f800000c20c8302000300049082130814c0821301148206010783020203020492ca3f800000ca0000000082130214830e82050007830200030004900f8408cd01010d080ac30783020303030493ca3f000000ca3f000000c212c382130814c082130814c082130814c082130814c082130814c082130814c082130814c08213061485188317c219ccec1aff09060ac30b83020203020492ca00000000ca000000000c830200030004908213031483108206060783020303030493ca3f000000ca00000000c3118408cc970d090ac30783020603060496ca00000000ca3f000000ca00000000ca3f000000c2ca0000000012c201c003820702089591870a000b84000305aa434320546f67676c650006ce0007100c07c20cc20ea84372756e63683e000dc310060fc391870a000b84000305a75072657365740006ce0007100c07c20cc20ea752687974686d000dc310040fc391870a000b84000305a54e6f74650006ce0007100c07c20cc30ea7426e64486c70000dc310080fc391870a000b84000305a9536e617073686f740006ce0007100c07c20cc30ea1000dc210000fc294870a000b84000305a54e6f74650006ce0007100c07c20cc30ea1000dc210040fc3870a010b85000105a74368726f6d650006ce0003000b07c208010cc30ea1000dc210040fc3870a020b85000105ac446f75626c652054616e6b0006ce00ff2d0007c308060cc30ea1000dc210040fc3870a030b85000105ad566f6c756d6520506564616c0006cdff8007c308070cc30ea1000dc210040fc3049ac09182000001890001010402ca0000000003ca3f8000000400050106831c001d0029c207000dc2c0c0c0c0c0c09282000101890008010702ca0000000003ca3f8000000400050706831c001d0029c207000dc2820002018a0008010502c003c00402050109ccff0acdff000bc30c00c00282009dd10012d10000d10000d10000d10000d10000d10002d1000ed10005d1000fd10005d10000d10000019d97cc12cc04cc45cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc02cc04cc1ccc7fcc00cc00cc7f97cc0ecc03cc00cc00cc00cc00cc0097cc05cc04cc0bcc7fcc01cc00cc0097cc0fcc00cc01cc00cc00cc00cc0097cc05cc04cc09cc7fcc01cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc00058f10ca42f000002d002ecabdccccd02fcabdccccd0300031c332003300340035003600370038c21e00cc8600068262121a000a8606000705080209140a938800c3019b9300c297120445000000009306c29702041c7f00007f9308c29705040b7f0100009309c2970f000100000000930ac2970504097f010000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc2970000000000000002dc004093c200ca3f80000093c201ca3f80000093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c003dc001492c2c292c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c204ab46656e64657220444c58000ec305ca42f000000c008800c3019b9300c297000445010000009306c29700041c7f00007f9308c29700040b7f0100009309c29700000100000000930ac2970004097f010000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc2970000000000000002dc004093c200ca3f80000093c201ca3f80000093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c003dc001492c2c292c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c204ab46656e64657220444c58000ec305ca42f000000c008800c3019b9300c297000445020000009306c29700041c7f0000009308c29700040b7f0100009309c29700000100000000930ac29700003064000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc2970000000000000002dc004093c200ca3f80000093c201ca3f80000093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c003dc001492c2c292c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c204ab46656e64657220444c58000ec305ca42f000000c000ddc0014c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c093c2"
    # switch 1 not set
    data = "000040004b1000008366cd03f4670068da1040a96c362d68656c697800da00303d000000600000001403000016030000d9030000ba040000aa050000d70500003e000000dd050000c80b0000c80b00008a078324a45033330023ce0380000025b276332e37312d33322d6731303339363631000082150016dc0014821300148205010783020303030493c3cac2400000ca3f0000008213061485188317c219cd010a1aff09010ac20b83020503050495ca3f800000ca43eb0000ca4516f000ca3f800000ca000000000c830200030004908213061485188317c219cc811aff09010ac20b83020b030b049bca00000000ca00000000ca00000000ca00000000ca3fb33330ca3fc00000ca00000000ca00000000ca00000000ca00000000ca000000000c830200030004908213061485188317c219651aff09010ac30b83020303030493ca00000000ca3f800000ca3f2b85200c830200030004908313061c011485188317c2190a1aff09110ac30b83020c030c049cca3f266666ca3d8f5c30ca3f000000ca3f4cccccca3f4cccccca3f400000ca3eccccccca3d23d700ca3f000000ca3f000000ca3e800000ca3f0000000c8302000300049082130814c08313061c021485188317c219cc961aff09140ac30b8302050305049501ca419f3333ca469d0800ca3f800000cac19000001bda00213633663539356262366466633337363937323134323865363134633461356237008213061485188317c219501aff09080ac30b83020703060497ca3e999998ca3d8f5c30ca00000000ca0000000006c2c20c830200030004908213061485188317c219ccfe1aff091d0ac30b83020203020492ca00000000ca000000000c83020003000490821301148206010783020203020492ca3f800000ca0000000082130214830e82050007830200030004900f8408cd01010d000ac30783020303030493ca3f000000ca3f000000c212c282130814c082130814c082130814c082130814c082130814c082130814c082130814c082130814c08213031483108206000783020003000490118408cc970d000ac30783020603060496ca00000000ca3f000000cac2700000ca3f000000c2ca0000000012c201c0038207020895c091870a000b84000305a54e6f74650006ce0007100c07c20cc20ea6536f6c6f3e000dc310040fc391870a000b84000305a54e6f74650006ce0007100c07c20cc30ea7426e64486c70000dc310080fc391870a000b84000305a9536e617073686f740006ce0007100c07c20cc30ea1000dc210000fc292870a000b84000305a54e6f74650006ce0007100c07c20cc30ea1000dc210000fc2870a010b85000105a74368726f6d650006ce0003000b07c208010cc30ea1000dc210000fc2049ac09182000001890001010402ca0000000003ca3f8000000400050106831c001d0029c207000dc2c0c0c0c0c0c095820005018a0008010502c003c00402050109ccff0acdff000bc30c0082000401890008011c02ca0000000003ca3e1999980400050706831c001d0229c207000dc282000301890008010702cac270000003cac19000000400050606831c001d0429c207000dc282000201890008011c02ca3f26666603ca3f7333340400050406831c001d0029c207000dc282000101890008011c02ca3f40000003ca3f6666660400050406831c001d0529c207000dc2c00282009dd10012d10000d10000d10000d10000d10000d10000d10005d10005d1000fd10005d10000d10000019d97cc12cc04cc45cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc05cc04cc24cc01cc00cc00cc0097cc05cc04cc0bcc7fcc01cc00cc0097cc0fcc00cc01cc00cc00cc00cc0097cc05cc04cc09cc7fcc01cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc00058f10ca42ee1c192d002ecabdccccd02fcabdccccd0300031c332003300340035003600370038c21e00cc8600068262041a000a8606000705080509140a938800c3019b9300c297000445000000009307c297000424010000009308c29700040b7f0100009309c29700000100000000930ac2970004097f010000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc2970000000000000002dc004093c200ca3f80000093c201ca3f40000093c202ca3f26666693c203cac190000093c204ca0000000093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c003dc001492c2c292c2c292c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c204ab46656e64657220444c58000ec305ca42ee1c190c008800c3019b9300c297000445010000009307c2970004247f0000009308c29700040b7f0100009309c29700000100000000930ac2970004097f010000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc2970000000000000002dc004093c200ca3f80000093c201ca3f40000093c202ca3f26666693c203cac190000093c204ca0000000093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c003dc001492c2c292c2c292c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c204ab44756573656e62657267000ec305ca42ee1c190c008800c3019b9300c297000445020000009307c2970004247f0000009308c29700040b7f0100009309c29700000100000000930ac2970004097f010000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc2970000000000000002dc004093c200ca3f80000093c201ca3f40000093c202ca3ecccccc93c203cac190000093c204ca0000000093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c003dc001492c2c292c2c292c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c204ab46656e64657220444c58000ec305ca42ee1c190c000ddc0014c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c30cdc0080da0021363366353935626236646663333736393732313432386536313463346135623700da0021643534656536386230666634363261356263323862646631343434393936393900da0021313832613037343837623234356261663864613431393965323732646162623400da0021326338323536313363336132303765616635306332333937343133306562656600da0021653238373934663664373361663039643764633735396661663862323333353100da0021323337306533366662306661313965376331666637633064303663376538356200da0021633034323635316131373365303039373833633933616432666532343037623800da0021623531623761313163353331363833643433326261646432633064373839336300da0021623762353037323032613137333835393436366465336332313039336338636600da0021393065363133623261356238313532323663383861613935383437363964346200da0021346635613566336538653464376539343861303665303666306438366139396200da0021386337666266656263633966303262316539373639623530346632333361653900da0021313432306232373039616438343330626233316263353438376261356631346100da0021363366353935626236646663333736393732313432386536313463346135623700da0021313035393238653236663637613962636336356361353137663934396237316100da0021333630326664636365663836663534643231373930666239623634646236386400da0021343463343166303936363832656562346266316266653430393637303039316200da0021396138326161653265663634313833353063613436353065383533363936303000da0021386339386231393365343062313035316132383333313431356239303932643100da0021653565656362396535333165383430353866363635626366393837666236363000da0021653230633239643264353732356534623038613535623738666530663165616300da0021363130383330636336386630363230643538623037343137356534383039393500da0021623362343338363535386639343535373761326534633138376166653639366100da0021623766613563396239333463336166383136386331303837373130396263656100da0021333431663732613663323936333232333765643264306133353566316438623200da0021326332346164333064616136613834386239366232643065373133313561383600a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a10065"
    # 06A Joan Jett
    data = "00000928141100008366cd0309670068da1109a96c362d68656c697800da00303d000000600000003203000034030000710400007705000067060000940600003e0000009a060000910c0000910c00008a078324a45033330023ce0380000025b276332e37312d33322d6731303339363631000082150216dc0014821300148205010783020303030493c3cac2400000ca3f0000008213061485188317c219cd010a1aff09010ac20b83020503050495ca3f800000ca43eb0000ca4516f000ca3f800000ca000000000c830200030004908213061485188317c219651aff09010ac30b83020303030493ca3e6147b0ca3f400000ca3e8000000c830200030004908213061485188317c219271aff09110ac30b83020c030c049cca3f428f5cca3e999998ca3f400000ca3f47ae14ca3e4cccd0ca3f4cccccca3f800000ca3f000000ca3f000000ca3f000000ca3f266666ca3f0000000c830200030004908213061485188317c219cc961aff09140ac30b830205030504950aca419f3333ca469d0800ca3f800000cac1ac00001bda00213930653631336232613562383135323236633838616139353834373639643462008213061485188317c219cd01ee1aff09080ac20b83020903080499ca3e570a40ca00000000ca3e800000ca3eccccccca3e6147b0ca00000000ca42dc0000ca45bb8000c20c830200030004908213061485188317c219501aff09080ac30b83020703060497ca3e999998ca3d8f5c30ca00000000ca0000000006c2c20c830200030004908213061485188317c219cd01051aff09010ac30b83020203020492ca3f800000c20c8302000300049082130814c0821301148206010783020203020492ca3f800000ca0000000082130214830e82050007830200030004900f8408cd01010d080ac30783020303030493ca3f000000ca3f000000c212c382130814c082130814c082130814c082130814c082130814c082130814c082130814c08213061485188317c219ccec1aff09060ac20b83020203020492ca00000000ca3f0000000c830200030004908213031483108206060783020303030493ca3f000000ca00000000c3118408cc970d090ac30783020603060496ca00000000ca3f000000ca00000000ca3f000000c2ca0000000012c201c003820702089591870a000b84000305a54e6f74650006ce0007100c07c20cc30ea6426f6f7374000dc3100a0fc391870a000b84000305a54e6f74650006ce0007100c07c20cc20ea752687974686d000dc310040fc391870a000b84000305a54e6f74650006ce0007100c07c20cc30ea7426e64486c70000dc310080fc391870a000b84000305a9536e617073686f740006ce0007100c07c20cc30ea1000dc210000fc294870a000b84000305a54e6f74650006ce0007100c07c20cc30ea1000dc210000fc2870a010b85000105a74368726f6d650006ce0003000b07c208010cc30ea1000dc210000fc2870a020b85000105ac446f75626c652054616e6b0006ce0010040007c208050cc30ea1000dc210000fc2870a030b85000105ad566f6c756d6520506564616c0006cdff8007c308070cc30ea1000dc210000fc2049ac09182000001890001010402ca0000000003ca3f8000000400050106831c001d0029c207000dc2c0c0c0c0c0c096820006018a0008010502c003c00402050109ccff0acdff000bc30c0082000501890008011c02ca0000000003ca3e1999980400050606831c001d0229c207000dc282000401890008011c02ca3f428f5c03ca3f8000000400050306831c001d0029c207000dc282000301890008011c02ca3f4ccccc03ca3f6666660400050306831c001d0529c207000dc282000201890008011202ca3e80000003ca3edc28f80400050206831c001d0229c207000dc282000101890008011202ca3e6147b003ca3ef5c2900400050206831c001d0029c207000dc2c00282009dd10012d10000d10000d10000d10000d10000d10005d10005d10005d1000fd10005d10000d10000019d97cc12cc04cc45cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc05cc04cc0ccc02cc01cc00cc0097cc05cc04cc24cc02cc00cc00cc0097cc05cc04cc0bcc7fcc01cc00cc0097cc0fcc00cc01cc00cc00cc00cc0097cc05cc04cc09cc7fcc01cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc00058f10ca42f000002d002ecabdccccd02fcabdccccd0300031c332003300340035003600370038c21e00cc8600068262031a000a8606000706080609140a938800c3019b9300c297000445000000009306c29700040c020100009307c297000424020000009308c29700040b7f0100009309c29700000100000000930ac2970004097f010000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc2970000000000000002dc004093c200ca3f80000093c201ca3e6147b093c202ca3e80000093c203ca3f4ccccc93c204ca3f428f5c93c205ca0000000093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c003dc001492c2c292c2c292c2c392c2c392c2c392c2c292c2c392c2c392c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c292c2c204ab46656e64657220444c58000ec305ca42f000000c008800c3019b9300c297000445010000009306c29700040c7f0100009307c2970004247f0000009308c29700040b7f0100009309c29700000100000000930ac2970004097f010000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc2970000000000000002dc004093c200ca3f80000093c201ca3e6147b093c202ca3e80000093c203ca3f4ccccc93c204ca3f428f5c93c205ca0000000093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c003dc001492c2c292c2c292c2c392c2c392c2c392c2c292c2c392c2c392c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c292c2c204ab46656e64657220424f58000ec305ca42f000000c008800c3019b9300c297000445020000009306c29700040c7f0100009307c2970004247f0000009308c29700040b7f0100009309c29700000100000000930ac29700003064000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc2970000000000000002dc004093c200ca3f80000093c201ca3e6147b093c202ca3e80000093c203ca3f4ccccc93c204ca3f428f5c93c205ca0000000093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c003dc001492c2c292c2c292c2c392c2c392c2c392c2c292c2c392c2c392c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c292c2c204ab46656e64657220444c58000ec305ca42f000000c000ddc0014c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c30cdc0080da0021363366353935626236646663333736393732313432386536313463346135623700da0021643534656536386230666634363261356263323862646631343434393936393900da0021313832613037343837623234356261663864613431393965323732646162623400da0021326338323536313363336132303765616635306332333937343133306562656600da0021653238373934663664373361663039643764633735396661663862323333353100da0021323337306533366662306661313965376331666637633064303663376538356200da0021633034323635316131373365303039373833633933616432666532343037623800da0021623531623761313163353331363833643433326261646432633064373839336300da0021623762353037323032613137333835393436366465336332313039336338636600da0021393065363133623261356238313532323663383861613935383437363964346200da0021346635613566336538653464376539343861303665303666306438366139396200da0021386337666266656263633966303262316539373639623530346632333361653900da0021313432306232373039616438343330626233316263353438376261356631346100da0021363366353935626236646663333736393732313432386536313463346135623700da0021313035393238653236663637613962636336356361353137663934396237316100da0021333630326664636365663836663534643231373930666239623634646236386400da0021343463343166303936363832656562346266316266653430393637303039316200da0021396138326161653265663634313833353063613436353065383533363936303000da0021386339386231393365343062313035316132383333313431356239303932643100da0021653565656362396535333165383430353866363635626366393837666236363000da0021653230633239643264353732356534623038613535623738666530663165616300da0021363130383330636336386630363230643538623037343137356534383039393500da0021623362343338363535386639343535373761326534633138376166653639366100da0021623766613563396239333463336166383136386331303837373130396263656100da0021333431663732613663323936333232333765643264306133353566316438623200da0021326332346164333064616136613834386239366232643065373133313561383600a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100"
    # 08B - Kompliment
    data = "0000ca00d50f00008366cd030d670068da0fcaa96c362d68656c697800da00303d000000600000000003000002030000f60300006804000058050000850500003e0000008b050000520b0000520b00008a078324a45033330023ce0380000025b276332e37312d33322d6731303339363631000082150016dc0014821300148205010783020303030493c3cac2400000ca3f0000008213061485188317c219cd010a1aff09010ac20b83020503050495ca3f800000ca43eb0000ca4516f000ca3f800000ca000000000c830200030004908213061485188317c219651aff09010ac30b83020303030493ca00000000ca3f800000ca3f2b85200c830200030004908313061c011485188317c2190a1aff09110ac30b83020c030c049cca3f266666ca3d8f5c30ca3f000000ca3f4cccccca3f4cccccca3f400000ca3eccccccca3d23d700ca3f000000ca3f000000ca3e800000ca3f0000000c8302000300049082130814c08313061c021485188317c219cc961aff09140ac30b8302050305049501ca419f3333ca469d0800ca3f800000cac19000001bda00213633663539356262366466633337363937323134323865363134633461356237008213061485188317c219cd01261aff09010ac20b83020a030a049aca3e4cccd0ca3e570a40ca3c23d700ca3e80000002ca3e99999808ca0000000006c20c830200030004908213061485188317c219501aff09080ac30b83020703060497ca3e999998ca3d8f5c30ca00000000ca0000000006c2c20c830200030004908213061485188317c219ccfe1aff091d0ac30b83020203020492ca00000000ca000000000c83020003000490821301148206010783020203020492ca3f800000ca0000000082130214830e82050007830200030004900f8408cd01010d000ac30783020303030493ca3f000000ca3f000000c212c282130814c082130814c082130814c082130814c082130814c082130814c082130814c082130814c08213031483108206000783020003000490118408cc970d000ac30783020603060496ca00000000ca3f000000cac2700000ca3f000000c2ca0000000012c201c0038207020895c092870a000b85000105ae44656c757865205068617365720006cd040d07c208060cc20ea7506861736572000dc310040fc3870a010b84000305a54e6f74650006ce006bffce07c30cc20ea7506861736572000dc310040fc391870a000b84000305a54e6f74650006ce0007100c07c20cc30ea7426e64486c70000dc310080fc391870a000b84000305a9536e617073686f740006ce0007100c07c20cc30ea1000dc210000fc292870a000b84000305a54e6f74650006ce0007100c07c20cc30ea1000dc210000fc2870a010b85000105a74368726f6d650006ce0003000b07c208010cc30ea1000dc210000fc2049ac09182000001890001010402ca0000000003ca3f8000000400050106831c001d0029c207000dc2c0c0c0c0c0c092820002018a0008010502c003c00402050109ccff0acdff000bc30c0082000101890008010702cac270000003cac19000000400050506831c001d0429c207000dc2c00282009dd10012d10000d10000d10000d10000d10000d10000d10005d10005d1000fd10005d10000d10000019d97cc12cc04cc45cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc05cc04cc24cc01cc00cc01cc0097cc05cc04cc0bcc7fcc01cc00cc0097cc0fcc00cc01cc00cc00cc00cc0097cc05cc04cc09cc7fcc01cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc00058f10ca42ee1c192d002ecabdccccd02fcabdccccd0300031c332003300340035003600370038c21e00cc8600068262031a000a8606000705080209140a938800c3019b9300c297000445000000009307c397000424010001009308c29700040b7f0100009309c29700000100000000930ac2970004097f010000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc2970000000000000002dc004093c200ca3f80000093c201cac190000093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c003dc001492c2c292c2c292c2c392c2c392c2c392c2c392c2c292c2c392c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c204ab46656e64657220444c58000ec305ca42ee1c190c008800c3019b9300c297000445010000009307c3970004247f0000009308c29700040b7f0100009309c29700000100000000930ac2970004097f010000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc2970000000000000002dc004093c200ca3f80000093c201cac190000093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c003dc001492c2c292c2c292c2c392c2c392c2c392c2c392c2c292c2c392c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c204ab46656e64657220424f58000ec305ca42ee1c190c008800c3019b9300c297000445020000009307c3970004247f0001009308c29700040b7f0100009309c29700000100000000930ac29700003064000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc2970000000000000002dc004093c200ca3f80000093c201cac190000093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c003dc001492c2c292c2c292c2c392c2c392c2c392c2c392c2c292c2c392c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c204ab46656e64657220444c58000ec305ca42ee1c190c000ddc0014c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c30cdc0080da0021363366353935626236646663333736393732313432386536313463346135623700da0021643534656536386230666634363261356263323862646631343434393936393900da0021313832613037343837623234356261663864613431393965323732646162623400da0021326338323536313363336132303765616635306332333937343133306562656600da0021653238373934663664373361663039643764633735396661663862323333353100da0021323337306533366662306661313965376331666637633064303663376538356200da0021633034323635316131373365303039373833633933616432666532343037623800da0021623531623761313163353331363833643433326261646432633064373839336300da0021623762353037323032613137333835393436366465336332313039336338636600da0021393065363133623261356238313532323663383861613935383437363964346200da0021346635613566336538653464376539343861303665303666306438366139396200da0021386337666266656263633966303262316539373639623530346632333361653900da0021313432306232373039616438343330626233316263353438376261356631346100da0021363366353935626236646663333736393732313432386536313463346135623700da0021313035393238653236663637613962636336356361353137663934396237316100da0021333630326664636365663836663534643231373930666239623634646236386400da0021343463343166303936363832656562346266316266653430393637303039316200da0021396138326161653265663634313833353063613436353065383533363936303000da0021386339386231393365343062313035316132383333313431356239303932643100da0021653565656362396535333165383430353866363635626366393837666236363000da0021653230633239643264353732356534623038613535623738666530663165616300da0021363130383330636336386630363230643538623037343137356534383039393500da0021623362343338363535386639343535373761326534633138376166653639366100da0021623766613563396239333463336166383136386331303837373130396263656100da0021333431663732613663323936333232333765643264306133353566316438623200da0021326332346164333064616136613834386239366232643065373133313561383600a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100656432"
    # 01c - Cl+Rhy
    data = "000054005f1000008366cd03f8670068da1054a96c362d68656c697800da00303d000000600000003603000038030000d8030000c2040000b2050000df0500003e000000e5050000dc0b0000dc0b00008a078324a45033330023ce0380000025b276332e37312d33322d6731303339363631000082150116dc0014821300148205010783020303030493c3cac2400000ca3f0000008213061485188317c219771aff09010ac30b83020703070497cac214666603ca3d1ba5e0ca3e4cccd0ca3f800000ca40e00000ca40c000000c830200030004908213061485188317c3192a1a3609120ac30b83020c030c049cca3eccccccca3ec7ae14ca3f333334ca3f147ae0ca3e800000ca3f4cccccca3f800000ca3f000000ca3f000000ca3ea8f5c4ca3f19999aca3f0000000c83020603050496ca40400000ca42a00000ca45fa0000ca00000000ca000000000582130814c082130814c082130814c082130814c082130814c08213061485188317c219ccfe1aff091d0ac30b83020203020492ca00000000ca000000000c83020003000490821301148206010783020203020492ca3f000000ca0000000082130214830e82050007830200030004900f8408cd01010d010ac30783020303030493ca3f000000ca3f000000c212c382130814c082130814c08213061485188317c219651aff09010ac30b83020303030493ca00000000ca3f800000ca3f2b85200c830200030004908313061c011485188317c2190a1aff09110ac30b83020c030c049cca3f266666ca3d8f5c30ca3f000000ca3f4cccccca3f4cccccca3f400000ca3eccccccca3d23d700ca3f000000ca3f000000ca3e800000ca3f0000000c830200030004908313061c021485188317c219cc961aff09140ac30b8302050305049501ca419f3333ca469d0800ca3f800000cac19000001bda002136336635393562623664666333373639373231343238653631346334613562370082130814c08213061485188317c219501aff09080ac30b83020703060497ca3e999998ca3d8f5c30ca00000000ca0000000006c2c20c8302000300049082130814c08213031483108206000783020003000490118408cc970d080ac30783020603060496ca00000000ca3ba3d700cac2700000ca3f800000c2ca0000000012c301c003820702089591870a000b84000305a54e6f74650006ce0007100c07c20cc20ea7434c2f524859000dc310040fc391870a000b84000305a54e6f74650006ce0007100c07c20cc20ea6536f6c6f3e000dc310020fc391870a000b84000305a54e6f74650006ce0007100c07c20cc30ea7426e64486c70000dc310080fc3c091870a000b84000305a54e6f74650006ce0007100c07c20cc30ea1000dc210000fc2049ac0c0c0c0c0c0c0c09682000501890008011702cac270000003ca000000000400051306831c001d0229c207000dc282000401890008011702ca0000000003cac1f000000400051306831c001d0029c207000dc282000301890008011c02ca0000000003ca3e1999980400051106831c001d0229c207000dc282000201890008010702cac270000003cac19000000400050f06831c001d0429c207000dc282000101890008011c02ca3f26666603ca3f7333340400050e06831c001d0029c207000dc282000001890008011c02ca3f40000003ca3f6666660400050e06831c001d0529c207000dc2c00282009dd10012d10000d10000d10000d10000d10000d10005d10005d10005d10000d10005d10000d10000019d97cc12cc04cc15cc28cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc05cc04cc18cc7fcc00cc00cc0097cc05cc04cc24cc7fcc00cc00cc0097cc05cc04cc0bcc7fcc01cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc05cc04cc09cc7fcc01cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc00058f10ca42ee1c192d002ecabdccccd02fcabdccccd0300031c332003300340035003600370038c21e00cc86000682620f1a000a8606000705080609140a938800c3019b9300c297000415280000009306c2970004187f0000009307c2970004247f0000009308c29700040b7f010000930ac2970004097f010000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc2970000000000000002dc004093c200ca3f40000093c201ca3f26666693c202cac190000093c203ca0000000093c204ca0000000093c205cac270000093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c003dc001492c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c204ab46656e64657220444c58000ec305ca42ee1c190c008800c3019b9300c297000445010000009306c297000030640100009307c2970004247f0000009308c29700040b7f010000930ac2970004097f010000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc2970000000000000002dc004093c200ca3f40000093c201ca3f26666693c202cac190000093c203ca0000000093c204ca0000000093c205cac270000093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c003dc001492c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c204ab44756573656e62657267000ec305ca42ee1c190c008800c3019b9300c297000445020000009306c297000030640100009307c2970004247f0000009308c29700040b7f010000930ac29700003064000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc2970000000000000002dc004093c200ca3f40000093c201ca3ecccccc93c202cac190000093c203ca0000000093c204ca0000000093c205cac270000093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c003dc001492c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c204ab46656e64657220444c58000ec305ca42ee1c190c000ddc0014c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c30cdc0080da0021363366353935626236646663333736393732313432386536313463346135623700da0021643534656536386230666634363261356263323862646631343434393936393900da0021313832613037343837623234356261663864613431393965323732646162623400da0021326338323536313363336132303765616635306332333937343133306562656600da0021653238373934663664373361663039643764633735396661663862323333353100da0021323337306533366662306661313965376331666637633064303663376538356200da0021633034323635316131373365303039373833633933616432666532343037623800da0021623531623761313163353331363833643433326261646432633064373839336300da0021623762353037323032613137333835393436366465336332313039336338636600da0021393065363133623261356238313532323663383861613935383437363964346200da0021346635613566336538653464376539343861303665303666306438366139396200da0021386337666266656263633966303262316539373639623530346632333361653900da0021313432306232373039616438343330626233316263353438376261356631346100da0021363366353935626236646663333736393732313432386536313463346135623700da0021313035393238653236663637613962636336356361353137663934396237316100da0021333630326664636365663836663534643231373930666239623634646236386400da0021343463343166303936363832656562346266316266653430393637303039316200da0021396138326161653265663634313833353063613436353065383533363936303000da0021386339386231393365343062313035316132383333313431356239303932643100da0021653565656362396535333165383430353866363635626366393837666236363000da0021653230633239643264353732356534623038613535623738666530663165616300da0021363130383330636336386630363230643538623037343137356534383039393500da0021623362343338363535386639343535373761326534633138376166653639366100da0021623766613563396239333463336166383136386331303837373130396263656100da0021333431663732613663323936333232333765643264306133353566316438623200da0021326332346164333064616136613834386239366232643065373133313561383600a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a100a10065"
    # 13c = New Preset
    data = "0000f400ff0c00008366cd0345670068da0cf4a96c362d68656c697800da00303d00000060000000ee020000f0020000990300008605000076060000a30600003e000000a9060000f40c0000f40c000089078324a45033330023ce0380000025b276332e37312d33322d6731303339363631000082150016dc0014821300148205010783020303030493c2cac2400000ca3f0000008213061485188317c219cd01051aff09010ac20b83020203020492ca3f800000c20c830200030004908213061485188317c219cd02021aff09110ac30b83020b030b049bca3eccccccca3f000000ca3f07ae14ca3f428f5cca3f47ae14ca3f199998ca3f000000ca3f000000ca3f000000ca3f000000ca3f0000000c830200030004908213061485188317c319371a3709100ac30b83020603050496ca3f800000ca419f3333ca469d0800ca3dccccd0ca340000000c0c83020603050496ca40d00000ca419f3333ca469d0800ca00000000cac0800000058213061485188317c219cd01f01aff09080ac30b83020703060497ca3e999998ca3ca3d700ca3eccccccca3df5c290ca3e4cccd0ca00000000c30c830200030004908213061485188317c219cc831aff09010ac30b83020c030c049cca43020000ca3fb33334ca00000000ca43de8000ca3fa66668cac0400000ca458ca000ca3f99999aca40000000ca42c80000ca463b8000ca000000000c830200030004908213061485188317c219781aff09010ac30b83020603060496ca3f0cccccca3f000000c2ca3db851f0ca3f400000ca000000000c8302000300049082130814c082130814c0821301148206010783020203020492ca3f000000cac00ccccd82130214830e82050007830200030004900f8408cd01010d000ac30783020303030493ca3f000000ca3f000000c212c282130814c082130814c082130814c082130814c082130814c082130814c082130814c082130814c08213031483108206000783020003000490118408cc970d000ac30783020603060496ca00000000ca3f000000ca00000000ca3f000000c2ca0000000012c201c003820701089591870a000b85000105a947616e796d6564650006ce00ff2d0007c308040cc20ea1000dc210000fc291870a000b85000105af4c412053747564696f20436f6d700006ce0084ff0007c308060cc20ea1000dc210000fc2c0c092870a000b84000305a54e6f74650006ce0007100c07c20cc30ea1000dc210000fc2870a010b85000105ad566f6c756d6520506564616c0006cd0d0607c208010cc30ea1000dc210000fc2049ac0c09182000001890002010402ca0000000003ca3f8000000400050106831c001d0029c207000dc2c0c0c0c0c0c09c82000c01890009010402cac270000003ca40c000000400050306831c011d0429c207010dc282000b01890009010402ca3f80000003ca414000000400050306831c011d0029c207010dc282000a01890009010402ca0000000003ca3f8000000400050406831c001d0229c207000dc282000901890009010402ca0000000003ca3f8000000400050406831c001d0429c207000dc282000801890009010402ca0000000003ca3f8000000400050406831c001d0029c207000dc282000701890009010402ca0000000003ca3f8000000400050206831c001d0329c207000dc282000601890009010402ca0000000003ca3f8000000400050206831c001d0429c207000dc282000501890009010402ca0000000003ca3f8000000400050206831c001d0229c207000dc282000401890009010402ca0000000003ca3f8000000400050206831c001d0629c207000dc282000301890009010402ca0000000003ca3f8000000400050206831c001d0029c207000dc282000201890009010402ca0000000003ca3f8000000400050206831c001d0529c207000dc282000101890009010402ca0000000003ca3f8000000400050206831c001d0129c207000dc20282009dd10000d10000d10000d10000d10000d10000d10000d10000d10000d10000d10005d10000d10000019d97cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc05cc04cc09cc7fcc01cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc00058f10ca42f000002d002ecabdccccd02fcabdccccd0300031c332003300340035003600370038c21e00cc8600068262021a000a8606000701080d09140a938800c3019b930ac2970004097f010000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc2970000000000000002dc004093c200ca3f80000093c201ca3f00000093c202ca3f19999893c203ca3ecccccc93c204ca3f00000093c205ca3f07ae1493c206ca3f47ae1493c207ca3f428f5c93c208ca3e99999893c209ca3e4cccd093c20aca3ecccccc93c20bca40d0000093c20ccac080000093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c003dc001492c2c292c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c204ab534e415053484f542031000ec205ca42f000000c008800c3019b930ac29700003064000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc2970000000000000002dc004093c200ca3f80000093c201ca3e4cccd093c202ca3ef5c29093c203ca3f33333493c204ca3f19999893c205ca3efae14893c206ca3f4f5c2893c207ca3f428f5c93c208ca3d75c28093c209ca3dccccd093c20aca3e4cccd093c20bca40c0000093c20cca0000000093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c003dc001492c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c204ab534e415053484f542032000ec205ca42f000000c008800c3019b930ac29700003064000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc2970000000000000002dc004093c200ca3f80000093c201ca3e99999893c202ca3ed70a3c93c203ca3f4ccccc93c204ca3f80000093c205ca3ef0a3d893c206ca3f47ae1493c207ca3f428f5c93c208ca3dccccd093c209ca3da3d71093c20aca3f19999893c20bca40e0000093c20cca0000000093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c003dc001492c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c204ab534e415053484f542033000ec205ca42f000000c000ddc0014c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c0"
    # 17c - New Preset
    data = "000084008f0b00008366cd03f4670068da0b84a96c362d68656c697800da00303d000000600000000f03000011030000bc0300008e0400007e050000ab0500003e000000b1050000840b0000840b000089078324a45033330023ce0380000025b276332e37312d33322d6731303339363631000082150016dc0014821300148205010783020303030493c2cac2400000ca3f0000008213061485188317c219771aff09010ac30b83020703070497cac214666603ca3d1ba5e0ca3e4cccd0ca3f800000ca40c00000ca40c000000c830200030004908213061485188317c219cd01d81aff09010ac20b83020403040494ca3e999998ca0000000006c20c830200030004908213061485188317c219cd012b1aff09010ac30b83020d030d049d00ca41100001ca00000000ca3f00000000cac10fffffca00000000ca3f000000ca3e4cccd0ca00000000ca00000000ca3f800000ca3f0000000c830200030004908213061485188317c319cd01f41a4009120ac30b830211031104dc0011ca3dccccd0ca3f000000ca3ed70a3cca3f000000ca3e800000ca3f6e147cca3e800000ca3f400000c2c2c2c3ca3f000000ca3f000000ca3f00000002c20c83020603050496ca40000000ca42480000ca4684d000ca00000000ca00000000068213061485188317c2195b1aff09080ac30b83020b030a049bca3f4cccccca3eccccccca3f000000ca3f800000ca3e999998ca00000000ca42c80000ca460b1000c206c30c830200030004908213061485188317c219ccf01aff09080ac30b83020703060497ca3f000000ca3dccccd0ca430f0000ca4592e000ca3eccccccca00000000c20c8302000300049082130814c082130814c0821301148206010783020203020492ca3f000000ca40a9999a82130214830e82050007830200030004900f8408cd01010d000ac30783020303030493ca3f000000ca3f000000c212c282130814c082130814c082130814c082130814c082130814c082130814c082130814c082130814c08213031483108206000783020003000490118408cc970d000ac30783020603060496ca00000000ca3f000000ca00000000ca3f000000c2ca0000000012c201c003820702089591870a000b85000105ab4475616c2050697463680006ce003200ff07c308030cc20ea1000dc210000fc292870a000b85000105aa50696e6720506f6e670006ce0006ff0007c308050cc20ea1000dc210000fc2870a010b85000105a84368616d6265720006ce00ff2d0007c308060cc20ea1000dc210000fc291870a000b85000105ad5363726970742050686173650006cd040d07c208020cc20ea1000dc210000fc2c0c0049ac0c0c0c0c0c0c0c0c09682000501890009010402ca0000000003ca3f8000000400050506831c001d0429c207000dc282000401890009010402ca0000000003ca3f8000000400050406831c001d0629c207000dc282000301890009010402c203c30400050406831c001d0829c207000dc282000201890009010402c203c30400050406831c001d0929c207000dc282000101890009010402ca0000000003ca3f8000000400050406831c001d0029c207000dc282000001890009010402c203c30400050406831c001d0a29c207000dc20282009dd10000d10000d10000d10000d10000d10000d10000d10000d10000d10000d10000d10000d10000019d97cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc0097cc00cc00cc00cc00cc00cc00cc00058f10ca42f000002d002ecabdccccd02fcabdccccd0300031c332003300340035003600370038c21e00cc8600068262041a000a8606000700080609140a938800c3019b930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc2970000000000000002dc004093c200c293c201ca3f00000093c202c393c203c293c204ca3f00000093c205ca3ee6666893c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c003dc001492c2c292c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c204ab534e415053484f542031000ec205ca42f000000c008800c3019b930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc2970000000000000002dc004093c200c293c201ca3f00000093c202c393c203c293c204ca3f00000093c205ca3ee6666893c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c003dc001492c2c292c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c204ab534e415053484f542032000ec205ca42f000000c008800c3019b930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc29700000000000000930dc2970000000000000002dc004093c200c293c201ca3f00000093c202c393c203c293c204ca3f00000093c205ca3ee6666893c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c093c240c003dc001492c2c292c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c292c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c392c2c204ab534e415053484f542033000ec205ca42f000000c000ddc0014c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c0"
    fs_info_list = fs_info_extract(data)

    for fs_info in fs_info_list:
        print(fs_info.to_string())

    print("")
    slots = slot_extract(data)
    for slot in slots:
        print(slot.to_string())
    main(sys.argv)
