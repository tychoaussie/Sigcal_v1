THIS IS ONLY FOR OLDER OBSPY INSTALLATIONS.
UPDATE YOUR OBSPY to version 10.x by running the following command
at the command prompt:

conda install -c obspy obspy

-----------

This directory contains one file that will fix the css 3.0 file format
in obspy. This will enable obspy to read css files with an 'i4'
format.

You must place this file in a specific directory.

If you have installed Obspy in the Anaconda installation, 
this file must be placed here:

C:\Anaconda\Lib\Site-packages\obspy-0.9.2-py2.7-win-amd64.egg\obspy\css\

Overwrite the exisiting core.py with this file

Delete the file core.pyc

Open Python.

Type "import obspy" to rebuild the compiled python file core.pyc
from the new script.

This hack will enable Obspy to open the i4 data format files.

