#!usr/bin/python3
from socket import *
import threading
import time
import sys
import ast

UPDATE_INTERVAL = 1  #1 secs
ROUTE_UPDATE_INTERVAL = 30  #in secs
NEIGHBOURS = 'neighbours'
SENDER = 'sender'
TIME = 'time'
SERVERNAME = 'localhost'
clientSocket = socket(AF_INET, SOCK_DGRAM)

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
    print("Dijsktra")
    time.sleep(30.0)
    while(True):
        for k in router.linkDict.keys():
            dijkstra(router.linkDict, router.routerName, k)
        time.sleep(30.0)


def printOutput(router: Router):
    print ("I am Router A")
    for a in router.neighbours:
        print("Least cost path to router C:AFDC and the cost is 4.5")
    return None

def constructMsg(router: Router):
    messageText = dict()
    neighDict = dict()

    for k, v in router.neighboursDict.items():
        neighDict[k] = v[1]
    
    router.linkDict[router.routerName] = neighDict
    print(str(router.linkDict))
    messageText[NEIGHBOURS] = neighDict

    messageText[SENDER] = router.routerName
    messageText[TIME] = time.time()

    return str(messageText)
    

def broadcastLSA(message : str, router : Router):
    while(True):
        for k, v in router.neighboursDict.items():
            port = v[0]
            clientSocket.sendto(message.encode(),(SERVERNAME, port))
            print(f'Router {router.routerName} sent message to: {k} at port: {port}')
        
        time.sleep(1.0)
        
                

def receiveMessage(router: Router):
    rcvdMsg, sender = clientSocket.recvfrom(2048)
    rcvdMsg = rcvdMsg.decode("utf-8") #decoding
    rcvdMsg = ast.literal_eval(rcvdMsg) # converting to dictionary
    sender = rcvdMsg[SENDER]
    return rcvdMsg, sender

def sendMessage(message: dict, router: Router):
    for k, v in router.neighboursDict.items():
        if k not in message and k is not message[SENDER]:    #forward received message to only those neighbours that havent received it
            port = v[0]
            clientSocket.sendto(str(message).encode(), (SERVERNAME, port))

def forwardMessage(router: Router):
    # print("forward")
    while (True):
        rcvdMsg, sender = receiveMessage(router)
        if lastReceived.get(sender, 0) < rcvdMsg[TIME]:
            print(rcvdMsg)
            lastReceived[sender] = rcvdMsg[TIME]
            router.linkDict[sender] = rcvdMsg[NEIGHBOURS]
            print("link dict:" + str(router.linkDict))
            sendMessage(rcvdMsg, router)
            
        # time.sleep(1.0)


def dijkstra(graph,src,dest,visited=[],distances={},predecessors={}):
    """ calculates a shortest path tree routed in src
    """    
    # a few sanity checks
    if src not in graph:
        raise TypeError('The root of the shortest path tree cannot be found')
    if dest not in graph:
        raise TypeError('The target of the shortest path cannot be found')    
    # ending condition
    if src == dest:
        # We build the shortest path and display it
        path=[]
        pred=dest
        while pred != None:
            path.append(pred)
            pred=predecessors.get(pred,None)
        print('shortest path: '+str(path)+" cost="+str(distances[dest])) 
    else :     
        # if it is the initial  run, initializes the cost
        if not visited: 
            distances[src]=0
        # visit the neighbors
        for neighbor in graph[src] :
            if neighbor not in visited:
                new_distance = distances[src] + graph[src][neighbor]
                if new_distance < distances.get(neighbor,float('inf')):
                    distances[neighbor] = new_distance
                    predecessors[neighbor] = src
        # mark as visited
        visited.append(src)
        # now that all neighbors have been visited: recurse                         
        # select the non visited node with lowest distance 'x'
        # run Dijskstra with src='x'
        unvisited={}
        for k in graph:
            if k not in visited:
                unvisited[k] = distances.get(k,float('inf'))        
        x=min(unvisited, key=unvisited.get)
        dijkstra(graph,x,dest,visited,distances,predecessors)


# if __name__ == "__main__":
filename = sys.argv[1]
router = readFile(filename)
clientSocket.bind((SERVERNAME, router.port))


msg = constructMsg(router)
thBroadcast = threading.Thread(target=broadcastLSA, args=(msg, router, ))
# thBroadcast.daemon = True
thBroadcast.start()

thForward = threading.Thread(target=forwardMessage, args=(router, ))
# thForward.daemon = True
thForward.start()

thDijsk = threading.Thread(target = calculateDijkstraForNode, args = (router, ))
# thDijsk.daemon = True
thDijsk.start()

