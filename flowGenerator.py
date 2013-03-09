#!/usr/bin/python

"CS244 Assignment 3: pFabric"

from time import sleep, time
import termcolor as T
from argparse import ArgumentParser
import socket
import traceback
import struct
import math
import sys

# Parse arguments
parser = ArgumentParser(description="Bufferbloat tests")
parser.add_argument('--src-ip',
                    help="source IP",
                    required=True)

parser.add_argument('--src-port',
                    help="source port",
                    type=int,
                    required=True)

parser.add_argument('--dest-ip',
                    help="destination IP",
                    required=True)

parser.add_argument('--dest-port',
                    help="destination port",
                    type=int,
                    required=True)

parser.add_argument('--num-packets',
                    help="number of packets",
                    type=int,
                    required=True)

parser.add_argument('--num-bands',
                    help="number of priority bands",
                    type=int,
                    required=True)

parser.add_argument('--max-packets',
                    help="maximum number of packets",
                    type=int,
                    required=True)

parser.add_argument('--priority',
                    help="set priority for flow",
                    type=int,
                    default=None)

parser.add_argument('--packet-size',
                    help="packet size (bytes)",
                    type=int,
                    default=1500)

# Expt parameters
args = parser.parse_args()
skt = None

def main():
    "Create flow"
    pkts = []
    pkt = ('%02x' % 0).decode('hex')*(args.packet_size-52-1)
    for prio in range(1, 17):
        pkts.append(('%02x' % prio).decode('hex') + pkt)

    # Create socket
    skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    skt.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 10000)
    skt.bind((args.src_ip, args.src_port))
    skt.connect((args.dest_ip, args.dest_port))

    # Print stats
    print args.num_packets
    print "%f" % time()

    # Send packets
    for i in xrange(args.num_packets):
        prio = args.priority
        if prio == None:
            packetsLeft = (args.num_packets - i)
            prio = int(math.floor(math.log(packetsLeft + 1)/math.log(args.max_packets + 1)*args.num_bands))
        #pkt = ('%02x' % prio).decode('hex')*(args.packet_size-52)
        #sendPkt = ('%02x' % prio).decode('hex') + pkt
        skt.sendall(pkts[prio-1])
    skt.close()
    sys.stdout.flush()

if __name__ == '__main__':
    try:
        main()
    except:
        if skt:
            skt.close()
        print "-"*80
        print "Caught exception.  Cleaning up..."
        print "-"*80
        traceback.print_exc(file=sys.stdout)

