import xlsxwriter
from datetime import datetime
import logging
log = logging.getLogger(__name__)


class ExcelLogger:
	def __init__(self, out_path='./dump.xlsx'):
		self.out_path = out_path
		self.excel_workbook = xlsxwriter.Workbook(out_path)

		self.format_x1_x10 = self.excel_workbook.add_format()
		self.format_x2_x10 = self.excel_workbook.add_format()
		self.format_x80_x10 = self.excel_workbook.add_format()

		self.format_x1_x10.set_pattern(1)
		self.format_x2_x10.set_pattern(1)
		self.format_x80_x10.set_pattern(1)
		self.format_x1_x10.set_bg_color('edf0e0')
		self.format_x2_x10.set_bg_color('f5c9ce')
		self.format_x80_x10.set_bg_color('fbeaa5')

		self.worksheet_all_ports = self.excel_workbook.add_worksheet("all")
		self.worksheet_x1x10 = self.excel_workbook.add_worksheet("x1x10")
		self.worksheet_x2x10 = self.excel_workbook.add_worksheet("x2x10")
		self.worksheet_x80x10 = self.excel_workbook.add_worksheet("x80x10")

		self.xlsx_row_num = 0
		self.x1_x10_row_num = 0
		self.x2_x10_row_num = 0
		self.x80_x10_row_num = 0

		self.session_start_time = datetime.now()
		self.packet_count = 0

	def save(self):
		self.excel_workbook.close()
		self.excel_workbook = None
		log.info("Saved Excel sheet at: " + str(self.out_path))

	def log(self, data):
		if self.excel_workbook is None:
			return

		time_offset = datetime.now() - self.session_start_time
		full_data_str = ''

		for i, d in enumerate(data):
			e = hex(d)
			if i == 9:
				full_data_str += (e + ', ')
			else:
				full_data_str += (e + ', ')

		if full_data_str.endswith(', '):
			full_data_str = full_data_str[:-2]

		# OUT (Host to Device)
		if data[4] == 0x1:

			self.worksheet_all_ports.write('A' + str(self.xlsx_row_num), self.packet_count)
			self.worksheet_all_ports.write('B' + str(self.xlsx_row_num), str(time_offset))
			self.worksheet_all_ports.write('C' + str(self.xlsx_row_num), full_data_str, self.format_x1_x10)

			self.worksheet_x1x10.write('A' + str(self.x1_x10_row_num), self.packet_count)
			self.worksheet_x1x10.write('B' + str(self.x1_x10_row_num), str(time_offset))
			self.worksheet_x1x10.write('C' + str(self.x1_x10_row_num), full_data_str, self.format_x1_x10)

			self.x1_x10_row_num += 1

		elif data[4] == 0x2:

			self.worksheet_all_ports.write('A' + str(self.xlsx_row_num), self.packet_count)
			self.worksheet_all_ports.write('B' + str(self.xlsx_row_num), str(time_offset))
			self.worksheet_all_ports.write('C' + str(self.xlsx_row_num), full_data_str, self.format_x2_x10)

			self.worksheet_x2x10.write('A' + str(self.x2_x10_row_num), self.packet_count)
			self.worksheet_x2x10.write('B' + str(self.x2_x10_row_num), str(time_offset))
			self.worksheet_x2x10.write('C' + str(self.x2_x10_row_num), full_data_str, self.format_x2_x10)

			self.x2_x10_row_num += 1

		elif data[4] == 0x80:

			self.worksheet_all_ports.write('A' + str(self.xlsx_row_num), self.packet_count)
			self.worksheet_all_ports.write('B' + str(self.xlsx_row_num), str(time_offset))
			self.worksheet_all_ports.write('C' + str(self.xlsx_row_num), full_data_str, self.format_x80_x10)


			self.worksheet_x80x10.write('A' + str(self.x80_x10_row_num), self.packet_count)
			self.worksheet_x80x10.write('B' + str(self.x80_x10_row_num), str(time_offset))
			self.worksheet_x80x10.write('C' + str(self.x80_x10_row_num), full_data_str, self.format_x80_x10)

			self.x80_x10_row_num += 1

		# IN (Device to Host)
		elif data[6] == 0x1:
			self.worksheet_all_ports.write('A' + str(self.xlsx_row_num), self.packet_count)
			self.worksheet_all_ports.write('B' + str(self.xlsx_row_num), str(time_offset))
			self.worksheet_all_ports.write('E' + str(self.xlsx_row_num), full_data_str, self.format_x1_x10)

			self.worksheet_x1x10.write('A' + str(self.x1_x10_row_num), self.packet_count)
			self.worksheet_x1x10.write('B' + str(self.x1_x10_row_num), str(time_offset))
			self.worksheet_x1x10.write('E' + str(self.x1_x10_row_num), full_data_str, self.format_x1_x10)

			self.x1_x10_row_num += 1
		elif data[6] == 0x2:
			self.worksheet_all_ports.write('A' + str(self.xlsx_row_num), self.packet_count)
			self.worksheet_all_ports.write('B' + str(self.xlsx_row_num), str(time_offset))
			self.worksheet_all_ports.write('E' + str(self.xlsx_row_num), full_data_str, self.format_x2_x10)

			self.worksheet_x2x10.write('A' + str(self.x2_x10_row_num), self.packet_count)
			self.worksheet_x2x10.write('B' + str(self.x2_x10_row_num), str(time_offset))
			self.worksheet_x2x10.write('E' + str(self.x2_x10_row_num), full_data_str, self.format_x2_x10)
			self.x2_x10_row_num += 1

		elif data[6] == 0x80:
			self.worksheet_all_ports.write('A' + str(self.xlsx_row_num), self.packet_count)
			self.worksheet_all_ports.write('B' + str(self.xlsx_row_num), str(time_offset))
			self.worksheet_all_ports.write('E' + str(self.xlsx_row_num), full_data_str, self.format_x80_x10)


			self.worksheet_x80x10.write('A' + str(self.x80_x10_row_num), self.packet_count)
			self.worksheet_x80x10.write('B' + str(self.x80_x10_row_num), str(time_offset))
			self.worksheet_x80x10.write('E' + str(self.x80_x10_row_num), full_data_str, self.format_x80_x10)

			self.x80_x10_row_num += 1

		else:
			print("WARNING: Unknown communication path in endpoint 0x1")

		self.xlsx_row_num += 1
		self.packet_count += 1

