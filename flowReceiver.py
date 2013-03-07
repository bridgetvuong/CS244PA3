#!/usr/bin/python

"CS244 Assignment 3: pFabric"

from time import sleep, time, strftime
import termcolor as T
from argparse import ArgumentParser
import socket
import traceback
import sys

# Parse arguments
parser = ArgumentParser(description="pFabric receiver")

parser.add_argument('--dest-port',
                    help="destination port",
                    type=int,
                    required=True)

parser.add_argument('--packet-size',
                    help="packet size (bytes)",
                    type=int,
                    default=1500)

# Expt parameters
args = parser.parse_args()

def main():

    start = time()

    skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    skt.bind(('', args.dest_port))
    skt.listen(1)
    conn, addr = skt.accept()
    count = 0
    while 1:
        data = conn.recv(args.packet_size - 52) # 52 is IP and TCP header sizes
        if not data: break
        count += 1
        h = ['%02x' % ord(i) for i in data]
    conn.close()
    skt.close()

    end = time()
    print count
    print "%.3f" % end
    sys.stdout.flush()

if __name__ == '__main__':
    try:
        main()
    except:
        print "-"*80
        print "Caught exception.  Cleaning up..."
        print "-"*80
        traceback.print_exc(file=sys.stdout)

