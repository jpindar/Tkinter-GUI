# pylint: disable=unused-argument
"""
File: socketdevice.py
 TODO pop up or other obvious error handling when exception occurs?
"""
import ipaddress
import logging

import time
import select
import socket

__author__ = 'jpindar@jpindar.com'

read_delay = 0.2
logger = logging.getLogger(__name__)


def parse_url(c):
    # The url shouldn't be http, but some people copy & paste this by accident
    assert isinstance(c, list)
    assert isinstance(c[0], str)
    s = c[0]
    assert isinstance(s, str)
    pos = s.find("https:\\")
    if pos >= 0:
        s = s[8:]  # skip https:\\
    pos = s.find("http:\\")
    if pos >= 0:
        s = s[7:]  # skip http:\\
    pos = s.find(":")  # the colon between ip address and port
    if pos >= 0:  # the order of these lines matters
        c[1] = s[pos + 1:]
        c[0] = s[:pos]
    else:
        c[0] = s
        # c[1] is already the default port
    return


"""
    socket.getaddrinfo(host, port, family=0, type=0, proto=0, flags=0)
    Translate the host/port argument into a sequence of 5-tuples that contain
    all the necessary arguments for creating a socket connected to that service.
    host is a domain name, a string representation of an IPv4/v6 address or None.
    port is a string service name such as 'http', a numeric port number or None.
"""


def validate_url(connection):
    # ipaddress.ip_address() fixes leading zeros
    # and throws reasonable exceptions for malformed addresses
    z = ipaddress.ip_address(connection[0])
    connection[0] = z.exploded  # are these the same?
    connection[0] = str(z)
    whole_list = socket.getaddrinfo(connection[0], int(connection[1]))
    ipv4_list = whole_list[0]
    sock_addr = ipv4_list[4]
    return sock_addr


class SocketDevice:
    """
    A TCP port, created by socket
    """

    def __init__(self):
        """
        constructor for serial device, no parameters
        create an instance variable but don't open the port
        """
        logger.info(" ")
        logger.info("SocketDevice constructor")
        self.comPort = None
        self.port_num = None
        self.sock = None

    def open_port(self, connection):
        """
        opens the port with fixed parameters in connection_info
        remote_host is an IP address in string form
        remote_port is an integer
        these are separated by a colon

         TODO  set timeout, default is too long?, ideally make this configurable
        """
        self.close_port()
        parse_url(connection)
        try:
            connection = validate_url(connection)
        except (OSError, ipaddress.AddressValueError, ipaddress.NetmaskValueError) as e:
            # Typical error is:
            # 11004 socket.gaierror   can be caused by malformed URL  "getaddrinfo failed"
            # or?
            #
            logger.warning("bad address\r\n")
            logger.warning(e.__class__)  # socket.gaierror
            logger.warning("error " + str(e.errno) + " " + e.__doc__)
            logger.warning(e.strerror)
            raise e
        except (ValueError, TypeError) as e:
            #
            #
            logger.warning("bad URL or IP address\r\n")
            logger.warning(e.__class__)  # socket.gaierror
            logger.warning(e.args[0])
            logger.warning(e.__doc__)

        logger.info("opening TCP socket " + str(connection[0]) + ":" + str(connection[1]))
        # dt = socket.getdefaulttimeout()
        # logger.info("socket default timeout setting is " + str(dt))
        # socket.setdefaulttimeout()
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # logger.info("socket timeout setting is " + str(self.sock.gettimeout()))
            # these apparently redundant parenthesis are not redundant
            self.sock.connect((connection[0], int(connection[1])))
        except OSError as e:
            # Typical error is:
            # [WinError 10060] TimeoutError A connection attempt failed because the connected party did not
            # properly respond after a period of time,
            #  or established connection failed because connected host has failed to respond
            #  This happens with a valid but non=existent url
            #
            logger.warning("connection attempt failed\r\n")
            logger.warning(e.__class__)  # TimeoutError  or #ConnectionRefusedError
            logger.warning("error " + str(e.errno) + " " + e.__doc__)
            logger.warning(e.strerror)
            raise e
        except [ValueError] as e:
            # I'd like to catch TypeError, but not allowed to catch classes that don't inherit from BaseException
            logger.warning("SocketDevice.openPort: invalid setting\r\n")
            logger.warning(e.__class__)
            # logger.warn(e.__doc__)
            # raise e
            return False
        except Exception as e:  # don't know what other exceptions sock.connect can raise
            logger.warning("SocketDevice.openPort: Can't open that socket\r\n")
            logger.warning(e.__class__)
            # logger.warn(e.__doc__)
            # raise e
            return False
        else:
            # assert isinstance(self.comPort, pyvisa.resources.serial.SerialInstrument)
            # not necessary if constructor worked, but assertions are good.
            logger.info("SocketDevice.openPort: opened a " + str(self.sock.__class__))
            return True

    def is_open(self):
        """
        This is really just checking if open_port() succeeded
        """
        if not hasattr(self, "sock"):
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
        # TODO: pop up or other obvious error handling when exception occurs?
        """
        response = None
        bytes_sent = 0
        if not hasattr(self, "sock"):
            logger.warning("can't write to non-existent socket")
            return response
        # msg = msg + "\n"
        # logger.info("SocketDevice.write: writing " + str(msg) + " to socket")
        msg_bytes = msg.encode(encoding="UTF-8")
        # if self.is_ready_to_write():
        #     pass
        try:
            bytes_sent = self.sock.send(msg_bytes)
            # success = self.sock.sendall(msg_bytes)
        except OSError as e:
            # TimeoutError, ConnectionAbortedError
            logger.warning("SocketDevice.write: error raised by socket write")
            logger.warning(e.__class__)
            logger.warning(e.__doc__)
            raise e  # TODO test this path
        except Exception as e:  # should never happen?
            logger.error(e.__class__)
            raise e
        if len(msg_bytes) != bytes_sent:
            pass  # not sure how to handle this
        return True

    """
    select.Select
    The first three arguments are sequences of 'waitable objects': either integers representing file descriptors
    or objects with a parameterless method named fileno() returning such an integer:
    rlist: wait until ready for reading
    wlist: wait until ready for writing
    xlist: wait for an 'exceptional condition' (see the manual page for what your system considers such a condition)
    Empty sequences are allowed, but acceptance of three empty sequences is platform-dependent.
    The optional timeout argument specifies a time-out as a floating point number in seconds. When the timeout argument
    is omitted the function blocks until at least one file descriptor is ready. A time-out value of zero specifies a
    poll and never blocks.
    The return value is a triple of lists of objects that are ready: subsets of the first three arguments. When the
    time-out is reached without a file descriptor becoming ready, three empty lists are returned.
    """

    def is_ready_to_read(self):
        # pylint: disable=unused-variable
        timeout = 10
        ready_to_read, ready_to_write, in_error = select.select([self.sock], [self.sock], [self.sock], timeout)
        return bool(self.sock in ready_to_read)

    def is_ready_to_write(self):
        # pylint: disable=unused-variable
        timeout = 10
        ready_to_read, ready_to_write, in_error = select.select([self.sock], [self.sock], [self.sock], timeout)
        return bool(self.sock in ready_to_write)

    def is_in_error(self):
        # pylint: disable=unused-variable
        timeout = 10
        ready_to_read, ready_to_write, in_error = select.select([self.sock], [self.sock], [self.sock], timeout)
        return bool(self.sock in in_error)

    def read(self):
        """
        reads a response from the socket
        """
        MAX_ATTEMPTS = 10
        done = False
        self.sock.setblocking(False)
        r_bytes = ""  # not None, because we want its len to be 0. can't take the len of None
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
            except (IOError, OSError) as e:
                # if using nonblocking I/O, error 10035 happens when there's
                # no data to read yet. This would be OK, but:
                # TODO add some limit so it can't get 'stuck' here
                if e.errno == 10035:
                    logger.warning(e.__doc__)
                else:
                    # typically [WinError 10054] An existing connection was forcibly closed by the remote host
                    logger.warning("error while trying to receive from the socket\r\n")
                    logger.warning(e.__class__)
                    logger.warning(e.__doc__)
                    logger.warning(e.strerror)
                    logger.warning(e.__cause__)
                    # raise e
                    return None
            except AttributeError as e:
                #
                logger.warning("error while trying to receive from the socket\r\n")
                logger.warning(e.__class__)
                logger.warning(e.__doc__)
                # logger.warning(e.strerror) AttributeError doesn't have a strerror
                logger.warning(e.__cause__)
                return None
            if attempts > MAX_ATTEMPTS:
                return None
            if r_bytes is None:
                done = False
            else:
                done = len(r_bytes) > 0

        r_str = str(r_bytes.decode(encoding="UTF-8"))  # cast bytes to string
        # logger.info("SocketDevice.read: got <" + r_str + ">")
        r_str = r_str.strip("\r\n")
        return r_str

    def close_port(self):
        # logger.info("close_port: closing socket")
        if not hasattr(self, "sock"):
            return
        if not hasattr(self.sock, "close"):
            return
        try:
            self.sock.close()
        except Exception as e:  # we don't know what exceptions sock.close can raise
            logger.warning(e.__class__)

    # def _readline(self, terminator='\r'):
    #     """
    #     implemented this myself because comport.readline() is extremely slow
    #     """
    #     eol = b'\r'      # '\r' or b'\r' ?
    #     c = None
    #     length_terminator = len(terminator)
    #     line = bytearray()
    #     try:
    #         while self.comPort.inWaiting() > 0:
    #             # c = self.comPort.read(self.comPort.inWaiting())   # not sure if this is better
    #             c = self.comPort.read(1)
    #             if c:
    #                 line += c
    #                 if line[-length_terminator:] == eol:
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
