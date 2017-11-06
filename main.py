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


__author__ = 'jpindar@jpindar.com'
const.PROGRAM_NAME = " Ultra-Q "
const.VERSION = "v1.04"
const.BUILD = "1.04.0"
globe.user_interrupt = False
globe.unsaved = False


class MainWindow(tk.Frame):
    """
    """
    major_freq_increment = 1
    minor_freq_increment = 0.0025

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.my_settings_window = None
        self.unsaved_text = False
        self.start_freq = 0.0
        self.stop_freq = 0.0
        self.overpower_bypass_b = tk.BooleanVar()
        self.write_b = tk.BooleanVar()
        self.logging_b = tk.BooleanVar()

        logger.info("creating main window")
        self.terminal_window = terminalwindow.TerminalWindow(self.parent, globe.dev_null)

        tk.Grid.rowconfigure(self, 6, weight =1)
        tk.Grid.columnconfigure(self, 1, weight=1)
        self.__create_top_bar()
        self.__create_freq_frame()
        self.__create_widgets()
        self._create_bottom_widgets()
        self.__create_menus()


    def __create_menus(self):
        self.menu_bar = tk.Menu(self)
        self.parent.config(menu=self.menu_bar)

        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label='File', menu=file_menu)
        file_menu.add_command(label='Exit', command=exit_handler)

        self.option_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label='Options', menu=self.option_menu)
        self.option_menu.add_checkbutton(label="Over power protection", onvalue=1, offvalue=0, variable=self.overpower_bypass_b, command=self.overpower_handler)
        self.option_menu.add_checkbutton(label="EEPROM write enable", onvalue=1, offvalue=0, variable=self.write_b, command=self.write_handler)
        if ENABLE_LOGGING:
            self.option_menu.add_checkbutton(label="log file", onvalue=1, offvalue=0, variable=self.logging_b, command=self.logging_handler)

        self.option_menu.entryconfig(0, state=tk.DISABLED)
        self.option_menu.entryconfig(1, state=tk.DISABLED)

        about_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label='About', menu=about_menu)
        about_menu.add_command(label='About', command=display_about_messagebox)
        about_menu.add_command(label='Help', command=display_help_messagebox)
        about_menu.add_command(label='Terminal', command=self.show_terminal)


    def __create_top_bar(self):
        global possible_ports
        possible_ports = serialdevice_pyserial.get_ports()
        self.top_bar = tk.Frame(self, height=20, background='#D9E5EE')
        self.top_bar.configure(borderwidth=2, relief='flat')
        self.top_bar.grid(row=0, column=0, columnspan=2, sticky=tk.E + tk.W)

        col = 0
        style = ttk.Style()
        style.theme_use('alt')
        self._comport_str = tk.StringVar()
        self.comport_label = tk.Label(self.top_bar, text="Com Port",bg='#D9E5EE')
        self.comport_label.grid(row=0, column=col, sticky='e')

        col += 1
        self.comport_dropdown = ttk.OptionMenu(self.top_bar, self._comport_str, possible_ports[0],
                                               *possible_ports, command = self.comport_handler)
        self.comport_dropdown.config(width=4)
        self.comport_dropdown.grid(row=0, column=col, sticky='w', padx=3, ipady=1)

        col += 1
        self.button_connect = tk.Button(self.top_bar, text="Connect", bg='light grey', command=self.connect_button_handler)
        self.button_connect.grid(row=0, column=col, padx=2, pady=2, sticky=tk.E)
        self.button_connect.bind('<Return>', self.connect_button_handler)

        col += 1
        photo = tk.PhotoImage(file=const.HEADER_IMAGE)
        self.image_label = tk.Label(self.top_bar, image=photo, bg = '#D9E5EE')
        self.image_label.photo = photo
        self.image_label.grid(row=0, column=col, padx = 10, sticky=tk.EW)


    def __create_freq_frame(self):
        self.freq_frame = tk.Frame(self, height=2, width=3,relief=tk.GROOVE,borderwidth=4)
        self.freq_frame.grid(row=2, column=0, rowspan=2,columnspan=3, padx=5, pady=5, sticky=tk.N + tk.EW)

        self.freq_subframe1 = tk.Frame(self.freq_frame,height=1, width = 3)
        self.freq_subframe1.grid(row=0, column=0)
        self.freq_subframe2 = tk.Frame(self.freq_frame,height=1, width = 3)
        self.freq_subframe2.grid(row=1, column=0)

        cntl_row = 0
        self.start_label = tk.Label(self.freq_subframe1, text="     ", width=12, anchor=tk.W)
        self.start_label.grid(row=cntl_row, column=0, padx=5, sticky=tk.W)

        tk.Label(self.freq_subframe1, text="", width=1).grid(row=cntl_row, column=1, sticky=tk.EW)

        tk.Label(self.freq_subframe1, text="", width=15).grid(row=cntl_row, column=2, sticky=tk.EW)
        self.freq_label1 = tk.Label(self.freq_subframe1, text=" FREQUENCY IN MHZ", width=20, state = tk.DISABLED)
        self.freq_label1.grid(row=cntl_row, column=2, sticky=tk.EW)

        tk.Label(self.freq_subframe1, text="", width=1).grid(row=cntl_row, column=3, sticky=tk.EW)

        self.stop_label = tk.Label(self.freq_subframe1, text="     ", width=12,  anchor=tk.E)
        self.stop_label.grid(row=cntl_row, column=4, padx=5, sticky=tk.E)

        self._freq_v = tk.DoubleVar()
        self._freq_s = tk.StringVar()

        cntl_row += 1
        self.leftButton = tk.Button(self.freq_subframe2, text='<<', command=lambda: self.freq_button_handler(-1 * self.major_freq_increment))
        self.leftButton.grid(row=cntl_row, column=1,  padx=1, pady=3, sticky='e')

        self.leftButton2 = tk.Button(self.freq_subframe2, text='<', command=lambda: self.freq_button_handler(-1 * self.minor_freq_increment))
        self.leftButton2.grid(row=cntl_row, column=2,  padx=1, pady=3, sticky='e')

        self.freq_box = tk.Entry(self.freq_subframe2,textvariable=self._freq_s,bg='light grey',width=10,font="-weight bold")
        self.freq_box.grid(row=cntl_row, column=3, padx = 5)
        self.freq_box.bind('<Return>', self.freq_box_handler)
        self.freq_box.config(state=tk.DISABLED)

        self.rightButton = tk.Button(self.freq_subframe2, text='>', command=lambda: self.freq_button_handler(self.minor_freq_increment))
        self.rightButton.grid(row=cntl_row, column=4, padx=1, pady=3, sticky='w')

        self.rightButton2 = tk.Button(self.freq_subframe2, text='>>',  command=lambda: self.freq_button_handler(self.major_freq_increment))
        self.rightButton2.grid(row=cntl_row, column=5, padx=1, pady=3, sticky='w')

        # TODO  implement these radiobuttons
        # cntl_row += 1
        # self.rb_frame = tk.Frame(self.freq_frame, height=1, width=4, bg="dark grey", borderwidth=5)
        # self.rb_frame.grid(row=cntl_row, column=0, rowspan=1,columnspan=8, padx=5, pady=5, ipady=[5], sticky=tk.N + tk.EW)
        # cntl_row = 0

        # self.radio_button_1 = tk.Button(self.rb_frame, text='__________')
        # self.radio_button_1.grid(row=cntl_row, column=0, padx=1, pady=3,sticky=tk.EW)
        # self.radio_button_2 = tk.Button(self.rb_frame, text='__________')
        # self.radio_button_2.grid(row=cntl_row, column=1, padx=1, pady=3,sticky=tk.EW)
        # self.radio_button_3 = tk.Button(self.rb_frame, text='__________')
        # self.radio_button_3.grid(row=cntl_row, column=2, padx=1, pady=3,sticky=tk.EW)
        # self.radio_button_4 = tk.Button(self.rb_frame, text='__________')
        # self.radio_button_4.grid(row=cntl_row, column=3, padx=1, pady=3,sticky=tk.EW)
        # self.radio_button_5 = tk.Button(self.rb_frame, text='__________')
        # self.radio_button_5.grid(row=cntl_row, column=4, padx=1, pady=3,sticky=tk.EW)
        # spacer
        # cntl_row += 1
        # tk.Label(self.freq_frame).grid(row=cntl_row, column=0,  sticky=tk.E+tk.W)

    def __create_widgets(self):

        self.uf_frame = tk.Frame(self, height=1, width=3,  relief=tk.GROOVE, borderwidth=4)
        self.uf_frame.grid(row=4, column=0, rowspan=1,  padx=5, pady=5, sticky=tk.N + tk.E + tk.W)

        self.gain_frame = tk.Frame(self, height=1, width=3, relief= tk.GROOVE, borderwidth=4)
        # self.gain_frame.grid(row=5, column=0, rowspan=1,columnspan=1,padx= 5, pady=5, sticky=tk.N + tk.E + tk.W)
        self.gain_frame.grid(row=5, column=0, rowspan=1,padx= 5, pady=5, sticky=tk.N + tk.E + tk.W)

        self.bypass_frame = tk.Frame(self, height=1, width=3,  relief= tk.GROOVE, borderwidth=4)
        self.bypass_frame.grid(row=6, column=0, rowspan=1,padx= 5, pady=5, sticky=tk.N + tk.E + tk.W)

        self._uf_s = tk.StringVar()

        self.uf_label = tk.Label(self.uf_frame, text="UltraFine tuning", width=16)
        self.uf_label.grid(row=0, column=0, sticky=tk.W)
        self.uf_label.config(state=tk.DISABLED)

        self.ufmode_i = tk.IntVar()

        self.ufmode_radio1 = tk.Radiobutton(self.uf_frame, text="calibrated", value=1,
                            variable=self.ufmode_i, command=self.ufmode_handler)
        self.ufmode_radio1.grid(row=1,column=0,sticky=tk.W)
        self.ufmode_radio1.config(state=tk.DISABLED)
        self.ufmode_radio0 = tk.Radiobutton(self.uf_frame, text="adjustable(0-255)", value=0,
                            variable=self.ufmode_i, command=self.ufmode_handler)
        self.ufmode_radio0.grid(row=2,column=0,sticky=tk.W)
        self.ufmode_radio0.config(state=tk.DISABLED)

        self.uf_leftButton = tk.Button(self.uf_frame,text='<', command=lambda: self.uf_button_handler(-1)  )
        self.uf_leftButton.grid(row=2,column=1, padx = 3)
        self.uf_box = tk.Entry(self.uf_frame, textvariable=self._uf_s, bg='light grey', width=5,font="-weight bold")
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

        self.gain_leftButton = tk.Button(self.gain_frame,text='<', command=lambda: self.gain_button_handler(-1)  )
        self.gain_leftButton.grid(row=0,column=1, padx = 3)

        self.gain_box = tk.Entry(self.gain_frame, textvariable=self._gain_s, bg='light grey', width=6,font="-weight bold")
        self.gain_box.grid(row=0, column=2, pady=5, padx= 5, sticky=tk.W)
        self.gain_box.bind('<Return>', self.gain_handler)
        self.gain_box.config(state=tk.DISABLED)

        self.gain_rightButton = tk.Button(self.gain_frame,text='>',command=lambda: self.gain_button_handler(1))
        self.gain_rightButton.grid(row=0,column=3, padx = 3, sticky='e')


    def _create_bottom_widgets(self):
        style = ttk.Style()
        style.theme_use('alt')
        self.bottom_bar = tk.Frame(self, height=40, borderwidth=5, relief='ridge')
        self.bottom_bar.grid(row=10, column=0, columnspan='2', sticky=tk.N + tk.S + tk.E + tk.W)
        self.bottom_bar.columnconfigure(1, weight=1)
        self.status_bar1 = tk.Label(self.bottom_bar, text=' ', font = text_font)
        self.status_bar1.grid(row=0, column=0, columnspan=1, sticky=tk.N + tk.S + tk.W)
        self.status_bar2 = tk.Label(self.bottom_bar, text='  ', font = text_font)
        self.status_bar2.grid(row=0, column=1, columnspan=1, sticky=tk.N + tk.S + tk.W + tk.E)
        self.status_bar3 = tk.Label(self.bottom_bar, text='  ', font = default_font, fg="red")
        self.status_bar3.grid(row=0, column=2, columnspan=1, sticky=tk.N + tk.S + tk.E)


    def enable_widgets(self, on_off):
        if on_off:
            new_state = tk.NORMAL
        else:
            new_state = tk.DISABLED
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
        self.option_menu.entryconfig(0, state=new_state)
        self.option_menu.entryconfig(1, state=new_state)
        self.uf_leftButton.config(state=new_state)
        self.uf_rightButton.config(state=new_state)
        if self.ufmode_i.get() == 0:
            self.uf_label.config(state=new_state)
            self.uf_box.config(state=new_state)


    # These functions have an optional 'event' parameter because button binding passes an
    # event object to the callback function, but the menu doesn't.
    # So you need it if the function is invoked by a button press, but not if it is from
    # a menu. It's easiest just to put the optional parameter on all of them.


    def gain_handler(self, event=None):
        """
          atten is max gain - desired gain
        """
        # logger.info(inspect.stack()[0][3])
        s = None
        try:
            s = self._gain_s.get()
        except ValueError as e:
            logger.warning(e.__class__)
            logger.warning("value error in " + inspect.stack()[0][3])

        # can't just do this:
        # g = float(s)
        # logger.info("setting the gain to " + str(g))
        # globe.dut.set_gain(g)  #no, firmware rev <2.01 don't have this
        # g = globe.dut.get_gain()
        # because there was one unit without gain commands
        try:
            a = globe.dut.nominal_gain-float(s)
        except ValueError as e:
            logger.warning(e.__class__)
            logger.warning("value error in " + inspect.stack()[0][3])
            return
        if a<0:
            a = 0
        logger.info("setting the attn to " + str(a))
        globe.dut.set_attn(a)
        #can't just query the gain cuz there was 1 unit w/o a gain query
        g = globe.dut.nominal_gain - globe.dut.get_attn()
        s = '{0:5.2f}'.format(g)
        self._gain_s.set(s)

    def gain_button_handler(self, increment, event=None):
        try:
            g = float(self._gain_s.get())
            g += (increment * globe.dut.attn_step_size)
            a = globe.dut.nominal_gain-g
            if a<0:
                a = 0
        except ValueError as e:
            logger.warning(e.__class__)
            logger.warning("value error in " + inspect.stack()[0][3])
            return
        logger.info("setting the attn to " + str(a))
        globe.dut.set_attn(a)
        #can't just query the gain cuz there was 1 unit w/o a gain query
        g = globe.dut.nominal_gain - globe.dut.get_attn()
        s = '{0:5.2f}'.format(g)
        self._gain_s.set(s)


    def bypass_handler(self, event=None):
        s = None
        try:
            s = self.bypass_i.get()
        except ValueError as e:
            logger.warning(e.__class__)
            logger.warning("value error in bypass_handler")
        b = bool(s == 1)
        logger.info("setting the dut byp to " + str(b))
        globe.dut.set_bypass(b)
        r = globe.dut.get_bypass()
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
        globe.dut.set_overpower_bypass_enable(b)
        r = globe.dut.get_overpower_bypass_enable()
        self.overpower_bypass_b.set(r)


    def logging_handler(self, event=None):
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
        globe.dut.set_write(b)
        r = globe.dut.get_write()
        self.write_b.set(r)

    def ufmode_handler(self, event=None):
        s = None
        try:
            s = self.ufmode_i.get()
        except ValueError as e:
            logger.warning(e.__class__)
            logger.warning("value error in ufmode_handler")
        b = bool(s == 1)
        logger.info("setting the uf mode to " + str(b))
        globe.dut.set_uf_mode(b)
        r = globe.dut.get_uf_mode()
        self.ufmode_i.set(r)
        if r:
            self.uf_box.config(state=tk.DISABLED)
            self.uf_leftButton.config(state=tk.DISABLED)
            self.uf_rightButton.config(state=tk.DISABLED)
        else:
            self.uf_box.config(state=tk.NORMAL)
            self.uf_leftButton.config(state=tk.NORMAL)
            self.uf_rightButton.config(state=tk.NORMAL)
            n = globe.dut.get_uf()
            self._uf_s.set(str(n))

    def uf_box_handler(self, event=None):
        try:
            s = self._uf_s.get()
        except ValueError as e:
            logger.warning(e.__class__)
            logger.warning("value error in " + inspect.stack()[0][3])
            return
        logger.info("setting the ultrafine to " + str(s))
        globe.dut.set_uf(s)
        f = globe.dut.get_uf()
        self._uf_s.set(str(f))

    def uf_button_handler(self, increment, event=None):
        try:
            f = int(self._uf_s.get())
        except ValueError as e:
            logger.warning(e.__class__)
            logger.warning("value error in " + inspect.stack()[0][3])
            return

        f += increment
        globe.dut.set_uf(f)
        f = globe.dut.get_uf()
        self._uf_s.set(str(f))


    def freq_button_handler(self, increment, event=None):
        # f = 0.0
        try:
            f = float(self._freq_s.get())
        except ValueError as e:
            logger.warning(e.__class__)
            logger.warning("value error in " + inspect.stack()[0][3])
            return
        f += increment
        logger.info("setting the freq to " + str(f))
        globe.dut.set_freq(f)
        f = globe.dut.get_freq()
        self._freq_v.set(float(f))
        self._freq_s.set(str(f))


    def freq_box_handler(self, event=None):
        s = None
        try:
            s = self._freq_s.get()
        except ValueError as e:
            logger.warning(e.__class__)
            logger.warning("value error in " + inspect.stack()[0][3])
        logger.info("setting the freq to " + str(s))
        globe.dut.set_freq(s)
        f = globe.dut.get_freq()
        self._freq_v.set(float(f))
        self._freq_s.set(str(f))


    def populate_comport_menu(self):
        global possible_ports
        possible_ports = serialdevice_pyserial.get_ports()
        self.comport_dropdown.set_menu(possible_ports[0], *possible_ports)
        n = len(possible_ports)
        if possible_ports[0] =='':
            return False
        else:
            self.comport_handler()
            return n > 0


    def comport_handler(self, event = None):
        try:
            globe.serial_port_num = int(self._comport_str.get())
        except Exception:   # if there is no comport number there, give up
            pass

    def connect_button_handler(self, event=None):
        self.status_bar1.config(text = "connecting...")
        self.enable_widgets(False)
        if globe.dut is not None:
            if globe.dut.port.is_open():
                globe.close_dut()

        if self._comport_str.get() == '':
            if not self.populate_comport_menu():
                self.status_bar1.config(text = "Cannot find any com ports. Connect device and try again.")
            else:
                self.status_bar1.config(text = "")
            return

        try:
            port_num = int(self._comport_str.get())
            globe.open_dut(port_num, self.terminal_window.textbox, mock = False)
        except Exception as e:
            logger.error(e.__class__)
            logger.error("Can't open a serial port\n")
            self.terminal_window.textbox.append("Couldn't open the serial port\n")
            self.status_bar1.config(text = "Cannot connect to a device on that port")
            return
        # would dut be None if it had been disconnected? No.
        if globe.dut is None:
            self.status_bar1.config(text = "Cannot connect to device on that port")
            return

        self.start_freq = globe.dut.get_start_freq()
        self.stop_freq = globe.dut.get_stop_freq()
        self.start_label.configure(text=str(self.start_freq)+ ' MHz')
        self.stop_label.configure(text=str(self.stop_freq)+ ' MHz')

        f = globe.dut.get_freq()
        self._freq_v.set(float(f))
        self._freq_s.set(str(f))
        self.minor_freq_increment = globe.dut.get_chan_spacing() / const.HZ_PER_MHZ

        #can't just query the gain cuz there was 1 unit w/o a gain query
        self._gain_s.set(str(globe.dut.nominal_gain - globe.dut.get_attn()))
        self.bypass_i.set(globe.dut.get_bypass())
        self.overpower_bypass_b.set(globe.dut.get_overpower_bypass_enable())
        self.write_b.set(globe.dut.get_write())
        # let the UF wait til other widgets are being enabled, looks bad to do it first
        n = globe.dut.get_uf_mode()
        self.ufmode_i.set(n)
        self.enable_widgets(True)
        if n:
            self.uf_box.config(state=tk.DISABLED)
            self.uf_leftButton.config(state=tk.DISABLED)
            self.uf_rightButton.config(state=tk.DISABLED)
        else:
            self.uf_box.config(state=tk.NORMAL)
            self.uf_leftButton.config(state=tk.NORMAL)
            self.uf_rightButton.config(state=tk.NORMAL)
            self._uf_s.set(str(globe.dut.get_uf()))
        self.status_bar1.config(text = "OK")
        self.poll_for_overpower_bypass()


    def show_terminal(self,event=None):
        self.terminal_window.textbox.clear()
        self.terminal_window.deiconify()


    def poll_for_overpower_bypass(self):
        if self.overpower_bypass_b.get():
            if globe.dut is not None:
                if globe.dut.port.is_open():
                    op = globe.dut.get_overpower_status()
                    if op:
                        self.status_bar3.config(text = "OVER POWER BYPASS")
                    else:
                        self.status_bar3.config(text = "")
        else:
            self.status_bar3.config(text = "")
        self.after(1000, self.poll_for_overpower_bypass)


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
    root_width = 500
    root_height = 450
    root_x = (root.winfo_screenwidth() / 2) - (root_width / 2)
    root_y = (root.winfo_screenheight() / 2) - (root_height / 2)
    root.geometry('%dx%d+%d+%d' % (root_width, root_height, root_x, root_y))
    root.resizable(width=False, height=False)


# do these before the GUI starts!
const.ICON_FILE = resource_path('company_logo.ico')
const.HEADER_IMAGE = resource_path('banner250x50.gif')

root = tk.Tk()
# use .option_add if you want to change the font,
# but inthis case changing the size & boldness is enough
# root.option_add("*Font", "courier 9 bold")
default_font = tk.font.nametofont("TkDefaultFont")
default_font.configure(size=9, weight="bold")
text_font = tk.font.nametofont("TkTextFont")

app = MainWindow(root)
app.pack(fill='both', expand='True')
set_root_size()
root.title(const.PROGRAM_NAME + " " + str(const.VERSION))
root.iconbitmap(const.ICON_FILE)
root.bind_all('<Escape>', user_interrupt_handler)
root.bind('<KeyPress-F1>', display_help_messagebox)
root.protocol('WM_DELETE_WINDOW', exit_handler)  # override the Windows "X" button
app.comport_handler()  # this updates the port number in globe, so the terminal window can use it if necessary

root.mainloop()


