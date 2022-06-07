# README #

### What is this repository for? ###

This is a simple desktop GUI which could be used to control a serial device.

### What else do I need ###

Python 3.4 or newer
TKinter (This is already part of most Python installs.)
PySerial (https://pypi.python.org/pypi/pyserial)
PyCrypt  (https://pypi.org/project/pycrypto/)

### How do I get set up? ###

To run this as python just run main.py

To package this as a standalone executable using PyInstaller:

Put onefile.spec and build.bat in a folder
In that folder create a folder called src, and put the source code and any images, icons etc. in it
Run build.bat
PyInstaller will put the new .exe in a folder called dist
Rename the exe as desired

### Who do I talk to? ###

written by jpindar@jpindar.com

