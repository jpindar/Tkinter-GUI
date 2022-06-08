"""
File: globe.py
      a place for stuff that isn't part of the GUI or the instruments
"""
__author__ = 'jpindar@jpindar.com'
import logging
from enum import Enum
import device

logger = logging.getLogger(__name__)

# unsaved = False
# user_interrupt = False
user_pause = False
# exiting = False
# file_name = None
dmm = None

# port serial_port_num should default to 0 to make other routines
# know it may not be valid
# until we call open_dut, dut is not any type so it
# doesn't have a place to store a serial_port_num
serial_port_num = 0


# so DUTkind.serial or globe.DUTkind.serial are members of
# the class DUTKind,  not of an instance of DUTKind
class DUTKind(Enum):
    mock = 0
    serial = 1
    network = 2


remote_port = '2101'  # default value, can be overridden
remote_address = ''
password = ''
password_length = 16  # arbitrary, but same as firmware
connection = ['', '']
user_interrupt = False
unsaved = False


class DevNull:
    """ a dummy output object for times when we want to suppress output """
    # pylint: disable=too-few-public-methods

    def __init__(self):
        pass

    def append(self, s):
        pass


dev_null = DevNull()


# def close_dut():
#     global dmm
#     dmm.port.close_port()
#     dmm.port = None
#     dmm = None
#     return


def parse_comport_name(c):
    if isinstance(c[0], str):
        if c[0][:4] == 'COM:':
            c[0] = int(c[0][4:])
        else:
            if c[0][:3] == 'COM':
                c[0] = int(c[0][3:])
    return int(c[0])



def open_dut(connection, output, kind):
    """
    connection info is a list of either a com port number or an ip address and port
    output is an object with an .append(string) method, typically a textbox
    kind is a enum of DUTKind
    """
    global dut
    global serial_port_num
    success = False
    assert isinstance(connection, list)
    if kind == DUTKind.serial or kind == DUTKind.mock:
        serial_port_num = parse_comport_name(connection)
    dut = device.Device(connection, output, kind)  # dumb constructor
    try:
        success = dut.connect()
    except (OSError, device.DeviceError) as e:
        logger.error(e.__class__)
        logger.error("Can't connect to the dut\n")
        return False
    except Exception as e:
        logger.error(e.__class__)
        logger.error("Can't connect to the dut\n")
        return False
    # assert(isinstance(dut,device.Device))
    dut.set_output(output)
    if success:
        if kind == DUTKind.serial:
            output.append("\nConnected\r\n")
        if kind == DUTKind.mock:
            output.append("\nConnected to a mock DUT\r\n")
        return True
    else:
        output.append("\nNot connected\n")
        dut = None
        return False


