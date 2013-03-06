#!/usr/bin/python

"CS244 Assignment 3: pFabric"

from time import sleep, time, strftime
import termcolor as T
from argparse import ArgumentParser
from scapy.all import *
import socket
import traceback

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

    start = time.time()

    print "HELLO!"
    skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    skt.bind(('', args.dest_port))
    skt.listen(1)
    conn, addr = skt.accept()
    print "CONNECTION ACCEPTED!"
    count = 0
    while 1:
        data = conn.recv(args.packet_size - 52) # 52 is IP and TCP header sizes
        if not data: break
        count += 1
        h = ['%02x' % ord(i) for i in data]
        print '%s x %d' % (h[0], len(data))
    print "Received %d packets" % (count)
    conn.close()
    skt.close()

    end = time.time()
    print "END TIME: %.3f" % end
    print "Everything took %.3f seconds" % (end - start)

if __name__ == '__main__':
    try:
        main()
    except:
        print "-"*80
        print "Caught exception.  Cleaning up..."
        print "-"*80
        traceback.print_exc(file=sys.stdout)

