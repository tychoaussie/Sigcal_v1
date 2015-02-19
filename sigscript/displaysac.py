import sys, # numpy as np, csv, time, string
import pylab as plt
from obspy.core import read, Trace, Stream, UTCDateTime
from obspy.sac import SacIO

# simple plotting program for plotting sac or miniseed files
# only one command line option: The file name.
# Use wildcards to import multiple streams thus:
# python sacdisplay.py c:/seismo/00000158_*.sac

infile = sys.argv[1]

st = read(infile)

print(st)
st.plot(color='gray',tick_format='%I:%M %p')
