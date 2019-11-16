# mdpAgents.py
# parsons/20-nov-2017
#
# Version 1
#
# The starting point for CW2.
#
# Intended to work with the PacMan AI projects from:
#
# http://ai.berkeley.edu/
#
# These use a simple API that allow us to control Pacman's interaction with
# the environment adding a layer on top of the AI Berkeley code.
#
# As required by the licensing agreement for the PacMan AI we have:
#
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).

# The agent here is was written by Simon Parsons, based on the code in
# pacmanAgents.py

from pacman import Directions
from game import Agent
import api
import random
import game
import util

def printGrid(grid):
    for column in list(reversed(grid)):
        print " ".join(map(str,column))
    print ""

# keyvalue of directions and their movement vectors
directions =     { Directions.NORTH: (0, 1),
                   Directions.SOUTH: (0, -1),
                   Directions.EAST:  (1, 0),
                   Directions.WEST:  (-1, 0),
                   Directions.STOP:  (0, 0)  }

def applyAction(x, y, direction):
    vector = directions[direction]
    return (x + vector[0], y + vector[1])


def getValidActions(grid, x, y):
    validActions = []
    # iterate over possible actions
    for action, vector in directions.iteritems():
        # apply vector movement to current x and y
        (nextX, nextY) = applyAction(x, y, action)

        try:
            nextCell = grid[nextY][nextX]
        except IndexError:
            # edge of the map
            continue

        # valid move if the next cell isn't a wall
        if nextCell != "w": validActions.append(action)

    return validActions



def getPerpendicularActions(action):
    if action == Directions.NORTH:
        return [ Directions.WEST, Directions.EAST ]
    elif action == Directions.EAST:
        return [ Directions.NORTH, Directions.SOUTH ]
    elif action == Directions.SOUTH:
        return [ Directions.EAST, Directions.WEST ]
    elif action == Directions.WEST:
        return [ Directions.SOUTH, Directions.NORTH ]
    else:
        # action == Directions.STOP
        return []




def getExpectedUtilityOfValidActions(x, y, validActions, utilityGrid):
    # Probability that Pacman carries out the intended action
    directionProb = 0.8
    # Probability that Pacman carries out a perpendicular action
    perpendicularActionProbability = 0.5 * (1 - directionProb)


    actionExpectedUtilities = {}
    for action in validActions:
        if action == Directions.STOP:
            actionExpectedUtilities[action] = utilityGrid[y][x]
            continue

        actionGridCoordinate = applyAction(x, y, action)
        actionExpectedUtilities[action] = utilityGrid[actionGridCoordinate[1]][actionGridCoordinate[0]] * directionProb
        
        for perpendicularAction in getPerpendicularActions(action):
            perpendicularGridCoordinate = applyAction(x, y, perpendicularAction)
            perpendicularUtility = utilityGrid[perpendicularGridCoordinate[1]][perpendicularGridCoordinate[0]] * perpendicularActionProbability
            actionExpectedUtilities[action] = actionExpectedUtilities[action] + perpendicularUtility
    
    return actionExpectedUtilities





discountFactor = 0.1

def getReward(grid, x, y):
    # reward for non-terminal states
    # this is an incentive for taking the shortest route
    reward = -0.04

    if grid[y][x] == "g":
        reward += -100
    elif grid[y][x] == "f":
        reward += 100
    
    return reward

class Grid():
    def __init__(self, state):
        self.state = state
        # initialize 2d array with correct dimensions
        (w, h) = api.corners(state)[3]
        self.entityGrid = [[" " for x in range(w+1)] for y in range(h+1)]

        # populate known information
        (x,y) = api.whereAmI(state)
        self.entityGrid[y][x] = "p"

        for (x,y) in api.food(state):
            self.entityGrid[y][x] = "f"

        for (x,y) in api.capsules(state):
            self.entityGrid[y][x] = "c"

        for (x,y) in api.ghosts(state):
            self.entityGrid[int(y)][int(x)] = "g"

        for (x,y) in api.walls(state):
            self.entityGrid[y][x] = "w"
    
    def getEntityGrid(self):
        return self.entityGrid

    def generateUtilityGrid(self):
        utilityGrid = [[0 for x in range(len(self.entityGrid[0]))] for y in range(len(self.entityGrid))]

        for (x,y) in api.ghosts(self.state):
            utilityGrid[int(y)][int(x)] = -1

        for (x,y) in api.food(self.state):
            utilityGrid[y][x] = 10

        # threshold to stop iterations
        errorThreshold = 0
        # number of iterations adjusting the error
        iterations = 0

        done = False
        while not done:
            iterations = iterations + 1
            # maximum error found so far
            maxError = -1

            for column in range(len(utilityGrid)):
                for row in range(len(utilityGrid[0])):
                    oldUtility = utilityGrid[column][row]

                    validActions = getValidActions(self.entityGrid, row, column)
                    expectedUtilityActions = getExpectedUtilityOfValidActions(row, column, validActions, utilityGrid)
                    
                    # if edge of board with no valid moves
                    if not expectedUtilityActions.values():
                        continue
                    
                    reward = getReward(self.entityGrid, row, column)
                    newUtility = reward + (discountFactor * max(expectedUtilityActions.values()))

                    # update utility grid with new utility
                    utilityGrid[column][row] = newUtility

                    currError = abs(newUtility - oldUtility)
                    maxError = max(currError, maxError)
            
            if maxError <= errorThreshold:
                done = True            
        
        print "iterations"
        print iterations

        return utilityGrid


class MDPAgent(Agent):

    # Constructor: this gets run when we first invoke pacman.py
    def __init__(self):
        print "Starting up MDPAgent!"
        self.name = "Pacman"

    # Gets run after an MDPAgent object is created and once there is
    # game state to access.
    def registerInitialState(self, state):
        print "Running registerInitialState for MDPAgent!"
        print "I'm at:"
        grid = Grid(state)
        
        
    # This is what gets run in between multiple games
    def final(self, state):
        print "Looks like the game just ended!"


    # For now I just move randomly
    def getAction(self, state):
        grid = Grid(state)
        utilityGrid = grid.generateUtilityGrid()

        validActionUtilities = {}
        (x, y) = api.whereAmI(state)
        for action in getValidActions(grid.getEntityGrid(), x, y):
            if action == Directions.STOP: continue
            (newX, newY) = applyAction(x,y, action)
            validActionUtilities[action] = utilityGrid[newY][newX]
        
        printGrid(grid.getEntityGrid())
        printGrid(utilityGrid)
        
        rationalMove = max(validActionUtilities, key=validActionUtilities.get)
        return api.makeMove(rationalMove, validActionUtilities.keys())
