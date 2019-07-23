#!usr/bin/python3

class Neighbour:
    neighbourName = ""
    port = 0    #has to be integer
    costToReach = -1.0  #has to be float with 1 decimal place

class Router:
    routerName = ""
    port = 0
    neighbourList = list(Neighbour) #will be list or dictionary?


def readFile(filename):
    return None
