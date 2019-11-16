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

# def getValidActions(grid, location):
        

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
        print "No perpendicular actions"
        return []


def applyActionOnState(state, action):
    print "applying action on state"

# class UtilityGrid(Grid):





        

class Grid():
    def __init__(self, state):
        # initialize 2d array with correct dimensions
        (w, h) = api.corners(state)[3]
        self.entityGrid = [[" " for x in range(w+1)] for y in range(h+1)]
        self.utilityGrid = [[0 for x in range(w+1)] for y in range(h+1)]

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

    def printEntityGrid(self):
        print "Print entityGrid"
        for column in list(reversed(self.entityGrid)):
            print ' '.join(column)
        print "Done"

    def generateUtilityGrid(self):
        utilityGrid = [[0 for x in range(len(self.entityGrid))] for y in range(len(self.entityGrid))]

        print "griid"
        for column in list(reversed(self.utilityGrid)):
            print ' '.join(str(column))

        # for (x,y) in api.ghosts(state):
        #     self.grid[int(y)][int(x)] = -1
        
        # threshold to stop iterations
        # delta = 0
        # deltaSmallerAfterIteration = False
        # while not deltaSmallerAfterIteration:
        #     for column in self.grid:
        #         for cell in column:
        #             oldUtility = cell


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
        grid.printEntityGrid()
        
        
    # This is what gets run in between multiple games
    def final(self, state):
        print "Looks like the game just ended!"
        grid = Grid(state)
        grid.printEntityGrid()

        grid.generateUtilityGrid()


    # For now I just move randomly
    def getAction(self, state):
        # Get the actions we can try, and remove "STOP" if that is one of them.
        legal = api.legalActions(state)
        # print state.legalActions(state)
        if Directions.STOP in legal:
            legal.remove(Directions.STOP)
        # Random choice between the legal options.      
        grid = Grid(state)
        grid.printEntityGrid()
        return api.makeMove(random.choice(legal), legal)




    # value iteration MDP

    # 
    discountFactor = 0.01

    # Probability that Pacman carries out the intended action
    directionProb = 0.8
    # Probability that Pacman carries out a perpendicular action
    perpendicularActionProbability = 0.5 * (1 - directionProb)
    
    # reward for non-terminal states
    # this is an incentive for taking the shortest route
    reward = -0.04

    # utility value of each fruit
    # maybe each fruit utility is a fraction of 1?
    foodUtility = 1

    # utility value of each ghost
    # maybe each ghost utility should be a fraction of -1?
    ghostUtility = -1




    
    

    def getKeyFromValue(self, dict, value):
        for k, v in dict.items():
            if v == value:
                return k
        raise ValueError("No key found")


    def getExpectedUtilityOfState(self, state):
        validActions = getValidActions(state)
        expectedUtility = {}

        # cache a few recursive calls to make it more performant?
        for action in validActions:
            nextState = applyActionOnState(state, action)
            nextStateUtility = getExpectedUtilityOfState(nextState)

            # probability of intended action times its utility
            expectedUtility[action] = directionProb * expectedUtility[action]

            # probability of perpendicular actions times their utilities
            perpendicularActions = getPerpendicularActions(action)
            for pAction in perpendicularActions:
                expectedUtility[pAction] += perpendicularActionProbability * expectedUtility[pAction]

        

        # the rational action is the one that maximizes the expected utility
        rationalAction = getKeyFromValue(max(expectedUtility.values()))

        utility = reward + (discountFactor * rationalAction)

        print "utility of state", expectedUtility
        return expectedUtility
