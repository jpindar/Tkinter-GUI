# pylint: disable=wrong-import-position,unused-argument,line-too-long
"""
File: socketdevice.py

"""
import logging
logger = logging.getLogger(__name__)
import time
import select
import socket
__author__ = 'jpindar@jpindar.com'

read_delay = 0.2



class SocketDevice:
    """
    A TCP port, created by socket
    """
    def __init__(self):
        """constructor for serial device, no parameters
        :rtype : SerialDevice
        create an instance variable but don't open the port
        """
        logger.info(" ")
        logger.info("SocketDevice constructor")
        self.exists = False
        self.comPort = None
        self.port_num = None
        self.sock = None
        self.remote_host = None
        self.remote_port = None
        logger.info("SocketDevice constructor done")


    def open_port(self, connection_info):
        """
         opens the port with fixed parameters in connection_info
         remote_host is an IP address in string form
         remote_port is an integer
         these are separated by a colon

          TODO  set timeout, default is too long?, ideally make this configurable

        """
        self.close_port()
        self.remote_host = connection_info[0]
        self.remote_port = connection_info[1]
        s2 = self.remote_host.find(':')  # the colon between ip address and port
        if s2>0:
            self.remote_port = self.remote_host[s2+1:]
            self.remote_host = self.remote_host[:s2]
        port_name = str(self.remote_host) + ':' + str(self.remote_port)
        logger.info("opening TCP socket " + port_name)
        # dt = socket.getdefaulttimeout()
        # socket.setdefaulttimeout()
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # t = self.sock.gettimeout()
            self.sock.connect((self.remote_host, int(self.remote_port)))   # the apparently redundant parenthesis are not redundant
            self.exists = True
        except OSError as e:
            # logger.warning("could not create the socket\r\n")
            logger.warning("could not connect the socket\r\n")
            logger.warning(e.__class__)    # TimeoutError
            logger.warning(e.__doc__)      # "Timeout expired"
            logger.warning(e.strerror)     # "a connection attempt failed because.....
            logger.warning(e.errno)
            logger.warning(e.winerror)
            raise e
        except [ValueError] as e:
            # I'd like to catch TypeError, but not allowed to catch classes that don't inherit from BaseException
            logger.warning("SocketDevice.openPort: invalid setting\r\n")
            logger.warning(e.__class__)
            # logger.warn(e.__doc__)
            # raise e
            return False
        except Exception as e:
            logger.warning("SocketDevice.openPort: Can't open that socket\r\n")
            logger.warning(e.__class__)
            # logger.warn(e.__doc__)
            # raise e
            return False
        else:
            # assert isinstance(self.comPort, pyvisa.resources.serial.SerialInstrument)
            # not necessary if constructor worked, but assertions are good.
            logger.info("SocketDevice.openPort: opened a " + str(self.sock.__class__))
            self.exists = True
            return True


    def is_open(self):
        """
        This is really just checking if open_port() succeeded
        :rtype: boolean
        """
        if not hasattr(self, 'sock'):
            logger.warning("isOpen():port does not exist")
            return False
        if self.sock is None:
            logger.warning("isOpen():port does not exist")
            return False
        return True

    def write(self, msg):
        """send a string
        :param msg: the string to send
        :return: none
        # TODO: do we need to check the port's status first?
        # TODO: pop up or other obvious error handling when exception occurs?
        """
        response = None
        bytes_sent = 0
        if not hasattr(self, 'sock'):
            logger.warning("can't write to non-existent socket")
            return response
        # msg = msg + "\n"
        # logger.info("SocketDevice.write: writing " + str(msg) + " to socket")
        msg_bytes = msg.encode(encoding='UTF-8')
        try:
            bytes_sent = self.sock.send(msg_bytes)
            # success = self.sock.sendall(msg_bytes)
        except OSError as e:
            if e == TimeoutError:
                logger.warning("SocketDevice.write: Timeout Error")
            else:
                logger.warning("SocketDevice.write: error raised by socket write")
            logger.warning("SocketDevice.write: can't write to the socket\r\n")
            logger.warning(e.__class__)
            # logger.warning(e.__doc__)
            # raise e
        except Exception as e:   # should never happen?
            logger.error(e.__class__)
            raise e
        if len(msg_bytes) != bytes_sent:
            pass  # not sure how to handle this
        return True


    def is_ready_to_read(self):
        potential_readers = [self.sock]
        potential_writers = [self.sock]
        potential_errs = [self.sock]
        timeout = 10
        ready_to_read, ready_to_write, in_error = select.select(potential_readers,potential_writers,potential_errs,timeout)
        return bool(self.sock in ready_to_read)

    def is_ready_to_write(self):
        potential_readers = [self.sock]
        potential_writers = [self.sock]
        potential_errs = [self.sock]
        timeout = 10
        ready_to_read, ready_to_write, in_error = select.select(potential_readers,potential_writers,potential_errs,timeout)
        return bool(self.sock in ready_to_write)

    def is_in_error(self):
        potential_readers = [self.sock]
        potential_writers = [self.sock]
        potential_errs = [self.sock]
        timeout = 10
        ready_to_read, ready_to_write, in_error = select.select(potential_readers,potential_writers,potential_errs,timeout)
        return bool(self.sock in in_error)

    def read(self):
        """
        reads a response from the socket
        :rtype: string
        """
        MAX_ATTEMPTS = 10
        done = False
        self.sock.setblocking(False)
        r_bytes = ""   # not None, because we want its len to be 0. can't take the len of None
        time.sleep(read_delay)  # read can fail if no delay here, 0.2 works
        if self.is_ready_to_read():
            pass
        attempts = 0
        while not done:
            attempts += 1
            try:
                r_bytes = self.sock.recv(1024)
            except ConnectionAbortedError as e:
                logger.warning("error while trying to receive from the socket\r\n")
                logger.warning(e.__class__)
                logger.warning(e.__doc__)
                logger.warning(e.strerror)
                logger.warning(e.__cause__)
                return None
            except OSError as e:
                # if using nonblocking I/O, error 10035 happens when there's
                # no data to read yet. This would be OK, but:
                # TODO add some limit so it can't get 'stuck' here
                if e.errno == 10035:
                    logger.warning(e.__doc__)
                else:
                    logger.warning("error while trying to receive from the socket\r\n")
                    logger.warning(e.__class__)
                    logger.warning(e.__doc__)
                    logger.warning(e.strerror)
                    logger.warning(e.__cause__)
                    # raise e   # could throw something here, depending on the cause?
                    return None
            except (IOError, AttributeError) as e:
                logger.warning("error while trying to receive from the socket\r\n")
                logger.warning(e.__class__)
                logger.warning(e.__doc__)
                logger.warning(e.strerror)
                logger.warning(e.__cause__)
                return None
            if attempts > MAX_ATTEMPTS:
                return None
            if r_bytes is None:
                done = False
            else:
                done = (len(r_bytes)>0)

        r_str = str(r_bytes.decode(encoding='UTF-8'))    # cast bytes to string
        # logger.info("SocketDevice.read: got <" + r_str + ">")
        r_str = r_str.strip('\r\n')
        return r_str


    def close_port(self):
        logger.info("close_port: closing socket")
        if not hasattr(self, 'sock'):
            return
        if not hasattr(self.sock, 'close'):
            return
        try:
            self.sock.close()
        except Exception as e:
            logger.warning(e.__class__)

    # def _readline(self, terminator='\r'):
    #     """
    #     implemented this myself because comport.readline() is extremely slow
    #     TODO figure out why?
    #     """
    #     eol = b'\r'      # '\r' or b'\r' ?
    #     c = None
    #     if terminator is not None:
    #         eol = terminator  # TODO pylint doesn't like this (redefined-variable-type) but it works
    #     length_eol = len(eol)
    #     line = bytearray()
    #     # TODO: needs length limit?
    #     try:
    #         while self.comPort.inWaiting() > 0:
    #             # c = self.comPort.read(self.comPort.inWaiting())   # not sure if this is better
    #             c = self.comPort.read(1)
    #             if c:
    #                 line += c
    #                 if line[-length_eol:] == eol:
    #                     break
    #             else:
    #                 break
    #     except Exception as e:
    #         logger.error("in _readline")
    #         logger.error(e.__class__)
    #         logger.error(str(e.args[0]))
    #         raise e  # let .read() handle it
    #     return bytes(line)
    #


