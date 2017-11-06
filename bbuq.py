# pylint: disable=wrong-import-position,unused-argument,line-too-long
"""
File: bbuq.py

Version: 1.03
Author: jpindar@jpindar.com


"""
__author__ = 'jpindar@jpindar.com'

import logging
logger = logging.getLogger(__name__)
import string
import globe
import serialdevice_pyserial


def correct_id(s):
    if s is None:
        return False
    s2 = s.upper()
    return bool(s2[:7] == "ULTRA-Q")



class UltraQ:
    """
       represents a BBUQ type Ultra-Q, regardless of connection type
    """
    default_name = "ASRL4::INSTR"
    class_name = 'UltraQ'
    friendly_name = 'UltraQ'


    def __init__(self, connection, output, kind):
        """
        constructor for an Ultra-Q device
        connection is a list containing either a serial port number
        or an ip address and a port
        output is anything with an .append(string) method
        kind is an enum representing the type of connection:
        serial, network or mock
        mock means open a serial port to whatever's there,
        without expecting it to respond correctly

         all methods like self.port.open_port(connection)
         should close the port (if it exists and is open) before opening it
        """
        self.kind = kind
        self.connection = connection
        self.exists = False
        self.comPort = None
        self.friendly_name = "Ultra-Q"
        self.port_num = None
        self.port = None
        self.output = output
        self.nominal_gain = 10.0
        self.revision = 0.0
        self.attn_step_size = 0.25
        logger.info(self.class_name + " constructor")
        if self.connect():
            self.login()


    def connect(self):
        success = None
        if self.kind == globe.DUTKind.serial or self.kind == globe.DUTKind.mock:
            try:
                self.port = serialdevice_pyserial.SerialDevice()  # just a dumb constructor
                success = self.port.open_port(self.connection)   # this is what actually does something
            except Exception as e:
                logger.error(e.__class__)
                logger.error("can't create serialdevice or open COM" + str(globe.serial_port_num))
                return False
        if not success:
            logger.info(self.class_name + " port constructor failed.\n")
            return False
        if self.kind == globe.DUTKind.mock:
            logger.info(self.class_name + " mock constructor is done.\n")
            self.exists = True
            return True
        return True


    def login(self):
        s = None
        # remember the first command sometimes fails, that's OK
        attempts = 0
        while attempts < 3:  # arbitrary, but must let it try several times
            attempts +=1
            try:
                self.port.write('ID?\r')
                s = self.port.read()
            except Exception as e:    # more specific exceptions should be already caught
                logger.error(e.__class__)
                logger.error("can't get_id()")
                raise e
            if correct_id(s):  # we are logged in
                break

        if correct_id(s):
            self.exists = True
            self.initialize_me()
            logger.info(self.class_name + " constructor is done.\n")
        else:
            self.exists = False
            logger.info(self.class_name + " constructor failed, raising IOError.\n")
            # TODO create a better exception class for this
            raise IOError


    def initialize_me(self):
        self.revision = self.get_revision()
        self.output.append('\n')
        self.nominal_gain = self.get_nominal_gain()
        self.attn_step_size = self.get_attn_step()


    def close(self):
        self.port.close_port()
        # self.destroy()

    def set_output(self, output):
        self.output = output

    def get_all(self):
        pass    # TODO create get_all()


    def get_id(self):
        msg = 'ID?\r'
        r = None
        logger.info('get_id: sending ' + msg)
        self.output.append(msg + '\n')  # ??
        # self.port.flushInput()  # nah
        self.port.write(msg)
        r = self.port.read()
        r = r.strip(' \r\n')
        logger.info('get_id: got <' + str(r) + '>')
        if r is None:
            r = "None"
        self.output.append(r)
        return r


    def get_revision(self):
        # returns something like "0.012.00" or "2.02"
        msg = 'REVISION?\r'
        logger.info('sending ' + msg)
        self.output.append(msg)
        self.port.write(msg)
        r = self.port.read()
        logger.info('got <' + str(r) + '>')
        r = r.strip(" revisionREVISIONversionVERSION\r\n")
        self.output.append(r)
        return r

    def get_any_freq(self, msg):
        logger.info('sending ' + msg)
        self.output.append(msg + '\n')
        self.port.write(msg)
        r = self.port.read()
        logger.info('got <' + str(r) + '>')
        self.output.append(r)
        r = r.strip(string.ascii_letters + ' \r\n')
        # logger.info(r)
        if r is None:
            return 0.0
        try:
            f = float(r)
        except ValueError:
            return 0.0
        return f


    def set_any_freq(self, msg) -> str:
        logger.info('sending ' + msg)
        self.output.append(msg + '\n')
        self.port.write(msg)
        r = self.port.read()
        logger.info('got <' + str(r) + '>')
        self.output.append(r)
        return r


    def get_any_boolean(self, msg):
        logger.info('sending ' + msg)
        self.output.append(msg + '\n')
        self.port.write(msg)
        r = self.port.read()
        logger.info('got <' + str(r) + '>')
        self.output.append(r)
        try:
            n = int(r)
        except ValueError:
            return None
        return n

    def set_any_boolean(self, msg, data):
        if data in [True, '1', 1]:
            msg += ' 1\r'
        else:
            msg += ' 0\r'
        logger.info('sending ' + msg)
        self.output.append(msg + '\n')
        self.port.write(msg)
        r = self.port.read()
        logger.info('got <' + str(r) + '>')
        self.output.append(r)
        return r

    def get_any_attn(self,msg):
        logger.info('sending ' + msg)
        self.output.append(msg + '\n')
        self.port.write(msg)
        r = self.port.read()
        logger.info('got <' + str(r) + '>')
        self.output.append(r)
        if r is None:
            return 0.0
        try:
            r = r.strip(string.ascii_letters + ' \r\n')
            f = float(r)
        except ValueError:
            return 0.0
        return f

    def set_any_attn(self, msg):
        logger.info('sending ' + msg)
        self.output.append(msg + '\n')
        self.port.write(msg)
        r = self.port.read()
        logger.info('got <' + str(r) + '>')
        self.output.append(r)
        return r

    def get_attn_step(self):
        return self.get_any_attn("ATT STEP?\r")


    def get_any_detector(self, msg):
        logger.info('sending ' + msg)
        self.output.append(msg + '\n')
        self.port.write(msg)
        r = self.port.read()
        logger.info('got <' + str(r) + '>')
        self.output.append(str(r))
        # if r is None:
        #     r = 0  # todo: improve this
        n = 0
        try:
            r = r.strip(string.ascii_letters + ' \r\n')
            # r = r.split(" ")
            logger.info(r)
            # r = int(r[-1])
            n = int(r)
            # zero out lowest 6 bits
            # r = r // 64
            # r = r * 64
        except (ValueError, AttributeError):
            n = 999999  # semantically, should be None, but this makes the calling code simpler
        logger.info('returning <' + str(n) + '>')
        return n

    def get_step(self):
        # returns an integer
        msg = "STEP?\r"
        logger.info('sending ' + msg)
        self.output.append(msg + '\n')
        self.port.write(msg)
        r = self.port.read()
        logger.info('got <' + str(r) + '>')
        self.output.append(r)
        if r is not None:
            r = int(r)
        return r

    def set_step(self, step):
        # returns 1 or 0 for lock status, used to return "OK"? Or was that the RF-ResQ?
        msg = "STEP " + str(step) + '\r'
        logger.info('sending ' + msg)
        self.output.append(msg + '\n')
        self.port.write(msg)
        r = self.port.read()
        logger.info('got <' + str(r) + '>')
        self.output.append(r)
        return r

    def get_uf(self):
        # returns an integer
        msg = "UFSE?\r"
        logger.info('sending ' + msg)
        self.output.append(msg + '\n')
        self.port.write(msg)
        r = self.port.read()
        logger.info('got <' + str(r) + '>')
        self.output.append(r)
        r = r.strip(" clicks\r\n")
        if r is not None:
            r = int(r)
        return r

    def set_uf(self, step):
        # returns integer, used to return "OK"? Or was that the RF-ResQ?
        msg = "UFSE " + str(step) + '\r'
        logger.info('sending ' + msg)
        self.output.append(msg + '\n')
        self.port.write(msg)
        r = self.port.read()
        logger.info('got <' + str(r) + '>')
        self.output.append(r)
        return r

    def get_lofreq(self):
        # OK
        return self.get_any_freq("LO?\r")

    def get_start_freq(self):
        # OK
        return self.get_any_freq("START FREQ?\r")

    def get_stop_freq(self):
        # OK
        return self.get_any_freq("STOP FREQ?\r")

    def get_freq(self):
        # OK
        return self.get_any_freq("FREQ?\r")

    def set_freq(self, freq: float) -> str:
        return self.set_any_freq("FREQ " + str(freq)[:10] + '\r')

    def set_lofreq(self, freq: float) -> str:
        return self.set_any_freq("LO " + str(freq)[:10] + '\r')

    def get_bypass(self):
        return self.get_any_boolean("BYPASS?\r")

    def get_overpower_status(self):
        #return self.get_any_boolean("OVERPOWER?\r")
        msg = "OVERPOWER?\r"
        # logger.info('sending ' + msg)
        # self.output.append(msg + '\n')
        self.port.write(msg)
        r = self.port.read()
        # logger.info('got <' + str(r) + '>')
        # self.output.append(r)
        try:
            r = int(r)
        except ValueError:
            r = None
        return r

    def set_bypass(self, b):
        self.set_any_boolean("BYPASS ", b)


    def get_overpower_bypass_enable(self):
        if float(self.revision) < 2.02:
            r = self.get_any_boolean("OVERPOWERBYPASS?\r")
        else:
            r = self.get_any_boolean("OVERPOWERBYPASSENABLE?\r")
        if r is None:
            return False
        return r

    def set_overpower_bypass_enable(self, b):
        if float(self.revision) < 2.02:
            self.set_any_boolean("OVERPOWERBYPASS", b)
        else:
            self.set_any_boolean("OVERPOWERBYPASSENABLE", b)

    def get_write(self):
        r = self.get_any_boolean("SAVESTATE?\r")
        if r is None:
            return True  # not sure what desired behavior is TODO
        return r

    def set_write(self, b):
        return self.set_any_boolean("SAVESTATE", b)

    def get_uf_mode(self):
        return self.get_any_boolean("UFCM?\r")

    def set_uf_mode(self, b):
        self.set_any_boolean("UFCM ", b)

    def get_nominal_gain(self):
        g = self.get_any_attn("NOMINALGAIN?\r")
        if self.revision == 2.0:  # workaround for bug in this firmware version
            if g is None:
                return 1
            return g/4.0   # this version erroneously returned the number of 0.25 dB steps
        else:
            if g is None:
                g = 1
            return g


    def get_gain(self):
        return self.get_any_attn("GAIN?\r")

    def set_gain(self, data: str):
        return self.set_any_attn("GAIN " + str(data)[:6] + '\r')


    def get_attn(self):
        return self.get_any_attn("ATTN?\r")

    def set_attn(self, data: str):
        # TODO should this take the absolute value?
        # or limit to positive numbers?
        # if data<0:
        #    data = 0
        return self.set_any_attn("ATTN " + str(data)[:6] + '\r')

    def get_max_attn(self):
        return self.get_any_attn("MXAT?\r")

    def get_detector_b(self):
        return self.get_any_detector("DETB?\r")

    def get_detector_a(self):
        return self.get_any_detector("DETA?\r")

    def get_max_step(self):
        msg = "MAX STEP?\r"
        logger.info('sending ' + msg)
        self.output.append(msg + '\n')
        self.port.write(msg)
        r = self.port.read()
        logger.info('got <' + str(r) + '>')
        self.output.append(r)
        return r

    def get_chan_spacing(self):
        msg = "CHAN SPACE?\r"
        logger.info('sending ' + msg)
        self.output.append(msg + '\n')
        self.port.write(msg)
        r = self.port.read()
        self.output.append(r)
        r = r.strip(string.ascii_letters + ' \r\n')
        logger.info('got <' + str(r) + '>')
        f = float(r)
        return f

    def set_chan_spacing(self, data):
        msg = "CHAN SPACE "+ str(data) + '\r'
        logger.info('sending ' + msg)
        self.output.append(msg + '\n')
        self.port.write(msg)
        r = self.port.read()
        logger.info('got <' + str(r) + '>')
        self.output.append(r)
        return r


def main():
    pass


if __name__ == "__main__":
    main()
