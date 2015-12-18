# Version 20150806
# This simple code will display a single trace in formats of SAC, CSS, Miniseed
# with basic units, and in terms of seconds.
# It will open only the first trace within the stream. 

# Now, the most important part -- The legalese:
# COPYRIGHT  BOARD OF TRUSTEES OF MICHIGAN STATE UNIVERSITY
# ALL RIGHTS RESERVED

# PERMISSION IS GRANTED TO USE, COPY, COMBINE AND/OR MERGE, CREATE DERIVATIVE
# WORKS AND REDISTRIBUTE THIS SOFTWARE AND SUCH DERIVATIVE WORKS FOR ANY PURPOSE,
# SO LONG AS THE NAME OF MICHIGAN STATE UNIVERSITY IS NOT USED IN ANY ADVERTISING
# OR PUBLICITY PERTAINING TO THE USE OR DISTRIBUTION OF THIS SOFTWARE WITHOUT 
# SPECIFIC, WRITTEN PRIOR AUTHORIZATION.  IF THE ABOVE COPYRIGHT NOTICE OR ANY
# OTHER IDENTIFICATION OF MICHIGAN STATE UNIVERSITY IS INCLUDED IN ANY COPY OF 
# ANY PORTION OF THIS SOFTWARE, THEN THE DISCLAIMER BELOW MUST ALSO BE INCLUDED.

# THIS SOFTWARE IS PROVIDED AS IS, WITHOUT REPRESENTATION FROM MICHIGAN STATE
# UNIVERSITY AS TO ITS FITNESS FOR ANY PURPOSE, AND WITHOUT WARRANTY BY MICHIGAN
# STATE UNIVERSITY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT
# LIMITATION THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE.

# THE MICHIGAN STATE UNIVERSITY BOARD OF TRUSTEES SHALL NOT BE LIABLE FOR ANY
# DAMAGES, INCLUDING SPECIAL, INDIRECT, INCIDENTAL, OR CONSEQUENTIAL DAMAGES,
# WITH RESPECT TO ANY CLAIM ARISING OUT OF OR IN CONNECTION WITH THE USE OF
# THE SOFTWARE, EVEN IF IT HAS BEEN OR IS HEREAFTER ADVISED OF THE POSSIBILITY
# OF SUCH DAMAGES.

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


