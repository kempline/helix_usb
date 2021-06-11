import json
import os
import sys
import subprocess
import uuid
import xlsxwriter
import logging


log = logging.getLogger(__name__)


class PcapngToXlsx:
    PATH_TSHARK_ABS = "/Applications/Wireshark.app/Contents/MacOS/tshark"

    def __init__(self):
        self.path_json_dump_file = None

    @staticmethod
    def check_os_supported():
        if os.name != 'posix':
            log.error("Operating system not supported yet.")
            return False
        if os.path.exists(PcapngToXlsx.PATH_TSHARK_ABS) is False:
            log.error("Cannot find tshark here: " + PcapngToXlsx.PATH_TSHARK_ABS)
            return False
        return True

    @staticmethod
    def pcapng_to_json(path_pcapng_input_abs, path_json_dump_file):
        command = \
            PcapngToXlsx.PATH_TSHARK_ABS + ' -V -T json -x -r "' + path_pcapng_input_abs + '" > "' + \
            path_json_dump_file + '"'

        result = subprocess.run(command, stdout=subprocess.PIPE, shell=True)

        if result.returncode != 0:
            log.error("Return value of tshark command not 0")
            return False

        return True

    @staticmethod
    def json_to_xlsx(path_json_dump_file, path_xlsx_out):

        workbook = xlsxwriter.Workbook(path_xlsx_out)
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

        endpoint_x1_times = [0, 0, 0]
        endpoint_x81_times = [0, 0, 0]

        xlsx_row_num = 0
        x1_x10_row_num = 0
        x2_x10_row_num = 0
        x80_x10_row_num = 0

        reported_unexpected_endpoints = list()
        endpoints_to_report = ["0x00000001", "0x00000081"]

        # open json and print
        with open(path_json_dump_file, "r") as read_file:
            data = json.load(read_file)
            for data_packet_no, packet in enumerate(data):
                if data_packet_no % 1000 == 0:
                    print('.', end='')
                source = packet["_source"]
                layers = source["layers"]
                usb = layers["usb"]

                usb_endpoint = usb["usb.endpoint_address"]
                if usb_endpoint in endpoints_to_report:
                    try:
                        # data (if any)
                        usb_capdata_raw = layers["usb.capdata_raw"]
                        usb_capdata_raw = usb_capdata_raw[0]

                        full_data_int = []
                        full_data_str = ''
                        for i in range(0, len(usb_capdata_raw), 2):
                            current_str = usb_capdata_raw[i:i+2]
                            full_data_int.append(int(current_str, 16))

                        for i, d in enumerate(full_data_int):
                            e = hex(d)
                            full_data_str += (e + ', ')

                        if full_data_str.endswith(', '):
                            full_data_str = full_data_str[:-2]

                        # packet no and time since session start
                        frame = layers["frame"]
                        frame_time_delta = frame["frame.time_delta"]
                        frame_time_relative = frame["frame.time_relative"]
                        frame_number = frame["frame.number"]
                        if usb_endpoint == "0x00000001":
                            if full_data_int[4] == 0x1 and full_data_int[5] == 0x10:

                                worksheet_all_ports.write('A' + str(xlsx_row_num), frame_number)
                                worksheet_all_ports.write('B' + str(xlsx_row_num), frame_time_relative)
                                worksheet_all_ports.write('E' + str(xlsx_row_num), full_data_str, format_x1_x10)
                                worksheet_all_ports.write('C' + str(xlsx_row_num),
                                                          str(float(frame_time_relative) - endpoint_x1_times[0]))
                                worksheet_all_ports.write('D' + str(xlsx_row_num),
                                                          str(float(frame_time_relative) - endpoint_x81_times[0]))

                                worksheet_x1x10.write('A' + str(x1_x10_row_num), frame_number)
                                worksheet_x1x10.write('B' + str(x1_x10_row_num), frame_time_relative)
                                worksheet_x1x10.write('E' + str(x1_x10_row_num), full_data_str, format_x1_x10)
                                worksheet_x1x10.write('C' + str(x1_x10_row_num),
                                                      str(float(frame_time_relative) - endpoint_x1_times[0]))
                                worksheet_x1x10.write('D' + str(x1_x10_row_num),
                                                      str(float(frame_time_relative) - endpoint_x81_times[0]))
                                x1_x10_row_num += 1

                                endpoint_x1_times[0] = float(frame_time_relative)

                            elif full_data_int[4] == 0x2 and full_data_int[5] == 0x10:

                                worksheet_all_ports.write('A' + str(xlsx_row_num), frame_number)
                                worksheet_all_ports.write('B' + str(xlsx_row_num), frame_time_relative)
                                worksheet_all_ports.write('E' + str(xlsx_row_num), full_data_str, format_x2_x10)
                                worksheet_all_ports.write('C' + str(xlsx_row_num),
                                                          str(float(frame_time_relative) - endpoint_x1_times[1]))
                                worksheet_all_ports.write('D' + str(xlsx_row_num),
                                                          str(float(frame_time_relative) - endpoint_x81_times[1]))

                                worksheet_x2x10.write('A' + str(x2_x10_row_num), frame_number)
                                worksheet_x2x10.write('B' + str(x2_x10_row_num), frame_time_relative)
                                worksheet_x2x10.write('E' + str(x2_x10_row_num), full_data_str, format_x2_x10)
                                worksheet_x2x10.write('C' + str(x2_x10_row_num),
                                                      str(float(frame_time_relative) - endpoint_x1_times[1]))
                                worksheet_x2x10.write('D' + str(x2_x10_row_num),
                                                      str(float(frame_time_relative) - endpoint_x81_times[1]))
                                x2_x10_row_num += 1

                                endpoint_x1_times[1] = float(frame_time_relative)

                            elif full_data_int[4] == 0x80 and full_data_int[5] == 0x10:

                                worksheet_all_ports.write('A' + str(xlsx_row_num), frame_number)
                                worksheet_all_ports.write('B' + str(xlsx_row_num), frame_time_relative)
                                worksheet_all_ports.write('E' + str(xlsx_row_num), full_data_str, format_x80_x10)
                                worksheet_all_ports.write('C' + str(xlsx_row_num),
                                                          str(float(frame_time_relative) - endpoint_x1_times[2]))
                                worksheet_all_ports.write('D' + str(xlsx_row_num),
                                                          str(float(frame_time_relative) - endpoint_x81_times[2]))

                                worksheet_x80x10.write('A' + str(x80_x10_row_num), frame_number)
                                worksheet_x80x10.write('B' + str(x80_x10_row_num), frame_time_relative)
                                worksheet_x80x10.write('E' + str(x80_x10_row_num), full_data_str, format_x80_x10)
                                worksheet_x80x10.write('C' + str(x80_x10_row_num),
                                                       str(float(frame_time_relative) - endpoint_x1_times[2]))
                                worksheet_x80x10.write('D' + str(x80_x10_row_num),
                                                       str(float(frame_time_relative) - endpoint_x81_times[2]))
                                x80_x10_row_num += 1

                                endpoint_x1_times[2] = float(frame_time_relative)

                            else:
                                print("WARNING: Unknown communication path in endpoint 0x1: " + str(full_data_int[4]) + ':' + str(full_data_int[5]))

                            xlsx_row_num += 1
                        else:  # endpoint 0x81
                            if full_data_int[6] == 0x1 and full_data_int[7] == 0x10:

                                worksheet_all_ports.write('A' + str(xlsx_row_num), frame_number)
                                worksheet_all_ports.write('B' + str(xlsx_row_num), frame_time_relative)
                                worksheet_all_ports.write('F' + str(xlsx_row_num), full_data_str, format_x1_x10)

                                worksheet_x1x10.write('A' + str(x1_x10_row_num), frame_number)
                                worksheet_x1x10.write('B' + str(x1_x10_row_num), frame_time_relative)
                                worksheet_x1x10.write('F' + str(x1_x10_row_num), full_data_str, format_x1_x10)
                                x1_x10_row_num += 1
                                endpoint_x81_times[0] = float(frame_time_relative)

                            elif full_data_int[6] == 0x2 and full_data_int[7] == 0x10:

                                worksheet_all_ports.write('A' + str(xlsx_row_num), frame_number)
                                worksheet_all_ports.write('B' + str(xlsx_row_num), frame_time_relative)
                                worksheet_all_ports.write('F' + str(xlsx_row_num), full_data_str, format_x2_x10)

                                worksheet_x2x10.write('A' + str(x2_x10_row_num), frame_number)
                                worksheet_x2x10.write('B' + str(x2_x10_row_num), frame_time_relative)
                                worksheet_x2x10.write('F' + str(x2_x10_row_num), full_data_str, format_x2_x10)
                                x2_x10_row_num += 1
                                endpoint_x81_times[1] = float(frame_time_relative)

                            elif full_data_int[6] == 0x80 and full_data_int[7] == 0x10:

                                worksheet_all_ports.write('A' + str(xlsx_row_num), frame_number)
                                worksheet_all_ports.write('B' + str(xlsx_row_num), frame_time_relative)
                                worksheet_all_ports.write('F' + str(xlsx_row_num), full_data_str, format_x80_x10)

                                worksheet_x80x10.write('A' + str(x80_x10_row_num), frame_number)
                                worksheet_x80x10.write('B' + str(x80_x10_row_num), frame_time_relative)
                                worksheet_x80x10.write('F' + str(x80_x10_row_num), full_data_str, format_x80_x10)
                                x80_x10_row_num += 1

                                endpoint_x81_times[2] = float(frame_time_relative)
                            else:
                                print("WARNING: Unknown communication path in endpoint 0x81: " + str(full_data_int[4]) + ':' + str(full_data_int[5]))

                            xlsx_row_num += 1
                    except KeyError:
                        # packet has no data we are interested in
                        pass
                else:
                    if usb_endpoint not in reported_unexpected_endpoints:
                        reported_unexpected_endpoints.append(usb_endpoint)

            if len(reported_unexpected_endpoints) > 0:
                print()
                print("pcapng input file contains endpoint(s) currently not monitored: ", end="")
                for usb_endpoint in reported_unexpected_endpoints:
                     print(usb_endpoint, end=" ")
                print()
        workbook.close()
        return True

    def convert(self, path_pcapng_input_abs, path_xlsx_out=None):
        if path_xlsx_out is None:
            path_xlsx_out = path_pcapng_input_abs + '.xlsx'

        path_json_dump_file = './tmp_dump_' + str(uuid.uuid4()) + '.json'
        try:
            if self.check_os_supported() is False:
                return False
            if os.path.exists(path_pcapng_input_abs) is False:
                log.error("Given input file does not exist: " + path_pcapng_input_abs)
                return False

            # call tshark to convert pcapng file to json
            # log.info('Converting pcapng file to json - this may take a while!')
            if self.pcapng_to_json(path_pcapng_input_abs, path_json_dump_file) is False:
                return False

            # log.info('Converting json file to xlsx sheet.')
            if self.json_to_xlsx(path_json_dump_file, path_xlsx_out) is False:
                return False
        except:
            pass
        finally:
            if os.path.exists(path_json_dump_file):
                os.remove(path_json_dump_file)
        log.info("Successfully stored xlsx file: " + path_xlsx_out)
        return True


def main(args):
    logging.basicConfig(
        level='INFO',
        format="%(asctime)s - %(levelname)s - %(message)s (%(name)s)",
        datefmt="%Y-%m-%d %H:%M:%S")

    if len(args) < 2:
        log.error('Please provide at least one source file!')
        return

    pcapng_conv = PcapngToXlsx()
    for i in range(1, len(args)):
        pcapng_conv.convert(args[i])
        print()
        print()
        print()


if __name__ == '__main__':
    main(sys.argv)
