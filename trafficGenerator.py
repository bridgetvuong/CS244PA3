#!/usr/bin/python

"CS244 Assignment 3: pFabric"

from time import sleep, time
import termcolor as T
from argparse import ArgumentParser
from scapy.all import *
import socket
import traceback

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

parser.add_argument('--packet-size',
                    help="packet size (bytes)",
                    type=int,
                    default=1500)

# Expt parameters
args = parser.parse_args()

def main():
    "Create flow"

    start = time.time()

    skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    skt.connect((args.dest_ip, args.dest_port))
    flow = StreamSocket(skt)
    for i in xrange(args.num_packets):
        pkt = IP(dst=args.dest_ip, len=args.packet_size)/TCP(dport=args.dest_port)/fuzz(Raw())
        flow.send(pkt)
    skt.close()
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

