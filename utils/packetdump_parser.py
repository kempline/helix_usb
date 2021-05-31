import csv
import re
import sys
import xlsxwriter
from usb_helper import UsbHelper


def extract_data(data_lines):
	data_to_capture = []
	local_data = []

	for line in data_lines:
		x = re.search("([0-9a-fA-F]{4})  ([0-9a-f ]+)   (.+)", line)
		if x is not None:
			hex_only = x.group(2)
			single_data = hex_only.split(' ')
			for d in single_data:
				if d == '':
					continue
				local_data.append(d)
			pass
	local_data = local_data[27:]
	return local_data


def export_all_endpoints(path_wireshark_dump, path_out_xlsx):
	with open(path_wireshark_dump) as csv_file:
		wireshark_dump_csv_reader = csv.reader(csv_file, delimiter=',')
		workbook = xlsxwriter.Workbook(path_out_xlsx)
		format_x1_x10 = workbook.add_format()
		format_x2_x10 = workbook.add_format()
		format_x80_x10 = workbook.add_format()

		format_x1_x10.set_pattern(1)
		format_x2_x10.set_pattern(1)
		format_x80_x10.set_pattern(1)
		format_x1_x10.set_bg_color('edf0e0')
		format_x2_x10.set_bg_color('f5c9ce')
		format_x80_x10.set_bg_color('fbeaa5')

		worksheet_all_ports = workbook.add_worksheet("all")
		worksheet_x1x10 = workbook.add_worksheet("x1x10")
		worksheet_x2x10 = workbook.add_worksheet("x2x10")
		worksheet_x80x10 = workbook.add_worksheet("x80x10")

		data_from_kpa = []
		current_frame_no = 0
		current_endpoint_address = 0
		current_time = 0
		capture_data_line_detected = False
		packet_data_recorder = []

		endpoint_x1_times = [0, 0, 0]
		endpoint_x81_times = [0, 0, 0]

		xlsx_row_num = 0
		x1_x10_row_num = 0
		x2_x10_row_num = 0
		x80_x10_row_num = 0
		for row in wireshark_dump_csv_reader:

			if len(row) == 0:
				continue
			str_row = row[0]

			x = re.search("([0-9]+)\s([0-9]+.[0-9]+).+host.+USB", str_row)
			if x is not None:
				current_time = x.group(2)
			if str_row.startswith('Frame '):
				idx_dp = str_row.index(':')
				current_frame_no = str_row[6:idx_dp]

			parts = str_row.split('    Endpoint: ')
			if len(parts) > 1:
				current_endpoint_address = parts[1]

			if capture_data_line_detected is True:
				packet_data_recorder.append(str_row)
			if str_row.startswith('Leftover Capture Data: '):
				capture_data_line_detected = True
			if str_row.startswith('No.     Time'):
				capture_data_line_detected = False

				if len(packet_data_recorder) > 0:

					# need 272 bytes
					full_data = extract_data(packet_data_recorder)
					full_data_int = []
					full_data_str = ''
					for d in full_data:
						full_data_int.append(int(d, 16))

					for i, d in enumerate(full_data_int):
						e = hex(d)
						if i == 9:
							full_data_str += (e + ', ')
						else:
							full_data_str += (e + ', ')

					if full_data_str.endswith(', '):
						full_data_str = full_data_str[:-2]

					data_row = [''] * 14

					if current_endpoint_address == '0x01':
						if full_data_int[4] == 0x1 and full_data_int[5] == 0x10:

							worksheet_all_ports.write('A' + str(xlsx_row_num), current_frame_no)
							worksheet_all_ports.write('B' + str(xlsx_row_num), current_time)
							worksheet_all_ports.write('E' + str(xlsx_row_num), full_data_str, format_x1_x10)
							worksheet_all_ports.write('C' + str(xlsx_row_num), str(float(current_time) - endpoint_x1_times[0]))
							worksheet_all_ports.write('D' + str(xlsx_row_num), str(float(current_time) - endpoint_x81_times[0]))

							worksheet_x1x10.write('A' + str(x1_x10_row_num), current_frame_no)
							worksheet_x1x10.write('B' + str(x1_x10_row_num), current_time)
							worksheet_x1x10.write('E' + str(x1_x10_row_num), full_data_str, format_x1_x10)
							worksheet_x1x10.write('C' + str(x1_x10_row_num), str(float(current_time) - endpoint_x1_times[0]))
							worksheet_x1x10.write('D' + str(x1_x10_row_num), str(float(current_time) - endpoint_x81_times[0]))
							x1_x10_row_num += 1

							endpoint_x1_times[0] = float(current_time)

						elif full_data_int[4] == 0x2 and full_data_int[5] == 0x10:

							worksheet_all_ports.write('A' + str(xlsx_row_num), current_frame_no)
							worksheet_all_ports.write('B' + str(xlsx_row_num), current_time)
							worksheet_all_ports.write('E' + str(xlsx_row_num), full_data_str, format_x2_x10)
							worksheet_all_ports.write('C' + str(xlsx_row_num), str(float(current_time) - endpoint_x1_times[1]))
							worksheet_all_ports.write('D' + str(xlsx_row_num), str(float(current_time) - endpoint_x81_times[1]))

							worksheet_x2x10.write('A' + str(x2_x10_row_num), current_frame_no)
							worksheet_x2x10.write('B' + str(x2_x10_row_num), current_time)
							worksheet_x2x10.write('E' + str(x2_x10_row_num), full_data_str, format_x2_x10)
							worksheet_x2x10.write('C' + str(x2_x10_row_num), str(float(current_time) - endpoint_x1_times[1]))
							worksheet_x2x10.write('D' + str(x2_x10_row_num), str(float(current_time) - endpoint_x81_times[1]))
							x2_x10_row_num += 1

							endpoint_x1_times[1] = float(current_time)

						elif full_data_int[4] == 0x80 and full_data_int[5] == 0x10:

							worksheet_all_ports.write('A' + str(xlsx_row_num), current_frame_no)
							worksheet_all_ports.write('B' + str(xlsx_row_num), current_time)
							worksheet_all_ports.write('E' + str(xlsx_row_num), full_data_str, format_x80_x10)
							worksheet_all_ports.write('C' + str(xlsx_row_num), str(float(current_time) - endpoint_x1_times[2]))
							worksheet_all_ports.write('D' + str(xlsx_row_num), str(float(current_time) - endpoint_x81_times[2]))

							worksheet_x80x10.write('A' + str(x80_x10_row_num), current_frame_no)
							worksheet_x80x10.write('B' + str(x80_x10_row_num), current_time)
							worksheet_x80x10.write('E' + str(x80_x10_row_num), full_data_str, format_x80_x10)
							worksheet_x80x10.write('C' + str(x80_x10_row_num), str(float(current_time) - endpoint_x1_times[2]))
							worksheet_x80x10.write('D' + str(x80_x10_row_num), str(float(current_time) - endpoint_x81_times[2]))
							x80_x10_row_num += 1

							endpoint_x1_times[2] = float(current_time)

						else:
							print("WARNING: Unknown communication path in endpoint 0x1")

						data_from_kpa.append(data_row)
						xlsx_row_num += 1
					elif current_endpoint_address == '0x81':
						if full_data_int[6] == 0x1 and full_data_int[7] == 0x10:

							worksheet_all_ports.write('A' + str(xlsx_row_num), current_frame_no)
							worksheet_all_ports.write('B' + str(xlsx_row_num), current_time)
							worksheet_all_ports.write('F' + str(xlsx_row_num), full_data_str, format_x1_x10)

							worksheet_x1x10.write('A' + str(x1_x10_row_num), current_frame_no)
							worksheet_x1x10.write('B' + str(x1_x10_row_num), current_time)
							worksheet_x1x10.write('F' + str(x1_x10_row_num), full_data_str, format_x1_x10)
							x1_x10_row_num += 1
							endpoint_x81_times[0] = float(current_time)

						elif full_data_int[6] == 0x2 and full_data_int[7] == 0x10:

							worksheet_all_ports.write('A' + str(xlsx_row_num), current_frame_no)
							worksheet_all_ports.write('B' + str(xlsx_row_num), current_time)
							worksheet_all_ports.write('F' + str(xlsx_row_num), full_data_str, format_x2_x10)

							worksheet_x2x10.write('A' + str(x2_x10_row_num), current_frame_no)
							worksheet_x2x10.write('B' + str(x2_x10_row_num), current_time)
							worksheet_x2x10.write('F' + str(x2_x10_row_num), full_data_str, format_x2_x10)
							x2_x10_row_num += 1
							endpoint_x81_times[1] = float(current_time)

						elif full_data_int[6] == 0x80 and full_data_int[7] == 0x10:

							worksheet_all_ports.write('A' + str(xlsx_row_num), current_frame_no)
							worksheet_all_ports.write('B' + str(xlsx_row_num), current_time)
							worksheet_all_ports.write('F' + str(xlsx_row_num), full_data_str, format_x80_x10)

							worksheet_x80x10.write('A' + str(x80_x10_row_num), current_frame_no)
							worksheet_x80x10.write('B' + str(x80_x10_row_num), current_time)
							worksheet_x80x10.write('F' + str(x80_x10_row_num), full_data_str, format_x80_x10)
							x80_x10_row_num += 1

							endpoint_x81_times[2] = float(current_time)
						else:
							print("WARNING: Unknown communication path in endpoint 0x81")
						data_from_kpa.append(data_row)
						xlsx_row_num += 1
					else:
						print("WARNING: Unknown endpoint: " + str(current_endpoint_address))
				packet_data_recorder = []

		workbook.close()
		return


def export_all_endpoints_legacy(path_wireshark_dump, path_out_csv):
	with open(path_wireshark_dump) as csv_file:
		csv_reader = csv.reader(csv_file, delimiter=',')
		data_from_kpa = []
		current_frame_no = 0
		current_endpoint_address = 0
		current_time = 0
		capture_data_line_detected = False
		packet_data_recorder = []

		endpoint_x1_times = [0, 0, 0]
		endpoint_x81_times = [0, 0, 0]

		for row in csv_reader:

			if len(row) == 0:
				continue
			str_row = row[0]

			x = re.search("([0-9]+)\s([0-9]+.[0-9]+).+host.+USB", str_row)
			if x is not None:
				current_time = x.group(2)
			if str_row.startswith('Frame '):
				idx_dp = str_row.index(':')
				current_frame_no = str_row[6:idx_dp]

			parts = str_row.split('    Endpoint: ')
			if len(parts) > 1:
				current_endpoint_address = parts[1]

			if capture_data_line_detected is True:
				packet_data_recorder.append(str_row)
			if str_row.startswith('Leftover Capture Data: '):
				capture_data_line_detected = True
			if str_row.startswith('No.     Time'):
				capture_data_line_detected = False

				if len(packet_data_recorder) > 0:

					# need 272 bytes
					full_data = extract_data(packet_data_recorder)
					full_data_int = []
					full_data_str = ''
					for d in full_data:
						full_data_int.append(int(d, 16))

					for d in full_data_int:
						e = hex(d)
						full_data_str += (e + ', ')
					if full_data_str.endswith(', '):
						full_data_str = full_data_str[:-2]

					data_row = [''] * 14
					data_row[0] = current_frame_no
					data_row[1] = current_time

					if current_endpoint_address == '0x01':
						if full_data_int[4] == 0x1 and full_data_int[5] == 0x10:
							data_row[2] = full_data_str										# x1x10 OUT
							data_row[3] = ''												# x1x10 IN
							data_row[4] = str(float(current_time) - endpoint_x1_times[0]) 	# x1x10 out-out
							data_row[5] = str(float(current_time) - endpoint_x81_times[0]) 	# x1x10 in-out
							endpoint_x1_times[0] = float(current_time)

						elif full_data_int[4] == 0x2 and full_data_int[5] == 0x10:
							data_row[6] = full_data_str  # x1x10 OUT
							data_row[7] = ''  # x1x10 IN
							data_row[8] = str(float(current_time) - endpoint_x1_times[1])  # x1x10 out-out
							data_row[9] = str(float(current_time) - endpoint_x81_times[1])  # x1x10 in-out
							endpoint_x1_times[1] = float(current_time)

						elif full_data_int[4] == 0x80 and full_data_int[5] == 0x10:
							data_row[10] = full_data_str  # x1x10 OUT
							data_row[11] = ''  # x1x10 IN
							data_row[12] = str(float(current_time) - endpoint_x1_times[2])  # x1x10 out-out
							data_row[13] = str(float(current_time) - endpoint_x81_times[2])  # x1x10 in-out
							endpoint_x1_times[2] = float(current_time)

						else:
							print("WARNING: Unknown communication path in endpoint 0x1")

						data_from_kpa.append(data_row)
					elif current_endpoint_address == '0x81':
						if full_data_int[6] == 0x1 and full_data_int[7] == 0x10:
							data_row[2] = ''  # x1x10 OUT
							data_row[3] = full_data_str  # x1x10 IN
							data_row[4] = ''  # x1x10 out-out
							data_row[5] = ''  # x1x10 in-out
							endpoint_x81_times[0] = float(current_time)

						elif full_data_int[6] == 0x2 and full_data_int[7] == 0x10:
							data_row[6] = ''  # x1x10 OUT
							data_row[7] = full_data_str  # x1x10 IN
							data_row[8] = ''  # x1x10 out-out
							data_row[9] = ''  # x1x10 in-out
							endpoint_x81_times[1] = float(current_time)

						elif full_data_int[6] == 0x80 and full_data_int[7] == 0x10:
							data_row[10] = ''  # x1x10 OUT
							data_row[11] = full_data_str  # x1x10 IN
							data_row[12] = ''  # x1x10 out-out
							data_row[13] = ''  # x1x10 in-out
							endpoint_x81_times[2] = float(current_time)
						else:
							print("WARNING: Unknown communication path in endpoint 0x81")
							continue
						data_from_kpa.append(data_row)
					else:
						print("WARNING: Unknown endpoint: " + current_endpoint_address)
				packet_data_recorder = []

		with open(path_out_csv, mode='w') as test_data_out_file:
			test_data_writer = csv.writer(test_data_out_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
			test_data_writer.writerow(['no', 'time', 'x1x10 OUT', 'x1x10 IN', 'x1x10 out-out', 'x1x10 in-out', 'x2x10 OUT', 'x2x10 IN', 'x2x10 out-out', 'x2x10 in-out', 'x1x80 OUT', 'x80x10 IN', 'x80x10 out-out', 'x80x10 in-out'])
			for test_data_entry in data_from_kpa:
				test_data_writer.writerow(test_data_entry)


file_list = [
	"all_amps_PLUS_cabs_in_slot_3_all_other_slots_empty",
	"all_amps_in_slot_3_all_other_slots_empty",
	"all_cabs_in_slot_3_all_other_slots_empty",
	"all_delays_in_slot_3_all_other_slots_empty",
	"all_drives_in_slot_3_all_other_slots_empty_ERROR_switching_to_Clathorn_Drive",
	"all_dynamics_in_slot_3_all_other_slots_empty",
	"all_eqs_in_slot_3_all_other_slots_empty",
	"all_filter_in_slot_3_all_other_slots_empty",
	"all_loopers_in_slot_3_all_other_slots_empty",
	"all_modulationsV2_in_slot_3_all_other_slots_empty",
	"all_modulations_in_slot_3_all_other_slots_empty",
	"all_pitch_synths_in_slot_3_all_other_slots_empty",
	"all_preamps_in_slot_3_all_other_slots_empty",
	"all_reverbs_in_slot_3_all_other_slots_empty",
	"all_send_return_in_slot_3_all_other_slots_empty",
	"all_vol_pan_in_slot_3_all_other_slots_empty",
	"all_wahs_in_slot_3_all_other_slots_empty",
	"all_modulationsSTEREO_in_slot_3_all_other_slots_empty",
	"all_reverbsSTEREO_in_slot_3_all_other_slots_empty",
	"all_eqsSTEREO_in_slot_3_all_other_slots_empty"
]


file_list = [
	"all_BASSamps_in_slot_3_all_other_slots_empty",
	"all_BASSamps_PLUS_cabs_in_slot_3_all_other_slots_empty",
	"all_BASSpreamps_in_slot_3_all_other_slots_empty",
	"all_cabsDUAL_in_slot_3_all_other_slots_empty",
	"all_delaysLEGACY_in_slot_3_all_other_slots_empty",
	"all_delaysSTEREO_in_slot_3_all_other_slots_empty",
	"all_drivesLEGACY_in_slot_3_all_other_slots_empty",
	"all_drivesSTEREO_in_slot_3_all_other_slots_empty",
	"all_dynamicsLEGACY_in_slot_3_all_other_slots_empty",
	"all_dynamicsSTEREO_in_slot_3_all_other_slots_empty",
	"all_filterLEGACY_in_slot_3_all_other_slots_empty",
	"all_filterSTEREO_in_slot_3_all_other_slots_empty",
	"all_MIC_JUST_ONE_preamps_in_slot_3_all_other_slots_empty",
	"all_modulationsLEGACY_in_slot_3_all_other_slots_empty",
	"all_pitch_synthsLEGACY_in_slot_3_all_other_slots_empty",
	"all_pitch_synthsSTEREO_in_slot_3_all_other_slots_empty",
	"all_reverbsLEGACY_in_slot_3_all_other_slots_empty",
	"all_send_returnSTEREO_in_slot_3_all_other_slots_empty",
	"all_vol_panSTEREO_in_slot_3_all_other_slots_empty",
	"all_wahsSTEREO_in_slot_3_all_other_slots_empty"
]

file_list = [
	"ich_habe_garkein_auto_auf_main_display",
	"moving_slots_up_and_down"
]


def main(args):

	for file_path in file_list:
		export_all_endpoints('../doc/' + file_path + '.txt', '../doc/' + file_path + '.xlsx')

	return

	# export_all_endpoints('../doc/all_amps_in_slot_3_all_other_slots_empty.txt', '../doc/all_amps_in_slot_3_all_other_slots_empty.csv')
	export_all_endpoints('../doc/all_drives_in_slot_3_all_other_slots_empty_ERROR_switching_to_Clathorn_Drive.txt', '../doc/all_drives_in_slot_3_all_other_slots_empty_ERROR_switching_to_Clathorn_Drive.csv')
	export_all_endpoints('../doc/all_modulations_in_slot_3_all_other_slots_empty.txt', '../doc/all_modulations_in_slot_3_all_other_slots_empty.csv')
	'''
	export_all_endpoints('../doc/connect_two_times.txt', '../doc/connect_two_times.csv')
	export_all_endpoints('../doc/connect_with_Fender_Cl_and_running_for_30s.txt', '../doc/connect_with_Fender_Cl_and_running_for_30s.csv')
	export_all_endpoints('../doc/connected_with_1b_1c_2a.txt', '../doc/connected_with_1b_1c_2a.csv')
	export_all_endpoints('../doc/ramping_drive_from_0_to_10_to_0.txt', '../doc/ramping_drive_from_0_to_10_to_0.csv')
	export_all_endpoints('../doc/switching_mod_slot6_PitchRingMod_to_AmRingMod.txt', '../doc/switching_mod_slot6_PitchRingMod_to_AmRingMod.csv')
	export_all_endpoints('../doc/switching_rvb_slot5_from_Ganymede_to_Searchlights.txt', '../doc/switching_rvb_slot5_from_Ganymede_to_Searchlights.csv')
	export_all_endpoints('../doc/switching_mod_slot6_PitchRingMod_to_AmRingMod.txt', '../doc/switching_mod_slot6_PitchRingMod_to_AmRingMod.csv')
	'''

if __name__ == '__main__':
	main(sys.argv)