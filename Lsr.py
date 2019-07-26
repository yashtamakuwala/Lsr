#!usr/bin/python3
from socket import *
import time
import sys
import json
import ast

UPDATE_INTERVAL = 1  #1 secs
ROUTE_UPDATE_INTERVAL = 30  #in secs
NEIGHBOURS = 'neighbours'
SENDER = 'sender'
TIME = 'time'
SERVERNAME = 'localhost'
clientSocket = socket(AF_INET, SOCK_DGRAM)

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
            router.neighboursDict[neighbour.neighbourName] = (neighbour.port ,float(neighbour.costToReach))

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
    messageText[TIME] = time.time()

    return str(messageText)
    

def sendMessage(message : str, router : Router):
    
    for k, v in router.neighboursDict.items():
        port = v[0]
        clientSocket.sendto(message.encode(),(SERVERNAME, port))
        print(f'Router {router.routerName} sent message to: {k} at port: {port}')
        

def receiveMessage(router: Router):
    rcvdMsg, sender = clientSocket.recvfrom(2048)
    rcvdMsg = rcvdMsg.decode("utf-8")
    rcvdMsg = ast.literal_eval(rcvdMsg) #decoding and converting to dictionary
    return rcvdMsg, sender

def forwardMessage(message: dict, router: Router):
    for k, v in router.neighboursDict.items():
        if k not in message:    #forward received message to only those neighbours that havent received it
            port = v[0]
            clientSocket.sendto(message.encode(),(SERVERNAME, port))

filename = sys.argv[1]
router = readFile(filename)
clientSocket.bind((SERVERNAME, router.port))
msg = constructMsg(router)

print(msg)
sendMessage(msg, router)

# time.sleep(5)
msg = receiveMessage(router)
print(msg)