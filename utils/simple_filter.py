import sys
import csv
from utils.formatter import format_1, ieee754_to_rendered_str
from modules import modules


class SlotInfo:
    def __init__(self):
        self.slot_no = 0
        self.on_off_state = 0

    def __eq__(self, other):
        if isinstance(other, SlotInfo) is False:
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
        return True

    def category(self):
        return None

    def to_string(self):
        # return '\'Standard Module: ' + self.module_id + ' - ' + str(self.params)
        return str(self.slot_no) + ':-'


class StandardSlotInfo(SlotInfo):
    def __init__(self):
        SlotInfo.__init__(self)
        self.module_id = ''
        self.params = []

    def __eq__(self, other):
        if isinstance(other, StandardSlotInfo) is False:
            return False
        if other.module_id != self.module_id:
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
            return str(self.slot_no) + ":" + description[0] + ' (' + description[1] + ')'
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
            return str(self.slot_no) + ":Amp+Cab (" + amp_description[1] + ' + ' + cab_description[1] + ')'
        except KeyError:
            print("ERROR: can't find module in modules: " + str(self.module_id))
            return str(self.slot_no) + ':NO MATCH FOR Amp: ' + self.amp_id + ', Cab: ' + self.cab_id

        # return '\'Amp: ' + self.amp_id + ', Cab: ' + self.amp_id + ' - Amp-Parameter: ' + str(self.amp_params) + ', Cab-Parameter: ' + str(self.cab_params)
        return str(self.amp_id + '1a' + self.cab_id)


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
                    '''
                    print("\'", end="")
                    for i in range(idx-4, idx):
                        print(value[i], end='')
                    print()
                    '''
                    #
                    print('\'' + value[idx-4:idx])
                    return
                except ValueError as _e:
                    pass
    print("No slot id found: " + value)


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


def parse_dual_cab_slot(slot_data):

    try:
        idx = slot_data.index('09100ac')
    except ValueError:
        return None

    slot_info = CabsDualSlotInfo()
    ac_data = slot_data[16:idx]

    '''
    try:
        idx_od_cd = ac_data.index('cd')
        ac_data_tmp = ac_data[0:idx_od_cd]
        ac_data_tmp += ac_data[idx_od_cd + 4:]
        ac_data = ac_data_tmp
    except ValueError:
        pass
    '''
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
        '''
        try:
            idx_od_cd = ac_data.index('cd')
            ac_data_tmp = ac_data[0:idx_od_cd]
            ac_data_tmp += ac_data[idx_od_cd + 4:]
            ac_data = ac_data_tmp
        except ValueError:
            pass
        '''

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


def slot_splitter_2(val):
    slots = val.split('8213')

    # find first slot starting with either 06 or 08
    slot_1_idx = -1
    for i, slot in enumerate(slots):
        if slot.startswith('06') or slot.startswith('08'):
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

    if not slots[0].startswith('00'):
        print("ERROR: Expected slot 0 (Chain 1 Input) to start with 00")
    if not slots[9].startswith('01'):
        print("ERROR: Expected slot 9 (Chain 1 Master) to start with 00")
    if not slots[10].startswith('02'):
        print("ERROR: Expected slot 10 (Chain 2 Input) to start with 00")
    if not slots[19].startswith('03'):
        print("ERROR: Expected slot 19 (Chain 2 Master) to start with 00")

    assignable_slots = [1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15, 16, 17, 18]
    for slot_idx in assignable_slots:
        if not (slot.startswith('06') or slot.startswith('08')):
            print("ERROR: Expected slot " + str(slot_idx) + " to start with 06 or 08")

    slot_infos = []
    for slot_idx in assignable_slots:
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
    main(sys.argv)
