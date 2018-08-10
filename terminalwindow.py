# pylint: disable=wrong-import-position,unused-argument,line-too-long
"""
File: terminalwindow.py
Date: Sep-2017
Version: 1.1
Author: jeannepindar@gmail.com AKA jpindar@jpindar.com
"""
ENABLE_LOGGING = False

__author__ = 'jeannepindar@gmail.com'
import logging
logger = logging.getLogger(__name__)

import tkinter as tk
from tkinter import ttk
import tkinter.scrolledtext as tkst
import const
import globe


class TextBox(tkst.ScrolledText):
    """
    inherits from ScrolledText so we can add a context menu and some methods
    """
    # pylint: disable=too-many-ancestors
    def __init__(self, parent, **kwargs):
        self.parent = parent
        super().__init__(parent, **kwargs)
        self.config(wrap='none', state="normal", borderwidth=3, relief='sunken', undo=1)
        self.__create_context_menu()
        self.bind('<Button-3>', self._show_context_menu)
        # fix control-Y binding - tkinter's default is weird, apparently for historical reasons
        self.bind('<Control-y>', self.redo)  # handling Ctrl + lowercase y
        self.bind('<Control-Y>', self.redo)  # handling Ctrl + uppercase y
        self.menu_bar = tk.Menu(self)
        self.parent.config(menu=self.menu_bar)
        self.logging_b = tk.BooleanVar()
        if ENABLE_LOGGING:
            self.option_menu = tk.Menu(self, tearoff=0)
            self.menu_bar.add_cascade(label='Options', menu=self.option_menu)
            self.option_menu.add_checkbutton(label="log file", onvalue=1, offvalue=0,
                                             variable=self.logging_b, command=self.logging_handler)

    def logging_handler(self): # TODO test this
        b = self.logging_b.get()
        if b:
            logging.disable(logging.NOTSET)
        else:
            logging.disable(999)

    def __create_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff='no')
        self.context_menu.add_command(label='Cut', command=self.cut)
        self.context_menu.add_command(label='Copy', command=self.copy)
        self.context_menu.add_command(label='Paste', command=self.paste)
        self.context_menu.add_command(label='Undo', command=self.undo)
        self.context_menu.add_command(label='Redo', command=self.redo)
        self.context_menu.add_command(label='Select All', command=self.select_all)

    def _show_context_menu(self, event):
        self.context_menu.tk_popup(event.x_root, event.y_root)
        return 'break'

    def cut(self, event=None):
        self.event_generate("<<Cut>>")
        return 'break'

    def copy(self, event=None):
        self.event_generate("<<Copy>>")
        return 'break'

    def paste(self, event=None):
        self.event_generate("<<Paste>>")
        return 'break'

    def undo(self, event=None):
        self.event_generate("<<Undo>>")
        return 'break'

    def redo(self, event=None):
        self.event_generate("<<Redo>>")
        return 'break'

    def select_all(self, event=None):
        self.tag_add('sel', '1.0', 'end')
        return 'break'

    def delete_all(self, event=None):
        self.delete('1.0', 'end')
        self.parent.unsaved_text = False
        return 'break'

    def append(self, msg):
        if msg is None:
            return
        if msg == '':
            return
        if msg[-1] not in '\r\n':
            msg += '\r'
        if msg[-1] == '\r':
            msg += '\n'
        self.insert(tk.END, msg)
        self.see(tk.END)
        self.update()
        globe.unsaved = True
        self.parent.unsaved_text = True

    def clear(self):
        self.tag_add('sel', '1.0', 'end')
        self.delete('1.0', 'end')
        self.parent.unsaved_text = False
        return 'break'


class TerminalWindow(tk.Toplevel):
    class_name = 'TerminalWindow'

    def __init__(self, parent, output, **kw):
        super().__init__(parent, **kw)
        self.minsize(200, 100)
        self.geometry("400x300")
        self.withdraw()
        self.parent = parent
        self.output = output
        self.title(const.PROGRAM_NAME + " terminal")
        self.iconbitmap(const.ICON_FILE)
        self.protocol('WM_DELETE_WINDOW', self.exit_handler)  # override the Windows "X" button
        self._sendstring = tk.StringVar()
        self.send_list = ['ID?']

        logger.info(" ")
        logger.info(self.class_name + " constructor")
        tk.Grid.rowconfigure(self, 0, weight =1)
        tk.Grid.columnconfigure(self, 0, weight=1)

        send_button_width = 10
        # sendbox_width = self.parent.winfo_width() - send_button_width
        sendbox_width = 30

        self.textbox = TextBox(self, wrap='none', state="normal", undo=1, width=30)
        self.textbox.grid(row=0, column=0, columnspan = 2, sticky='n' + 's' + 'e' + 'w')

        self.send_box = ttk.Combobox(self, textvariable=self._sendstring, values=self.send_list, width=sendbox_width)
        self.send_box.grid(row=1, column=0, padx='5', sticky=tk.W + tk.E + tk.NS)
        self.send_box.bind('<Return>', self.send_button_handler)

        self.button_send = ttk.Button(self, text="send", width=send_button_width,
                                      command=self.send_button_handler)
        self.button_send.grid(row=1, column=1, sticky='w', padx=20)
        self.button_send.bind('<Return>', self.send_button_handler)


    def send_button_handler(self, event=None):
        if globe.dut is None:
            # logger.info("globe.dut is None, so call globe.open_dut()")
            globe.open_dut([globe.serial_port_num], self.textbox, kind = globe.DUTKind.mock)
        if globe.dut is None:
            return
        if globe.dut.port.is_open():
            msg = self._sendstring.get()
            globe.dut.port.write(msg + '\r')
            self.send_box.select_range(0, tk.END)
            self.textbox.append(msg + '\r\n')
            try:
                self.textbox.append(globe.dut.port.read())
            except Exception as e:
                logger.error(e.__class__)
            if msg is None:
                return
            if msg not in self.send_list:
                self.send_list.insert(0, msg)
                self.send_box['values'] = self.send_list
        return 'break'

    def exit_handler(self,event=None):
        self.iconify()

