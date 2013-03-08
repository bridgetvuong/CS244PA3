#!/usr/bin/env python
from argparse import ArgumentParser

import glob
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sys
import math

parser = ArgumentParser()
parser.add_argument('-o', '--out',
                    help="Save plot to output file, e.g.: --out plot.png",
                    dest="out",
                    default=None)

parser.add_argument('--dir',
                    help="Directory from which outputs of the sweep are read.",
                    required=True)

parser.add_argument('--refdir',
                    help="Directory from which reference outputs of the sweep are read.",
                    required=True)

parser.add_argument('--bw',
                    help="link bandwidth in Mbps",
                    type=int,
                    default=1000)

parser.add_argument('--delay',
                    help="end-to-end RT delay in us",
                    type=int,
                    default=12)

parser.add_argument('--packet-size',
                    help="packet size in bytes",
                    type=int,
                    default=150)

args = parser.parse_args()

# line 1: number of packets sent or received
# line 2: time
# return: (num packets, time)
def parse_data(filename):
    lines = open(filename, 'r').readlines()
    if len(lines) == 2:
        return (int(lines[0]), float(lines[1]))
    else:
        return (int(lines[0]), float(lines[1]), float(lines[2]))

# TODO: normalize flow completion times
# map load to time
avgBestCompletionTimes = {}
for flowSizeDir in sorted(glob.glob("%s/*/" % args.refdir)):
    flowSize = int(str.split(flowSizeDir, "/")[-2])
    print "=== flowSize = %s ===" % flowSize
    sumCompletionTimes = 0.0
    minBestCompletionTimes = -1
    maxBestCompletionTimes = -1
    numTrials = len(glob.glob("%ssend-*.txt" % flowSizeDir))
    for flowNum in xrange(numTrials):
        sendFile = "%ssend-%d.txt" % (flowSizeDir, flowNum)
        recvFile = "%srecv-%d.txt" % (flowSizeDir, flowNum)
        (numSent, start, end1) = parse_data(sendFile)
        (numRecv, end) = parse_data(recvFile)
        bestPossible = float(numSent) * args.packet_size / (args.bw * 1000000 / 8) + float(args.delay) / 2 / 1000
        completionTime = end1-start
        sumCompletionTimes += completionTime
        if minBestCompletionTimes < 0 or completionTime < minBestCompletionTimes:
            minBestCompletionTimes = completionTime
        if maxBestCompletionTimes < 0 or completionTime > maxBestCompletionTimes:
            maxBestCompletionTimes = completionTime
        print "IDEAL: Flow of size %d took %f to complete" % (numSent, (end1-start))
        #print "=== best possible rate: %f" % (bestPossible)
    avgBestCompletionTimes[flowSize] = (sumCompletionTimes-minBestCompletionTimes-maxBestCompletionTimes) / (numTrials-2)

# TODO: normalize flow completion times
# map load to time
loads = []
avgCompletionTimes = []
for loadDir in sorted(glob.glob("%s/*/" % args.dir)):
    load = str.split(loadDir, "/")
    loadNum = float(load[len(load)-2])
    print "=== Load = %.3f ===" % loadNum
    sumCompletionTimes = 0.0
    nFlows = len(glob.glob("%ssend-*.txt" % loadDir))
    for flowNum in xrange(nFlows):
        sendFile = "%ssend-%d.txt" % (loadDir, flowNum)
        recvFile = "%srecv-%d.txt" % (loadDir, flowNum)
        (numSent, start, end1) = parse_data(sendFile)
        (numRecv, end) = parse_data(recvFile)
        #normalizedCompletionTime = math.log(numSent, 2) * args.delay / 1000000
        #bestPossibleRate = float(args.packet_size) / (float(args.delay) / 1000)
        #bestPossible = float(numSent) * float(args.packet_size) / bestPossibleRate
        #bestPossible = float(numSent) * args.packet_size / (args.bw * 1000000 / 8) + float(args.delay) / 2 / 1000
        bestPossible = avgBestCompletionTimes[numSent]
        sumCompletionTimes += (end1-start) / bestPossible
        print "Flow of size %d took %f to complete, minimum possible %f" % (numSent, (end1-start), bestPossible)
        #print "=== best possible rate: %f" % (bestPossible)
    loads.append(loadNum)
    avgCompletionTimes.append(sumCompletionTimes / nFlows)

print loads
print avgCompletionTimes
plt.plot(loads, avgCompletionTimes, label="minTCP")
plt.legend()
plt.ylabel("Average Flow Completion Time")
plt.xlabel("Load Level")

if args.out:
    print "Saving to %s" % args.out
    plt.savefig(args.out)
else:
    plt.show()