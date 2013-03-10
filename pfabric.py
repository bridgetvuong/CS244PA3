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
                    default=None)

parser.add_argument('--nhosts',
                    help="number of hosts",
                    type=int,
                    default=54)

parser.add_argument('--packet-size',
                    help="packet size in bytes",
                    type=int,
                    default=1500)

parser.add_argument('--time',
                    help="number of seconds for each load",
                    type=int,
                    default=6000)

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

    # Configure txqueuelen
    queueLen = 150
    if usePFabric:
        queueLen = 15
    setQueueLenCmd = "ifconfig %%s txqueuelen %d" % queueLen
    call(setQueueLenCmd % "eth0", shell=True)
    for i in xrange(args.nhosts):
        call(setQueueLenCmd % ("s0-eth%d" % (i+1)), shell=True)
    call("ifconfig", shell=True)

    # tcpdump at both hosts
    tcpdumpCmd = "sudo tcpdump -n -x > %s/%s/%%s" % (args.outputdir, args.tcp)
    hosts = net.hosts
#    for host in hosts:
#        host.popen(tcpdumpCmd % ("tcpdump-%s.txt" % host.name), shell=True)

    # Send flows
    outputDir = "%s/%s" % (args.outputdir, args.tcp)
    flowReceiveCmd = "sudo python multipleFlowReceiver.py --dest-port %%d --packet-size %%d --output-dir %s/%%.1f --time %%d > %s/%%.1f/%%s" % (outputDir, outputDir)
    flowStartCmd = "sudo python multipleFlowGenerator.py --src-ip %%s --num-bands %%d --packet-size %%d --workload %%s --dest-file %s/%%s --bw %%d --load %%f --time %%d --output-dir %s/%%.1f > %s/%%.1f/%%s" % (args.outputdir, outputDir, outputDir)

    for load in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
        print "===== Starting load level %.1f" % load
        os.system("mkdir %s/%s/%.1f" % (args.outputdir, args.tcp, load))

        # Start receivers
        destPort = 11125
        waitList = []
        for src in hosts:
            outfile = open("%s/receivers-%s.txt" % (args.outputdir, src.name), 'w+')
            for dest in hosts:
                outfile.write(str(dest.IP()) + '\n')
                outfile.write(str(destPort) + '\n')
            outfile.close()

        for dest in hosts:
            waitElem = dest.popen(flowReceiveCmd  % (destPort, args.packet_size, load, args.time, load, "recv-%s.txt" % (dest.name)), shell=True)
            waitList.append(waitElem)

        print "Opened all receivers"
        sleep(5)

        # Start senders
        # effectiveLoad = load/(args.nhosts - 1)
        for src in hosts:
        #for i in xrange(len(hosts)-1):
        #    src = hosts[i]
            waitElem = src.popen(flowStartCmd % (src.IP(), NUM_PRIO_BANDS, args.packet_size, args.workload,
                                      "receivers-%s.txt" % (src.name), args.bw, load, args.time + 5,
                                      load, load, "send-%s.txt" % (src.name)), shell=True)
            waitList.append(waitElem)
        print "Opened all senders"

        # Wait for receivers
        for waitElem in waitList:
            waitElem.communicate()

    #CLI(net)
    net.stop()

    # Reset to normal TCP
    tcpConfigCmd = "sudo ./tcpconfig/TCPConfig.sh"
    call(tcpConfigCmd, shell=True)
    print "TCP reset"

    # Reset to default txqueuelen
    queueLen = 1000
    call("sudo ifconfig eth0 txqueuelen %d" % queueLen, shell=True)
    call("ifconfig", shell=True)
    print "txqueuelen reset"

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

