"""
File: serialdevice_pyserial.py

Unlike some libraries, pySerial works with comports up to at least COM99. Nice.

One reason there are several similar ways to read from the port is that I was getting some
unexpected variations in speed when calling pySerial's routines. You'd think the built-in
routines would be faster but they weren't always.

TODO: test what happens if any of these are called on a port that's not open
(such as one whose USB cable has been disconnected)

baud rates of 19200, 115200, and 230400 work
baud rate of 460800 doesn't work reliably

"""
__author__ = 'jpindar@jpindar.com'
import logging
import time
import serial
import serial.tools.list_ports
from typing import List, Dict, Optional, Any, Union


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_ports() -> List[Union[int, str]]:
    """
    ask pySerial for a list of serial ports
    """
    possible_ports: List[serial.ListPortInfo] = serial.tools.list_ports.comports()
    ports: List[Union[int, str]] = []
    for i in possible_ports:
        s = str(i.device) + ' ' + str(i.description) + ' ' + str(i.hwid)
        logger.info(s)
        s = i.device   # something like 'COM4', depending on the OS
        # TODO make this crossplatform
        ports.append(int(s[3:]))  # from position 3 to the end, to handle multi-digit port numbers
    logger.info("ports reported by pySerial:" + str(ports))
    if (ports is None) or (ports == []):
        return ['']  # because we are most likely going to display this
    return ports


class SerialDevice:
    """
    An object that represents a generic device accessed via a serial port
    """

    def __init__(self):
        """
        Constructor for serial device, no parameters
        This constructor just creates the object, doesn't open the serial port
        """
        self.port = None
        self.port_num = None
        self.baud_rate = 19200
        self.read_delay = 0.2
        self.timeout = 2
        self.write_timeout = 2
        self.read_mode = 1

    def open_port(self, connection_info: List= None) -> None:
        """
        opens a serial port
        connection_info[0] should be an integer, 0 meaning COM1, etc
        or None. If it is None, self.port_num is used.
        """
        self.close_port()
        if not connection_info is None:
            self.port_num = connection_info[0]
        # TODO make this crossplatform
        self.port_name = "COM" + str(self.port_num)
        logger.info("opening serial port " + self.port_name)
        try:
            self.port = serial.Serial(port=self.port_name,
                                         baudrate=self.baud_rate,
                                         parity=serial.PARITY_NONE,
                                         stopbits=serial.STOPBITS_ONE,
                                         bytesize=serial.EIGHTBITS,
                                         timeout=self.timeout,
                                         write_timeout=self.write_timeout)
        except ValueError as e:
            logger.warning("SerialDevice.openPort: Serial port setting out of range\r\n")
            logger.warning(e.__class__)
            logger.warning(e.__doc__)
            raise e
        except (serial.SerialException, serial.SerialTimeoutException) as e:
            logger.warning("SerialDevice.openPort: Can't open that serial port")
            logger.warning(e.__class__)
            logger.warning(e.__doc__)
            logger.warning(e.args[0])   # or  just args
            raise e
        except Exception as e:
            logger.warning("SerialDevice.openPort: Can't open that serial port\r\n")
            logger.warning(e.__class__)
            logger.warning(e.__doc__)
            raise e
        else:
            logger.info("opened a " + str(self.port.__class__))

    def is_open(self) -> bool:
        if not hasattr(self, 'port'):
            logger.warning("is_open(): serial port does not exist")
            return False
        if self.port is None:
            logger.warning("is_open(): serial port does not exist")
            return False
        if not self.port.isOpen():
            logger.warning("is_open(): port.isOpen() is false")
            return False
        return True

    def close_port(self) -> None:
        if not hasattr(self, 'port'):
            return
        if not hasattr(self.port, 'close'):
            return
        try:
            self.port.close()
        except Exception as e:
            logger.warning(e.__class__)
            raise e

    def write(self, msg: str) -> None:
        """
        send a string
        TODO: consider adding a termintion if one is not included
        """
        # self.port.reset_input_buffer()
        # self.port.reset_output_buffer()
        if not self.is_open():
            logger.warning("can't write to the serial port because it is not open")
            # TODO raise an appropriate exception here
            return
        # logger.info("SerialDevice.write: writing " + str(msg) + " to serial port")
        try:
            self.port.write(msg.encode(encoding='UTF-8'))
        # if the port was never opened it would cause an attribute error
        # but that would be detected by the self.is_open
        except serial.PortNotOpenError as e:
            logger.warning("SerialDevice.write: can't write to the serial port\r\n")
            logger.warning(e.__class__)
            logger.warning(e.__doc__)
            raise e
        except serial.SerialException as e:
            # this is the error  you get if the USB cable for a virtual com port has disconnected
            logger.warning("SerialDevice.write: can't write to the serial port\r\n")
            logger.warning(e.__class__)
            logger.warning(e.__doc__)
            raise e
        except Exception as e:
            logger.error(e.__class__)
            raise e

    def read(self, terminator=serial.LF, max_size=1000, mode=None) -> Optional[str]:
        """
        reads a response from the serial port
        TODO: investigate possible timing issues: is self.port.readline() slow ?
        """
        if mode == None:
            mode = self.read_mode
        # delay was 0.2 for old, slow BBUQ device
        # time.sleep(read_delay)  # read can fail if no delay here, 0.2 works
        if not self.is_open():  # this only checks the higher level software, not the actual port
            logger.warning("can't read from the serial port because it is not open")
            # TODO raise an appropriate exception here - IOError?
            return None
        r_bytes: bytearray = bytearray()
        try:
            # print(time.time())
            if mode == 1:
                r_bytes = self.port.readline(max_size)
            elif mode == 2:
                r_bytes = self.port.read_until(terminator, max_size)
            elif mode == 3:
                r_bytes = self._read_until(terminator, max_size)
            else:
                r_bytes = self._readline(terminator, max_size)
            # print(time.time())
        except serial.PortNotOpenError as e:
            logger.warning(e.__class__)
            logger.warning(e.__doc__)
            logger.warning(e.strerror)
            logger.warning(e.__cause__)
            # raise e
            return None
        except serial.SerialException as e:
            # this is the error  you get if the USB cable for a virtual com port has disconnected
            logger.warning("SerialDevice.read: error raised by serial port read")
            logger.warning(e.__class__)
            logger.warning(e.__doc__)
            logger.warning(e.strerror)
            logger.warning(e.__cause__)
            # raise e
            return None
        except (IOError, AttributeError) as e:
            logger.warning("SerialDevice.read: didn't get a response from serial port " + str(self.port_num))
            logger.warning("exception: " + str(e.__class__))
            logger.warning(e.__doc__)
            # logger.warning(e.strerror)  # attributeError has no strerror
            logger.warning(e.__cause__)
            return None
        else:
            r_str: str = r_bytes.decode(encoding='UTF-8')
            return r_str.strip('\r\n')

    def _read_until(self, terminator: Union[str, bytes] = serial.LF, max_size=1000) -> bytearray:
        """
        Read until a termination sequence is found, the size
        is exceeded or until timeout occurs.
        This is copied from serialutil.py, part of pySerial
        But it runs faster here?
        """
        length_of_termination = len(terminator)
        line: bytearray = bytearray()
        count = 0
        c: bytes = bytes()
        while True:
            c = self.port.read(1)
            if c:
                line += c
                count += 1
                if line[-length_of_termination:] == terminator:
                    break
                if max_size is not None and count >= max_size:
                    break
            else:
                logger.warning("read timeout")
                break
        return line

    def _readline(self, terminator: Union[str, bytes] = serial.LF, max_size=1000) -> bytearray:
        """
        implemented this myself because PySerial's readline() is extremely slow
        #  the default value of max_size is a completely arbitrary number
        """
        length_of_termination = len(terminator)
        line: bytearray = bytearray()
        count = 0
        c: bytes = bytes()
        try:
            while self.port.inWaiting() > 0:
                # c = self.port.read(self.port.inWaiting())   # would this be faster?
                c = self.port.read(1)
                if c:
                    line += c
                    count += 1
                    if line[-length_of_termination:] == terminator:
                        break
                    if count > max_size:
                        break
                else:
                    logger.warning("read timeout")
                    break
        except Exception as e:
            logger.error("in _readline")
            logger.error(e.__class__)
            raise e  # let .read() handle it

        return line
