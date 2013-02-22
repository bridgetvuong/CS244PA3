#!/usr/bin/python

"CS244 Assignment 3: pFabric"

from mininet.topo import Topo
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.log import lg
from mininet.util import dumpNodeConnections

import subprocess
from subprocess import Popen, PIPE
from time import sleep, time
from multiprocessing import Process
import termcolor as T
from argparse import ArgumentParser
from signal import SIGTERM

import sys
import os

def cprint(s, color, cr=True):
    """Print in color
       s: string to print
       color: color to use"""
    if cr:
        print T.colored(s, color)
    else:
        print T.colored(s, color),


# Parse arguments

parser = ArgumentParser(description="Buffer sizing tests")

class pFabricTopo(Topo):
    "Simple topology for pFabric experiment."

    def __init__(self, n=2):
        super(pFabricTopo, self).__init__()

        # TODO: create two hosts
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')

        # Here I have created a switch.  If you change its name, its
        # interface names will change from s0-eth1 to newname-eth1.
        switch = self.addSwitch('s0')

        # TODO: Add links with appropriate characteristics
        self.addLink(h1, switch,
          bw=1000, delay='0ms', max_queue_size=10, use_htb=True)
        self.addLink(h2, switch,
          bw=1000, delay='0ms', max_queue_size=10, use_htb=True)
        return

def main():
    "Create network and run pFabric experiment"

    start = time()
    # Reset to known state
    topo = pFabricTopo()
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()

    dumpNodeConnections(net.hosts)
    net.pingAll()

    h1 = net.getNodeByName('h1')
    h2 = net.getNodeByName('h2')
    receiver = h2.popen("sudo python trafficServer.py --dest-port %d > receiver.txt" % (1234), shell=True)
    sender = h1.popen("sudo python trafficGenerator.py --dest-ip %s --dest-port %d --num-packets %d > sender.txt" % (h2.IP(), 1234, 10), shell=True)

    sleep(10)
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

