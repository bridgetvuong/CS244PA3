#!/usr/bin/env python
from argparse import ArgumentParser

import glob
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sys
import math

BITS_PER_MEGABIT = 1000000
BITS_PER_BYTE = 8
MICROSECS_PER_SEC = 1000000

parser = ArgumentParser()
parser.add_argument('-o', '--out',
                    help="Save plot to output file, e.g.: --out plot.png",
                    dest="out",
                    default=None)

parser.add_argument('--dir',
                    help="Directory from which outputs of the sweep are read.",
                    required=True)

parser.add_argument('--nflows',
                    help="Number of flows per load",
                    type=int,
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
                    default=1500)

args = parser.parse_args()

# line 1: number of packets sent or received
# line 2: time
# return: (num packets, time)
def parse_data(filename):
    lines = open(filename, 'r').readlines()
    return (int(lines[0]), float(lines[1]))

# TODO: normalize flow completion times
# map load to time
loads = []
avgCompletionTimes = []
for loadDir in sorted(glob.glob("%s/*/" % args.dir)):
    load = str.split(loadDir, "/")
    loadNum = float(load[len(load)-2])
    print "=== Load = %.3f ===" % loadNum
    sumCompletionTimes = 0.0
    for flowNum in xrange(args.nflows):
        sendFile = "%ssend-%d.txt" % (loadDir, flowNum)
        recvFile = "%srecv-%d.txt" % (loadDir, flowNum)
        (numSent, start) = parse_data(sendFile)
        (numRecv, end) = parse_data(recvFile)
        #normalizedCompletionTime = math.log(numSent, 2) * args.delay / 1000000
        bestPossible = float(numSent) * args.packet_size / (args.bw * BITS_PER_MEGABIT / BITS_PER_BYTE) + float(args.delay) / 2 / MICROSECS_PER_SEC
        sumCompletionTimes += (end-start) / bestPossible
        print "Flow of size %d took %f to complete, minimum possible %f" % (numSent, (end-start), bestPossible)
    loads.append(loadNum)
    avgCompletionTimes.append(sumCompletionTimes / float(args.nflows))

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
