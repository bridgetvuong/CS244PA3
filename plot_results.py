#!/usr/bin/env python
from argparse import ArgumentParser

import glob
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sys
import math
import string

BITS_PER_MEGABIT = 1000000
BITS_PER_BYTE = 8
MILLISECS_PER_SEC = 1000

parser = ArgumentParser()
parser.add_argument('-o', '--out',
                    help="Save plot to output file, e.g.: --out plot.png",
                    dest="out",
                    default=None)

parser.add_argument('--dir',
                    help="Directory from which outputs of the sweep are read.",
                    required=True)

#parser.add_argument('--refdir',
#                    help="Directory from which reference outputs of the sweep are read.",
#                    required=True)

parser.add_argument('--bw',
                    help="link bandwidth in Mbps",
                    type=int,
                    default=100)

parser.add_argument('--delay',
                    help="end-to-end RT delay in ms",
                    type=int,
                    default=0)

parser.add_argument('--packet-size',
                    help="packet size in bytes",
                    type=int,
                    default=1500)

args = parser.parse_args()

# line 1: number of packets sent or received
# line 2: time
# return: (num packets, time)
def parse_data(filename):
    lines = open(filename, 'r').readlines()
    if len(lines) is not 2:
        return (None, None)
    return (int(lines[0]), float(lines[1]))

# TODO: normalize flow completion times
# map load to time
"""
avgBestCompletionTimes = {}
for flowSizeDir in sorted(glob.glob("%s/*/*/" % args.refdir)):
    print flowSizeDir
    flowSize = int(str.split(flowSizeDir, "/")[-2])
    print "=== flowSize = %s ===" % flowSize
    sumCompletionTimes = 0.0
    completionTimes = []
    numTrials = len(glob.glob("%ssend-*.txt" % flowSizeDir))
    for flowNum in xrange(numTrials):
        sendFile = "%ssend-%d.txt" % (flowSizeDir, flowNum)
        recvFile = "%srecv-%d.txt" % (flowSizeDir, flowNum)
        (numSent, start, end1) = parse_data(sendFile)
        (numRecv, end) = parse_data(recvFile)
        bestPossible = float(numSent) * args.packet_size / (args.bw * 1000000 / 8) + float(args.delay) / 2 / 1000
        completionTime = end1-start
        completionTimes.append(completionTime)
        sumCompletionTimes += completionTime
        #print "IDEAL: Flow of size %d took %f to complete" % (numSent, (end1-start))
        #print "=== best possible rate: %f" % (bestPossible)
    avgBestCompletionTimes[flowSize] = sum(sorted(completionTimes)[1:-1]) / (numTrials - 2)
"""

# TODO: normalize flow completion times
# map load to time
for typeDir in sorted(glob.glob("%s/*/" % args.dir)): 
    typeName = typeDir.split('/')[-2]
    print typeName

    loads = []
    avgCompletionTimes = []
    for loadDir in sorted(glob.glob("%s/*/" % typeDir)):
        load = str.split(loadDir, "/")
        loadNum = float(load[-2])
        print "=== Load = %.3f ===" % loadNum

        completionTimes = []
        sumCompletionTimes = 0.0
        numGoodFlows = 0.0
        for sendFile in glob.glob("%ssend-*-*.txt" % loadDir):
            recvFile = string.replace(sendFile, 'send', 'recv')
            if len(glob.glob(recvFile)) is 0:
                continue
            (numSent, start) = parse_data(sendFile)
            if numSent == None:
                # Error occured. Skip this data point
                continue
            (numReceived, end) = parse_data(recvFile)
            if numReceived == None:
                continue
            numGoodFlows += 1
            #normalizedCompletionTime = math.log(numSent, 2) * args.delay / 1000000
            #bestPossibleRate = float(args.packet_size) / (float(args.delay) / 1000)
            #bestPossible = float(numSent) * float(args.packet_size) / bestPossibleRate
            bestPossible = float(numSent) * args.packet_size / (args.bw * BITS_PER_MEGABIT / BITS_PER_BYTE) + float(args.delay) / 2 / 1000
            #bestPossible = avgBestCompletionTimes[numSent]
            normalizedFCT = (end-start) / bestPossible
            sumCompletionTimes += normalizedFCT
            completionTimes.append(normalizedFCT)
            if end-start < 0:
                print numSent, numReceived
            print "Flow of size %d took %f to complete, minimum possible %f" % (numSent, (end-start), bestPossible)
            #print "=== best possible rate: %f" % (bestPossible)
        loads.append(loadNum)
        # take out bottom 2 and top 2
        #print sorted(completionTimes)
        avgCompletionTime = sum(sorted(completionTimes)) / (numGoodFlows)
        avgCompletionTimes.append(avgCompletionTime)

    print loads
    print avgCompletionTimes
    plt.plot(loads, avgCompletionTimes, label=typeName)
plt.legend()
plt.ylabel("Average Flow Completion Time")
plt.xlabel("Load Level")

if args.out:
    print "Saving to %s" % args.out
    plt.savefig(args.out)
else:
    plt.show()
