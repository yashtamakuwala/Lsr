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
    linkDict = dict()   #Global topology
    msg = dict()

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
    
    while(True):
        time.sleep(ROUTE_UPDATE_INTERVAL)
        paths, distances = dijkstra(router.linkDict, router.routerName)
        # print("paths: ", str(paths))
        # print("distances: ", str(distances))
        currRouter = router.routerName
        
        print ("I am Router ", currRouter)
        printOutput(paths, distances, currRouter)
        


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

    router.msg = messageText
    return str(messageText)
    

def broadcastLSA(router : Router):
    while(True):
        message = constructMsg(router)
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
    # forwarder = rcvdMsg.get(FORWARDER, None)
    sender = rcvdMsg[SENDER]
    return rcvdMsg, sender

def forwardMessage(router: Router):
    while (True):
        rcvdMsg, sender = receiveMessage(router)
        # print("LAST RECEIVED:" + str(lastReceived))
        if lastReceived.get(sender, 0) < rcvdMsg[TIME]:
            # print(f'received msg: {rcvdMsg} from {sender}')
            if sender is not router.routerName:     #sender shouldnt be current router
                lastReceived[sender] = rcvdMsg[TIME]
            router.linkDict[sender] = rcvdMsg[NEIGHBOURS]
            # print("Time diff for sender", sender, " LAST RECEIVED:" + str(lastReceived))
            sendMessage(rcvdMsg, router)

# router wont send msg to original sender and the router it received the message from
def sendMessage(message: dict, router: Router):
    clientSocket = socket(AF_INET, SOCK_DGRAM)
    originalSender = message[SENDER]
    forwardingRouter = message.get(FORWARDER, None)
    nodes = list(router.neighboursDict.keys())
    for node in nodes:
        v = router.neighboursDict[node]
        if node is not originalSender and node is not forwardingRouter:    #forward received message to only those neighbours that havent received it
            port = v[0]
            try:
                message[FORWARDER] = router.routerName
                clientSocket.sendto(str(message).encode(), (SERVERNAME, port))
            except:
                pass
            

# https://stackoverflow.com/a/22899400/4933540
def dijkstra(nodesDict: dict, current: str):
    nodes = nodesDict.keys()
    unvisited = {node: None for node in nodes} #using None as +inf
    distances = dict()
    currentDistance = 0
    unvisited[current] = currentDistance
    path = current
    paths = dict()

    try:
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
    except:
        pass
    return paths, distances


def checkForDeadNodes(router: Router):
    while(True): 
        currentTime = time.time()
        allNodes = list(lastReceived.keys())
        for node in allNodes:
            lastTimeRcvd = lastReceived[node]

            routerNeighDictKeys = list(router.neighboursDict.keys())
            if node in routerNeighDictKeys:
                if ((currentTime - lastTimeRcvd) > 3) : #3s for neighbours and 13s for non-neighbour
                    print(f'Deleting neighbour {node} for router {router.routerName} from lastReceived')
                    print(f'currtime: {currentTime} lastTimeRcvd : {lastTimeRcvd}')
                    removeNodePresence(router, node)
            else:
                if ((currentTime - lastTimeRcvd) > 14):
                    print(f'Deleting distant {node} for router {router.routerName} from lastReceived')
                    print(f'currtime: {currentTime} lastTimeRcvd : {lastTimeRcvd}')
                    removeNodePresence(router, node)

# remove node from last received and router.neighboursDict
def removeNodePresence(router: Router, node: str):

    

    _ = lastReceived.pop(node)
    _ = router.linkDict.pop(node)
    for k in router.linkDict:
        if node in router.linkDict[k]:
            _ = router.linkDict[k].pop(node)
        # for keyDict in router.linkDict[k]:
    
    if node in router.msg[NEIGHBOURS]:
        _ = router.msg[NEIGHBOURS].pop(node)

    if node in router.neighboursDict:
        _ = router.neighboursDict.pop(node)    

# if __name__ == "__main__":
filename = sys.argv[1]
router = readFile(filename)
print("router neighbours: ",router.neighboursDict)
thBroadcast = threading.Thread(target=broadcastLSA, args=(router, ))
thBroadcast.start()

thForward = threading.Thread(target=forwardMessage, args=(router, ))
# thForward.daemon = True
thForward.start()

thDijks = threading.Thread(target = calculateDijkstraForNode, args = (router, ))
# thDijsk.daemon = True
thDijks.start()

tdead = threading.Thread(target = checkForDeadNodes, args = (router, ))
tdead.start()