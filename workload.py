import os
import random
import sys

class Workload():
    dist = []

    def __init__(self, distfile):
        f = open(distfile, 'r')
        for line in f.readlines():
            self.dist.append(tuple([float(i) for i in str.split(line)]))

    def getMaxFlowSize(self):
        return self.dist[len(self.dist)-1][1]

    def getAverageFlowSize(self):
        return sum([s[0]*s[1] for s in self.dist])

    def getFlowSize(self):
            ind = random.random()
            for s in self.dist:
                if ind <= s[0]:
                    return s[1]

