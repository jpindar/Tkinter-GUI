# README #

### What is this repository for? ###

* A desktop GUI provided for our customers to control their BBUQ (a variant of the Ultra-Q filter).
* Version 1

### How do I get set up? ###

To run as python you will need:

Python 3.4 (I am sticking with 3.4 since that's the last version that works with WinXP. Yes, some customers still use XP.)
PySerial (https://pypi.python.org/pypi/pyserial)

To 'compile' to a standalone executable:

Pyinstaller spec files are included.
Put the desired source files, including any images, icons etc.,  in a folder named src
Delete any previous build and dist folders
run pyinstaller <name of spec file>


### Who do I talk to? ###

* jpindar@jpindar.com  aka jeannepindar@gmail.com
* TelGaAs Inc.