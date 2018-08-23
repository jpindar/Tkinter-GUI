"""
File: globe.py
      a place for stuff that isn't part of the GUI or the instruments
"""
__author__ = 'jpindar@jpindar.com'
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

remote_port = '2101'  # default value, can be overridden
remote_address = ''
password = ''
password_length = 16 # arbitrary, but same as firmware
connection = None


class DevNull:
    # pylint: disable=too-few-public-methods
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


def parse_comport_name(connection):
    if isinstance(connection[0], str):
        if connection[0][:4]=='COM:':
            connection[0] = int(connection[0][4:])
        else:
            if connection[0][:3]=='COM':
                connection[0] = int(connection[0][3:])
    return int(connection[0])



def open_dut(connection, output, kind):
    """
    connection info is a list of either a com port number or an ip address and port
    output is an object with an .append(string) method
    kind is a enum of DUTKind
    """
    global dut
    global serial_port_num
    success = False
    assert isinstance(connection, list)
    if kind == DUTKind.serial or kind == DUTKind.mock:
        serial_port_num = parse_comport_name(connection)
    dut = bbuq.UltraQ(connection, output, kind) # dumb constructor
    try:
        if dut.connect():
            success = dut.login()
    except (OSError, bbuq.UltraQError) as e:
        logger.error(e.__class__)
        logger.error("Can't connect to the dut\n")
        return False
    except Exception as e:
        logger.error(e.__class__)
        logger.error("Can't connect to the dut\n")
        return False
    # assert(isinstance(dut,bbuq.UltraQ))
    dut.set_output(output)
    if success:
        output.append("\nConnected\r\n")
        return True
    else:
        output.append("\nNot connected\n")
        dut = None
        return False


