# README #

### What is this repository for? ###

This is a desktop GUI provided for our customers to control their BBUQ (a variant of the Ultra-Q filter).



### What else do I need ###

Python 3.4 (We're sticking with 3.4 since that's the last version that works with WinXP, and some customers still use XP.)
TKinter (This is already part of most Python installs.)
PySerial (https://pypi.python.org/pypi/pyserial)
PyCrypt  (https://pypi.org/project/pycrypto/)

### How do I get set up? ###

To run this as python just run main.py

To package this as a standalone executable using PyInstaller:

Put onefile.spec file and build.bat in a folder
In that folder create a folder called src, and put the source code and any images, icons etc. in it
Run build.bat
PyInstaller will put the new .exe in a folder called dist
Rename the exe as desired

### Who do I talk to? ###

written by jpindar@jpindar.com  aka jeannepindar@gmail.com


