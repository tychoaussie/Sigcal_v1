#!/usr/bin/env python

"""
Grid search function for best-fit response curve parameters: free period, damping ratio, and scale factor.
 
"""
###### LA-CC-14-079 ###############################################################
# Author: Hans Hartse, LANL : August, 2014
# Modified by D Burk, Michigan State University
# Version: 20140828
#
# Modification 20140828 : Adjust amplitude calculation to start at 2x freeperiod to 5x freeperiod
# Also correct the path of the plot file output
#
# holds the following functions:
# write_sacpz - write a SAC-style pole-zero file where input is an ObsPy "dictionary"
# find_pole_zero - grid search about MSU measured/estimated response, free-period, and damping factor
# plot_response_curves - plots amplitude and phase curves using best-fit information from grid search
# plot_misfit_results - plot an RMS misfit vs iteration number from grid search

import numpy as np
import matplotlib.pyplot as plt
import os.path
#from obspy 
import obspy.signal.invsim as sim

# write a function that will take obsby resp "dictionary" info
# and create a sac pole-zero file
# add one extra zero for sac pz to declare velocity, rather than displacement




def write_sacpz(fname, resp):

# resp is the obspy data structure holding poles, zeros, and scale factor

    with open(fname,'w') as f:
        f.write("ZEROS {}\n".format(len(resp['zeros']) + 1 ))
        f.write("POLES {}\n".format(len(resp['poles'])))
        for pole in resp['poles']:
            f.write("{:e} {:e}\n".format(pole.real, pole.imag))
        f.write("CONSTANT {:e}".format(resp['gain']))

    spz = "SAC pole-zero file is named %s" % ( fname )
    print ( "\n" )
    print spz

# done with custom sac pz write function "write_sacpz"








# start of function that does a grid search to find a response that best fits the MSU measured response
# function "find_pole_zero"
                              # Input parameters:
                              # freq_msu: List of frequencies of n terms
                              # amp_msu: List of ampltudes at those frequencies (n terms)
                              # seismometer: Seismometer description
                              # msu_freep: Measured Free-period frequency from calibration
                              # msu_damp: Measured damping ratio from calibration
                              # nsearch: Constraint options (0 = fully constrainted,1,2,3 = full grid search)
                              # coarse_search: The step size for grid searching parameters (Typ 0.1)
                              # fine_search: Step size for fine grid searching (typ 0.005)
                              # nloops: Number of iterations to try for best fit (Typ. 4)
                              # ngrids: Total number of grid points within the search to use (typ. 20)
 
def find_pole_zero(freq_msu,amp_msu,seismometer,msu_freep,msu_damp,nsearch,coarse_search,fine_search,nloops,ngrids,lmult,hmult):

# ngrids is the number of grid points to be searched for each parameter, per each "percentage" loop
                        # At nsearch = 3, grid search on amplitude, damping ratio, and free period.
    nfreqs = ngrids
    if ( nsearch < 3 ): # Set flags. Free period is constrained at nsearch = 2
        nfreqs = 1
    ndamps = ngrids
    if ( nsearch < 2 ): # Set flags. Free period & Damping ratio is constrained at nsearch = 1
        ndamps = 1
    nscales = ngrids
    if ( nsearch < 1 ): # set flags. Free period, Damping Ratio, and amplitude are all constrained.
        nscales = 1

# search the grids nloops times, first between coarse_search percent smaller than starting params 
#   and coarse_search percent larger than starting params, then, eventually search only within fine_search percent
#   of the best params found on each previous loop search

    search_range = np.linspace(coarse_search, fine_search, nloops)

# freq_msu is array holding frequency values where MSU made amp measurements
# amp_msu is array holding amplitude values measured by MSU
# note that msu_freep is the MSU estimated freee period in seconds

# now find average amplitude from MSU measurements where freq > 1 Hz
#
# edit: Change the average amplitude calculation to use frequencies greater than 
# 3x the free period frequency but less than 8x the free-period frequency.
# This program calculates only two poles & zeros: Response should be flat within
# this passband and avoids any weird issues at higher frequencies and keeps 
# calculation off the knee of the response curve in cases of high or low damping
# ratios
# - drb 08/28/2014

    count = 0
    amp_average = 0.
    for i, freq in enumerate(freq_msu):
        if ( freq > lmult * msu_freep) and (freq < hmult * msu_freep):  
                                      # Set frequency discriminator to msu_freep * 2 to get off the 
                                      # knee of the curve for SP instruments - drb
           amp_average = amp_average + amp_msu[i] 
           count += 1
    amp_average = amp_average / float(count)

                                      # set preliminary "best parameters"

    best_freep = msu_freep 
    best_damp = msu_damp
    best_scale = amp_average

                                      # best_fit is the RMS misfit between MSU observed 
                                      # and model amplitudes in log10 space,
                                      #    an outrageously large value, initially

    best_fit = 1000000.

                                      # an index counter to keep track of the total number of searches/misfits

    j = 0

                                      # for use with later plotting
                                      # prepare array to hold total number of interation results

    misfits = np.zeros(nscales * ndamps * nfreqs * nloops)

                                      # prepare array to store each iteration number

    misfit_count = np.zeros(nscales * ndamps * nfreqs * nloops)

                                      # start of loops 

    for range in search_range:

                                      # build a list of "corner frequencies" to test
                                      # I think these "corner frequencies" - in ObsPy Speak means 1/free period of seismometer

        freep_adjust = best_freep * range
        fp_long = best_freep + freep_adjust
        fp_short = best_freep - freep_adjust

                                      # the case where free period is held constant at the MSU-supplied value

        if ( nsearch < 3 ):
            fp_long = best_freep
            fp_short = best_freep

                                      # np.linspace will create an array from low_freq to high_freq over nfreqs of even spacing

        corners = np.linspace(1./fp_long, 1./fp_short, nfreqs)
        print ( "\nsearching free periods between %f and %f seconds" % ( fp_long, fp_short ) )

                                      # build a list of damping factors to test

        damp_adjust = best_damp * range
        low_damp = best_damp - damp_adjust 
        high_damp = best_damp + damp_adjust
        if ( high_damp >= 1.0 ):
            print ( "\nwarning - damping factor is %f - must be below 1.0 - setting damping to 0.9999" % ( high_damp ) )
            high_damp = 0.9999
        if ( nsearch < 2 ):
            low_damp = best_damp
            high_damp = best_damp

        damps = np.linspace(low_damp, high_damp, ndamps)
        print ( "searching damping factors between %f and %f" % ( low_damp, high_damp ) )

                                      # build a list of scale factors to test

        scale_adjust = best_scale * range
        low_scale = best_scale - scale_adjust 
        high_scale = best_scale + scale_adjust
        if ( nsearch < 1 ):
            low_scale = best_scale
            high_scale = best_scale
            nscales = 1
        scales = np.linspace(low_scale, high_scale, nscales)
        print ( "searching scale factors between %f and %f" % ( low_scale, high_scale ) )

                                      # here are the grid search loops, over corners, dampings, and scales

        for corner in corners:   
            for damp in damps:
                for scale in scales:

                                      # the key obspy function to find inst resp based on "corner frequency" and damping constant 
                                      # cornFreq2Paz takes an instrument's corner freq and damping factor to produce
                                      #   an Obspy-style paz file

                    resp = sim.cornFreq2Paz(corner, damp) 
                    resp['gain'] = scale
                    amp_predicted = np.zeros_like(freq_msu)
                    for i, freq in enumerate(freq_msu):
                        amp_predicted[i] = sim.paz2AmpValueOfFreqResp(resp, freq) 
    
                    misfit = np.linalg.norm(np.log10(amp_msu) - np.log10(amp_predicted))
                    misfits[j] = misfit
                    misfit_count[j] = j + 1
       
                    if ( misfit < best_fit ):
                       best_fit = misfit
                       best_corner = corner
                       best_damp = damp
                       best_scale = scale
                       best_index = j

                    j = j + 1

                                      # find the best free period, which is 1/best_corner
                                      # this happens at the end of a particlar grid search loop

        best_freep  = 1./best_corner 

                                      # end of all loops

                                      # find poles and zeros using best corner freq, damp and scale 

    resp = sim.cornFreq2Paz(best_corner, best_damp) 
    resp['gain'] = best_scale
    return(resp, best_freep, best_damp, best_scale, amp_average, misfits, misfit_count, best_index) 
                                      # end of function "find_pole_zero"









#
#
                             # start of function "plot_response_curve"
                             # function plot_response_curve
#
#

def plot_response_curves(resp, freq_msu, amp_msu, best_freep, best_damp, best_scale, msu_freep,\
msu_damp, amp_average, amp_label, seismometer, sac_pz_file):

                             # build an array of zeros with same length as freq_msu

    amp_predicted = np.zeros_like(freq_msu)

                             # loop over the frequencies present in the msu data file one at a time
                             # to find the amplitudes predicted for a given frequency 
                             # based on the best resp file

    for i, freq in enumerate(freq_msu):
        amp_predicted[i] = sim.paz2AmpValueOfFreqResp(resp, freq) 

                             # this code taken straight from the Obspy webpage examples 
                             # numbers for obspy to create a resp curve, based on an fft of a time series
                             # with sample rate of 0.01

    samp_rate = 0.01
    npts = 16384

                             # obtain "continuous" amp and freq values from obsby function to display continuous response curve

    poles = resp['poles']
    zeros = resp['zeros']
    h, f = sim.pazToFreqResp(poles, zeros, best_scale, samp_rate, npts, freq=True)

                             # plotting amp vs freq

    plt.figure()

#plt.subplot(121)
                             # plot the continuous response curve, and the msu data, 

    plt.loglog(f, abs(h), freq_msu, amp_msu, 'go', markersize=6 )

                             # plot the predicted amplitudes at the MSU frequencies

    plt.loglog(freq_msu, amp_predicted, 'ro', markersize=4 )

                             # labels

    plt.xlabel('Frequency [Hz]')

                             # this str function is part of the standard Python, no need to "import" a special "package"

    plt.ylabel( str(amp_label) )
    plt.suptitle('Frequency vs Amplitude: Seismometer ' + str(seismometer) )

                             # plot over range from 2/3 * minimum frequency to 2.0 * maximum frequency  
                             # and over range from 2/3 * minimum amplitude to 2.0 * maximum amplitude  

    plx_min = freq_msu[0] * 0.66
    plx_max = freq_msu[len(freq_msu) - 1] * 2.00
    ply_min = amp_msu[0] * 0.66
    ply_max = amp_msu[len(freq_msu) - 1] * 2.00
    plt.axis([plx_min, plx_max, ply_min, ply_max])

    freep_per = 100. * ( abs ( best_freep - msu_freep ) / msu_freep )
    damp_per = 100. * ( abs ( best_damp - msu_damp ) / msu_damp )
    scale_per = 100. * ( abs ( best_scale - amp_average ) / amp_average )

    tfp = "free per = %.3f sec (%.2f%% MSU: %.3f)" % ( best_freep, freep_per, msu_freep )
    print ( "\n" )
    print tfp
    tdr = "damping = %.3f (%.2f%% MSU: %.3f)" % ( best_damp, damp_per, msu_damp )
    print tdr
    tsf = "scale = %.2f (%.2f%% average amp: %.2f)" % ( best_scale, scale_per, amp_average )
    print tsf
    spz = "SAC pole-zero file is named %s" % ( sac_pz_file )

                             # post results as text lines on the plot

    xtext = plx_min * 7.
    ytext = ply_min * 8.
    plt.text( xtext, ytext, tfp )
    ytext = ply_min * 5.
    plt.text( xtext, ytext, tdr )
    ytext = ply_min * 2.8
    plt.text( xtext, ytext, tsf )
    ytext = ply_min * 1.7
    plt.text( xtext, ytext, spz )

                             # post some symbols and text for a legend

    amp_symbol = np.zeros(1)
    amp_symbol[0] = best_scale * 1.0
    freq_symbol = np.zeros(1)
    freq_symbol[0] = freq_msu[0]
    plt.loglog(freq_symbol, amp_symbol, 'go', markersize=6 )
    plt.text( freq_symbol[0] * 1.1, amp_symbol[0], 'Measurment', va='center' )
    amp_symbol[0] = best_scale * 0.70
    freq_symbol[0] = freq_msu[0]
    plt.loglog(freq_symbol, amp_symbol, 'ro', markersize=4 )
    plt.text( freq_symbol[0] * 1.1, amp_symbol[0], 'Model Best Fit', va='center' )
    plt.grid(True, which='major')
    plt.grid(True, which='minor')
    fig = os.getcwd()+"\\"+seismometer + '_freq_v_amp' + '.png' # Place it in current working directory - drb
    txt = "plotted best-fit frequency vs amplitude results - saved in file: %s" % ( fig )
    print "\n"
    print txt
    plt.savefig( fig )

    plt.show()
#    plt.close()


                             # plotting phase vs freq, not sure how much this can be trusted

#plt.subplot(122)

    plt.figure()

                             #take negative of imaginary part

    phase = np.unwrap(np.arctan2(-h.imag, h.real))
    plt.semilogx(f, phase)
    plt.xlabel('Frequency [Hz]')

    plt.ylabel('Phase [radians]')

                             # title, centered above both subplots

    plt.suptitle('Frequency vs Phase: Seismometer ' + str(seismometer) )
    plt.axis([0.004, 100, -3.5, 0.5])

                             # make more room in between subplots for the ylabel of right plot

#plt.subplots_adjust(wspace=0.3)
    plt.grid(True, which='major')
    plt.grid(True, which='minor')
    fig = os.getcwd()+"\\"+ seismometer + '_freq_v_phase' + '.png'
    txt = "plotted best-fit frequency vs phase results - saved in file: %s" % ( fig )
    print "\n"
    print txt
    plt.savefig( fig )
#    plt.show()
#    plt.close()

# end of function plot_response_curves











# start function to plot iteration number vs misfit for grid search work

def plot_misfit_results(misfits,misfit_count,seismometer,best_index):    

# plotting count vs misfit for final grid search 

    misfit_max = np.amax(misfits)
    misfit_min = np.amin(misfits)
    j = len(misfit_count)
    plt.figure()

#plt.subplot(121)

    plt.plot(misfit_count, misfits, 'bo', markersize=4 )
    plt.plot(misfit_count[best_index], misfits[best_index], 'r^', markersize=8 )
    plt.xlabel('Grid Search Interation Count')
    plt.ylabel( 'RMS Misfit in Log10 Space' )
    plt.suptitle('Final Grid Search: Seismometer ' + str(seismometer) )
    plt.axis([-5, j + 5, misfit_min * 0.9, misfit_max * 1.1])
    plt.grid(True, which='major')
    plt.grid(True, which='minor')
    fig = os.cwd()+seismometer + '_misfit' + '.png'
    txt = "plotted rms misfit vs iteration number - saved in file: %s" % ( fig )
    print "\n"
    print txt
    plt.savefig( fig )
    plt.show()
    plt.close()

