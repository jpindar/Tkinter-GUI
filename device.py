# pylint: disable=unused-argument
"""
File: device.py

Version: 1.03
Author: jpindar@jpindar.com


"""
from time import sleep
from time import time
import string
import globe
import serialdevice_pyserial
import socketdevice
import logging

__author__ = 'jpindar@jpindar.com'

logger = logging.getLogger(__name__)


class DeviceError(Exception):
    """Raise for my specific kind of exception"""

    def __init___(self, name, response):
        super().__init__()
        self.name = name
        self.response = response


class DeviceLoggedOutError(DeviceError):
    """Raise for my specific kind of exception"""

    def __init___(self, name, response):
        super().__init__()


class DeviceTimeoutError(DeviceError):
    """Raise for my specific kind of exception"""

    def __init___(self, name, response):
        super().__init__()


class DeviceResponseError(DeviceError):
    """Raise for my specific kind of exception"""

    def __init___(self, name, response):
        super().__init__()


# class ValidationError(Exception):
#     def __init__(self, message, errors):
#
#         # Call the base class constructor with the parameters it needs
#         super(ValidationError, self).__init__(message)
#   or    super().__init__(message)
#
#         # Now for your custom code...
#         self.errors = errors


def is_correct_id(s):
    if s is None:
        return False
    s2 = s.upper()
    return bool(s2[:7] == "Fluke")


def is_password_prompt(s):
    if s is None:
        return False
    if s[-9:] == 'password:':
        return True
    return False


class Device:
    """
        represents a device regardless of connection type
    """
    # pylint: disable=too-many-public-methods, too-many-instance-attributes
    PASSWORD_LENGTH = 16

    def __init__(self, connection, output, kind):
        """
        constructor for a Device
        connection is a list containing either a serial port number
        or an ip address and a port
        output is anything with an .append(string) method, typically a textbox
        kind is an enum representing the type of connection:
        serial, network or mock

        So device is either a serialdevice_pyserial.SerialDevice()
        or a socketdevice.SocketDevice()
        or a mock

        mock means open a serial port to whatever's there,
        without expecting it to respond correctly

         all methods like self.port.open_port(connection)
         should close the port (if it exists and is open) before opening it
        """
        assert isinstance(connection, list)
        self.kind = kind
        self.connection = connection
        self.comPort = None
        self.port_num = None
        self.port = None
        self.output = output
        self.nominal_gain = 10.0
        self.revision = 0.0
        self.attn_step_size = 0.25  # this will be overridden

    def connect(self):
        success = None
        if self.kind == globe.DUTKind.serial or self.kind == globe.DUTKind.mock:
            self.port = serialdevice_pyserial.SerialDevice()
            try:
                success = self.port.open_port(self.connection)
            except Exception as e:
                logger.error(e.__class__)
                logger.error("can't open COM port" + str(globe.serial_port_num))
                return False
        elif self.kind == globe.DUTKind.network:
            self.port = socketdevice.SocketDevice()  # just a dumb constructor
            try:
                success = self.port.open_port(self.connection)  # this is what actually does something
            except OSError as e:
                # Typical error is:
                # [WinError 10060] A connection attempt failed because the connected party did not properly
                # respond after a period of time,
                #  or established connection failed because connected host has failed to respond
                # This error was already logged, only re-raised to move this UI stuff to this higher level
                self.output.append(e.__doc__)      # "Timeout expired"
                self.output.append(e.strerror)     # "a connection attempt failed because.....
                return False
            except Exception as e:
                logger.error(e.__class__)  # Value Error? TypeError? happens due to a malformed URL, or if it is None
                logger.error("can't create socketdevice or open network socket")
                # output.append("Can't open the network connection " + connection[0] + ':' + str(connection[1]) + "\n")
                return False
        # at this point, success means we've opened a com port. Doesn't mean there's anything there.
        if not success:
            logger.info("connect failed.\n")
            return False
        if self.kind == globe.DUTKind.mock:
            # logger.info("mock constructor is done.\n")
            return True
        sleep(0.5)  # because trying to write to the socket immediately after opening it doesn't always work
        if self.kind == globe.DUTKind.serial:
            self.initialize_me()
        return True

    def login(self):
        globe.password = globe.password[:Device.PASSWORD_LENGTH]
        s = None
        logger.info("attempting to log in\r")
        attempts = 0
        while attempts < 4:
            attempts += 1
            try:
                self.port.write('ID?\r')
                s = self.port.read()
            except OSError as e:
                logger.error(e.__class__)
                break
            except Exception as e:
                logger.error(e.__class__)
                break

            if is_correct_id(s):  # we are logged in or don't need to log in
                break   # break out of the while loop

            if is_password_prompt(s):
                success, s = self.send_password()
                if not success:
                    break

        if is_correct_id(s):
            logger.info("ID is correct, reading some data from device")
            self.initialize_me()
            logger.info("Connected\n")
            return True
        else:
            logger.info(" Failed to Connect\n")
            return False

    def send_password(self):
        logger.info("sending password")
        r = None
        try:
            self.port.write(globe.password + '\r')
            r = self.port.read()  # should respond with "OK"
        except OSError as e:
            logger.error(e.__class__)
            return False, r
        except Exception as e:
            logger.error(e.__class__)
            return False, r
        if r is None:
            logger.info("response is None")
            r = ""
            return False, r
        if r[:2] != "OK":   # if characters 0 thru 1 of s does = OK, go around the while loop again, getting the ID
            # self.output.append(s)
            logger.info("response is not 'OK'")
            r = ""
            return False, r
        else:
            logger.info("response is 'OK'")
            r = ""
            return True, r

    def initialize_me(self):
        # t1 = time()
        self.revision = self.get_revision()
        self.output.append('\n')
        self.nominal_gain = self.get_nominal_gain()
        self.attn_step_size = self.get_attn_step()
        # print(time() - t1)

    def close(self):
        self.port.close_port()
        # self.destroy()

    def set_output(self, output):
        self.output = output

    def get_all(self):
        old_output = self.output  # save output destination
        self.output = globe.dev_null  # suppress output
        s = "firmware revision: " + self.get_revision()
        old_output.append(s)

        # s = "max step: " + self.get_max_step() + "\r"
        # s += "step: " + str(self.get_step())
        # s += "nominal gain: " + str(self.get_nominal_gain())

        s = "start frequency: " + str(self.get_start_freq()) + " MHz\n"
        s += "stop frequency: " + str(self.get_stop_freq()) + " MHz\n"
        s += "current frequency: " + str(self.get_freq()) + " MHz\n"
        s += "channel spacing: " + str(self.get_chan_spacing()) + " KHz\n"
        s += "UltraFine tuning calibration mode: " + str(self.get_uf_mode()) + "\n"
        s += "UltraFine tuning setting: " + str(self.get_ultrafine()) + "\n"
        s += "synthesizer lock status: " + self.get_lock() + "\n"
        old_output.append(s)

        s = "gain setting: " + str(self.get_gain()) + " dB\n"
        s += "manual bypass status: " + str(self.get_bypass()) + "\n"
        s += "overpower bypass enable: " + str(self.get_overpower_bypass_enable()) + "\n"
        s += "overpower bypass status: " + str(self.get_overpower_status()) + "\n"
        s += "eeprom write mode: " + str(self.get_eeprom_write_mode()) + "\n"
        old_output.append(s)
        self.output = old_output  # restore output destination
        return

    def get_id(self):
        msg = 'ID?\r'
        r = None
        logger.info('get_id: sending ' + msg)
        self.output.append(msg + '\n')  # ??
        try:
            # self.port.flushInput()
            self.port.write(msg)
            r = self.port.read()
        except OSError as e:
            if e == TimeoutError:
                self.output.append("\nTimeout Error")
            else:
                self.output.append("\nCommunication Error\n")
        except Exception as e:
            logger.error(e.__class__)
            return
        r = r.strip(' \r\n')
        logger.info('get_id: got <' + str(r) + '>')
        self.output.append(r)
        if r is None:
            raise DeviceResponseError("None", "Bad response: None")
        if 'password' in r:
            raise DeviceLoggedOutError("LoggedOut", r)
        return r

    def get_revision(self):
        # returns something like "0.012.00" or "2.02"
        msg = 'REVISION?\r'
        r = None
        logger.info('sending ' + msg)
        self.output.append(msg)
        try:
            self.port.write(msg)
            r = self.port.read()
        except OSError as e:
            if e == TimeoutError:
                self.output.append("\nTimeout Error")
            else:
                self.output.append("\nCommunication Error\n")
        except Exception as e:    # more specific exceptions should be already caught
            logger.error(e.__class__)
            logger.error("can't communicate")
            raise e
        logger.info('got <' + str(r) + '>')
        self.output.append(r)
        if r is None:
            raise DeviceResponseError("None", "Bad response: None")
        if 'password' in r:
            raise DeviceLoggedOutError("LoggedOut", r)
        r2 = r.strip(" revisionREVISION\r\n")
        # now r2 should be something like "2.01"
        return r2

    def get_any_attn(self, msg):
        r = None
        logger.info('sending ' + msg)
        self.output.append(msg + '\n')
        try:
            self.port.write(msg)
            r = self.port.read()
        except OSError as e:
            if e == TimeoutError:
                self.output.append("\nTimeout Error")
            else:
                self.output.append("\nCommunication Error\n")
        except Exception as e:    # more specific exceptions should be already caught
            logger.error(e.__class__)
            # logger.error("can't log in")
            raise e
        logger.info('got <' + str(r) + '>')
        self.output.append(r)
        if r is None:
            raise DeviceResponseError("None", "Bad response: None")
        if 'password' in r:
            raise DeviceLoggedOutError("LoggedOut", r)
        r2 = r.strip(string.ascii_letters + ' \r\n')
        try:
            f = float(r2)
        except ValueError:
            raise DeviceResponseError("ValueError", "Bad response: '" + r + "'")
        return f

    def set_any_attn(self, msg):
        logger.info('sending ' + msg)
        self.output.append(msg + '\n')
        r = None
        try:
            self.port.write(msg)
            r = self.port.read()
        except OSError as e:
            if e == TimeoutError:
                self.output.append("\nTimeout Error")
            else:
                self.output.append("\nCommunication Error\n")
        except Exception as e:    # more specific exceptions should be already caught
            logger.error(e.__class__)
            # logger.error("can't log in")
            raise e
        logger.info('got <' + str(r) + '>')
        self.output.append(r)
        if r is None:
            raise DeviceResponseError("None", "Bad response: None")
        if 'password' in r:
            raise DeviceLoggedOutError("LoggedOut", r)
        return r

    def get_any_boolean(self, msg):
        logger.info('sending ' + msg)
        self.output.append(msg + '\n')
        r = None
        try:
            self.port.write(msg)
            r = self.port.read()
        except OSError as e:
            if e == TimeoutError:
                self.output.append("\nTimeout Error")
            else:
                self.output.append("\nCommunication Error\n")
        except Exception as e:    # more specific exceptions should be already caught
            logger.error(e.__class__)
            # logger.error("can't log in")
            raise e
        logger.info('got <' + str(r) + '>')
        self.output.append(r)
        if r is None:
            raise DeviceResponseError("None", "Bad response: None")
        if 'password' in r:
            raise DeviceLoggedOutError("LoggedOut", r)
        try:
            r2 = int(r)
        except ValueError:
            raise DeviceResponseError("ValueError", "Bad response: '" + r + "'")
        return r2

    def set_any_boolean(self, msg, data):
        if data in [True, '1', 1]:
            msg += ' 1\r'
        else:
            msg += ' 0\r'
        logger.info('sending ' + msg)
        self.output.append(msg + '\n')
        r = None
        try:
            self.port.write(msg)
            r = self.port.read()
        except OSError as e:
            if e == TimeoutError:
                self.output.append("\nTimeout Error")
            else:
                self.output.append("\nCommunication Error\n")
        except Exception as e:    # more specific exceptions should be already caught
            logger.error(e.__class__)
            # logger.error("can't log in")
            raise e
        logger.info('got <' + str(r) + '>')
        self.output.append(r)
        if r is None:
            raise DeviceResponseError("None", "Bad response: None")
        if 'password' in r:
            raise DeviceLoggedOutError("LoggedOut", r)
        return r

    def get_any_detector(self, msg):
        logger.info('sending ' + msg)
        self.output.append(msg + '\n')
        r = None
        try:
            self.port.write(msg)
            r = self.port.read()
        except OSError as e:
            if e == TimeoutError:
                self.output.append("\nTimeout Error")
            else:
                self.output.append("\nCommunication Error\n")
        except Exception as e:    # more specific exceptions should be already caught
            logger.error(e.__class__)
            # logger.error("can't log in")
            raise e
        logger.info('got <' + str(r) + '>')
        self.output.append(str(r))
        if r is None:
            raise DeviceResponseError("None", "Bad response: None")
        if 'password' in r:
            raise DeviceLoggedOutError("LoggedOut", r)
        n = 0
        r = r.strip(string.ascii_letters + '= \r\n')
        try:
            n = int(r)
            # zero out lowest 6 bits
            # r = r // 64
            # r = r * 64
        except (ValueError, AttributeError):
            raise DeviceResponseError("ValueError", "Bad response: '" + r + "'")
        logger.info('returning <' + str(n) + '>')
        return n

    def get_any_freq(self, msg):
        logger.info('sending ' + msg)
        self.output.append(msg)
        r = None
        try:
            self.port.write(msg)
            r = self.port.read()
        except OSError as e:
            if e == TimeoutError:
                self.output.append("\nTimeout Error")
            else:
                self.output.append("\nCommunication Error\n")
        except Exception as e:    # more specific exceptions should be already caught
            logger.error(e.__class__)
            # logger.error("can't log in")
            raise e
        logger.info('got <' + str(r) + '>')
        self.output.append(r)
        if r is None:
            raise DeviceResponseError("None", "Bad response: None")
        if 'password' in r:
            raise DeviceLoggedOutError("LoggedOut", r)
        r = r.strip(string.ascii_letters + ' \r\n')
        if r is None:   # TypeError would catch this
            raise DeviceResponseError("None", "Bad response: only whitespace or terminations")
        try:
            f = float(r)
        except (ValueError, AttributeError, TypeError) as e:
            raise DeviceResponseError("ValueError", "Bad response: '" + r + "'")
        return f

    def set_any_freq(self, msg) -> str:
        logger.info('sending ' + msg)
        self.output.append(msg + '\n')
        r = None
        try:
            self.port.write(msg)
            r = self.port.read()
        except OSError as e:
            logger.error(e.__class__)
            if e == TimeoutError:
                self.output.append("\nTimeout Error")
            else:
                self.output.append("\nCommunication Error\n")
            # raise e
        except Exception as e:    # more specific exceptions should be already caught
            logger.error(e.__class__)
            raise e
        logger.info('got <' + str(r) + '>')
        self.output.append(r)
        if r is None:
            raise DeviceResponseError("None", "Bad response: None")
        if 'password' in r:
            raise DeviceLoggedOutError("LoggedOut", r)
        return r

    def get_any_string(self, msg):
        logger.info('sending ' + msg)
        self.output.append(msg)
        r = None
        try:
            self.port.write(msg)
            r = self.port.read()
        except OSError as e:
            if e == TimeoutError:
                self.output.append("\nTimeout Error")
            else:
                self.output.append("\nCommunication Error\n")
        except Exception as e:    # more specific exceptions should be already caught
            logger.error(e.__class__)
            # logger.error("can't log in")
            raise e
        r = r.rstrip("\r\n")
        logger.info('got <' + str(r) + '>')
        return r

    def get_any_ultrafine(self, msg):
        logger.info('sending ' + msg)
        self.output.append(msg + '\n')
        r = None
        try:
            self.port.write(msg)
            r = self.port.read()
        except OSError as e:
            if e == TimeoutError:
                self.output.append("\nTimeout Error")
            else:
                self.output.append("\nCommunication Error\n")
        except Exception as e:    # more specific exceptions should be already caught
            logger.error(e.__class__)
            # logger.error("can't log in")
            raise e
        logger.info('got <' + str(r) + '>')
        self.output.append(r)
        if r is None:
            raise DeviceResponseError("None", "Bad response: None")
        if 'password' in r:
            raise DeviceLoggedOutError("LoggedOut", r)
        r = r.strip(" clicks\r\n")
        if r is None:
            raise DeviceResponseError("None", "Bad response: None")
        try:
            r2 = int(r)
        except (ValueError, AttributeError):
            raise DeviceResponseError("ValueError", "Bad response: '" + r + "'")
        return r2

    def set_any_ultrafine(self, msg):
        # returns integer, used to return "OK"? Or was that the RF-ResQ?
        logger.info('sending ' + msg)
        self.output.append(msg + '\n')
        r = None
        try:
            self.port.write(msg)
            r = self.port.read()
        except OSError as e:
            if e == TimeoutError:
                self.output.append("\nTimeout Error")
                raise DeviceTimeoutError("none", "unknown")
            else:
                self.output.append("\nCommunication Error\n")
                raise DeviceResponseError("none", "unknown")
        except Exception as e:    # more specific exceptions should be already caught
            logger.error(e.__class__)
            # logger.error("can't log in")
            raise e
        logger.info('got <' + str(r) + '>')
        self.output.append(r)
        if r is None:
            raise DeviceResponseError("None", "Bad response: None")
        if 'password' in r:
            raise DeviceLoggedOutError("LoggedOut", r)
        return r

    def get_chan_spacing(self):
        msg = "CHAN SPACE?\r"
        logger.info('sending ' + msg)
        self.output.append(msg + '\n')
        r = None
        try:
            self.port.write(msg)
            r = self.port.read()
        except OSError as e:
            if e == TimeoutError:
                self.output.append("\nTimeout Error")
                raise DeviceTimeoutError("none", "unknown")
            else:
                self.output.append("\nCommunication Error\n")
                raise DeviceResponseError("none", "unknown")
        except Exception as e:    # more specific exceptions should be already caught
            logger.error(e.__class__)
            # logger.error("can't log in")
            raise e
        self.output.append(r)
        logger.info('got <' + str(r) + '>')
        if r is None:
            raise DeviceResponseError("None", "Bad response: None")
        if 'password' in r:
            raise DeviceLoggedOutError("LoggedOut", "foo")
        r2 = r.strip(string.ascii_letters + ' \r\n')
        if r2 is None:
            raise DeviceResponseError("None", "Bad response: '" + r + "' (None)")
        try:
            f = float(r2)
        except ValueError:
            raise DeviceResponseError("ValueError", "Bad response: '" + r + "'")
        return f

    # def set_chan_spacing(self, data):
    #     msg = "CHAN SPACE " + str(data) + '\r'
    #     logger.info('sending ' + msg)
    #     self.output.append(msg + '\n')
    #     self.port.write(msg)
    #     r = self.port.read()
    #     logger.info('got <' + str(r) + '>')
    #     self.output.append(r)
    #     if 'password' in r:
    #         raise DeviceLoggedOutError("LoggedOut",r)
    #     return r

    def get_max_step(self):
        msg = "MAX STEP?\r"
        logger.info('sending ' + msg)
        self.output.append(msg + '\n')
        r = None
        try:
            self.port.write(msg)
            r = self.port.read()
        except OSError as e:
            if e == TimeoutError:
                self.output.append("\nTimeout Error")
                raise DeviceTimeoutError("none", "unknown")
            else:
                self.output.append("\nCommunication Error\n")
                raise DeviceResponseError("none", "unknown")
        except Exception as e:    # more specific exceptions should be already caught
            logger.error(e.__class__)
            # logger.error("can't log in")
            raise e
        logger.info('got <' + str(r) + '>')
        self.output.append(r)
        if r is None:
            raise DeviceError("None", "Bad response: None")
        if 'password' in r:
            raise DeviceLoggedOutError("LoggedOut", r)
        return r

    def get_overpower_status(self):
        msg = "OVERPOWER?\r"
        r = None
        try:
            self.port.write(msg)
            r = self.port.read()
        except OSError as e:
            if e == TimeoutError:
                self.output.append("\nTimeout Error")
                raise DeviceTimeoutError("none", "unknown")
            else:
                self.output.append("\nCommunication Error\n")
                raise DeviceResponseError("none", "unknown")
        except Exception as e:    # more specific exceptions should be already caught
            logger.error(e.__class__)
            # logger.error("can't log in")
            raise e
        if r is None:
            raise DeviceResponseError("None", "Bad response: None")
        if 'password' in r:
            raise DeviceLoggedOutError("LoggedOut", r)
        try:
            r2 = int(r)
        except (ValueError, AttributeError):
            raise DeviceResponseError("ValueError", "Bad response: '" + r + "'")
        return r2

    def get_step(self):
        msg = "STEP?\r"
        logger.info('sending ' + msg)
        self.output.append(msg + '\n')
        r = None
        try:
            self.port.write(msg)
            r = self.port.read()
        except OSError as e:
            if e == TimeoutError:
                self.output.append("\nTimeout Error")
                raise DeviceTimeoutError("none", "unknown")
            else:
                self.output.append("\nCommunication Error\n")
                raise DeviceResponseError("none", "unknown")
        except Exception as e:    # more specific exceptions should be already caught
            logger.error(e.__class__)
            # logger.error("can't log in")
            raise e
        logger.info('got <' + str(r) + '>')
        self.output.append(r)
        if r is None:
            raise DeviceResponseError("None", "Bad response: None")
        if 'password' in r:
            raise DeviceLoggedOutError("LoggedOut", "foo")
        try:
            r2 = int(r)
        except (ValueError, AttributeError):
            raise DeviceResponseError("ValueError", "Bad response: '" + r + "'")
        return r2

    def set_step(self, step):
        # returns 1 or 0 for lock status, used to return "OK"? Or was that the RF-ResQ?
        msg = "STEP " + str(step) + '\r'
        logger.info('sending ' + msg)
        self.output.append(msg + '\n')
        r = None
        try:
            self.port.write(msg)
            r = self.port.read()
        except OSError as e:
            if e == TimeoutError:
                self.output.append("\nTimeout Error")
                raise DeviceTimeoutError("none", "unknown")
            else:
                self.output.append("\nCommunication Error\n")
                raise DeviceResponseError("none", "unknown")
        except Exception as e:    # more specific exceptions should be already caught
            logger.error(e.__class__)
            # logger.error("can't log in")
            raise e
        logger.info('got <' + str(r) + '>')
        self.output.append(r)
        if r is None:
            raise DeviceResponseError("None", "Bad response: None")
        if 'password' in r:
            raise DeviceLoggedOutError("LoggedOut", r)
        return r


#     #### methods that essentially just call another method


    def get_nominal_gain(self):
        g = self.get_any_attn("NOMINALGAIN?\r")
        if self.revision == 2.0:  # workaround for bug in this firmware version
            if g is None:
                return 1.0
            return g / 4.0   # this version erroneously returned the number of 0.25 dB steps
        else:
            if g is None:
                return 1.0
            return g

    def get_agc(self):
        return self.get_any_boolean("AGC?\r")

    def get_attn_step(self):
        return self.get_any_attn("ATT STEP?\r")

    def get_if_freq(self):
        return self.get_any_freq("IFRQ?\r")

    def get_start_freq(self):
        return self.get_any_freq("START FREQ?\r")

    def get_stop_freq(self):
        return self.get_any_freq("STOP FREQ?\r")

    def get_freq(self):
        return self.get_any_freq("FREQ?\r")

    def set_freq(self, freq: float) -> str:
        return self.set_any_freq("FREQ " + str(freq)[:10] + '\r')

    def get_lofreq(self):
        # return self.get_any_freq("LO?\r")
        return self.get_any_freq("LOFREQ?\r")

    def get_lock(self):
        # string instead of boolean cuz it can be handy to get debug info this way
        return self.get_any_string("LOCK?\r")

    def set_lofreq(self, freq: float) -> str:
        # return self.set_any_freq("LO " + str(freq)[:10] + '\r')
        return self.set_any_freq("LOFREQ " + str(freq)[:10] + '\r')

    def get_bypass(self):
        # return self.get_any_boolean("ACT?\r")
        return self.get_any_boolean("BYPASS?\r")

    def set_bypass(self, b):
        self.set_any_boolean("BYPASS", b)

    def get_overpower_bypass_enable(self):
        if self.revision == 0.0:
            self.revision = self.get_revision()
        r = None
        try:
            if float(self.revision) < 2.02:
                r = self.get_any_boolean("OVERPOWERBYPASS?\r")
            else:
                r = self.get_any_boolean("OVERPOWERBYPASSENABLE?\r")
        except DeviceError as e:
            logger.error(e.__class__)
            return False
        if r is None:
            return False
        return r

    def set_overpower_bypass_enable(self, b):
        if self.revision == 0.0:
            self.revision = self.get_revision()
        try:
            if float(self.revision) < 2.02:
                self.set_any_boolean("OVERPOWERBYPASS", b)
            else:
                self.set_any_boolean("OVERPOWERBYPASSENABLE", b)
        except DeviceError as e:
            logger.error(e.__class__)

    def get_eeprom_write_mode(self):
        r = self.get_any_boolean("SAVESTATE?\r")
        if r is None:
            return True  # not sure what desired behavior is TODO
        return r

    def set_eeprom_write_mode(self, b):
        return self.set_any_boolean("SAVESTATE", b)

    def set_baud(self, b):
        return self.set_any_boolean("BAUD", b)

    def get_uf_mode(self):
        return self.get_any_boolean("UFCM?\r")

    def set_uf_mode(self, b):
        self.set_any_boolean("UFCM", b)

    def get_gain(self):
        return self.get_any_attn("GAIN?\r")

    def set_gain(self, data: str):
        return self.set_any_attn("GAIN " + str(data)[:6] + '\r')

    def get_attn(self):
        return self.get_any_attn("ATTN?\r")

    def set_attn(self, data: str):
        # TODO should this take the absolute value?
        # or limit to positive numbers?
        return self.set_any_attn("ATTN " + str(data)[:6] + '\r')

    def get_max_attn(self):
        return self.get_any_attn("MXAT?\r")

    def get_ultrafine(self):
        return self.get_any_ultrafine("UFSE?\r")

    def set_ultrafine(self, data: int):
        return self.set_any_ultrafine("UFSE " + str(data) + '\r')

    def get_detector_b(self):
        return self.get_any_detector("DETB?\r")

    def get_detector_a(self):
        return self.get_any_detector("DETA?\r")
