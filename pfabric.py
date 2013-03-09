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
                    default=100)

parser.add_argument('--delay',
                    help="end-to-end RT delay in ms",
                    type=int,
                    default=0)

parser.add_argument('--nhosts',
                    help="number of hosts",
                    type=int,
                    default=2)

parser.add_argument('--packet-size',
                    help="packet size in bytes",
                    type=int,
                    default=1500)

parser.add_argument('--nflows-per-host',
                    help="number of flows per host",
                    type=int,
                    default=100)

parser.add_argument('--dest-file',
                    help="file with host info",
                    default="receivers")

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
#    for host in hosts:
#        host.popen(tcpdumpCmd % ("tcpdump-%s.txt" % host.name), shell=True)

    # Send flows
    outputDir = "%s/%s" % (args.outputdir, args.tcp)
    flowReceiveCmd = "sudo python flowReceiver.py --dest-port %%d --packet-size %%d > %s/%%s/%%s" % (outputDir)
    flowStartCmd = "sudo python multipleFlowGenerator.py --src-ip %%s --num-bands %%d --packet-size %%d --workload %%s --dest-file %%s --bw %%d --load %%f --nflows %%d --output-dir %s/%%.1f > %s/%%.1f/%%s" % (outputDir, outputDir)

    for load in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
        random.seed(1234568)
        print "===== Starting load level %.1f" % load
        os.system("mkdir %s/%s/%.1f" % (args.outputdir, args.tcp, load))
        portNum = 1025

        receivers = []
        waitList = []
        # Choose random receiver and start receiving
        for src in hosts:
            outfile = open("receivers-%s.txt" % src.name, 'w+')
            for i in xrange(args.nflows_per_host):
                dest = hosts[len(hosts)-1]#hosts[random.randrange(args.nhosts)]
                destPort = portNum
                portNum += 1
                receivers.append((dest, destPort))
                waitElem = dest.popen(flowReceiveCmd  % (destPort, args.packet_size, load, "recv-%s-%d.txt" % (src.IP(), i)), shell=True)
                waitList.append(waitElem)
                outfile.write(str(dest.IP()) + '\n')
                outfile.write(str(destPort) + '\n')
            outfile.close()

        print "Opened all receivers"
        sleep(5)

        #for src in hosts:
        for i in xrange(len(hosts)-1):
            src = hosts[i]
            #print "   Sending %d packets from %s:%d to %s:%d" % (flowSize, src.name, srcPort, dest.name, destPort)
            src.popen(flowStartCmd % (src.IP(), NUM_PRIO_BANDS, args.packet_size, args.workload, "receivers-%s.txt" % (src.name), args.bw, load, args.nflows_per_host, load, load, "send-%s.txt" % (src.name)), shell=True)
        print "Opened all senders"

        for waitElem in waitList:
            waitElem.communicate()

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

