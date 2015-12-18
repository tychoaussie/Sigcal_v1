__author__ = "Daniel Burk <burkdani@msu.edu>"
__version__ = "20151204"
__license__ = "MIT"


import os
import sys
# import obspy
from obspy.iris import Client
import numpy as np
from obspy import UTCDateTime
from obspy.taup import TauPyModel
client = Client()



class phaselist(object):
    '''Phaselist is a program for listing out the phases and predicted arrival times between a 
       published event origin time, hypocenter and station location.
       Right now, we have to explicitly type in the station location coordinates but
       in future versions, I want to pull them from a station location file like what is found
       within the c:/EVENTCAT/locations directory.


       Syntax: phaselist ORIGIN_TIME STLAT STLON EVLAT EVLON EVDEPTH 
       where,
            ORIGINTIME is of the format: yyyy-mm-ddTHH:MM:SS (note the letter T)
            STLAT,EVLAT is of format dd.00000 where dd is positive for positive latittudes 
            STLON,EVLON is of format ddd.0000 where ddd is positive for longitudes to the east
            of zero degrees longitude
            EVDEPTH is listed in kilometers. Positive values point down into the earth.

       

       Typical useage:
       C:\Anaconca\sigscript> phaselist 2015-11-30T09:49:13 42.74695 -84.39015 36.737 -98.006 5.00
 

    '''

                 # Function getoptions:
                 # Retrieve any command line options and populate the initial conditions. 
                 # If initial conditions are not met, or fail in any way, prompt the user
                 # to fill in the initial conditions.
                 # Return the option list to the program, consisting of the origin time,
                 # station coordinates, event coordinates, and event depth.                    
def getoptions():

    try:
        OT = sys.argv[1]
        stlat = float(sys.argv[2])
        stlon = float(sys.argv[3])
        evlat = float(sys.argv[4])
        evlon = float(sys.argv[5])
        depth = float(sys.argv[6])
    except:
                      # Enter the parameters
        print "Either no command line options were entered, or one of them was incorrect."
        OT = raw_input('Enter origin time in format yyyy-mm-ddTHH:MM:SS > ') 
        stlat = float(raw_input('Enter the station latitude. > '))
        stlon = float(raw_input('Enter the station longitude. > '))
        evlat = float(raw_input('Enter the event latitude. > '))
        evlon = float(raw_input('Enter the event longitude. > '))
        depth = float(raw_input('Enter the event depth. > '))


    return(OT,stlat,stlon,evlat,evlon,depth)





def main():
                                      #           MAIN PROGRAM BODY
    OT,stlat,stlon,evlat,evlon,depth = getoptions()
    origin_time = UTCDateTime(str(OT))
    result = client.distaz(stalat=stlat, stalon=stlon, evtlat=evlat,evtlon=evlon)
    model = TauPyModel(model="AK135")
    arrivals = model.get_travel_times(source_depth_in_km=depth,distance_in_degree=result['distance'])#,
                                     #phase_list = ['P','PcP','PP','PKiKP','S','SS','ScS','SKiKS'])
    print "Distance = {0:.1f} arc degrees.".format(result['distance'])
    print "{0:.0f} Km distance.".format(result['distance']*111.25)
    print "{0:.0f} deg back Azimuth.".format(result['backazimuth'])
    table = client.traveltime(evloc=(evlat,evlon),staloc=[(stlat,stlon)],evdepth=depth)
    print "Selected phase list:\n"
    print (table.decode())

                   #   Print the phases, travel time and forecasted arrival time.
    phasename = []
    phasetime = []
    arrivaltime = []
    print "For origin time {}, ".format(origin_time)
    print "TauP big list of phases and arrival times:"
    for i in range(0,len(arrivals)):
        phasename.append(arrivals[i].name)
        phasetime.append(arrivals[i].time)
        at = origin_time+(arrivals[i].time)
        arrivaltime.append(at)
        print 'Phase: {0} \t arrives in {1:.2f} sec. at time {2:02.0f}:{3:02.0f}:{4:02.0f}.{5:02.0f}' \
              .format(arrivals[i].name,arrivals[i].time,at.hour,at.minute,at.second,at.microsecond/10000)
    arrivalpaths = model.get_ray_paths(source_depth_in_km=depth,distance_in_degree=result['distance'])#,\
                                #        phase_list = ['P','PcP','PP','PKiKP','S','SS','ScS','SKiKS'])
    arrivalpaths.plot()

 

#
# Check and run the main function here:
#
if __name__ == '__main__':
  main()
 