import sys
import os
from .utils.usb_monitor import UsbMonitor
cwd = os.getcwd()
helix_usb_path = os.path.join(cwd, 'helix_usb')
sys.path.append(helix_usb_path)

from .helix_usb import HelixUsb
