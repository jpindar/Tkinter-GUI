#! python3
# pylint: disable=wrong-import-position, protected-access,unused-argument,line-too-long
"""
a simple Python3.4 GUI using pySerial and tkinter
Project: BBUQ GUI
File: main.py
Date: 10/2017
Author: jeannepindar@gmail.com  aka jpindar@jpindar.com


"""
# TODO add logo on help and about boxes
# TODO input power indicator?
# TODO help file (esp related to atten range, step size)
# pylint: disable=wrong-import-position
import inspect
import logging

ENABLE_LOGGING = False

log_filename = 'Ultra-Q.log'
logger = logging.getLogger(__name__)
if ENABLE_LOGGING:
    if __name__ == "__main__":
        logging.basicConfig(filename=log_filename, filemode='w', format='%(levelname)-8s:%(asctime)s %(name)s: %(message)s',
                            level=logging.INFO)
    # logger.setLevel(logging.CRITICAL)
else:
    logging.disable(999)   # disables all loggers, logger.disabled = True only disables for this file
logger.info("testing logger")
import time
import os
import tkinter as tk
import tkinter.messagebox as tmb
from tkinter import ttk
from tkinter import font
import sys
import serialdevice_pyserial
import terminalwindow
import const
import globe
import bbuq

__author__ = 'jpindar@jpindar.com'
const.PROGRAM_NAME = " Ultra-Q "
const.VERSION = "v1.05"
const.BUILD = "1.05.0"
globe.user_interrupt = False
globe.unsaved = False
poll_timing = 1000


class MainWindow(tk.Frame):
    """
    """
    major_freq_increment = 1
    minor_freq_increment = 0.0025


    class TopBar1(tk.Frame):
        def __init__(self, parent, gparent,**kw):
            super().__init__(parent, **kw)
            self.comport_str = tk.StringVar()
            self.comport_label = tk.Label(self, text="Connection",bg='#D9E5EE')
            self.comport_label.grid(row=0, column=0, sticky=tk.E)
            self.comport_dropdown = ttk.OptionMenu(self, self.comport_str, command = self.comport_handler)
            self.comport_dropdown.config(width=8)
            self.comport_dropdown.grid(row=0, column=1, sticky=tk.W, padx=3, ipady=1)
            self.populate_comport_menu()
            self.button_connect = tk.Button(self, text="Connect", bg='light grey',
                                           command=gparent.connect_button_handler)
            self.button_connect.grid(row=0, column=2, padx=2, pady=2, sticky=tk.E)
            self.button_connect.bind('<Return>', gparent.connect_button_handler)


        def comport_handler(self, event = None):
            try:
                s = self.comport_str.get()
                if s[:3] == 'COM':
                    globe.serial_port_num = int(s[3:])
            except ValueError: # if there is no comport number there, give up
                pass

        def populate_comport_menu(self):
            possible_ports = serialdevice_pyserial.get_ports()
            if possible_ports[0] != '':
                possible_ports = ["COM" + str(p) for p in possible_ports]
                possible_ports.append('network')
            else:
                possible_ports[0]='network'
            self.comport_dropdown.set_menu(possible_ports[0], *possible_ports)
            n = len(possible_ports)
            if possible_ports[0] =='':
                return False
            else:
                self.comport_handler()
                return n > 0

    class TopBar2(tk.Frame):
        def __init__(self, parent, gparent, **kw):
            super().__init__(parent, **kw)
            self.remote_address_str = tk.StringVar()
            self.address_label = tk.Label(self, text="Address",bg='#D9E5EE')
            self.address_label.grid(row=0, column=0, sticky='e')
            self.remote_address_box = tk.Entry(self, textvariable=self.remote_address_str,width=15)
            self.remote_address_box.grid(row=0, column=1, padx=5,sticky=tk.W)
            # self.remote_address_box.bind('<Return>', self.remote_address_box_handler)
            # self.remote_address_box.config(state=tk.DISABLED)
            self.remote_port_str = tk.StringVar()
            self.port_label = tk.Label(self, text="Port",bg='#D9E5EE')
            self.port_label.grid(row=1, column=0, sticky='e')
            self.remote_port_box = tk.Entry(self, textvariable=self.remote_port_str,width=5)
            self.remote_port_box.grid(row=1, column=1, padx=5,sticky=tk.W)
            # self.remote_port_box..bind('<Return>', gparent.connect_button_handler)

            self.remote_address_str.set(globe.remote_address)
            self.remote_port_str.set(globe.remote_port)
            self.button_connect = tk.Button(self, text="Connect", bg='light grey',
                                            command=gparent.connect_button_handler)
            self.button_connect.grid(row=0, column=3, padx=2, pady=2, sticky=tk.E)
            self.button_connect.bind('<Return>', gparent.connect_button_handler)

    class TopBar3(tk.Frame):
        def __init__(self, parent, gparent, **kw):
            super().__init__(parent, **kw)


            self.password_str = tk.StringVar()
            self.password_label = tk.Label(self, text="Password",bg='#D9E5EE')
            self.password_label.grid(row=0, column=0, sticky='e')
            self.password_box = tk.Entry(self, textvariable=self.password_str,width=15)
            self.password_box.grid(row=0, column=1, padx=5,sticky=tk.W)
            self.password_box.bind('<Return>', gparent.connect_button_handler2)
            self.button_connect = tk.Button(self, text="Connect", bg='light grey',
                                            command=gparent.connect_button_handler2)
            self.button_connect.grid(row=0, column=3, padx=2, pady=2, sticky=tk.E)
            self.button_connect.bind('<Return>', gparent.connect_button_handler2)


    class TopBar0(tk.Frame):
        def __init__(self, parent, **kw):
            super().__init__(parent, **kw)
            self.config(bg = '#D9E5EE')
            self.rowconfigure(99, weight = 1)
            self.rowconfigure(0,minsize = 70)
            self.columnconfigure(0,minsize = 290)
            self.label1 = tk.Label(self, text = ' ', bg = '#D9E5EE' )
            self.label1.grid(row=0, column=0, sticky=tk.NS + tk.EW)


    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.my_settings_window = None
        self.unsaved_text = False
        self.overpower_bypass_b = tk.BooleanVar()
        self.write_b = tk.BooleanVar()
        self.logging_b = tk.BooleanVar()
        self.serial_port_b = tk.BooleanVar()
        self.network_port_b = tk.BooleanVar()

        logger.info("creating main window")
        self.terminal_window = terminalwindow.TerminalWindow(self.parent, globe.dev_null)

        self.top_frame = tk.Frame(self,  relief=tk.FLAT,borderwidth=0, bg = '#D9E5EE')
        self.top_frame.grid(row=0, column=0, sticky=tk.NS + tk.EW)

        self.freq_frame = tk.Frame(self, height=2, width=3,relief=tk.GROOVE,borderwidth=4)
        self.freq_frame.grid(row=1, column=0, padx=(5,2), pady=5, sticky=tk.N + tk.EW)

        self.mid_frame = tk.Frame(self,relief=tk.FLAT,borderwidth=0)
        self.mid_frame.grid(row=2, column=0, sticky=tk.NS + tk.EW)

        self.rowconfigure(9,weight=1)  # this row is a spacer
        tk.Frame(self,relief=tk.FLAT,borderwidth=0).grid(row=9,column=0)

        self.bottom_bar = tk.Frame(self, height=40, borderwidth=5, relief='ridge')
        self.bottom_bar.grid(row=10, column=0, columnspan='2', sticky=tk.N + tk.S + tk.E + tk.W)
        self.bottom_bar.columnconfigure(1, weight=1)

        self.__create_menus()
        self.__fill_top_frame()
        self.__fill_freq_frame()
        self.__fill_mid_frame()
        self.__fill_bottom_bar()
        self.top_bar0.tkraise()
        self.top_bar1.comport_handler()  # this updates the port number in globe, so the terminal window can use it if necessary


    def __create_menus(self):
        self.menu_bar = tk.Menu(self)
        self.parent.config(menu=self.menu_bar)

        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label='File', menu=file_menu)
        file_menu.add_command(label='Exit', command=exit_handler)

        self.connect_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label='Connection', menu=self.connect_menu)
        self.connect_menu.add_checkbutton(label="Serial Port", onvalue=1, offvalue=0,
                         variable=self.serial_port_b, command=self.port_selection_handler1)
        self.connect_menu.add_checkbutton(label="Network Address", onvalue=1, offvalue=0,
                         variable=self.network_port_b, command=self.port_selection_handler2)

        self.option_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label='Options', menu=self.option_menu)
        self.option_menu.add_checkbutton(label="Over power protection", onvalue=1, offvalue=0,
                        variable=self.overpower_bypass_b, command=self.overpower_handler)
        self.option_menu.add_checkbutton(label="EEPROM write enable", onvalue=1, offvalue=0,
                        variable=self.write_b, command=self.write_handler)
        if ENABLE_LOGGING:
            self.option_menu.add_checkbutton(label="log file", onvalue=1, offvalue=0, variable=self.logging_b, command=self.logging_handler)

        self.option_menu.entryconfig(0, state=tk.DISABLED)
        self.option_menu.entryconfig(1, state=tk.DISABLED)

        about_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label='About', menu=about_menu)
        about_menu.add_command(label='About', command=display_about_messagebox)
        about_menu.add_command(label='Help', command=display_help_messagebox)
        about_menu.add_command(label='Terminal', command=show_terminal)

    def __fill_top_frame(self):
        self.top_bar0 = self.TopBar0(self.top_frame, width =290, background='#D9E5EE')
        self.top_bar0.configure(borderwidth=2, relief='flat')
        self.top_bar0.grid(row=0, column=0, ipady=5 ,sticky=tk.NS + tk.W)

        self.top_bar1 = self.TopBar1(self.top_frame, gparent=self, background='#D9E5EE')
        self.top_bar1.configure(borderwidth=2, relief='flat')
        self.top_bar1.grid(row=0, column=0, ipady=5, sticky=tk.NSEW)

        self.top_bar2 = self.TopBar2(self.top_frame, gparent=self, background='#D9E5EE')
        self.top_bar2.configure(borderwidth=2, relief='flat')
        self.top_bar2.grid(row=0, column=0, ipady =5, sticky=tk.NSEW)

        self.top_bar3=self.TopBar3(self.top_frame, gparent=self, background='#D9E5EE')
        self.top_bar3.configure(borderwidth=2, relief='flat')
        self.top_bar3.grid(row=0, column=0, ipady=5, sticky=tk.NSEW)

        photo = tk.PhotoImage(file=const.HEADER_IMAGE)
        self.image_label = tk.Label(self.top_frame, image=photo, anchor=tk.E, bg = '#D9E5EE')
        self.image_label.photo = photo
        self.image_label.grid(row=0, column=4,sticky=tk.NS + tk.E)

    def __fill_freq_frame(self):
        self.freq_subframe1 = tk.Frame(self.freq_frame,height=1, width = 4)
        self.freq_subframe1.grid(row=0, column=0)
        self.freq_subframe2 = tk.Frame(self.freq_frame,height=1, width = 4)
        self.freq_subframe2.grid(row=1, column=0)

        self.start_label = tk.Label(self.freq_subframe1, text="     ", width=16, anchor=tk.W)
        self.start_label.grid(row=0, column=0, padx=5, sticky=tk.W)
        tk.Label(self.freq_subframe1, text="", width=1).grid(row=0, column=1, sticky=tk.EW)
        tk.Label(self.freq_subframe1, text="", width=15).grid(row=0, column=2, sticky=tk.EW)
        self.freq_label1 = tk.Label(self.freq_subframe1, text=" FREQUENCY IN MHZ", width=20, state = tk.DISABLED)
        self.freq_label1.grid(row=0, column=2, sticky=tk.EW)
        tk.Label(self.freq_subframe1, text="", width=1).grid(row=0, column=3, sticky=tk.EW)
        self.stop_label = tk.Label(self.freq_subframe1, text="     ", width=16,  anchor=tk.E)
        self.stop_label.grid(row=0, column=4, padx=5, sticky=tk.E)

        self._freq_s = tk.StringVar()
        self.leftButton = tk.Button(self.freq_subframe2, text='<<', command=lambda: self.freq_button_handler(-1 * self.major_freq_increment))
        self.leftButton.grid(row=1, column=1,  padx=1, pady=3, sticky='e')
        self.leftButton2 = tk.Button(self.freq_subframe2, text='<', command=lambda: self.freq_button_handler(-1 * self.minor_freq_increment))
        self.leftButton2.grid(row=1, column=2,  padx=1, pady=3, sticky='e')
        self.freq_box = tk.Entry(self.freq_subframe2,textvariable=self._freq_s, width=10,font="-weight bold")
        self.freq_box.grid(row=1, column=3, padx = 5)
        self.freq_box.bind('<Return>', self.freq_box_handler)
        self.freq_box.config(state=tk.DISABLED)
        self.rightButton = tk.Button(self.freq_subframe2, text='>', command=lambda: self.freq_button_handler(self.minor_freq_increment))
        self.rightButton.grid(row=1, column=4, padx=1, pady=3, sticky='w')
        self.rightButton2 = tk.Button(self.freq_subframe2, text='>>',  command=lambda: self.freq_button_handler(self.major_freq_increment))
        self.rightButton2.grid(row=1, column=5, padx=1, pady=3, sticky='w')


    def __fill_mid_frame(self):
        self.uf_frame = tk.Frame(self.mid_frame, height=1, width=3,  relief=tk.GROOVE, borderwidth=4)
        self.uf_frame.grid(row=0, column=0, rowspan=1,  padx=5, pady=5, sticky=tk.N + tk.E + tk.W)

        self.gain_frame = tk.Frame(self.mid_frame, height=1, width=3, relief= tk.GROOVE, borderwidth=4)
        # self.gain_frame.grid(row=5, column=0, rowspan=1,columnspan=1,padx= 5, pady=5, sticky=tk.N + tk.E + tk.W)
        self.gain_frame.grid(row=1, column=0, rowspan=1,padx= 5, pady=5, sticky=tk.N + tk.E + tk.W)

        self.bypass_frame = tk.Frame(self.mid_frame, height=1, width=3,  relief= tk.GROOVE, borderwidth=4)
        self.bypass_frame.grid(row=2, column=0, rowspan=1,padx= 5, pady=5, sticky=tk.N + tk.E + tk.W)

        self._uf_s = tk.StringVar()
        self.uf_label = tk.Label(self.uf_frame, text="UltraFine tuning", width=16)
        self.uf_label.grid(row=0, column=0, sticky=tk.W)
        self.uf_label.config(state=tk.DISABLED)
        self._ufmode_i = tk.IntVar()
        self.ufmode_radio1 = tk.Radiobutton(self.uf_frame, text="calibrated", value=1,
                            variable=self._ufmode_i, command=self.ufmode_handler)
        self.ufmode_radio1.grid(row=1,column=0,sticky=tk.W)
        self.ufmode_radio1.config(state=tk.DISABLED)
        self.ufmode_radio0 = tk.Radiobutton(self.uf_frame, text="adjustable(0-255)", value=0,
                            variable=self._ufmode_i, command=self.ufmode_handler)
        self.ufmode_radio0.grid(row=2,column=0,sticky=tk.W)
        self.ufmode_radio0.config(state=tk.DISABLED)
        self.uf_leftButton = tk.Button(self.uf_frame,text='<', command=lambda: self.uf_button_handler(-1))
        self.uf_leftButton.grid(row=2,column=1, padx = 3)
        self.uf_box = tk.Entry(self.uf_frame, textvariable=self._uf_s,width=5,font="-weight bold")
        self.uf_box.grid(row=2, column=2, padx =5, pady=5,sticky=tk.W)
        self.uf_box.bind('<Return>', self.uf_box_handler)
        self.uf_box.config(state=tk.DISABLED)
        self.uf_rightButton = tk.Button(self.uf_frame,text='>',command=lambda: self.uf_button_handler(1))
        self.uf_rightButton.grid(row=2,column=3, padx = 3, sticky='e')

        self.bypass_i = tk.IntVar()
        self.bypass_chk = tk.Checkbutton(self.bypass_frame, text = "manual bypass", variable=self.bypass_i,command = self.bypass_handler)
        self.bypass_chk.grid(row=0, column=0, sticky=tk.W)
        self.bypass_chk.config(state=tk.DISABLED)

        self._gain_s = tk.StringVar()
        self.gain_label = tk.Label(self.gain_frame, text="gain", width=7, anchor = tk.E)
        self.gain_label.grid(row=0, column=0, sticky=tk.W)
        self.gain_label.config(state=tk.DISABLED)
        self.gain_leftButton = tk.Button(self.gain_frame,text='<', command=lambda: self.gain_button_handler(-1))
        self.gain_leftButton.grid(row=0,column=1, padx = 3)
        self.gain_box = tk.Entry(self.gain_frame, textvariable=self._gain_s,width=6,font="-weight bold")
        self.gain_box.grid(row=0, column=2, pady=5, padx= 5, sticky=tk.W)
        self.gain_box.bind('<Return>', self.gain_handler)
        self.gain_box.config(state=tk.DISABLED)
        self.gain_rightButton = tk.Button(self.gain_frame,text='>',command=lambda: self.gain_button_handler(1))
        self.gain_rightButton.grid(row=0,column=3, padx = 3, sticky='e')


    def __fill_bottom_bar(self):
        self.status_bar1 = tk.Label(self.bottom_bar, text=' ', font = text_font)
        self.status_bar1.grid(row=0, column=0, columnspan=1, sticky=tk.N + tk.S + tk.W)
        self.status_bar2 = tk.Label(self.bottom_bar, text='  ', font = text_font)
        self.status_bar2.grid(row=0, column=1, columnspan=1, sticky=tk.N + tk.S + tk.W + tk.E)
        self.status_bar3 = tk.Label(self.bottom_bar, text='  ', font = default_font, fg="red")
        self.status_bar3.grid(row=0, column=2, columnspan=1, sticky=tk.N + tk.S + tk.E)
        self.status_bar1.config(text=".")

    def status1(self,msg, **kwargs):
        self.status_bar1.config(text=msg,**kwargs )
        self.update()

    def enable_widgets(self, on_off, uf_mode=True):
        if on_off:
            new_state = tk.NORMAL
        else:
            new_state = tk.DISABLED
        self.option_menu.entryconfig(0, state=new_state)
        self.option_menu.entryconfig(1, state=new_state)
        self.freq_box.config(state=new_state)
        self.freq_label1.config(state=new_state)
        self.start_label.config(state=new_state)
        self.stop_label.config(state=new_state)
        self.bypass_chk.config(state=new_state)
        self.gain_label.config(state=new_state)
        self.gain_box.config(state=new_state)
        self.gain_leftButton.config(state=new_state)
        self.gain_rightButton.config(state=new_state)
        self.uf_label.config(state=new_state)
        self.ufmode_radio0.config(state=new_state)
        self.ufmode_radio1.config(state=new_state)
        if uf_mode:
            self.uf_label.config(state=tk.DISABLED)
            self.uf_box.config(state=tk.DISABLED)
            self.uf_leftButton.config(state=tk.DISABLED)
            self.uf_rightButton.config(state=tk.DISABLED)
        else:
            self.uf_label.config(state=new_state)
            self.uf_box.config(state=new_state)
            self.uf_leftButton.config(state=new_state)
            self.uf_rightButton.config(state=new_state)


    def port_selection_handler1(self):
        if self.serial_port_b.get():
            self.network_port_b.set(False)
            globe.dut_kind = globe.DUTKind.serial
            self.top_bar1.tkraise()
        else:
            self.network_port_b.set(True)
            globe.dut_kind = globe.DUTKind.network

    def port_selection_handler2(self):
        if self.network_port_b.get():
            self.serial_port_b.set(False)
            globe.dut_kind = globe.DUTKind.network
            self.top_bar2.tkraise()
        else:
            self.serial_port_b.set(True)
            globe.dut_kind = globe.DUTKind.serial

    # These functions have an optional 'event' parameter because button binding passes an
    # event object to the callback function, but the menu doesn't.
    # So you need it if the function is invoked by a button press, but not if it is from
    # a menu. It's easiest just to put the optional parameter on all of them.


    def gain_handler(self, event=None):
        """
          atten is max gain - desired gain
        """
        # can't just do this:
        # g = float(s)
        # logger.info("setting the gain to " + str(g))
        # globe.dut.set_gain(g)  #no, firmware rev <2.01 don't have this
        # g = globe.dut.get_gain()
        # because there was one unit without gain commands
        # logger.info(inspect.stack()[0][3])
        s = None
        try:
            s = self._gain_s.get()
            a = globe.dut.nominal_gain-float(s)
            if a<0:
                a = 0
            logger.info("setting the attn to " + str(a))
            globe.dut.set_attn(a)
            # can't just query the gain cuz there was 1 unit w/o a gain query
            g = globe.dut.nominal_gain - globe.dut.get_attn()
        except bbuq.UltraQResponseError as e:
            self.status1("Bad or no response from device")
            return
        except bbuq.UltraQLoggedOutError as e:
            self.status1("Not Connected to Device")
            return
        except ValueError as e:
            logger.warning(e.__class__)
            logger.warning("value error in " + inspect.stack()[0][3])
            return
        s = '{0:5.2f}'.format(g)
        self._gain_s.set(s)

    def gain_button_handler(self, increment, event=None):
        try:
            g = float(self._gain_s.get())
            g += (increment * globe.dut.attn_step_size)
            a = globe.dut.nominal_gain-g
            if a<0:
                a = 0
            logger.info("setting the attn to " + str(a))
            globe.dut.set_attn(a)
            # can't just query the gain cuz there was 1 unit w/o a gain query
            g = globe.dut.nominal_gain - globe.dut.get_attn()
        except bbuq.UltraQResponseError as e:
            self.status1("Bad or no response from device")
            return
        except bbuq.UltraQLoggedOutError as e:
            self.status1("Not Connected to Device")
            return
        except ValueError as e:
            logger.warning(e.__class__)
            logger.warning("value error in " + inspect.stack()[0][3])
            return
        self._gain_s.set('{0:5.2f}'.format(g))

    def bypass_handler(self, event=None):
        s = None
        try:
            s = self.bypass_i.get()
        except ValueError as e:
            logger.warning(e.__class__)
            logger.warning("value error in bypass_handler")
        b = bool(s == 1)
        logger.info("setting the dut byp to " + str(b))
        try:
            globe.dut.set_bypass(b)
            r = globe.dut.get_bypass()
        except bbuq.UltraQResponseError as e:
            self.status1("Bad or no response from device")
            return
        except bbuq.UltraQLoggedOutError as e:
            self.status1("Not Connected to Device")
            return
        self.bypass_i.set(r)

    def overpower_handler(self, event=None):
        s = None
        try:
            s = self.overpower_bypass_b.get()
        except ValueError as e:
            logger.warning(e.__class__)
        if s:
            b = 1
        else:
            b = 0
        logger.info("setting the over power protection to " + str(b))
        try:
            globe.dut.set_overpower_bypass_enable(b)
            r = globe.dut.get_overpower_bypass_enable()
        except bbuq.UltraQResponseError as e:
            self.status1("Bad or no response from device")
            return
        except bbuq.UltraQLoggedOutError as e:
            self.status1("Not Connected to Device")
            return
        self.overpower_bypass_b.set(r)

    def logging_handler(self, event=None): # TODO test this
        b = self.logging_b.get()
        if b:
            logging.disable(logging.NOTSET)
        else:
            logging.disable(999)

    def write_handler(self, event=None):
        """
        why is this even here? If someone needs this, they should set it in their code,
        not from the GUI
        """
        try:
            s = self.write_b.get()
        except ValueError as e:
            logger.warning(e.__class__)
            logger.warning("value error in write_handler")
            return
        if s:
            b = 1
        else:
            b = 0
        logger.info("setting the EEPROM write to " + str(b))
        try:
            globe.dut.set_write(b)
            r = globe.dut.get_write()
        except bbuq.UltraQResponseError as e:
            self.status1("Bad or no response from device")
            return
        except bbuq.UltraQLoggedOutError as e:
            self.status1("Not Connected to Device")
            return
        self.write_b.set(r)

    def ufmode_handler(self, event=None):
        s = None
        try:
            s = self._ufmode_i.get()
        except ValueError as e:
            logger.warning(e.__class__)
            logger.warning("value error in ufmode_handler")
        b = bool(s == 1)
        logger.info("setting the uf mode to " + str(b))
        try:
            globe.dut.set_uf_mode(b)
            r = globe.dut.get_uf_mode()
            n = globe.dut.get_ultrafine()
        except bbuq.UltraQResponseError as e:
            self.status1("Bad or no response from device")
            return
        except bbuq.UltraQLoggedOutError as e:
            self.status1("Not Connected to Device")
            return

        self._ufmode_i.set(r)
        if r:
            self.uf_box.config(state=tk.DISABLED)
            self.uf_leftButton.config(state=tk.DISABLED)
            self.uf_rightButton.config(state=tk.DISABLED)
        else:
            self.uf_box.config(state=tk.NORMAL)
            self.uf_leftButton.config(state=tk.NORMAL)
            self.uf_rightButton.config(state=tk.NORMAL)
            self._uf_s.set(str(n))

    def uf_box_handler(self, event=None):
        try:
            s = self._uf_s.get()
        except ValueError as e:
            logger.warning(e.__class__)
            logger.warning("value error in " + inspect.stack()[0][3])
            return
        logger.info("setting the ultrafine to " + str(s))
        try:
            globe.dut.set_ultrafine(s)
            f = globe.dut.get_ultrafine()
        except bbuq.UltraQResponseError as e:
            self.status1("Bad or no response from device")
            return
        except bbuq.UltraQLoggedOutError as e:
            self.status1("Not Connected to Device")
            return
        self._uf_s.set(str(f))

    def uf_button_handler(self, increment, event=None):
        try:
            f = int(self._uf_s.get())
        except ValueError as e:
            logger.warning(e.__class__)
            logger.warning("value error in " + inspect.stack()[0][3])
            return
        f += increment
        try:
            globe.dut.set_ultrafine(f)
            f = globe.dut.get_ultrafine()
        except bbuq.UltraQResponseError as e:
            self.status1("Bad or no response from device")
            return
        except bbuq.UltraQLoggedOutError as e:
            self.status1("Not Connected to Device")
            return
        self._uf_s.set(str(f))

    def freq_button_handler(self, increment, event=None):
        try:
            f = float(self._freq_s.get())
        except ValueError as e:
            logger.warning(e.__class__)
            logger.warning("value error in " + inspect.stack()[0][3])
            return
        f += increment
        logger.info("setting the freq to " + str(f))
        try:
            globe.dut.set_freq(f)
            f2 = globe.dut.get_freq() # if this fails, it raises the exception
            # but then device & gui might be out of sync
        except bbuq.UltraQResponseError as e:
            self.status1("Bad or no response from device")
            return
        except bbuq.UltraQLoggedOutError as e:
            self.status1("Not Connected to Device")
            return
        else:
            self.status1("")
            self._freq_s.set("{:.6f}".format(f2))


    def freq_box_handler(self, event=None):
        s = None
        f = 0.0
        try:
            s = self._freq_s.get()
            f = float(s)
        except ValueError as e:
            logger.warning(e.__class__)
            logger.warning("value error in " + inspect.stack()[0][3])
        logger.info("setting the freq to " + str(f))
        try:
            globe.dut.set_freq(f)
            f = globe.dut.get_freq()
        except bbuq.UltraQResponseError as e:
            self.status1("Bad or no response from device")
            return
        except bbuq.UltraQLoggedOutError as e:
            self.status1("Not Connected to Device")
            return
        self._freq_s.set("{:.6f}".format(f))


    def connect_button_handler(self, event=None):
        self.status1(" ")
        self.enable_widgets(False)
        if globe.dut is not None:
            globe.close_dut()  # this sets globe.dut to None
        if globe.dut_kind == globe.DUTKind.network:
            try:
                globe.remote_address = self.top_bar2.remote_address_str.get()
                globe.remote_port = self.top_bar2.remote_port_str.get()
                self.top_bar3.tkraise()
                self.top_bar3.password_box.focus_set()
                return   # go wait for user to enter password and click again
            except Exception as e:
                logger.error(e.__class__)
                self.status1("Cannot connect to a device at that address")
                return
        else:
            if self.top_bar1.comport_str.get() == '':
                if not self.top_bar1.populate_comport_menu():
                    self.status1("Cannot find any com ports. Connect device and try again.")
                else:
                    self.status1("")
                return
            try:
                port_num = int(self.top_bar1.comport_str.get())
                self.status1("connecting...")
                globe.open_dut([port_num], self.terminal_window.textbox,globe.DUTKind.serial)
            except Exception as e:
                logger.error(e.__class__)
                logger.error("Can't open a serial port\n")
                self.terminal_window.textbox.append("Couldn't open the serial port\n")
                self.status1("Cannot connect to a device on that port")
                return
        # would dut be None if it had been disconnected? No.
        if globe.dut is None:
            self.status1("Cannot connect to device on that port")
            return
        self.refresh_gui()

    def connect_button_handler2(self, event=None):
        self.enable_widgets(False)
        if globe.dut is not None:
            globe.close_dut()  # this sets globe.dut to None
        try:
            globe.remote_address = self.top_bar2.remote_address_str.get()
            globe.remote_port = self.top_bar2.remote_port_str.get()
            globe.password = self.top_bar3.password_str.get()
            self.status1("Connecting to device at " + globe.remote_address + ':' + globe.remote_port)
            globe.open_dut([globe.remote_address, globe.remote_port], app.terminal_window.textbox, kind = globe.DUTKind.network)
        except Exception as e:
            logger.error(e.__class__)
            logger.error("Can't open a socket\n")
            app.terminal_window.textbox.append("Couldn't open the socket\n")
            self.status1("Cannot connect to a device")
            self.top_bar3.password_str.set("")
            self.top_bar2.tkraise()
            return
        finally:
            self.top_bar3.password_str.set("")
            self.top_bar2.tkraise()

        if globe.dut is None:
            self.status1("Cannot connect to device")
            return
        self.refresh_gui()

    def refresh_gui(self):
        uf_mode = None
        try:
            globe.start_freq = globe.dut.get_start_freq()
            globe.stop_freq = globe.dut.get_stop_freq()
            # both of these ways  of setting the label work.
            # is the second one more efficient?
            self.start_label.configure(text=str(globe.start_freq)+ ' MHz')
            self.stop_label['text']=str(globe.stop_freq)+ ' MHz'
            self._freq_s.set("{:.6f}".format(globe.dut.get_freq()))
            self.minor_freq_increment = globe.dut.get_chan_spacing() / const.HZ_PER_MHZ
            # can't just query the gain cuz there was 1 unit w/o a gain query
            self._gain_s.set(str(globe.dut.nominal_gain - globe.dut.get_attn()))
            self.bypass_i.set(globe.dut.get_bypass())
            self.overpower_bypass_b.set(globe.dut.get_overpower_bypass_enable())
            self.write_b.set(globe.dut.get_write())
            # let the UF wait til other widgets are being enabled, looks bad to do it first
            uf_mode = globe.dut.get_uf_mode() # TODO this once got called when globe.dut was None, can't replicate
            self._ufmode_i.set(uf_mode)
            uf_setting = globe.dut.get_ultrafine()
            self._uf_s.set(str(uf_setting))
        except bbuq.UltraQResponseError as e:
            self.status1("Bad or no response from device")
            return
        except bbuq.UltraQLoggedOutError as e:
            self.status1("Not Connected to Device")
            return
        # except Exception as e:
        #     pass
        self.enable_widgets(True, uf_mode)
        self.status_bar1.config(text = "OK")
        self.poll_for_overpower_bypass()




    def poll_for_overpower_bypass(self):
        pass
        # if self.overpower_bypass_b.get():
        #     if globe.dut is not None:
        #         if globe.dut.port.is_open():
        #             op = globe.dut.get_overpower_status()
        #             if op:
        #                 self.status_bar3.config(text = "OVER POWER BYPASS")
        #             else:
        #                 self.status_bar3.config(text = "")
        # else:
        #     self.status_bar3.config(text = "")
        # self.after(poll_timing, self.poll_for_overpower_bypass)


def show_terminal():
    app.terminal_window.textbox.clear()
    app.terminal_window.deiconify()

def user_interrupt_handler(event=None):
    globe.user_interrupt = True
    return 'break'


def display_about_messagebox(event=None):
    about_string = const.PROGRAM_NAME + " " + const.VERSION + "\n"
    about_string += " TelGaAs Inc.\n" + " telgaas.com \n"
    about_string += __author__ + "\n"
    tmb.showinfo("About " + const.PROGRAM_NAME, about_string, icon=tmb.INFO)
    return 'break'


def display_help_messagebox(event=None):
    help_string = "Contact TelGaAs Inc. at telgaas.com for help\n\n"
    help_string += "USB drivers for Ultra-Q filters are available at \n"
    help_string += "http://www.ftdichip.com/Drivers/VCP.htm"
    tmb.showinfo("Help", help_string, icon=tmb.INFO)
    return 'break'


def exit_handler(event=None):
    logger.info('QUITTING')
    if globe.dut is not None:
        globe.close_dut()
    logger.info('calling root.destroy and os.exit()')
    root.destroy()

    # TODO: not sure if os._exit is the best practice here, but it works OK
    # sys.exit()  #this doesn't work - the test loop keeps going until it crashes due to the textbox being gone.
    # raise SystemExit doesn't always work
    # noinspection PyProtectedMember
    os._exit(0)


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller
        PyInstaller creates a temp folder and stores path in _MEIPASS
        if sys doesn't have _MEIPASS, default to the path to __file__  (i.e. this file)
    """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


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
const.HEADER_IMAGE = resource_path('banner250x50.gif')

root = tk.Tk()
style = ttk.Style()
style.theme_use('alt')
# use .option_add if you want to change the font,
# root.option_add("*Font", "courier 9 bold")
default_font = tk.font.nametofont("TkDefaultFont")
default_font.configure(size=9, weight="bold")
text_font = tk.font.nametofont("TkTextFont")

bold_style = ttk.Style()
bold_style.configure("bold.TButton", font ='bold')
#  or bold_style.configure("bold.TButton", font = ('Sans','10','bold'))

app = MainWindow(root)
app.pack(fill='both', expand='True')
set_root_size()
root.title(const.PROGRAM_NAME + " " + str(const.VERSION))
root.iconbitmap(const.ICON_FILE)
root.bind_all('<Escape>', user_interrupt_handler)
root.bind('<KeyPress-F1>', display_help_messagebox)
root.protocol('WM_DELETE_WINDOW', exit_handler)  # override the Windows "X" button
# app.comport_handler()  # this updates the port number in globe, so the terminal window can use it if necessary

root.mainloop()


