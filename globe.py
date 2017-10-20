# pylint: disable=wrong-import-position
"""
File: globe.py
"""
__author__ = 'jpindar@jpindar.com'
import logging
logger = logging.getLogger(__name__)

import bbuq

# unsaved = False
# user_interrupt = False
user_pause = False
# exiting = False
# file_name = None
dut = None

# port serial_port_num should default to 0 to make other routines
# know it may not be valid
# until we call open_dut, dut is not an Ultra-Q (or any type) so it
# doesn't have a place to store a serial_port_num
serial_port_num = 0


class DevNull:
    def __init__(self):
        pass

    def append(self,s):
        pass

dev_null = DevNull()


def close_dut():
    global dut
    dut.port.close_port()
    dut = None


def open_dut(port_num, output, mock=False):
    global dut
    global serial_port_num
    serial_port_num = port_num
    if dut is None:
        try:
            dut = bbuq.UltraQ(output, mock)
        except Exception as e:
            logger.error(e.__class__)
            logger.error("Can't create the dut\n")
            return
    dut.set_output(output)
    # logger.info('globe.open_dut is done')
    if dut.exists:
        output.append("Connected to DUT.\n")


