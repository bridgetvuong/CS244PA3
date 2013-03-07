#!/usr/bin/env python
from argparse import ArgumentParser

import glob
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sys

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
    sumCompletionTimes = 0.0
    for flowNum in xrange(args.nflows):
        print "Parsing flow %d" % flowNum
        sendFile = "%ssend-%d.txt" % (loadDir, flowNum)
        recvFile = "%srecv-%d.txt" % (loadDir, flowNum)
        (numSent, start) = parse_data(sendFile)
        (numRecv, end) = parse_data(recvFile)
        sumCompletionTimes += (end-start)
    load = str.split(loadDir, "/")
    loads.append(float(load[len(load)-2]))
    avgCompletionTimes.append(sumCompletionTimes / args.nflows)

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
