import os
import random
import sys

class Workload():
    dist = []
    avgFlowSize = 0.0

    def __init__(self, distfile):
        f = open(distfile, 'r')
        for line in f.readlines():
            self.dist.append(tuple([float(i) for i in str.split(line)]))
        prev = 0.0
        for s in self.dist:
            self.avgFlowSize += (s[0] - prev)*s[1]
            prev = s[0]

    def getMaxFlowSize(self):
        return self.dist[len(self.dist)-1][1]

    def getAverageFlowSize(self):
        return self.avgFlowSize

    def getAllFlowSizes(self):
        return [s[1] for s in self.dist]

    def getFlowSize(self):
            ind = random.random()
            for s in self.dist:
                if ind <= s[0]:
                    return int(s[1])
