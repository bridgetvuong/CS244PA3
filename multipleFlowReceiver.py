import select 
import socket 
import sys 
import threading 
from time import time
from argparse import ArgumentParser
import traceback

# Parse arguments
parser = ArgumentParser(description="pFabric receiver")

parser.add_argument('--time',
                    help="number of seconds to run",
                    type=int,
                    default=6000)

parser.add_argument('--output-dir',
                    help="output directory",
                    required=True)

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

class Server: 
    def __init__(self): 
        self.host = '' 
        self.port = args.dest_port 
        self.backlog = 128
        self.size = args.packet_size - 52
        self.server = None 
        self.threads = [] 

    def open_socket(self): 
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 15000000)
            self.server.bind((self.host,self.port))
            self.server.listen(self.backlog)
        except: 
            if self.server: 
                self.server.close() 
            print "*"*80
            print "Caught exception."
            print "*"*80
            traceback.print_exc(file=sys.stdout)
            sys.exit(1) 

    def run(self):
        self.open_socket()
        print args.time
        start = time()
        while time() - start < args.time: 
            inputready,outputready,exceptready = select.select([self.server],[],[]) 

            for s in inputready: 

                if s == self.server: 
                    # handle the server socket 
                    c = Client(self.server.accept()) 
                    c.start() 
                    self.threads.append(c) 

        # close all threads 

        self.server.close() 
        for c in self.threads: 
            c.join() 

class Client(threading.Thread): 
    def __init__(self,(client,address)): 
        threading.Thread.__init__(self) 
        self.client = client 
        self.address = address 
        self.size = args.packet_size - 52

    def run(self):
        count = 0
        while 1: 
            data = self.client.recv(self.size) 
            if data: 
                count += 1
            else: break
        end = time()
        outfile = open("%s/recv-%s-%d.txt" % (args.output_dir, self.address[0], self.address[1]), 'w+')
        outfile.write(str(count) + '\n')
        outfile.write(str(end) + '\n')
        self.client.close() 


if __name__ == "__main__": 
    print "HI"
    s = Server()
    print "HI AGAIN" 
    s.run()
    print "HI LASTLY"