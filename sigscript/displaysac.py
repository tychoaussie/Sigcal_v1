# Version 20150806
# This simple code will display a single trace in formats of SAC, CSS, Miniseed
# with basic units, and in terms of seconds.
# It will open only the first trace within the stream. 

import sys # numpy as np, csv, time, string
import pylab as plt
from obspy.core import read, Trace, Stream, UTCDateTime
from obspy.sac import SacIO

# simple plotting program for plotting sac or miniseed files
# only one command line option: The file name.
# Use wildcards to import multiple streams thus:
# python sacdisplay.py c:/seismo/00000158_*.sac

infile = sys.argv[1]

st = read(infile)
CH0 = st[0].data
i = []
i.extend(range(0,len(st[0].data)))
i[:] = [x / st[0].stats.sampling_rate for x in i]

plt.plot(i,CH0, '-b', label = "Waveform of counts vs seconds")

plt.xlabel("Seconds")
plt.ylabel("Counts")
plt.show()

st[0].plot(number_of_ticks = 48, tick_format='%M:%S',tick_rotation = 90, color = 'blue')


