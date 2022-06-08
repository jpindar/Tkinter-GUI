#! python3
# pylint: disable=protected-access,unused-argument,bad-continuation
"""
a simple Python3.4 GUI using pySerial and tkinter
Project: DEVICE GUI
File: main.py
Date: 3/2019
Author: jeannepindar@gmail.com  aka jpindar@jpindar.com
"""
# TODO add logo on help and about boxes
# TODO input power indicator?
# TODO help file (esp related to atten range, step size)

import inspect
import logging
from time import time
from typing import List, Dict, Optional, Any, Union
import json
import os
import tkinter as tk
import tkinter.messagebox as tmb
from tkinter import ttk
from tkinter import font
import sys
import cryptlib
import socketdevice
import serialdevice_pyserial
import terminalwindow
import const
import globe
import device


ENABLE_LOGGING = True
log_filename = 'Device.log'
__author__ = 'jpindar@jpindar.com'
const.PROGRAM_NAME = " Device Control "
const.VERSION = "v1.10"
const.BUILD = "1.10.0"
globe.user_interrupt = False
globe.unsaved = False
poll_timing = 1000
password_file = "settings.txt"
key1 = "123456"  # obviously this isn't secure, it's just an example
logger = logging.getLogger(__name__)
if ENABLE_LOGGING:
    logging.basicConfig(filename=log_filename, filemode='w', format='%(levelname)-8s:%(asctime)s %(name)s: %(message)s',
                        level=logging.INFO)
    # logger.setLevel(logging.CRITICAL)
    # logging.disable(logging.NOTSET)
else:
    logging.disable(999)   # disables all loggers, logger.disabled = True only disables for this file

logger.info("testing logger")


class MainWindow(tk.Frame):
    # pylint: disable=too-many-instance-attributes, too-many-ancestors
    """
    Note that all of the TopBarN frames overlay each other, and the one we
    want to be active at any time is brought to the top
    """
    # major_freq_increment = 1
    # minor_freq_increment = 0.0025  # TODO read this from channel spacing

    """  TopBar1 contains the address dropdown, a connect button, and the logo """
    class TopBar1(tk.Frame):
        def __init__(self, parent, gparent, **kw):
            super().__init__(parent, **kw)
            self.comport_str = tk.StringVar()
            self.comport_label = tk.Label(self, text="Connection", bg=kw['background'])
            self.comport_label.grid(row=0, column=0, sticky=tk.E)
            self.comport_dropdown = ttk.OptionMenu(self, self.comport_str, command=self.comport_handler)
            self.comport_dropdown.config(width=8)
            self.comport_dropdown.grid(row=0, column=1, sticky=tk.W, padx=3, ipady=1)
            self.populate_comport_menu()
            self.button_connect = tk.Button(self, text="Connect", bg='light grey',
                                            command=gparent.connect_button_handler)
            self.button_connect.grid(row=0, column=2, padx=2, pady=2, sticky=tk.E)
            self.button_connect.bind('<Return>', gparent.connect_button_handler)


        def comport_handler(self, event=None) -> None:
            try:
                s = self.comport_str.get()
                if s[:3] == 'COM':  # TODO make this cross platform
                    globe.serial_port_num = int(s[3:])
            except ValueError:  # if there is no comport number there, give up
                pass

        def populate_comport_menu(self) -> bool:
            possible_ports = serialdevice_pyserial.get_ports()
            if possible_ports[0] != '':  # TODO make this cross platform
                possible_ports = ["COM" + str(p) for p in possible_ports]
                possible_ports.append('network')
            else:
                possible_ports[0] = 'network'
            self.comport_dropdown.set_menu(possible_ports[0], *possible_ports)
            n = len(possible_ports)
            if possible_ports[0] == '':
                return False
            else:
                self.comport_handler()
                return n > 0

    class TopBar2(tk.Frame):
        def __init__(self, parent, gparent, **kw):
            super().__init__(parent, **kw)
            self.remote_address_str = tk.StringVar()
            self.address_label = tk.Label(self, text="Address", bg='#D9E5EE')
            self.address_label.grid(row=0, column=0, sticky='e')
            self.remote_address_box = tk.Entry(self, textvariable=self.remote_address_str, width=15)
            self.remote_address_box.grid(row=0, column=1, padx=5, sticky=tk.W)
            self.remote_address_str.set(globe.remote_address)
            self.remote_address_box.bind('<Return>', gparent.connect_button_handler2)
            self.button_connect = tk.Button(self, text="Connect", bg='light grey',
                                            command=gparent.connect_button_handler2)
            self.button_connect.grid(row=0, column=3, padx=2, pady=2, sticky=tk.E)
            self.button_connect.bind('<Return>', gparent.connect_button_handler2)

    class TopBar3(tk.Frame):
        def __init__(self, parent, gparent, **kw):
            super().__init__(parent, **kw)
            self.password_str = tk.StringVar()
            self.password_label = tk.Label(self, text="Password", bg='#D9E5EE')
            self.password_label.grid(row=0, column=0, sticky='e')
            self.password_box = tk.Entry(self, textvariable=self.password_str, width=15)
            self.password_box.grid(row=0, column=1, padx=5, sticky=tk.W)
            self.password_box.bind('<Return>', gparent.connect_button_handler3)
            self.button_connect = tk.Button(self, text="Connect", bg='light grey',
                                            command=gparent.connect_button_handler3)
            self.button_connect.grid(row=0, column=3, padx=2, pady=2, sticky=tk.E)
            self.button_connect.bind('<Return>', gparent.connect_button_handler3)



    """ main window constructor """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent  # main window's parent is root
        self.my_settings_window = None
        self.unsaved_text = False
        self.write_b = tk.BooleanVar()
        self.logging_b = tk.BooleanVar()
        self.fast_baud_b = tk.BooleanVar()
        self.save_password_b = tk.BooleanVar()
        # terminal_window's parent is also root
        logger.info("creating main window")
        self.terminal_window = terminalwindow.TerminalWindow(self.parent, globe.dev_null)

        self.top_frame = tk.Frame(self, relief=tk.FLAT, borderwidth=0, bg='#00FF00')
        self.top_frame.grid(row=0, column=0, sticky=tk.NS + tk.EW)

        self.mid_frame_1 = tk.Frame(self, height=2, width=3, relief=tk.FLAT, borderwidth=0)
        self.mid_frame_1.grid(row=1, column=0, padx=(5, 2), pady=2, sticky=tk.N + tk.EW)

        self.mid_frame_2 = tk.Frame(self, relief=tk.FLAT, borderwidth=0, bg='#8888FF')
        self.mid_frame_2.grid(row=2, column=0, padx=(5, 2), sticky=tk.NS + tk.EW)

        self.rowconfigure(9, weight=1)  # this row is a spacer
        tk.Frame(self, relief=tk.FLAT, borderwidth=0, bg='#FF00FF').grid(row=9, column=0)

        self.bottom_bar = tk.Frame(self, height=40, borderwidth=5, relief='ridge')
        self.bottom_bar.grid(row=10, column=0, columnspan='2', sticky=tk.N + tk.S + tk.E + tk.W)
        self.bottom_bar.columnconfigure(1, weight=1)

        self.__create_menus()
        self.__fill_top_frame()
        self.__fill_mid_frame()
        self.__fill_bottom_bar()
        self.top_bar1.tkraise()
        self.top_bar1.comport_handler()  # this updates the port number in globe, so the terminal window can use it if necessary


    def __create_menus(self):
        self.menu_bar = tk.Menu(self)  # create a horizontal menu
        self.parent.config(menu=self.menu_bar)  # and attach it to MainWindow's parent

        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label='File', menu=self.file_menu)
        self.file_menu.add_command(label='Exit', command=exit_handler)

        # TODO initial state of these?
        # overpower and write enable can be read from dut in GUI refresh
        self.option_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label='Options', menu=self.option_menu)
        self.option_menu.add_checkbutton(label="enable some feature", onvalue=1, offvalue=0,
                                         variable=self.write_b, command=self.feature_handler)
        self.option_menu.add_checkbutton(label="115200 baud", onvalue=1, offvalue=0,
                                         variable=self.fast_baud_b, command=self.fast_baud_handler)
        self.option_menu.add_checkbutton(label="save password", onvalue=1, offvalue=0,
                                         variable=self.save_password_b, command=self.save_password_handler)
        if ENABLE_LOGGING:
            self.logging_b = True
            self.option_menu.add_checkbutton(label="write log file", onvalue=1, offvalue=0, variable=self.logging_b,
                                             command=self.logging_handler)

        self.option_menu.entryconfig(0, state=tk.DISABLED)
        self.option_menu.entryconfig(1, state=tk.DISABLED)

        self.about_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label='About', menu=self.about_menu)
        self.about_menu.add_command(label='About', command=display_about_messagebox)
        self.about_menu.add_command(label='Help', command=display_help_messagebox)
        self.about_menu.add_command(label='Terminal', command=show_terminal)

    def __fill_top_frame(self):
        # three top_bars, only one will be visible at a time
        # their parent is the top_frame, their gparent is MainWindow
        self.top_bar1 = self.TopBar1(self.top_frame, gparent=self, width=290, background='#8888FF')
        self.top_bar2 = self.TopBar2(self.top_frame, gparent=self, width=290, background='#8888FF')
        self.top_bar3 = self.TopBar3(self.top_frame, gparent=self, width=290, background='#8888FF')

        self.top_bar1.configure(borderwidth=2, relief='flat')
        self.top_bar2.configure(borderwidth=2, relief='flat')
        self.top_bar3.configure(borderwidth=2, relief='flat')

        self.top_bar1.grid(row=0, column=0, ipady=5, sticky=tk.NSEW)
        self.top_bar2.grid(row=0, column=0, ipady=5, sticky=tk.NSEW)
        self.top_bar3.grid(row=0, column=0, ipady=5, sticky=tk.NSEW)

        photo = tk.PhotoImage(file=const.HEADER_IMAGE)  # 250x50 banner image
        self.image_label = tk.Label(self.top_frame, image=photo, anchor=tk.E, bg='#D9E5EE')
        self.image_label.photo = photo
        self.image_label.grid(row=0, column=4, sticky=tk.NS + tk.E)



    def __fill_mid_frame(self):
        self.A_frame = tk.Frame(self.mid_frame_2, height=5, width=3, relief=tk.GROOVE, borderwidth=4, bg="#00FFFF")
        self.A_frame.grid(row=0, column=0, rowspan=1, padx=5, pady=5, sticky=tk.N + tk.E + tk.W)
        self.spacer_label = tk.Label(self.A_frame, text="SPACER")
        self.spacer_label.grid(row=0, column=0, sticky=tk.W)

        self.B_frame = tk.Frame(self.mid_frame_2, height=1, width=3, relief=tk.GROOVE, borderwidth=4, bg="#00FFFF")
        self.B_frame.grid(row=1, column=0, rowspan=1, padx=5, pady=5, sticky=tk.N + tk.E + tk.W)
        self.spacer_label = tk.Label(self.B_frame, text="SPACER")
        self.spacer_label.grid(row=0, column=0, sticky=tk.W)

        self.C_frame = tk.Frame(self.mid_frame_2, height=1, width=3, relief=tk.GROOVE, borderwidth=4, bg="#00FFFF")
        self.C_frame.grid(row=2, column=0, rowspan=1, padx=5, pady=5, sticky=tk.N + tk.E + tk.W)
        self.spacer_label = tk.Label(self.C_frame, text="SPACER")
        self.spacer_label.grid(row=0, column=0, sticky=tk.W)

    def __fill_bottom_bar(self):
        self.status_bar1 = tk.Label(self.bottom_bar, text=' ', font=text_font)
        self.status_bar1.grid(row=0, column=0, columnspan=1, sticky=tk.N + tk.S + tk.W)
        self.status_bar2 = tk.Label(self.bottom_bar, text='  ', font=text_font)
        self.status_bar2.grid(row=0, column=1, columnspan=1, sticky=tk.N + tk.S + tk.W + tk.E)
        self.status_bar3 = tk.Label(self.bottom_bar, text='  ', font=default_font, fg="red")
        self.status_bar3.grid(row=0, column=2, columnspan=1, sticky=tk.N + tk.S + tk.E)
        self.status_bar1.config(text=".")

    def status1(self, msg, **kwargs):
        self.status_bar1.config(text=msg, **kwargs)
        self.update()

    def enable_widgets(self, on_off):
        if on_off:
            new_state = tk.NORMAL
        else:
            new_state = tk.DISABLED
        self.option_menu.entryconfig(0, state=new_state)
        self.option_menu.entryconfig(1, state=new_state)
        self.option_menu.entryconfig(2, state=tk.NORMAL)  # always enabled

    # These functions have an optional 'event' parameter because button binding passes an
    # event object to the callback function, but the menu doesn't.
    # So you need it if the function is invoked by a button press, but not if it is from
    # a menu. It's easiest just to put the optional parameter on all of them.

    def logging_handler(self, event=None) -> None:
        b = self.logging_b.get()
        if b:
            logging.disable(logging.NOTSET)  # enables logging
        else:
            logging.disable(999)  # disables logging


    def feature_handler(self, event=None) -> None:
        """
        whatever feature you want to toggle
        """
        if globe.dut is None:  # never happens
            return
        try:
            s = self.write_b.get()
        except ValueError as e:
            logger.warning(e.__class__)
            logger.warning("value error in feature_handler")
            return
        if s:
            b = 1
        else:
            b = 0
        logger.info("setting the feature to " + str(b))
        try:
            pass   # commented out because the device doesn't have these commands at this time
            # globe.dut.set_feature_mode(b)
            # r = globe.dut.get_feature_mode()
        except device.DeviceResponseError as e:
            self.status1("Bad or no response from device", bg='red')
            return
        except device.DeviceLoggedOutError as e:
            self.status1("Not Connected to Device", bg='red')
            return
        # self.write_b.set(r)

    def save_password_handler(self, event=None) -> None:
        try:
            s = self.save_password_b.get()
        except ValueError as e:
            logger.warning(e.__class__)
            logger.warning("value error in save_password_handler")
            return
        logger.info("setting the save_password to " + str(s))
        self.save_password_b.set(s)
        if s:  # you just checked the box
            save_password_to_file()

        if not s:   # when you just unchecked the box
            # not sure if clearing these is the expected behavior
            # self.top_bar3.password_str.set("")
            # self.top_bar2.remote_address_str.set("")
            delete_password_file()


    def fast_baud_handler(self, event=None) -> None:
        """
        this is awkward
        """
        try:
            s = self.fast_baud_b.get()
        except ValueError as e:
            logger.warning(e.__class__)
            logger.warning("value error in fast_baud_handler")
            return
        # seems odd to define baud rates here...
        # TODO move these to dut
        if s:
            b = 1
            serialdevice_pyserial.baud_rate = 115200
        else:
            b = 0
            serialdevice_pyserial.baud_rate = 19200
        logger.info("setting the fast_baud to " + str(b))
        try:
            if globe.dut is not None:
                globe.dut.set_baud(b)
        except device.DeviceResponseError as e:
            self.status1("Bad or no response from device", bg='red')
            return
        except Exception as e:
            logger.info(e.__class__)
        # except device.DeviceLoggedOutError as e:
        #    self.status1("Not Connected to Device", bg = 'SystemButtonFace')
        #    return
        # self.fast_baud_b.set(b)




    def connect_button_handler(self, event=None) -> None:
        success = None
        self.status1(" ", bg='SystemButtonFace')
        self.enable_widgets(False)
        if globe.dut is not None:
            globe.close_dut()  # this sets globe.dut to None
        if self.top_bar1.comport_str.get() == 'network':
            self.top_bar2.tkraise()
            self.top_bar2.remote_address_box.focus_set()
            return   # go wait for user to enter url and click again
        else:
            if self.top_bar1.comport_str.get() == '':
                if not self.top_bar1.populate_comport_menu():
                    self.status1("Cannot find any com ports. Connect device and try again.", bg='red')
                else:
                    self.status1("", bg='SystemButtonFace')
                return
            try:
                s = self.top_bar1.comport_str.get()
                self.status1("connecting...", bg='SystemButtonFace')
                # success = globe.open_dut([s], self.terminal_window.textbox, globe.DUTKind.serial)
                success = globe.open_dut([s], self.terminal_window.textbox, globe.DUTKind.mock)
            except Exception as e:
                logger.error(e.__class__)
                logger.error("Can't open a serial port\n")
                self.terminal_window.textbox.append("Couldn't open the serial port\n")
                self.status1("Cannot connect to a device on that port", bg='red')
                return
        # would dut be None if it had been disconnected? No.
        if globe.dut is None:
            self.status1("Cannot connect to device on that port", bg='red')
            return
        if not success:
            self.status1("Cannot connect to device on that port", bg='red')
            return
        self.refresh_gui()
        self.status1("Connected", bg='SystemButtonFace')  # self.status_bar1.config(text = "Connected to " + s)
        # self.poll_for_overpower_bypass()
        # self.listen_for_overpower_bypass()


    def connect_button_handler2(self, event=None) -> None:
        self.enable_widgets(False)  # not sure if this is needed here or in connect_button_handler3
        globe.remote_address = self.top_bar2.remote_address_str.get()
        success = None
        globe.connection = [globe.remote_address, globe.remote_port]
        socketdevice.parse_url(globe.connection)  # parse it here because we want it to display nicely
        self.status1("Connecting to device at " + globe.connection[0] + ':' + globe.connection[1], bg='SystemButtonFace')

        try:
            success = globe.open_dut(globe.connection, app.terminal_window.textbox, kind=globe.DUTKind.network)
        except Exception as e:
            logger.error(e.__class__)
            logger.error("Can't open a socket\n")
            app.terminal_window.textbox.append("Couldn't open the socket\n")
            self.status1("Cannot connect to device at " + globe.connection[0] + ':' + globe.connection[1], bg='red')
            success = False

        if not success:
            self.status1("Cannot connect to device at " + globe.connection[0] + ':' + globe.connection[1], bg='red')
            return   # give up
        else:
            self.top_bar3.tkraise()
            self.top_bar3.password_box.focus_set()
            return   # go wait for user to enter password and click again


    def connect_button_handler3(self, event=None) -> None:
        if globe.dut is None:  # never happens
            return
        self.enable_widgets(False)  # not sure if this is needed here or in connect_button_handler2
        success = None
        globe.password = self.top_bar3.password_str.get()
        try:
            success = globe.dut.login()  # even for a unit that doesn't need it, this tests the ID
        except Exception as e:  # DeviceError
            logger.error(e.__class__)
            logger.error("Can't log in\n")
            app.terminal_window.textbox.append("Couldn't log in\n")
            self.status1("Cannot connect to a device", bg='red')
            if not self.save_password_b.get():
                self.top_bar3.password_str.set("")
            self.top_bar1.tkraise()
            return
        finally:
            # not sure if this is desired behavior
            # if not self.save_password_b.get():
            #    self.top_bar3.password_str.set("")
            self.top_bar2.tkraise()  # this may not actually happen til we get back to the mainloop

        if globe.dut is None:
            self.status1("Cannot connect to device at " + globe.connection[0] + ':' + globe.connection[1], bg='red')
            return
        if not success:
            self.status1("Cannot connect to device at that address", bg='red')
            return
        if self.save_password_b.get():
            save_password_to_file()
        self.refresh_gui()
        self.status1("Connected to device at " + globe.connection[0] + ':' + globe.connection[1], bg='SystemButtonFace')
        # TODO put IP address in title bar?
        # self.poll_for_overpower_bypass()
        # self.listen_for_overpower_bypass()


    def refresh_gui(self) -> None:
        if globe.dut is None:  # never happens
            return
        try:
            pass
            # self.write_b.set(globe.dut.get_feature_mode())
        except device.DeviceResponseError as e:
            logger.error(e.__class__)
            self.status1("Bad or no response from device", bg='red')
            return
        except device.DeviceLoggedOutError as e:
            logger.error(e.__class__)
            self.status1("Not Connected to Device", bg='red')
            return
        except device.DeviceTimeoutError as e:
            logger.error(e.__class__)
            self.status1("No response from device", bg='red')
            return
        self.enable_widgets(True)


def encode(data, key):
    if data == '':
        data = ' '
    try:
        s: str = cryptlib.encrypt(data, key)
        return s
    except Exception as e:
        return ''


def decode(enc, key):
    try:
        s = cryptlib.decrypt(enc, key)
        if s == ' ':
            s = ''
        return s
    except UnicodeDecodeError as e:
        return ""
    except Exception as e:
        return ""


def save_password_to_file():
    # should this save the password from app.top_bar3.password_str.get()
    # or from globe.password?
    # it depends on what the desired behavior is
    a = app.top_bar2.remote_address_str.get()
    p = app.top_bar3.password_str.get()
    data = {"1": encode(a, key1),
            "2": encode(p, key1)
            }
    try:
        fname = user_path(password_file)
        # open() will not create directories, so create them if they don't exist
        os.makedirs(os.path.dirname(fname), exist_ok=True)
        with open(fname, 'w') as the_file:
            json.dump(data, the_file, indent=4, sort_keys=True)
            the_file.close()
    except (OSError, IOError) as e:
        logmsg = "Error while trying to save a file "
        logger.warning(logmsg)
        logger.warning(e.__class__)
        # tmb.showerror(title="File Error", message="Error while saving settings."+fname, icon='error')


def read_password_from_file():
    # If there isn't a file, that's OK
    # if there is, put addr in self.top_bar2.remote_address_str
    # and pwd in self.top_bar3.password_str
    # if the file exists, set "save password" to true
    # if not, set it to false
    try:
        fname = user_path(password_file)
        logger.info("filename to load is " + fname)
        if not os.path.isfile(fname):
            return
    except (OSError, IOError) as e:
        logmsg = "Error while trying to read a file "
        logger.warning(logmsg)
        logger.warning(e.__class__)
        app.save_password_b.set(False)
        return

    try:
        with open(fname) as f:
            data = json.load(f)
        a = decode(data['1'], key1)
        p = decode(data['2'], key1)
        app.save_password_b.set(True)
        app.top_bar2.remote_address_str.set(a)
        app.top_bar3.password_str.set(p)
    except (OSError, IOError, ValueError, KeyError) as e:
        logmsg = "Error while trying to read a file "
        logger.warning(logmsg)
        logger.warning(e.__class__)
        app.save_password_b.set(False)
        return
    except Exception as e:
        logmsg = "Error while trying to read a file "
        logger.warning(logmsg)
        logger.warning(e.__class__)
        app.save_password_b.set(False)
        return
    # logger.info(str(data))


def delete_password_file():
    try:
        fname = user_path(password_file)
        os.remove(fname)
    except (OSError, IOError) as e:
        logmsg = "Error while trying to delete a file "
        logger.warning(logmsg)
        logger.warning(e.__class__)


def show_terminal():
    app.terminal_window.textbox.clear()
    app.terminal_window.deiconify()


def user_interrupt_handler(event=None):
    globe.user_interrupt = True
    # 'break' tells Tkinter to ignore the event that triggers this callback
    return 'break'


def display_about_messagebox(event=None):
    about_string = const.PROGRAM_NAME + " " + const.VERSION + "\n"
    about_string += "Acme Inc.\n" + " jpindar.com \n\n"
    about_string += __author__ + "\n"
    tmb.showinfo("About " + const.PROGRAM_NAME, about_string, icon=tmb.INFO)
    return 'break'


def display_help_messagebox(event=None):
    help_string = "Contact Acme Inc. at jpindar.com for help\n\n"
    help_string += "USB drivers are available at \n"
    help_string += "http://www.ftdichip.com/Drivers/VCP.htm\n\n"
    help_string += "This program operates at 19200 baud except when the 115200 baud option is selected.\n\n"
    # help_string += user_path(password_file)
    tmb.showinfo("Help", help_string, icon=tmb.INFO)
    return 'break'


def exit_handler(event=None):
    logger.info('QUITTING')
    if globe.dut is not None:
        globe.close_dut()
    logger.info('calling root.destroy and os.exit()')
    root.destroy()
    # not sure if os._exit is the best practice here, but it works OK
    # sys.exit()  #this doesn't work - the test loop keeps going until it crashes due to the textbox being gone.
    # raise SystemExit doesn't always work
    # noinspection PyProtectedMember
    os._exit(0)


def resource_path(relative_path):
    """ This is for getting resources that were packaged with the code.
        Get absolute path to resource, works for dev and for PyInstaller
        PyInstaller creates a temp folder and stores path in _MEIPASS
        if sys doesn't have _MEIPASS, default to the path to __file__  (i.e. this file)
    """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def user_path(relative_path):
    """ This is for getting and saving stuff like config files
        that need to change at runtime and persist to the next run
        Unfortunately, many of the ways of getting a user's directory
        are unreliable, and many explicit paths don't work (due to permissions?)
    """
    # my_home = os.getenv("HOME") # doesn't always work - some systems have no HOME env variable or a bad one
    # my_home = expanduser("~") # works in IDE, works on XOTIC, but points to SPB_Data .exe on VAIO
    # my_home = os.getenv('USERPROFILE') # this works! (so far...)
    my_home = os.path.expanduser(os.getenv('USERPROFILE'))  # this works! (so far...)
    p = os.path.join(my_home, "device", relative_path)
    # p = 'C:\\foo.txt'  nope
    # p = 'C:\\Users\\jpindar\\device\\_SOFTWARE\\settings.txt' Yep
    # p = 'C:\\Users\\jpindar\\baz\\settings.txt' only if baz already exists
    return p


def set_root_size():
    """
    set the dimensions of the window and where it is placed
    must be done after creating the MainWindow
    """
    root_width = 550
    root_height = 450
    root_x = (root.winfo_screenwidth() / 2) - (root_width / 2)
    root_y = (root.winfo_screenheight() / 2) - (root_height / 2)
    root.geometry('%dx%d+%d+%d' % (root_width, root_height, root_x, root_y))
    root.resizable(width=False, height=False)


# do these before the GUI starts!
const.ICON_FILE = resource_path('company_logo.ico')
const.HEADER_IMAGE = resource_path('banner250x50.png')

root = tk.Tk()
style = ttk.Style()
style.theme_use('alt')
# use .option_add if you want to change the font,
# root.option_add("*Font", "courier 9 bold")
default_font = tk.font.nametofont("TkDefaultFont")
default_font.configure(size=9, weight="bold")
text_font = tk.font.nametofont("TkTextFont")

bold_style = ttk.Style()
bold_style.configure("bold.TButton", font='bold')
#  or bold_style.configure("bold.TButton", font = ('Sans','10','bold'))

app = MainWindow(root)
app.pack(fill='both', expand=1)
set_root_size()
root.title(const.PROGRAM_NAME + " " + str(const.VERSION))
root.iconbitmap(const.ICON_FILE)
root.bind_all('<Escape>', user_interrupt_handler)
root.bind('<KeyPress-F1>', display_help_messagebox)
root.protocol('WM_DELETE_WINDOW', exit_handler)  # override the Windows "X" button
# app.comport_handler()  # this updates the port number in globe, so the terminal window can use it if necessary
read_password_from_file()
app.enable_widgets(False)
root.mainloop()


