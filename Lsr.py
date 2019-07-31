#!usr/bin/python3
from socket import *
import threading
import time
import sys
import ast
import pdb

UPDATE_INTERVAL = 1  #1 secs
ROUTE_UPDATE_INTERVAL = 30  #in secs
NEIGHBOURS = 'neighbours'
SENDER = 'sender'
TIME = 'time'
SERVERNAME = 'localhost'
FORWARDER = 'forwarder'
# clientSocket = socket(AF_INET, SOCK_DGRAM)

lastReceived = dict()

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
    linkDict = dict()
    

class Message:
    seqNo = 0
    messageText = dict()
    sender = ""
    receivers = set() #set of Router or Neighbour

def readFile(filename):
    with open(filename, "r") as file:
        router = Router()
        l1 = file.readline().rstrip()
        router.routerName, router.port = l1.split(' ')
        router.port = int(router.port)
        noOfNeighbors = int(file.readline())
        neighDict = dict()

        for i in range(noOfNeighbors):
            neighbour = Neighbour()
            n = file.readline().rstrip()
            neighbour.neighbourName, neighbour.costToReach, neighbour.port = n.split(' ')
            neighbour.port = int(neighbour.port)
            neighbour.costToReach = float(neighbour.costToReach)
            router.neighbours.append(neighbour)
            router.neighboursDict[neighbour.neighbourName] = (neighbour.port, neighbour.costToReach) #TODO: perhaps dont need to send port number

            neighDict[neighbour.neighbourName] = neighbour.costToReach  

        
    return router

#to be called every Route_update_interval and 2*Route_update_interval when topology changes
def calculateDijkstraForNode(router : Router):
    time.sleep(30.0)
    while(True):
        # for node in router.linkDict.keys():
        paths, distances = dijkstra(router.linkDict, router.routerName)
        # print("paths: ", str(paths))
        # print("distances: ", str(distances))
        currRouter = router.routerName
        
        print ("I am Router ", currRouter)
        printOutput(paths, distances, currRouter)
        time.sleep(30.0)


def printOutput(paths: dict, distances: dict, currentRouter: str):
    for node, distance in distances.items():
        if node is not currentRouter:
            print("Least cost path to router ", node ,":",str(paths[node]), " and the cost is ", distance)

def constructMsg(router: Router):
    messageText = dict()
    neighDict = dict()

    for k, v in router.neighboursDict.items():
        neighDict[k] = v[1]
    
    router.linkDict[router.routerName] = neighDict
    messageText[NEIGHBOURS] = neighDict

    messageText[SENDER] = router.routerName
    messageText[TIME] = time.time()

    return str(messageText)
    

def broadcastLSA(message : str, router : Router):
    while(True):
        clientSocket = socket(AF_INET, SOCK_DGRAM)
        for k, v in router.neighboursDict.items():
            port = v[0]
            clientSocket.sendto(message.encode(),(SERVERNAME, port))
            # print(f'Router {router.routerName} sent message to: {k} at port: {port}')
        
        time.sleep(1.0)
        
def receiveMessage(router: Router):
    clientSocket = socket(AF_INET, SOCK_DGRAM)
    clientSocket.bind((SERVERNAME, router.port))
    rcvdMsg = clientSocket.recvfrom(2048)
    rcvdMsg = rcvdMsg[0].decode("utf-8") #decoding
    rcvdMsg = ast.literal_eval(rcvdMsg) # converting to dictionary
    rcvdMsg[FORWARDER] = router.routerName
    sender = rcvdMsg[SENDER]
    return rcvdMsg, sender

# TODO: dont send to A->B->C->D. C wont send received msg of A from B to B,
def sendMessage(message: dict, router: Router):
    clientSocket = socket(AF_INET, SOCK_DGRAM)
    originalSender = message[SENDER]
    forwardingRouter = message[FORWARDER]
    for k, v in router.neighboursDict.items():
        if k is not originalSender or k is not forwardingRouter:    #forward received message to only those neighbours that havent received it
            port = v[0]
            clientSocket.sendto(str(message).encode(), (SERVERNAME, port))

def forwardMessage(router: Router):
    while (True):
        rcvdMsg, sender = receiveMessage(router)
        if lastReceived.get(sender, 0) < rcvdMsg[TIME]:
            # print(rcvdMsg)
            lastReceived[sender] = rcvdMsg[TIME]
            router.linkDict[sender] = rcvdMsg[NEIGHBOURS]
            # print("link dict:" + str(router.linkDict))
            sendMessage(rcvdMsg, router)


def dijkstra(nodesDict: dict, current: str):
    nodes = nodesDict.keys()
    unvisited = {node: None for node in nodes} #using None as +inf
    distances = dict()
    currentDistance = 0
    unvisited[current] = currentDistance
    path = current
    paths = dict()

    while True:
        for neighbour, distance in nodesDict[current].items():
            if neighbour not in unvisited: 
                    continue
            newDistance = currentDistance + distance
            if unvisited[neighbour] is None or unvisited[neighbour] > newDistance:
                unvisited[neighbour] = newDistance
        distances[current] = currentDistance
        del unvisited[current]
        if not unvisited: 
                break
        candidates = [node for node in unvisited.items() if node[1]]
        current, currentDistance = sorted(candidates, key = lambda x: x[1])[0]
        
        path += current
        paths[current] = path

    return paths, distances

# if __name__ == "__main__":
filename = sys.argv[1]
router = readFile(filename)


msg = constructMsg(router)
thBroadcast = threading.Thread(target=broadcastLSA, args=(msg, router, ))
# pdb.set_trace()
# thBroadcast.daemon = True
thBroadcast.start()

thForward = threading.Thread(target=forwardMessage, args=(router, ))
# thForward.daemon = True
thForward.start()

thDijsk = threading.Thread(target = calculateDijkstraForNode, args = (router, ))
# thDijsk.daemon = True
thDijsk.start()

