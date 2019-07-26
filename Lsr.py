#!usr/bin/python3
from socket import *
import time

UPDATE_INTERVAL = 1  #1 secs
ROUTE_UPDATE_INTERVAL = 30  #in secs
NEIGHBOURS = 'neighbours'
SENDER = 'sender'

class Neighbour:
    # def __init__(self, neighbourName, port, costToReach):
    #     self.neighbourName = neighbourName
    #     self.port = port
    #     self.costToReach = costToReach

    neighbourName = ""
    port = 0    #has to be integer
    costToReach = -1.0  #has to be float with 1 decimal place, will not change after initialisation
    # cost is bidrection => A->B = B->A

    def __repr__(self):
        return str(self.neighbourName + "-" + self.costToReach + "-" + str(self.port))

class Router:
    routerName = ""
    port = 0
    neighbours = list() #will be list or dictionary?
    neighboursDict = dict()
    

class Message:
    seqNo = 0
    messageText = dict()
    sender = ""
    receivers = set() #set of Router or Neighbour

def readFile(filename):
    with open(filename, "r") as file:
        router = Router()
        l1 = file.readline()
        router.routerName, router.port = l1.split(' ')
        router.port = int(str(router.port[:-1]))
        noOfNeighbors = int(file.readline())

        for i in range(noOfNeighbors):
            neighbour = Neighbour()
            n = file.readline()
            neighbour.neighbourName, neighbour.costToReach, neighbour.port = n.split(' ')
            neighbour.port = int(str(neighbour.port[:-1]))
            router.neighbours.append(neighbour)
            router.neighboursDict[neighbour.neighbourName] = float(neighbour.costToReach)

    return router

#to be called every Route_update_interval and 2*Route_update_interval when topology changes
def calculateDijkstraForNode(router : Router):
    return None

def printOutput(router: Router):
    print ("I am Router A")
    for a in router.neighbours:
        print("Least cost path to router C:AFDC and the cost is 4.5")
    return None

def constructMsg(router: Router):
    messageText = dict()
    messageText[NEIGHBOURS] = router.neighboursDict
    messageText[SENDER] = router.routerName
    messageText['time'] = time.time()

    return messageText
    

router = readFile('configA.txt')

print(constructMsg(router))