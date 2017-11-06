# pylint: disable=wrong-import-position,unused-argument,line-too-long
"""
File: serialdevice_pyserial.py

Unlike some libraries, pySerial works with comports up to at least COM99. Nice.
"""
__author__ = 'jpindar@jpindar.com'

import logging
logger = logging.getLogger(__name__)

import time
import serial
import serial.tools.list_ports
# from serial.tools.list_ports import comports

read_delay = 0.2


# noinspection PySimplifyBooleanCheck
def get_ports():
    """
    ask pySerial for a list of com ports
    :return: a list of strings, each representing an integer
    """
    possible_ports = serial.tools.list_ports.comports()
    ports = []
    for i in possible_ports:
        s = str(i.device) +'*'+str(i.description)+'*'+str(i.hwid)
        logger.info(s)
        s = i.device   # something like 'COM4'
        ports.append(int(s[3:]))  # from position 3 to the end
    logger.info(str(ports))
    if (ports is None) or (ports == []):
        return ['']
    return ports


class SerialDevice:
    """
    A serial port, created by pySerial
    """
    def __init__(self):
        """constructor for serial device, no parameters
        :rtype : SerialDevice
        create an instance variable but don't open the port
        """
        logger.info(" ")
        logger.info("SerialDevice constructor")
        self.exists = False
        self.comPort = None
        self.friendly_name = "serial port"
        self.port_num = None
        logger.info("SerialDevice constructor done")


    def open_port(self, port_num):
        """
         opens the port with fixed parameters
        :param port_num: COM1 is port 0, etc
        :return:
        """
        if port_num == 0:
            return      # should never happen
        self.close_port()
        port_name = "COM" + str(port_num)
        logger.info("opening serial port " + port_name)
        try:
            baud_rate = 19200
            # baud_rate = 115200  # works
            # baud_rate = 230400  # works
            # baud_rate = 460800    # doesn't work reliably
            self.comPort = serial.Serial(port=port_name,
                                         baudrate=baud_rate,
                                         parity=serial.PARITY_NONE,
                                         stopbits=serial.STOPBITS_ONE,
                                         bytesize=serial.EIGHTBITS,
                                         timeout = 2,
                                         write_timeout = 2)
            # if this fails, object will have no comPort attribute.
            # this can be checked, but is it better to have comPort is None?
            self.exists = True
        except ValueError as e:
            logger.warning("SerialDevice.openPort: Serial port setting out of range\r\n")
            logger.warning(e.__class__)
            # logger.warn(e.__doc__)
            raise e
        except serial.SerialException as e:
            logger.warning("SerialDevice.openPort: Can't open that serial port\r\n")
            logger.warning(e.__class__)
            # logger.warn(e.__doc__)
            raise e
        except Exception as e:
            logger.warning("SerialDevice.openPort: Can't open that serial port\r\n")
            logger.warning(e.__class__)
            # logger.warn(e.__doc__)
            raise e
        else:
            # assert isinstance(self.comPort, pyvisa.resources.serial.SerialInstrument)
            # not necessary if constructor worked, but assertions are good.
            logger.info("SerialDevice.openPort: opened a " + str(self.comPort.__class__))
            # self.port_num = port_num
            logger.info("Constructor is done")

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

    def write(self, msg):
        """send a string
        :param msg: the string to send
        :return: none
        # don't need to check if port is open, comport.write() does that
        # TODO: pop up or other obvious error handling when exception occurs?
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
                logger.warning("SerialDevice._readline: port not open error")
            else:
                logger.warning("SerialDevice._readline: error raised by serial port read")
            logger.warning("SerialDevice.write: can't write to the serial port\r\n")
            logger.warning(e.__class__)
            # logger.warning(e.__doc__)
            # raise e
        except Exception as e:   # should never happen?
            logger.error(e.__class__)
            raise e
        # logger.info("Done")


    def read(self):
        """
        reads a response from the serial port
        :rtype: string

        # don't need to check if port is open, self._readline will throw an exception if its not
        # don't use self.comPort.readline() because comport.readline() is extremely slow
        # maybe it's waiting for a timeout?
        """
        response = None
        r=""
        time.sleep(read_delay)  # read can fail if no delay here, 0.2 works
        try:
            # response = self.comPort.readline()
            response = self._readline()  # response is of type 'bytes'
            # if (response is None) or (response == ""):
            # do what?  return "" ?
            r = str(response.decode(encoding='UTF-8'))    # cast bytes to string
            # logger.info("received " + r)
        except serial.SerialException as e:
            if e == serial.portNotOpenError:
                logger.warning("SerialDevice._readline: port not open error")
            else:
                logger.warning("SerialDevice._readline: error raised by serial port read")
            logger.warning(e.args[0])
            logger.warning(e.__class__)
            # raise e   # could throw something here, depending on the cause?
            return None
        except (IOError, AttributeError) as e:
            logger.warning("exception: " + str(e.__class__))
            logger.warning(str(e.args))
            logmsg = "SerialDevice.read: didn't get a response from serial port " + str(self.port_num)
            logger.warning(logmsg)
            logger.warning("<" + str(r) + ">")
        else:
            # logger.info("SerialDevice.read: got <" + str(r) + ">")
            r += '\n'   # because read strips the term. Which is really, really wrong, but whatever.
                        # TODO find a better fix
            return r


    def close_port(self):
        logger.info("close_port: closing serial port")
        if not hasattr(self, 'comPort'):
            return
        if not hasattr(self.comPort, 'close'):
            return
        try:
            self.comPort.close()
        except Exception as e:
            logger.warning(e.__class__)

    def _readline(self, terminator='\r'):
        """
        implemented this myself because comport.readline() is extremely slow
        TODO figure out why?
        """
        eol = b'\r'      # '\r' or b'\r' ?
        c = None
        if terminator is not None:
            eol = terminator  # TODO pylint doesn't like this (redefined-variable-type) but it works
        length_eol = len(eol)
        line = bytearray()
        # TODO: needs length limit?
        try:
            while self.comPort.inWaiting() > 0:
                # c = self.comPort.read(self.comPort.inWaiting())   # not sure if this is better
                c = self.comPort.read(1)
                if c:
                    line += c
                    if line[-length_eol:] == eol:
                        break
                else:
                    break
        except Exception as e:
            logger.error("in _readline")
            logger.error(e.__class__)
            logger.error(str(e.args[0]))
            raise e  # let .read() handle it
        return bytes(line)


