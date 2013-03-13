#!/usr/bin/env python
from argparse import ArgumentParser

import glob
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sys
from math import floor
import string

BITS_PER_MEGABIT = 1048576
BITS_PER_BYTE = 8
MILLISECS_PER_SEC = 1000
BYTES_PER_KB = 1024
BYTES_PER_MB = 1048576

parser = ArgumentParser()

parser.add_argument('--dir',
                    help="Directory from which outputs of the sweep are read.",
                    required=True)

parser.add_argument('--scale',
                    help="Scale factor for workload distribution.",
                    type=int,
                    required=True)

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
    if len(lines) is not 4:
        return (None, None, None, None)
    return (int(lines[0]), float(lines[1]), int(lines[2]), float(lines[3]))

# map load to time
for typeDir in sorted(glob.glob("%s/*/" % args.dir)): 
    typeName = typeDir.split('/')[-2]
    print typeName

    loads = []
    avgCompletionTimes = []
    avgCompletionTimesSmall = []
    avgCompletionTimesSmall_99percentile = []
    avgCompletionTimesMed = []
    avgCompletionTimesLarge = []
    for loadDir in sorted(glob.glob("%s/*/" % typeDir)):
        load = str.split(loadDir, "/")
        loadNum = float(load[-2])
        print "=== Load = %.3f ===" % loadNum

        completionTimesSmall = []
        sumCompletionTimes = 0.0
        sumCompletionTimesSmall = 0.0
        sumCompletionTimesMed = 0.0
        sumCompletionTimesLarge = 0.0
        numSmall = 0
        numMed = 0
        numLarge = 0
        for sendFile in glob.glob("%ssend-*-*.txt" % loadDir):

            (numSent, start, numReceived, end) = parse_data(sendFile)
            if numSent == None or numReceived == None:
                # Skip this data point
                continue
            if numSent != numReceived:
                continue

            bestPossible = float(numSent) * args.packet_size / (args.bw * BITS_PER_MEGABIT / BITS_PER_BYTE) + float(args.delay) / 2 / MILLISECS_PER_SEC
            normalizedFCT = (end-start) / bestPossible
            sumCompletionTimes += normalizedFCT
            if numSent < (100*BYTES_PER_KB/args.packet_size)/float(args.scale): # 100 KB
                sumCompletionTimesSmall += normalizedFCT
                numSmall += 1
                completionTimesSmall.append(normalizedFCT)
            elif numSent < (19*BYTES_PER_MB/args.packet_size)/float(args.scale): # 10 MB
                sumCompletionTimesMed += normalizedFCT
                numMed += 1
            else:
                sumCompletionTimesLarge += normalizedFCT
                numLarge += 1
                
            #print "Flow of size %d took %f to complete, minimum possible %f" % (numSent, (end-start), bestPossible)
        loads.append(loadNum)
        avgCompletionTimes.append(sumCompletionTimes / (numSmall + numMed + numLarge))
        avgCompletionTimesSmall.append(sumCompletionTimesSmall / numSmall)
        completionTimesSmall_99percentile = sorted(completionTimesSmall)[int(floor(0.99*numSmall)):]
        avgCompletionTimesSmall_99percentile.append(sum(completionTimesSmall_99percentile) / len(completionTimesSmall_99percentile))
        avgCompletionTimesMed.append(sumCompletionTimesMed / numMed)
        avgCompletionTimesLarge.append(sumCompletionTimesLarge / numLarge)

    print loads
    print avgCompletionTimes
    print avgCompletionTimesSmall
    print avgCompletionTimesSmall_99percentile
    print avgCompletionTimesMed
    print avgCompletionTimesLarge

    type = typeName
    if (type == "minTCP"):
        type += "+pFabric"
    plt.figure(1)
    plt.plot(loads, avgCompletionTimes, label=type)
    plt.figure(2, figsize=(28,5))
    plt.subplot(141)
    plt.plot(loads, avgCompletionTimesSmall, label=type)
    plt.subplot(142)
    plt.plot(loads, avgCompletionTimesSmall_99percentile, label=type)
    plt.subplot(143)
    plt.plot(loads, avgCompletionTimesMed, label=type)
    plt.subplot(144)
    plt.plot(loads, avgCompletionTimesLarge, label=type)

plt.figure(1)
plt.legend(loc=2)
plt.ylabel("Average Flow Completion Time")
plt.xlabel("Load Level")

plt.figure(2, figsize=(28,5))
plt.subplot(141)
plt.legend(loc=2)
plt.ylabel("Average Flow Completion Time")
plt.xlabel("Load Level")
plt.title("(0, %.1fKB]: Avg" % (100.0/float(args.scale)))

plt.subplot(142)
plt.legend(loc=2)
plt.ylabel("Average Flow Completion Time")
plt.xlabel("Load Level")
plt.title("(0, %.1fKB]: 99th percentile" % (100.0/float(args.scale)))

plt.subplot(143)
plt.legend(loc=2)
plt.ylabel("Average Flow Completion Time")
plt.xlabel("Load Level")
plt.title("(%.1fKB, %.1fMB]: Avg" % (100.0/float(args.scale), 10.0/float(args.scale)))

plt.subplot(144)
plt.legend(loc=2)
plt.ylabel("Average Flow Completion Time")
plt.xlabel("Load Level")
plt.title("(%.1fMB, infinity): Avg" % (10.0/float(args.scale)))

plt.figure(1)
print "Saving to %s/total.png" % args.dir
plt.savefig("%s/total.png" % args.dir)

plt.figure(2)
print "Saving to %s/breakdown.png" % args.dir
plt.savefig("%s/breakdown.png" % args.dir)
