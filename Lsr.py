#!usr/bin/python3
from socket import *
import threading
import time
import sys
import ast
import pdb
import copy

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
    lastSent = None

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

       
# def printOutput(paths: str, distances: str, currentRouter: str):
#     print("Least cost path to router ", node ,":",str(paths[node]), " and the cost is ", round(distance,1))

def constructMsg(router: Router):
    messageText = dict()
    neighDict = dict()
    nodes = list(router.neighboursDict.keys())

    for node in nodes:
        neighDict[node] = router.neighboursDict[node][1]
    
    router.linkDict[router.routerName] = neighDict

    messageText[NEIGHBOURS] = neighDict
    messageText[SENDER] = router.routerName
    messageText[TIME] = time.time()

    router.msg = messageText
    return str(messageText)
    

def broadcastLSA(router : Router):
    while(True):
        # time.sleep(UPDATE_INTERVAL)
        if router.lastSent is None or time.time() > (router.lastSent + 1.0):
            message = constructMsg(router)
            clientSocket = socket(AF_INET, SOCK_DGRAM)
            nodes = list(router.neighboursDict.keys())
            for node in nodes:
                port = router.neighboursDict[node][0]
                clientSocket.sendto(message.encode(),(SERVERNAME, port))
                d = ast.literal_eval(message)
                # print("Sending time: ", d[TIME])
                # print(f'Router {router.routerName} sent message to: {node} at port: {port}')
            router.lastSent = time.time()
                        
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
        # print('')
        # print("LAST RECEIVED:" + str(lastReceived))
        # print("msg: ", rcvdMsg)

        # if sender is 'D':
        #     print(rcvdMsg)
        currTime = time.time()
        if lastReceived.get(sender, 0) < rcvdMsg[TIME]:
        # if lastReceived.get(sender, 0) < currTime:
            # print(f'received msg: {rcvdMsg} from {sender}')
            if sender is not router.routerName:     #sender shouldnt be current router
                lastReceived[sender] = rcvdMsg[TIME]
                # lastReceived[sender] = currTime
                router.linkDict[sender] = rcvdMsg[NEIGHBOURS]
                # print("Time diff for sender", sender, " LAST RECEIVED:" + str(lastReceived))
                sendMessage(rcvdMsg, router)

# router wont send msg to original sender and the router it received the message from
def sendMessage(message: dict, router: Router):
    clientSocket = socket(AF_INET, SOCK_DGRAM)
    originalSender = message[SENDER]
    forwardingRouter = message.get(FORWARDER, None)
    if forwardingRouter is not None:
        lastReceived[forwardingRouter] = time.time()
    
    nodes = list(router.neighboursDict.keys())
    # print(f"Neighbours of {router.routerName} are {nodes}")
    for node in nodes:
        v = router.neighboursDict[node]
        if node is not originalSender and node is not forwardingRouter:
            port = v[0]
            try:
                message[FORWARDER] = router.routerName
                clientSocket.sendto(str(message).encode(), (SERVERNAME, port))
            except Exception as msg:   #TODO: check this
                print('Error: %s', msg)
                

#to be called every Route_update_interval and 2*Route_update_interval when topology changes
def calculateDijkstraForNode(router : Router):
    
    while(True):
        time.sleep(ROUTE_UPDATE_INTERVAL)
        allLinkages = copy.copy(router.linkDict)
        nodes = set(allLinkages.keys())
        currRouter = router.routerName
        
        print ("I am Router ", currRouter)
        
        for node in nodes:
            linkages = copy.deepcopy(allLinkages)
            if node is not currRouter:
                distance, path = dijkstra(linkages, currRouter, node)
                print("Least cost path to router ", node ,":", path, " and the cost is ", distance)
            

# https://gist.github.com/amitabhadey/37af83a84d8c372a9f02372e6d5f6732
def dijkstra(graph,start,goal):

    shortest_distance = {} 
    track_predecessor = {} 
    unseenNodes = graph 
    infinity = 5000 
    track_path = [] 

    for node in unseenNodes:
        shortest_distance[node] = infinity

    shortest_distance[start] = 0

    while unseenNodes:
        min_distance_node = None

        for node in unseenNodes:
            if min_distance_node is None:
                min_distance_node = node

            elif shortest_distance[node] < shortest_distance[min_distance_node]:
                min_distance_node = node

        path_options = graph[min_distance_node].items()

        for child_node, weight in path_options:

            if weight + shortest_distance[min_distance_node] < shortest_distance[child_node]:
                shortest_distance[child_node] = weight + shortest_distance[min_distance_node]
                track_predecessor[child_node] = min_distance_node
        unseenNodes.pop(min_distance_node)

    currentNode = goal

    while currentNode != start:

        try:
            track_path.insert(0,currentNode)
            currentNode = track_predecessor[currentNode]
        except KeyError:
            print('Path not reachable')
            break
    track_path.insert(0,start)

    if shortest_distance[goal] != infinity:
        distance = round(shortest_distance[goal], 1)
        path = ''.join(track_path)
        return distance, path



def checkForDeadNodes(router: Router):
    while(True): 
        time.sleep(3)   #TODO:
        allNodes = list(lastReceived.keys())
        for node in allNodes:
            lastTimeRcvd = lastReceived[node]

            routerNeighDictKeys = list(router.neighboursDict.keys())
            currentTime = time.time()
            if node in routerNeighDictKeys:
                if ((currentTime - lastTimeRcvd) > 4) : #3s for neighbours and 13s for non-neighbour
                    print(f'Deleting neighbour {node} for router {router.routerName} from lastReceived')
                    print(f'currtime: {currentTime} lastTimeRcvd : {lastTimeRcvd}')
                    print("LasTRcvd:",lastReceived)
                    removeNodePresence(router, node)
            else:
                if ((currentTime - lastTimeRcvd) > 13):
                    print(f'Deleting distant {node} for router {router.routerName} from lastReceived')
                    print(f'currtime: {currentTime} lastTimeRcvd : {lastTimeRcvd}')
                    print("LasTRcvd:",lastReceived)
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
thBroadcast = threading.Thread(target=broadcastLSA, args=(router, ))
thBroadcast.start()

thForward = threading.Thread(target=forwardMessage, args=(router, ))
thForward.start()

thDijks = threading.Thread(target = calculateDijkstraForNode, args = (router, ))
thDijks.start()

tdead = threading.Thread(target = checkForDeadNodes, args = (router, ))
tdead.start()