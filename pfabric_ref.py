#!/usr/bin/python

"CS244 Assignment 3: pFabric"

from mininet.topo import Topo
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.log import lg, setLogLevel
from mininet.util import dumpNodeConnections
from mininet.cli import CLI

from argparse import ArgumentParser
from multiprocessing import Process
from signal import SIGTERM
from subprocess import call, Popen, PIPE
from time import sleep, time

import os
import random
import sys
import termcolor

from workload import Workload
from pFabricTopo import pFabricTopo

# Number of priorities supported
NUM_PRIO_BANDS = 16

def cprint(s, color, cr=True):
    """Print in color
       s: string to print
       color: color to use"""
    if cr:
        print termcolor.colored(s, color)
    else:
        print termcolor.colored(s, color),


# Parse arguments
parser = ArgumentParser(description="pFabric tests")

parser.add_argument('--outputdir',
                    help="output directory",
                    required=True)

parser.add_argument('--workload',
                    help="workload distribution file",
                    required=True)

parser.add_argument('--tcp',
                    help="'TCP' or 'minTCP'",
                    required=True)

parser.add_argument('--bw',
                    help="link bandwidth in Mbps",
                    type=int,
                    default=1000)

parser.add_argument('--delay',
                    help="end-to-end RT delay in us",
                    type=int,
                    default=12)

parser.add_argument('--nhosts',
                    help="number of hosts",
                    type=int,
                    default=2)

parser.add_argument('--packet-size',
                    help="packet size in bytes",
                    type=int,
                    default=150)

parser.add_argument('--nruns',
                    help="number of runs to average",
                    type=int,
                    default=10)

# Expt parameters
args = parser.parse_args()

hostNames = []

def main():
    "Create network and run pFabric experiment"

    if args.tcp != 'minTCP' and args.tcp != 'TCP':
        print "Bad TCP argument."
        exit(1)

    os.system("mkdir %s" % args.outputdir)
    os.system("mkdir %s/%s" % (args.outputdir, args.tcp))

    start = time()

    # Initialize workload
    workload  = Workload(args.workload)

    # Reset to known state
    usePFabric = (args.tcp == "minTCP")
    topo = pFabricTopo(n=args.nhosts, bw=args.bw, delay=args.delay, usepFabric=usePFabric, numPrioBands=NUM_PRIO_BANDS)
    #setLogLevel('debug')
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()

    dumpNodeConnections(net.hosts)
    net.pingAll()

    # Configure TCP to use reno and disable advanced features
    tcpConfigCmd = "sudo ./tcpconfig/%sConfig.sh" % args.tcp
    call(tcpConfigCmd, shell=True)

    # tcpdump at both hosts
    tcpdumpCmd = "sudo tcpdump -n -x > %s/%s/%%s" % (args.outputdir, args.tcp)
    hosts = net.hosts
    for host in hosts:
        host.popen(tcpdumpCmd % ("tcpdump-%s.txt" % host.name), shell=True)

    # Send flows
    flowReceiveCmd = "sudo python flowReceiver.py --dest-port %%d --packet-size %%d > %s/%s/%%d/%%s" % (args.outputdir, args.tcp)
    flowStartCmd = "sudo python flowGenerator.py --src-ip %%s --src-port %%d --dest-ip %%s --dest-port %%d --num-packets %%d --num-bands %%d --max-packets %%d --packet-size %%d > %s/%s/%%d/%%s" % (args.outputdir, args.tcp)

    for flowSize in workload.getAllFlowSizes():
        print "===== Starting flow size %d" % flowSize
        os.system("mkdir %s/%s/%d" % (args.outputdir, args.tcp, flowSize))

        # Choose random receiver and start receiving
        for i in xrange(args.nruns):
            dest = hosts[random.randrange(args.nhosts)]
            destPort = random.randrange(1025, 9999)
            wait = dest.popen(flowReceiveCmd  % (destPort, args.packet_size, flowSize, "recv-%d.txt" % (i)), shell=True)

            sleep(5)

            # Choose random sender and flow size according to distribution
            src = hosts[random.randrange(args.nhosts)]
            srcPort = random.randrange(1025, 9999)

            print "   Sending %d packets from %s:%d to %s:%d" % (flowSize, src.name, srcPort, dest.name, destPort)
            src.popen(flowStartCmd % (src.IP(), srcPort, dest.IP(), destPort, flowSize, NUM_PRIO_BANDS,
                                      workload.getMaxFlowSize(), args.packet_size, flowSize, "send-%d.txt" % (i)), shell=True)

            wait.communicate()

    #CLI(net)
    net.stop()

    # Reset to normal TCP
    tcpConfigCmd = "sudo ./tcpconfig/TCPConfig.sh"
    call(tcpConfigCmd, shell=True)
    print "TCP reset"

    end = time()
    cprint("Everything took %.3f seconds" % (end - start), "yellow")

if __name__ == '__main__':
    try:
        main()
    except:
        print "-"*80
        print "Caught exception.  Cleaning up..."
        print "-"*80
        import traceback
        traceback.print_exc()
        os.system("killall -9 top bwm-ng tcpdump cat mnexec iperf; mn -c")

