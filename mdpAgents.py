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


class MDPAgent(Agent):

    # Constructor: this gets run when we first invoke pacman.py
    def __init__(self):
        print "Starting up MDPAgent!"
        self.name = "Pacman"
        # keyvalue of directions and their movement vectors
        self.directions =     { Directions.NORTH: (0, 1),
                                Directions.SOUTH: (0, -1),
                                Directions.EAST:  (1, 0),
                                Directions.WEST:  (-1, 0),
                                Directions.STOP:  (0, 0)  }
        self.utilityGrid = None


    # Gets run after an MDPAgent object is created and once there is
    # game state to access.
    def registerInitialState(self, state):
        print "Running registerInitialState for MDPAgent!"


    # This is what gets run in between multiple games
    def final(self, state):
        print "Looks like the game just ended!"


    # Generates a 2d array of the entities in the pacman game
    def generateEntityGrid(self, state):
        # initialize 2d array with correct dimensions from state
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


    # Generates a 2d array of rewards of each coordinate
    def generateRewardGrid(self, state):
        # a negative incentive for non-terminal states
        # this is an incentive for taking the shortest route
        initialValue = -5
        # initialize 2d array with correct dimensions
        (w, h) = api.corners(state)[3]
        rewardGrid = [[initialValue for x in range(w+1)] for y in range(h+1)]

        ghosts = api.ghosts(state)
        foods = api.food(state)
        walls = api.walls(state)

        for (x,y) in foods:
            rewardGrid[y][x] = 100

        # fill a radius around each ghost with negative reward
        # size of radius dependent on number of foods remaining
        # pacman feels no fear when almost winning
        radius = 5 if len(foods) > 3 else 2
        for (x,y) in ghosts:
            self.floodFill(rewardGrid, int(x),int(y), radius)

        for (x,y) in walls:
            rewardGrid[y][x] = 0

        return rewardGrid
    

    # Generates expected utilities grid out of entities using value iteration
    def generateUtilityGrid(self, entityGrid, rewardGrid, utilityGrid=None):
        # if utility grid not provided, initialize all values to 0
        if not utilityGrid:
            utilityGrid = [[0 for x in range(len(entityGrid[0]))] for y in range(len(entityGrid))]

        # weighting of expected future utilities
        # impacts long term vs. short term
        discountFactor = 0.9
        # threshold to stop value iterations
        errorThreshold = 0.1

        done = False
        while not done:
            # maximum error found so far
            maxError = -1

            for column in range(len(utilityGrid)):
                for row in range(len(utilityGrid[0])):
                    oldUtility = utilityGrid[column][row]
                    expectedUtilityActions = {}

                    for direction in self.directions:
                        nextCoordinate = self.applyAction(row, column, direction)
                        
                        # Probability that Pacman carries out the intended action
                        directionProb = 0.8
                        # Probability that Pacman carries out a perpendicular action
                        perpendicularActionProbability = 0.5 * (1 - directionProb)

                        # move is invalid if out of grid or into a wall
                        if (
                            nextCoordinate[0] < 0 or
                            nextCoordinate[1] < 0 or
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
                        for perpendicularDirection in self.getPerpendicularDirections(direction):
                            perpendicularGridCoordinate = self.applyAction(row, column, perpendicularDirection)
                            # perpendicular action is invalid if it goes outside the grid
                            if (
                                perpendicularGridCoordinate[0] < 0 or
                                perpendicularGridCoordinate[1] < 0 or
                                perpendicularGridCoordinate[0] >= len(utilityGrid[0]) or
                                perpendicularGridCoordinate[1] >= len(utilityGrid)
                              ):
                                # if not a walkable square agent remains in same position
                                expectedUtilityActions[direction] = perpendicularActionProbability * utilityGrid[column][row]
                            else:
                                # if walkable movement, calculate expected utility of target position
                                perpendicularUtility = utilityGrid[perpendicularGridCoordinate[1]][perpendicularGridCoordinate[0]] * perpendicularActionProbability
                                expectedUtilityActions[direction] = expectedUtilityActions[direction] + perpendicularUtility

                    reward = rewardGrid[column][row]
                    newUtility = reward + (discountFactor * max(expectedUtilityActions.values()))

                    # update utility grid with new utility
                    utilityGrid[column][row] = newUtility

                    currError = abs(newUtility - oldUtility)
                    # keep only the highest error
                    maxError = max(currError, maxError)

            # Stop value iteration when error is under the set threshold
            # makes code run much faster if we allow for a small error
            if maxError <= errorThreshold:
                done = True            

        return utilityGrid


    # Gets next action for pacman to perform
    def getAction(self, state):
        entityGrid = self.generateEntityGrid(state)
        rewardGrid = self.generateRewardGrid(state)
        # pass old utility grid to initialize value iteration with an approximation
        self.utilityGrid = self.generateUtilityGrid(entityGrid, rewardGrid, self.utilityGrid)

        # keyvalue pair of actions and their respective expected utilities
        validActionUtilities = {}
        (x, y) = api.whereAmI(state)

        for action in api.legalActions(state):
            if action == Directions.STOP: continue
            (newX, newY) = self.applyAction(x,y, action)
            validActionUtilities[action] = self.utilityGrid[newY][newX]
        
        # self.printGrid(entityGrid)
        # self.printGrid(self.utilityGrid)
        # self.printGrid(rewardGrid)
        
        # the rational move is the one that maximizes the expected utility
        rationalMove = max(validActionUtilities, key=validActionUtilities.get)
        return api.makeMove(rationalMove, validActionUtilities.keys())


    ## Utility functions 

    # Formats then prints grids to terminal to help debugging
    def printGrid(self, grid):
        for column in list(reversed(grid)):
            print " ".join(map(str,column))
        print ""

    # Returns the coordinate after applying
    # the direction provided as a vector movement
    def applyAction(self, x, y, direction):
        # gets vector movement of the direction
        vector = self.directions[direction]
        return (x + vector[0], y + vector[1])

    # Returns list of actions perpendicular to the one provided
    def getPerpendicularDirections(self, direction):
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

    # calculates manhatan distance between two coordinates
    def manhattanDistance(self, x1, y1, x2, y2):
        return int(abs(x1 - x2) + abs(y1 - y2))

    # flood fills grid with negative value up
    # to depth provided
    def floodFill(self, grid, x, y, depth):
        if depth > 0:
            try:
                grid[y][x] = -103
            except IndexError:
                # halt if cell doesn't exist
                return
            self.floodFill(grid, x, y+1, depth-1)
            self.floodFill(grid, x, y-1, depth-1)
            self.floodFill(grid, x+1, y, depth-1)
            self.floodFill(grid, x-1, y, depth-1)
