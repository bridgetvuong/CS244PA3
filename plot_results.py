#!/usr/bin/env python
from util.helper import *
import glob
import sys
from collections import defaultdict

parser = argparse.ArgumentParser()
parser.add_argument('-o', '--out',
                    help="Save plot to output file, e.g.: --out plot.png",
                    dest="out",
                    default=None)

parser.add_argument('--dir',
                    dest="dir",
                    help="Directory from which outputs of the sweep are read.",
                    required=True)

parser.add_argument('--nflows',
                    dest="nflows",
                    help="Number of flows per load",
                    required=True)

args = parser.parse_args()

# line 1: number of packets sent or received
# line 2: time
# return: (num packets, time)
def parse_data(filename):
    lines = open(filename).readLines()
    return (int(lines[0]), float(lines[1]))

# TODO: normalize flow completion times
# map load to time
loads = []
avgCompletionTimes = []
for loadName in glob.glob("%s/*"):
    sumCompletionTimes = 0
    for flowNum in xrange(args.nflows):
        print "Parsing flow %d" % flowNum
        sendFile = glob.glob("%s/%s/send-%d.txt" % (args.dir, loadName, flowNum))[0]
        recvFile = glob.glob("%s/%s/recv-%d.txt" % (args.dir, loadName, flowNum))[0]
        (numSent, start) = parse_data(sendFile)
        (numRecv, end) = parse_data(sendFile)
        sumCompletionTimes += (end-start)
    loads.append(float(loadName))
    avgCompletionTimes.append(sumCompletionTimes / args.nflows)

plt.plot(loads, avgCompletionTimes, label="Average Flow Completion Times")
#plt.legend()
plt.ylabel("Average Flow Completion Time")
plt.xlabel("Load Level")

if args.out:
    print "Saving to %s" % args.out
    plt.savefig(args.out)
else:
    plt.show()
