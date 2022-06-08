"""
module to control a Fluke 8845A digital multimeter
uses serialdevice, which uses pySerial
The meter should be in its native (i.e. 8845A) mode and set for 'computer' mode, not 'terminal' mode

"""
__author__ = 'jpindar@jpindar.com'

import sys
import time
from typing import List, Dict, Optional, Any, Union
import serialdevice
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Multimeter(serialdevice.SerialDevice):
    """
    controls a Fluke 8845A digital multimeter
    """
    default_address = 5  # address to use if optional parameter is not supplied by caller
    default_baud = 19200
    display_name = 'Fluke Multimeter'  # name to use in GUI messages etc.
    ID_QUERY = "*IDN?\n"
    GOOD_ID_RESPONSE = "FLUKE,8845A,9344019,09/29/06-16:59"  # when in 8845A mode
    GOOD_ID_RESPONSE_45 = "FLUKE, 45, 9344019, 2.0 D2.0"  # when in Fluke 45 emulation mode
    ERROR_CODE_OK = "+0,\"No error\""
    read_delay = 10
    read_mode = 1
    timeout = 5.0


    def __init__(self, address: int = default_address, baud=default_baud):
        super().__init__()
        self.port_num = address
        self.baud_rate = baud
        self.open_port()

    def reset(self):
        self.write("*rst\n")

    def clear_errors(self):
        self.write("*cls\n")

    def get_errors(self):
        self.write("SYST:ERR?\n")
        response = self.read()
        return response

    def remote(self):
        self.write("SYST:REM\n")

    def query(self, cmd: str) -> Optional[str]:
        """ TODO: implement the Abort, Retry, Ignore system that I used in the complete software

        """
        response = None
        finished = False
        while not finished:
            try:
                logger.info("sending <" + cmd + ">")
                self.write(cmd)
                time.sleep(self.read_delay)
                response = self.read()
                finished = True
                # return response
            # except (serialdevice.SerialException, serialdevice.SerialTimeoutException) as e:
            except (serialdevice.serial.SerialException, serialdevice.serial.SerialTimeoutException) as e:
                logger.warning("SerialDevice.query\r\n")
                logger.warning(e.__class__)
                logger.warning(e.__doc__)
                logger.warning(e.args[0])   # or  just args
                # raise e
                return ""
            except Exception as e:
                logger.warning("SerialDevice.query\r\n")
                logger.warning(e.__class__)
                logger.warning(e.__doc__)
                raise e
        return response

    def get_ID(self):
        logger.info(str("sending query: " + self.ID_QUERY))
        try:
            s = self.query(self.ID_QUERY)
        except (serialdevice.serial.SerialException, serialdevice.serial.SerialTimeoutException) as e:
            logger.warning("SerialDevice.query\r\n")
            logger.warning(e.__class__)
            logger.warning(e.__doc__)
            logger.warning(e.args[0])   # or  just args
            # raise e
            return None
        except Exception as e:
            logger.warning(e.__class__)
            logger.warning(e.__doc__)
            logger.warning(e.__cause__)
            raise e
        logger.info(str("response is " + s))
        return s

    def get_DCVolts(self, scale=None):
        """
         note that this returns 9.9E37 when the device's display reads "overload"
        """
        s = None
        cmd = "MEAS:VOLT:DC? "
        if scale is not None:
            cmd += str(scale)
        cmd += "\n"
        logger.info(str("sending query: " + cmd))
        try:
            s = self.query(cmd)
        except (serialdevice.serial.SerialException, serialdevice.serial.SerialTimeoutException) as e:
            logger.warning("SerialDevice.query\r\n")
            logger.warning(e.__class__)
            logger.warning(e.__doc__)
            logger.warning(e.args[0])   # or  just args
            # raise e
            return None
        except Exception as e:
            logger.warning(e.__class__)
            logger.warning(e.__doc__)
            logger.warning(e.__cause__)
            raise e
        logger.info(str("response is " + s))
        try:
            f = float(s)
        except ValueError:
            logger.warning("The response could not be converted to a float")
            return None
        return f


def main():
    """
    basic usage example
    There are checks here that are for testing and aren't needed in production code

    The exception handling here is not good, but would be done differently
    depending on the context anyway
    """
    log_filename = "multimeter.log"
    logging.basicConfig(filename=log_filename, filemode='a', format='%(levelname)-8s:%(asctime)s %(name)s: %(message)s')
    logger.setLevel(logging.INFO)
    logger.info("multimeter demo")
    print("Connecting to Fluke DMM")
    try:
        dmm = Multimeter()
        dmm.open_port()
    except Exception as e:
        print("There was a problem finding the instrument")
        sys.exit()
    else:
        print("Found the instrument at " + str(dmm.port_name))
    if dmm.port is None:
        sys.exit()

    assert isinstance(dmm.port, serialdevice.serial.Serial)
    if dmm.is_open():
        print('serial port is open')
    msg = Multimeter.ID_QUERY
    dmm.write(msg)
    s = dmm.read()
    print("The device returned ID string:  " + s)
    if s == Multimeter.GOOD_ID_RESPONSE:
        print("OK")
    elif s == Multimeter.GOOD_ID_RESPONSE_45:
        print("The meter is in the wrong mode (Fluke 45 emulation).")
        sys.exit()
    else:
        print("ERROR")
        sys.exit()

    s = dmm.get_errors()
    if s != Multimeter.ERROR_CODE_OK:
        print(s)
    dmm.clear_errors()

    dmm.remote()
    print("measuring DC voltage...")
    try:
        v = dmm.get_DCVolts()
    except Exception as e:
        print("get_DCVolts() had a problem: ", e.__class__)
        raise e
    else:
        assert isinstance(v, float)
        print(f"{v} volts dc")

    dmm.close_port()


if __name__ == '__main__':
    main()


