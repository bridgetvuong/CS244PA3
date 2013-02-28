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
parser = ArgumentParser(description="pFabric receiver")

parser.add_argument('--dest-port',
                    help="destination port",
                    type=int,
                    required=True)

# Expt parameters
args = parser.parse_args()

def main():
    "Create flow"

    start = time.time()

    skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    skt.bind(('', args.dest_port))
    skt.listen(1)
    conn, addr = skt.accept()
    while 1:
        data = conn.recv(1500 - 52) # Packet size - IP and TCP header sizes
        if not data: break
        h = ['%02x' % ord(i) for i in data]
        print string.join(h)
        print 
        print len(data)
        print 
    conn.close()
    skt.close()

    end = time.time()
    cprint("Finished receiving at time %.3f" % (end), "yellow")
    cprint("Everything took %.3f seconds" % (end - start), "yellow")

if __name__ == '__main__':
    try:
        main()
    except:
        print "-"*80
        print "Caught exception.  Cleaning up..."
        print "-"*80
        traceback.print_exc(file=sys.stdout)

