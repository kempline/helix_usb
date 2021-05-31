import usb.core
import usb.util
import time
import re
import threading
import logging
log = logging.getLogger(__name__)


class UsbDescriptor:
    def __init__(self, device_id, bus, address, device):
        self.device_id = device_id
        self.bus = bus
        self.address = address
        self.device = device

    def __eq__(self, other):
        if self.device_id == other.device_id and self.bus == other.bus and self.address == other.address:
            return True
        else:
            return False


class UsbMonitor:
    POLLING_INTERVAL_IN_SEC = 1
    regex = r"DEVICE ID ([a-f0-9]*:[a-f0-9]*) on Bus ([0-9][0-9][0-9]) Address ([0-9][0-9][0-9]) [=]*"

    def __init__(self, white_list_device_ids=list()):
        self.reported_devices = list()
        self.usb_device_found_cb_list = list()
        self.usb_device_lost_cb_list = list()
        self.request_terminate = False
        self.white_list_device_ids = white_list_device_ids
        self.monitor_thread = None

    @staticmethod
    def device_to_usb_descriptor(device):
        matches = re.finditer(UsbMonitor.regex, str(device), re.MULTILINE)
        for matchNum, match in enumerate(matches, start=1):

            if len(match.groups()) != 3:
                print('Unexpected group size while looking for USB data (3 expected): ' +
                      str(len(match.groups())))
                continue

            _ = match.group(0)
            device_id = match.group(1)
            bus = match.group(2)
            address = match.group(3)

            return UsbDescriptor(device_id, bus, address, device)
        return None

    def monitor(self):
        log.info('Looking for connected USB devices: ' + str(self.white_list_device_ids))
        while not self.request_terminate:
            connected_devices = list()
            for dev in usb.core.find(find_all=True):

                usb_descriptor = self.device_to_usb_descriptor(dev)

                if usb_descriptor is not None:
                    connected_devices.append(usb_descriptor)

            # look for new devices
            for dev in connected_devices:
                if dev not in self.reported_devices:
                    if dev.device_id in self.white_list_device_ids:
                        for cb in self.usb_device_found_cb_list:
                            cb(dev)

            # look for lost devices
            for dev in self.reported_devices:
                if dev not in connected_devices:
                    if dev.device_id in self.white_list_device_ids:
                        for cb in self.usb_device_lost_cb_list:
                            cb(dev)

            self.reported_devices = connected_devices
            time.sleep(self.POLLING_INTERVAL_IN_SEC)

    def start(self):
        self.monitor_thread = threading.Thread(target=self.monitor, args=())
        self.monitor_thread.start()

    def register_device_found_cb(self, cb):
        self.usb_device_found_cb_list.append(cb)

    def register_device_lost_cb(self, cb):
        self.usb_device_lost_cb_list.append(cb)
