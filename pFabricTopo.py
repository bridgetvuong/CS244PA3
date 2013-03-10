from mininet.topo import Topo

class pFabricTopo(Topo):
    "Simple topology for pFabric experiment."

    def __init__(self, n=2, bw=100, delay=None, usepFabric=True, numPrioBands=16):
        super(pFabricTopo, self).__init__()

        # create hosts
        global hostNames
        hostNames = [self.addHost('h%d' % i) for i in xrange(n)]

        # Here I have created a switch.  If you change its name, its
        # interface names will change from s0-eth1 to newname-eth1.
        switch = self.addSwitch('s0')

        # Add links with appropriate characteristics
        linkOptions = {'bw': bw}
        if delay:
            linkOptions['delay'] = '%dms' % (delay/4)
            linkOptions['max_queue_size'] = 150
        if usepFabric:
            if delay: linkOptions['max_queue_size'] = 15
            linkOptions['use_prio'] = True
            linkOptions['num_bands'] = numPrioBands

        for i in xrange(n):
            self.addLink(hostNames[i], switch, **linkOptions)
