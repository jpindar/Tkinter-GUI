"""
File: globe.py
"""
__author__ = 'jpindar@jpindar.com'
# pylint: disable=wrong-import-position
import logging
logger = logging.getLogger(__name__)

from enum import Enum
import bbuq

# unsaved = False
# user_interrupt = False
user_pause = False
# exiting = False
# file_name = None
dut = None
start_freq = 0
stop_freq = 0


# port serial_port_num should default to 0 to make other routines
# know it may not be valid
# until we call open_dut, dut is not an Ultra-Q (or any type) so it
# doesn't have a place to store a serial_port_num
serial_port_num = 0


# so DUTkind.serial or globe.DUTkind.serial are members of
# the class DUTKind,  not of an instance of DUTKind
class DUTKind(Enum):
    mock = 0
    serial = 1
    network = 2

dut_kind = DUTKind.serial
remote_address = '10.0.0.10'
remote_port = '2101'
password = ''
password_length = 16 # arbitrary, but same as firmware


class DevNull:
    def __init__(self):
        pass

    def append(self,s):
        pass

dev_null = DevNull()


def close_dut():
    global dut
    dut.port.close_port()
    dut.port = None
    dut = None
    return


def open_dut(connection, output, kind):
    """
    connection info is a list of either a com port number or an ip address and port
    output is sonething with an .append(string) method
    kind is a enum of DUTKind
    """
    global dut
    global serial_port_num

    if kind == DUTKind.serial or kind == DUTKind.mock:
        serial_port_num = connection[0]
    if dut is None:
        try:
            dut = bbuq.UltraQ(connection, output, kind)
        except (OSError, bbuq.UltraQError) as e:
            logger.error(e.__class__)
            logger.error("Can't create the dut\n")
            return
        except Exception as e:
            logger.error(e.__class__)
            logger.error("Can't create the dut\n")
            return
    dut.set_output(output)
    if dut.exists:
        output.append("\nConnected to DUT.\r\n")
    else:
        output.append("\nNot connected to DUT.\n")
        dut = None
    return


