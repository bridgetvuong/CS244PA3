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

# Number of priorities supported
NUM_PRIO_BANDS = 16
PACKET_SIZE = 1500

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
                    default=10000)

parser.add_argument('--delay',
                    help="end-to-end RT delay in us",
                    type=int,
                    default=12)

parser.add_argument('--nhosts',
                    help="number of hosts",
                    type=int,
                    default=2)

parser.add_argument('--nflows',
                    help="number of flows",
                    type=int,
                    default=1000)

# Expt parameters
args = parser.parse_args()

hostNames = []

class pFabricTopo(Topo):
    "Simple topology for pFabric experiment."

    def __init__(self, n=2):
        super(pFabricTopo, self).__init__()

        # create hosts
        global hostNames
        hostNames = [self.addHost('h%d' % i) for i in xrange(n)]

        # Here I have created a switch.  If you change its name, its
        # interface names will change from s0-eth1 to newname-eth1.
        switch = self.addSwitch('s0')

        usepFabric = (args.tcp == 'minTCP')
        # Add links with appropriate characteristics
        linkOptions = {'bw': args.bw, 'delay': '%dus' % (args.delay/4), 'max_queue_size': 150}
        if usepFabric:
            linkOptions['max_queue_size'] = 15
            linkOptions['use_prio'] = True
            linkOptions['num_bands'] = NUM_PRIO_BANDS

        for i in xrange(n):
            self.addLink(hostNames[i], switch, **linkOptions)

def main():
    "Create network and run pFabric experiment"

    if args.tcp != 'minTCP' and args.tcp != 'TCP':
        print "Bad TCP argument."
        exit(1)

    start = time()

    # Initialize workload
    workload  = Workload(args.workload)

    # Reset to known state
    topo = pFabricTopo(args.nhosts)
    #setLogLevel('debug')
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()

    dumpNodeConnections(net.hosts)
    net.pingAll()

    # Configure TCP to use reno and disable advanced features
    tcpConfigCmd = "sudo ./%sConfig.sh" % args.tcp
    call(tcpConfigCmd, shell=True)

    # tcpdump at both hosts
    tcpdumpCmd = "sudo tcpdump -n -x > %s"
    hosts = net.hosts#[net.getNodeByName(hostName) for hostName in hostNames]
    for host in hosts:
        host.popen(tcpdumpCmd % ("tcpdump-%s.txt" % host.name), shell=True)

    # Send flows
    flowReceiveCmd = "sudo python flowReceiver.py --dest-port %d --packet-size %d > %s/%s"
    flowStartCmd = "sudo python flowGenerator.py --src-ip %s --src-port %d --dest-ip %s --dest-port %d --num-packets %d --num-bands %d --max-packets %d --packet-size %d > %s/%s"

    for load in [0.5]: #[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
        receivers = []
        waitList = []
        # Choose random receiver and start receiving
        for i in xrange(args.nflows):
            dest = hosts[0]#random.randrange(args.nhosts)]
            destPort = random.randrange(1025, 9999)
            receivers.append((dest, destPort))
            waitElem = dest.popen(flowReceiveCmd  % (destPort, PACKET_SIZE, args.outputdir, "recv-%f-%d-%s.txt" % (load, i, dest.name)), shell=True)
            waitList.append(waitElem)

        sleep(5)

        for i in xrange(args.nflows):

            # Choose random sender and flow size according to distribution
            src = hosts[1]#random.randrange(args.nhosts)]
            srcPort = random.randrange(1025, 9999)
            flowSize = 3000#workload.getFlowSize()

            dest = receivers[i][0]
            destPort = receivers[i][1]

            print "Sending %d packets from %s:%d to %s:%d" % (flowSize, src.name, srcPort, dest.name, destPort)
            src.popen(flowStartCmd % (src.IP(), srcPort, dest.IP(), destPort, flowSize, NUM_PRIO_BANDS,
                                      workload.getMaxFlowSize(), PACKET_SIZE, args.outputdir, "send-%f-%d-%s.txt" % (load, i, src.name)), shell=True)

            # Lambda is arrival rate = load*capacity converted to flows/s
            lambd = load * args.bw * 1000000 / 8 / PACKET_SIZE / workload.getAverageFlowSize()
            waitTime = random.expovariate(lambd)
            print lambd
            print "Waiting %f seconds before next flow..." % waitTime
            sleep(waitTime)

        for waitElem in waitList:
            waitElem.communicate()

    #CLI(net)
    net.stop()

    # Reset to normal TCP
    tcpConfigCmd = "sudo ./TCPConfig.sh"
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

