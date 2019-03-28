# pylint: disable=wrong-import-position,unused-argument,line-too-long
"""
File: serialdevice_pyserial.py

Unlike some libraries, pySerial works with comports up to at least COM99. Nice.

 TODO pop up or other obvious error handling when exception occurs?
"""
__author__ = 'jpindar@jpindar.com'

import logging
logger = logging.getLogger(__name__)
import time
import serial
import serial.tools.list_ports
# from serial.tools.list_ports import comports

read_delay = 0.2
baud_rate = 19200 # normal, don't change this
# baud_rate = 115200  # works
# baud_rate = 230400  # works
# baud_rate = 460800  # doesn't work reliably


# noinspection PySimplifyBooleanCheck
def get_ports():
    """
    ask pySerial for a list of com ports
    :return: a list of strings, each representing an integer
    """
    possible_ports = serial.tools.list_ports.comports()
    ports = []
    for i in possible_ports:
        s = str(i.device) +' '+str(i.description)+' '+str(i.hwid)
        logger.info(s)
        s = i.device   # something like 'COM4'
        ports.append(int(s[3:]))  # from position 3 to the end, to handle multi-digit port numbers
    logger.info("ports reported by pySerial:" + str(ports))
    if (ports is None) or (ports == []):
        return ['']
    return ports


class SerialDevice:
    """
    An object that represents a generic serial device
    """
    def __init__(self):
        """
        Constructor for serial device, no parameters
        This constructor just creates the object, doesn't give it a serial port
        :rtype : SerialDevice
        """
        logger.info(" ")
        logger.info("SerialDevice constructor")
        self.comPort = None
        self.port_num = None


    def open_port(self, connection_info):
        """
        opens a serial port
        connection_info[0] should be an integer, 0 meaning COM1, etc
        returns True if it succeeded, False if there was an error
        :param connection_info: a list, 0th element is an integer
        :return: boolean
        """
        self.close_port()
        self.port_num = connection_info[0]
        port_name = "COM" + str(self.port_num)
        logger.info("opening serial port " + port_name)
        try:
            self.comPort = serial.Serial(port=port_name,
                                         baudrate=baud_rate,
                                         parity=serial.PARITY_NONE,
                                         stopbits=serial.STOPBITS_ONE,
                                         bytesize=serial.EIGHTBITS,
                                         timeout = 2,
                                         write_timeout = 2)

        except ValueError as e:
            logger.warning("SerialDevice.openPort: Serial port setting out of range\r\n")
            logger.warning(e.__class__)
            # logger.warn(e.__doc__)
            return False
        except [serial.SerialException, serial.SerialTimeoutException] as e:
            logger.warning("SerialDevice.openPort: Can't open that serial port\r\n")
            logger.warning(e.__class__)
            logger.warning(e.__doc__)
            return False
        except Exception as e:
            logger.warning("SerialDevice.openPort: Can't open that serial port\r\n")
            logger.warning(e.__class__)
            logger.warning(e.__doc__)
            return False
        else:
            # assert isinstance(self.comPort, pyvisa.resources.serial.SerialInstrument)
            logger.info("SerialDevice.openPort: opened a " + str(self.comPort.__class__))
            return True


    def is_open(self):
        """
        This is really just checking if open_port() succeeded
        :rtype: boolean
        """
        if not hasattr(self, 'comPort'):
            logger.warning("isOpen():port does not exist")
            return False
        if self.comPort is None:
            logger.warning("isOpen():port does not exist")
            return False
        return True


    def close_port(self):
        if not hasattr(self, 'comPort'):
            return
        if not hasattr(self.comPort, 'close'):
            return
        try:
            self.comPort.close()
        except Exception as e:
            logger.warning(e.__class__)


    def write(self, msg):
        """
        send a string
        don't need to check if port is open, comport.write() does that

        :param msg: the string to send
        :return: none
        """
        # self.comPort.reset_input_buffer()
        # self.comPort.reset_output_buffer()
        response = None
        if not hasattr(self, 'comPort'):
            logger.warning("can't write to non-existent port")
            return response
        # msg = msg + "\n"
        # logger.info("SerialDevice.write: writing " + str(msg) + " to serial port")
        try:
            self.comPort.write(msg.encode(encoding='UTF-8'))
            # except serial.portNotOpenError as e:   # nope, this causes a Type error
        except serial.SerialException as e:
            if e == serial.portNotOpenError:
                logger.warning("SerialDevice.write: port not open error")
            else:
                logger.warning("SerialDevice.write: error raised by serial port write")
            logger.warning("SerialDevice.write: can't write to the serial port\r\n")
            logger.warning(e.__class__)
            # logger.warning(e.__doc__)
            # raise e
        except Exception as e:  # should never happen?
            logger.error(e.__class__)
            raise e


    def read(self):
        """
        reads a response from the serial port
        don't use self.comPort.readline() because it is slow
        : rtype: string
        """
        r_bytes = None
        time.sleep(read_delay)  # read can fail if no delay here, 0.2 works

        try:
            r_bytes = self._readline()
        except serial.SerialException as e:
            if e == serial.portNotOpenError:
                logger.warning("SerialDevice._readline: port not open error")
            else:
                logger.warning("SerialDevice._readline: error raised by serial port read")
            logger.warning(e.__class__)
            logger.warning(e.__doc__)
            logger.warning(e.strerror)
            logger.warning(e.__cause__)
            # raise e   # could throw something here, depending on the cause?
            return None
        except (IOError, AttributeError) as e:
            logger.warning("SerialDevice.read: didn't get a response from serial port " + str(self.port_num))
            logger.warning(e.__class__)
            logger.warning(e.__doc__)
            logger.warning(e.strerror)
            logger.warning(e.__cause__)
            return None
        else:
            r_str = str(r_bytes.decode(encoding='UTF-8'))  # cast bytes to string
            r_str = r_str.strip('\r\n')
        return r_str


    def _readline(self, terminator='\r'):
        """
        implemented this myself because PySerial's readline() is extremely slow
        :param terminator: read until you receive this termination character(s)
        :return: bytes (because that's what the original .readline() returns)
        """
        MAX_COUNT = 1000  # a completely arbitrary number
        c = None
        length_of_termination = len(terminator)
        line = bytearray()
        count = 0
        try:
            while self.comPort.inWaiting() > 0:
                # c = self.comPort.read(self.comPort.inWaiting())   # would this be faster?
                c = self.comPort.read(1)
                if c:
                    line += c
                    count += 1
                    if line[-length_of_termination:] == terminator:
                        break
                    if count > MAX_COUNT:
                        break
                else:
                    break
        except Exception as e:
            logger.error("in _readline")
            logger.error(e.__class__)
            raise e  # let .read() handle it
        return bytes(line)


