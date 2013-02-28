#!/usr/bin/python

"CS244 Assignment 3: pFabric"

from time import sleep, time
import termcolor as T
from argparse import ArgumentParser
from scapy.all import *
import socket
import traceback
import struct

def cprint(s, color, cr=True):
    """Print in color
       s: string to print
       color: color to use"""
    if cr:
        print T.colored(s, color)
    else:
        print T.colored(s, color),


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

def toHexString(num):
    return struct.pack('>i', num)

def main():
    "Create flow"

    start = time.time()

    print "HELLO!"
    skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    skt.bind((args.src_ip, args.src_port))
    skt.connect((args.dest_ip, args.dest_port))
    print "SOCKET CONNECTED!"
    for i in xrange(1,args.num_packets+1):
        prio = args.priority
        if prio == None:
            packetsLeft = (args.num_packets - i)
            prio = packetsLeft*args.num_bands/args.max_packets
        print prio
        pkt = ('%02x' % prio).decode('hex')*(args.packet_size-52)
        skt.sendall(pkt)
    skt.close()
    print "SOCKET CLOSED!"
    end = time.time()
    cprint("Everything took %.3f seconds" % (end - start), "yellow")

if __name__ == '__main__':
    try:
        main()
    except:
        print "-"*80
        print "Caught exception.  Cleaning up..."
        print "-"*80
        traceback.print_exc(file=sys.stdout)

