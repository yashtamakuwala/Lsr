#!usr/bin/python3
from socket import *


UPDATE_INTERVAL = 1  #1 secs
ROUTE_UPDATE_INTERVAL = 30  #in secs

class Neighbour:
    neighbourName = ""
    port = 0    #has to be integer
    costToReach = -1.0  #has to be float with 1 decimal place, will not change after initialisation
    # cost is bidrection => A->B = B->A

class Router:
    routerName = ""
    port = 0
    neighbours = set(Neighbour) #will be list or dictionary?

class Message:
    messageText = ""
    sender = ""
    receivers = set(Router)

def readFile(filename):
    return None

#to be called every Route_update_interval and 2*Route_update_interval when topology changes
def calculateDijkstraForNode(router : Router):
    return None

def printOutput(router: Router):
    print ("I am Router A")
    for a in router.neighbours:
        print("Least cost path to router C:AFDC and the cost is 4.5")
    return None

