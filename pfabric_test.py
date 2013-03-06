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

import sys
import os

# Number of priorities supported
NUM_PRIO_BANDS = 16
MAX_PACKETS = 100

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
          bw=10000, delay='0ms', max_queue_size=10, use_prio=True, num_bands=NUM_PRIO_BANDS)
        self.addLink(h2, switch,
          bw=1000, delay='0ms', max_queue_size=10, use_prio=True, num_bands=NUM_PRIO_BANDS)
        return

def main():
    "Create network and run pFabric experiment"

    start = time()
    # Reset to known state
    topo = pFabricTopo()
    setLogLevel('debug')
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()

    dumpNodeConnections(net.hosts)
    net.pingAll()

    h1 = net.getNodeByName('h1')
    h2 = net.getNodeByName('h2')

    # Configure TCP to use reno and disable advanced features
    tcpConfigCmd = "sudo ./tcpConfig.sh"
    subprocess.call(tcpConfigCmd, shell=True)
    print "TCP configured"

    # tcpdump at both hosts
    tcpdumpCmd = "sudo tcpdump -n -x > %s"
    h1.popen(tcpdumpCmd % ("send_tcpdump.txt"), shell=True)
    h2.popen(tcpdumpCmd % ("recv_tcpdump.txt"), shell=True)

    flowReceiveCmd = "sudo python flowReceiver.py --dest-port %d > %s"
    flowStartCmd = "sudo python flowGenerator.py --src-ip %s --src-port %d --dest-ip %s --dest-port %d --num-packets %d --num-bands %d --max-packets %d --priority %d  > %s"

    # Run test with high-priority long flow and low-priority short flow
    # Expect long flow to finish before short flow
    recv_long = h2.popen(flowReceiveCmd  % (1234, "recv_long1.txt"), shell=True)
    recv_short = h2.popen(flowReceiveCmd  % (1235, "recv_short1.txt"), shell=True)
    sleep(5)
    h1.popen(flowStartCmd % (h1.IP(), 1234, h2.IP(), 1234, 1000, NUM_PRIO_BANDS, MAX_PACKETS, 1, "send_long1.txt"), shell=True)
    h1.popen(flowStartCmd % (h1.IP(), 1235, h2.IP(), 1235, 20, NUM_PRIO_BANDS, MAX_PACKETS, 16, "send_short1.txt"), shell=True)

    recv_long.communicate()
    recv_short.communicate()

    # Run test with low-priority long flow and high-priority short flow
    # Expect short flow to finish before long flow
    recv_long = h2.popen(flowReceiveCmd  % (1236, "recv_long2.txt"), shell=True)
    recv_short = h2.popen(flowReceiveCmd  % (1237, "recv_short2.txt"), shell=True)
    sleep(5)
    h1.popen(flowStartCmd % (h1.IP(), 1236, h2.IP(), 1236, 1000, NUM_PRIO_BANDS, MAX_PACKETS, 16, "send_long2.txt"), shell=True)
    h1.popen(flowStartCmd % (h1.IP(), 1237, h2.IP(), 1237, 20, NUM_PRIO_BANDS, MAX_PACKETS, 1, "send_short2.txt"), shell=True)

    recv_long.communicate()
    recv_short.communicate()

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

