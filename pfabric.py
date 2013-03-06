#!/usr/bin/python

"CS244 Assignment 3: pFabric"

from mininet.topo import Topo
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.log import lg, setLogLevel
from mininet.util import dumpNodeConnections
from mininet.cli import CLI

import subprocess
from subprocess import Popen, PIPE
from time import sleep, time
from multiprocessing import Process
import termcolor as T
from argparse import ArgumentParser
from signal import SIGTERM

import random
import sys
import os

# Number of priorities supported
NUM_PRIO_BANDS = 16
NUM_HOSTS = 2
PACKET_SIZE = 1500

def cprint(s, color, cr=True):
    """Print in color
       s: string to print
       color: color to use"""
    if cr:
        print T.colored(s, color)
    else:
        print T.colored(s, color),


# Parse arguments
parser = ArgumentParser(description="pFabric tests")

parser.add_argument('--workload',
                    help="'data mining' or 'web search'",
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
        hostNames = [self.addHost('h%d' % i) for i in xrange(NUM_HOSTS)]

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

        for i in xrange(NUM_HOSTS):
            self.addLink(hostNames[i], switch, **linkOptions)

webSearchWorkload = [
    (0.15, 6),
    (0.2, 13),
    (0.3, 19),
    (0.4, 33),
    (0.53, 53),
    (0.6, 133),
    (0.7, 667),
    (0.8, 1333),
    (0.9, 3333),
    (0.97, 6667),
    (1, 20000)
]

dataMiningWorkload = [
    (0.5, 1),
    (0.6, 2),
    (0.7, 3),
    (0.8, 7),
    (0.9, 267),
    (0.95, 2107),
    (0.99, 66667),
    (1, 666667)
]

averageWebSearchFlowSize = sum([s[0]*s[1] for s in webSearchWorkload])
averageDataMiningFlowSize = sum([s[0]*s[1] for s in dataMiningWorkload])

def getMaxFlowSize():
    if args.workload == "web search":
        return 20000
    else:
        return 666667

def getAverageFlowSize():
    if args.workload == "web search":
        return averageWebSearchFlowSize
    else:
        return averageDataMiningFlowSize

def getFlowSize():
    ind = random.random()
    if args.workload == "web search":
        dist = webSearchWorkload
    else:
        dist = dataMiningWorkload
    for s in dist:
        if ind <= s[0]:
            return s[1]

def main():
    "Create network and run pFabric experiment"

    if args.tcp != 'minTCP' and args.tcp != 'TCP':
        print "Bad TCP argument."
        exit(1)
    if args.workload != 'web search' and args.workload != 'data mining':
        print "Bad workload argument."
        exit(1)

    start = time()
    # Reset to known state
    topo = pFabricTopo()
    setLogLevel('debug')
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()

    dumpNodeConnections(net.hosts)
    net.pingAll()

    # Configure TCP to use reno and disable advanced features
    tcpConfigCmd = "sudo ./%sConfig.sh" % args.tcp
    subprocess.call(tcpConfigCmd, shell=True)

    # tcpdump at both hosts
    tcpdumpCmd = "sudo tcpdump -n -x > %s"
    hosts = [net.getNodeByName(hostName) for hostName in hostNames]
    for host in hosts:
        host.popen(tcpdumpCmd % ("tcpdump-%s.txt" % host.name), shell=True)

    flowReceiveCmd = "sudo python flowReceiver.py --dest-port %d > %s"
    flowStartCmd = "sudo python flowGenerator.py --src-ip %s --src-port %d --dest-ip %s --dest-port %d --num-packets %d --num-bands %d --max-packets %d > %s"

    for load in [0.5]: #[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
        receivers = []
        for i in xrange(args.nflows):
            dest = hosts[random.randrange(NUM_HOSTS)]
            destPort = random.randrange(1025, 9999)
            receivers.append((dest, destPort))
            dest.popen(flowReceiveCmd  % (destPort, "recv-%f-%d-%s.txt" % (load, i, dest.name)), shell=True)

        sleep(5)

        for i in xrange(args.nflows):

            # generate random sender and receiver
            src = hosts[random.randrange(NUM_HOSTS)]
            srcPort = random.randrange(1025, 9999)
            flowSize = getFlowSize()

            dest = receivers[i][0]
            destPort = receivers[i][1]

            print "Sending %d packets from %s:%d to %s:%d" % (flowSize, src.name, srcPort, dest.name, destPort)
            src.popen(flowStartCmd % (src.IP(), srcPort, dest.IP(), destPort, flowSize, NUM_PRIO_BANDS, getMaxFlowSize(), "send-%f-%d-%s.txt" % (load, i, src.name)), shell=True)

            lambd = args.bw * 1000000 / 8 * load / getAverageFlowSize() / PACKET_SIZE
            waitTime = random.expovariate(lambd)
            print lambd, waitTime
            print "Waiting %f seconds before next flow..." % waitTime
            sleep(waitTime)
        
    for i in xrange(2*90):
        sleep(0.5)
        print ". ",
        sys.stdout.flush()

    CLI(net)
    net.stop()
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

