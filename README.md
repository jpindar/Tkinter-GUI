# README #

### What is this repository for? ###

BBUQGUI is a desktop GUI provided for our customers to control their BBUQ (a variant of the Ultra-Q filter).

Copyright TelGaAS Inc. 2018

### What else do I need ###

Python 3.4 (We're sticking with 3.4 since that's the last version that works with WinXP, and some customers still use XP.)  
TKinter (This is already part of most Python installs.)  
PySerial (https://pypi.python.org/pypi/pyserial)
PyCrypt  (https://pypi.org/project/pycrypto/)

### How do I get set up? ###

To run this as python just run main.py

To package this as a standalone executable:

Pyinstaller spec files are included
Put the desired source files, including any images, icons etc.,  in a folder named src  
Delete any previous build and dist folders  
Run pyinstaller <name of spec file>  

### Who do I talk to? ###

written by jpindar@jpindar.com  aka jeannepindar@gmail.com

copyright TelGaAs Inc.  http://telgaas.com/
