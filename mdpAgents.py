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


def getPerpendicularDirections(direction):
    if direction == Directions.NORTH:
        return [ Directions.WEST, Directions.EAST ]
    elif direction == Directions.EAST:
        return [ Directions.NORTH, Directions.SOUTH ]
    elif direction == Directions.SOUTH:
        return [ Directions.EAST, Directions.WEST ]
    elif direction == Directions.WEST:
        return [ Directions.SOUTH, Directions.NORTH ]
    else:
        # direction == Directions.STOP
        return []



def getReward(grid, x, y):
    # reward for non-terminal states
    # this is an incentive for taking the shortest route
    reward = -5.04

    if grid[y][x] == "g":
        reward += -100
    elif grid[y][x] == "f":
        reward += 100
    elif grid[y][x] == "w":
        reward = 0
    
    return reward

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
        
    # This is what gets run in between multiple games
    def final(self, state):
        print "Looks like the game just ended!"


    def generateEntityGrid(self, state):
        # initialize 2d array with correct dimensions
        (w, h) = api.corners(state)[3]
        entityGrid = [[" " for x in range(w+1)] for y in range(h+1)]

        # populate known information
        (x,y) = api.whereAmI(state)
        entityGrid[y][x] = "p"

        for (x,y) in api.food(state):
            entityGrid[y][x] = "f"

        for (x,y) in api.capsules(state):
            entityGrid[y][x] = "c"

        for (x,y) in api.ghosts(state):
            entityGrid[int(y)][int(x)] = "g"

        for (x,y) in api.walls(state):
            entityGrid[y][x] = "w"
        
        return entityGrid

    
    def generateUtilityGrid(self, entityGrid):
        utilityGrid = [[0 for x in range(len(entityGrid[0]))] for y in range(len(entityGrid))]

        # threshold to stop iterations
        errorThreshold = 0.5
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
                    expectedUtilityActions = {}

                    for direction in directions:
                        nextCoordinate = applyAction(row, column, direction)
                        
                        # Probability that Pacman carries out the intended action
                        directionProb = 0.8
                        # Probability that Pacman carries out a perpendicular action
                        perpendicularActionProbability = 0.5 * (1 - directionProb)


                        # move is invalid if out of grid or into a wall
                        if (
                            nextCoordinate[0] < 0 or nextCoordinate[1] < 0 or
                            nextCoordinate[0] >= len(utilityGrid[0]) or
                            nextCoordinate[1] >= len(utilityGrid) or
                            entityGrid[nextCoordinate[1]][nextCoordinate[0]] == "w"
                           ):
                            # invalid move means agent remains on same square
                            expectedUtilityActions[direction] = directionProb * utilityGrid[column][row]
                        else:
                            # move is valid and agents utility is of new position
                            expectedUtilityActions[direction] = directionProb * utilityGrid[nextCoordinate[1]][nextCoordinate[0]]
                        
                        # add expected utility of perpendicular actions
                        for perpendicularDirection in getPerpendicularDirections(direction):
                            perpendicularGridCoordinate = applyAction(row, column, perpendicularDirection)
                            if (
                                nextCoordinate[0] < 0 or nextCoordinate[1] < 0 or
                                nextCoordinate[0] >= len(utilityGrid[0]) or
                                nextCoordinate[1] >= len(utilityGrid) or
                                entityGrid[nextCoordinate[1]][nextCoordinate[0]] == "w"
                              ):
                                # if not a walkable square agent remains in same position
                                expectedUtilityActions[direction] = perpendicularActionProbability * utilityGrid[column][row]
                            else:
                                # if walkable movement, calculate expected utility of target position
                                perpendicularUtility = utilityGrid[perpendicularGridCoordinate[1]][perpendicularGridCoordinate[0]] * perpendicularActionProbability
                                expectedUtilityActions[direction] = expectedUtilityActions[direction] + perpendicularUtility

                    reward = getReward(entityGrid, row, column)
                    discountFactor = 0.7

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


    def getAction(self, state):
        entityGrid = self.generateEntityGrid(state)
        utilityGrid = self.generateUtilityGrid(entityGrid)

        validActionUtilities = {}
        (x, y) = api.whereAmI(state)
        for action in api.legalActions(state):
            # if action == Directions.STOP: continue
            (newX, newY) = applyAction(x,y, action)
            validActionUtilities[action] = utilityGrid[newY][newX]
        
        printGrid(entityGrid)
        printGrid(utilityGrid)
        
        rationalMove = max(validActionUtilities, key=validActionUtilities.get)
        return api.makeMove(rationalMove, validActionUtilities.keys())
