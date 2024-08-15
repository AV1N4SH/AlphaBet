#!/usr/bin/env python
from subprocess import call
import os
import sys
import random
import threading
import time
import math
from collections import deque
from itertools import product

class Dice:
	numsides = 6
	def __init__(self):
		#All dice start unrolled
		self.faceup = 0
	#rolling die randomizes faceup value
	def roll(self):
		self.faceup=random.randint(1,self.numsides)

class Liar:
	#Initial hand size
	numdice = 5
	def __init__(self,name):
		#Each Player starts with an empty hand
		self.hand =[]
		self.name = str(name)
		for x in range(self.numdice):
			self.gain()
	def lose(self):
		del self.hand[0]
	def gain(self):
		self.hand.append(Dice())
	def isActive(self):
		if len(self.hand)>0:
			return True
		else:
			return False
	def getDiceFaceUp(self):
		diceup=[]
		for dice in self.hand:
			diceup.append(dice.faceup)
		return diceup
	def bid(self):
		bid = (input("What will you bid?"))
		try:
			bid = eval(bid)
		except:
			pass
		return bid
	def rollAllDice(self):
		for die in self.hand:
			die.roll()

class Game:
	numPlayers = 4
	def __init__(self):
		self.Players = deque()
		#Setup Game
		for index in range(self.numPlayers):
			self.Players.append(Liar("Player " + str(index)))
		print("Game On")
		while (self.multiplePlayersRemaining()):
			players = self.Players
			newRound = Round(players)
			self.Players = newRound.playersleft
		print("Game Over! The last remaining player, " + str(self.Players[0].name) +" has "+str(len(self.Players[0].hand))+ "dice left!")

	def multiplePlayersRemaining(self):
		if (len(self.Players)>1):
			return True
		else:
			return False
		
class Round:
	def __init__(self,Players):
		#The Inaugural Bid of a round is Exactly 0 1's. This implementation not elegant but is at least functional in terms of betting hierachy
		#You could change the inaugural bid to be something else if you wanted in a metered game
		self.currentbid = (1,0,1)
		self.submittedbid = (1,0,1)
		self.bidhistory = []
		self.bidgrid=[]
		self.generateBidGrid(Players)
		for player in Players:
			player.rollAllDice()
		#Play is a function that is recursive if the Player bids, and has an exit condition upon challenge.
		#Let's Start Playing!
		self.play(Players)
		#Should Only Reach this condition upon challenge when play is over
		#Only enter condition if Exact Style Bid
		if self.currentbid[0]==1:
			if self.getActualDiceCount(Players)==self.currentbid[1]:
				print("The actual dice count is " + str(self.getActualDiceCount(Players)) + " " + str(self.currentbid[2]) + "'s! Challenger loses!")
				Players[0].lose()
				Players[-1].gain()
				if Players[0].hand==[]:
					print("You lose" + str(Players[0].name))
					del Players[0]
				#since the challenger lost, the play reverses since previous bettor was correct
				print("Play Reverses!")
				starter = [Players.popleft()]
				Players.reverse()
				Players.extendleft(starter)
			else:
				print("The actual dice count is " + str(self.getActualDiceCount(Players)) + " " + str(self.currentbid[2]) + "'s! ")	
				if ((self.getActualDiceCount(Players)<self.currentbid[1] and self.isChallengeUnder()) or (self.getActualDiceCount(Players)>self.currentbid[1] and self.isChallengeOver()) or (self.getActualDiceCount(Players)!=self.currentbid[1] and self.isChallengeStraight())):
					print("Challenger wins!")
					Players[-1].lose()
					if Players[-1].hand==[]:
						print("You lose" + str(Players[-1].name))
						del Players[1]
				else:
					print("Both Bidder and Challenger are wrong")
		#Otherwise, treat as normal
		else:
			if self.getActualDiceCount(Players)>=self.currentbid[1]:
				print("The actual dice count is " + str(self.getActualDiceCount(Players)) + " " + str(self.currentbid[2]) + "'s! Challenger loses!")
				Players[0].lose()
				if Players[0].hand==[]:
					print("You lose" + str(Players[0].name))
					del Players[0]
				starter = [Players.popleft()]
				#since the challenger lost, the rotation reverses since previous bettor was correct
				print("Play Reverses!")
				Players.reverse()
				Players.extendleft(starter)
			else:
				print("The actual dice count is " + str(self.getActualDiceCount(Players)) + " " + str(self.currentbid[2]) + "'s! Challenger wins!")
				Players[-1].lose()
				if Players[-1].hand==[]:
					print("You lose" + str(Players[-1].name))
					del Players[-1]
		print("This is the end of the Round")
		self.playersleft = Players
		print("The remaining players are")
		for player in self.playersleft:
			print(player.name)
	def generateBidGrid(self,Players):
		maxquantity = self.getTotalDiceInPlay(Players)
		maxvalue = Players[0].hand[0].numsides
		for d in range(maxquantity):
			self.bidgrid.append([])
		for n in range(maxvalue):
			lvl=1
			for b in self.bidgrid:
				b.append((lvl,n+1))
				lvl+=1
		return self.bidgrid

	def dice_match_probability(self,num_dice, num_sides, face1, face2, total_matches):
		"""
		Calculate the probability of getting a specific total number of matches to two face values.
		
		:param num_dice: Number of dice being rolled
		:param num_sides: Number of sides on each die
		:param face1: First face value we're looking for
		:param face2: Second face value we're looking for
		:param total_matches: The total number of dice showing either face1 or face2
		:return: The probability as a float between 0 and 1
		"""
		if total_matches > num_dice:
			return 0.0
		
		# Probability of rolling either face1 or face2 on a single die
		p_match = 2 / num_sides if face1 != face2 else 1 / num_sides
		
		# Probability of not rolling either face1 or face2 on a single die
		p_no_match = 1 - p_match
		
		# Use the binomial probability formula
		probability = (
			math.comb(num_dice, total_matches) * 
			(p_match ** total_matches) * 
			(p_no_match ** (num_dice - total_matches))
		)
		
		return probability

	def printBidGrid(self):
		for row in self.bidgrid:
			print(row)
			print('\n')
	def generateProbabidity(self,bid,Players):
		matches=0
		dicesfaceup = Players[0].getDiceFaceUp()
		for face in dicesfaceup:
			if face==bid[1] or face==6:
				matches+=1
		if matches >= bid[0]:
			return str(100)+"%"
		else:
			needed = bid[0] - matches
			outstanding = self.getTotalDiceInPlay(Players) - len(Players[0].hand)
			return str(round(((self.dice_match_probability(outstanding,Players[0].hand[0].numsides,bid[1],6,needed))*100),2))+"%"
	
	def printProbabidityGrid(self,Players):
		probabiditygrid=[]
		for row in self.bidgrid:
			probabidityrow = []
			for bid in row:
				probabidityrow.append(self.generateProbabidity(bid,Players))
			probabiditygrid.append(probabidityrow)
		for row in probabiditygrid:
			print(row)
			print('\n')
			
	def play(self,Players):
		#In productionalized game form, probabidity grid will be overlayed over bid grid
		self.printBidGrid()
		self.printProbabidityGrid(Players)
		self.submitBidRequest(Players,self.currentbid)
		submittedbid = Players[0].bid()
		if (self.isValidBidFormat(submittedbid) and self.isValidBidPrecision(submittedbid,Players)):
			print("this is a valid bidformat")
			self.submittedbid = submittedbid
			#Technically, a challenge is just a bid of either (0,0,0) (1,0,0) or (0,0,1)
			if (self.isValidChallenge()==False):
				if (self.isValidRaise()):
					if (self.submittedbid[0]==0):
						print(Players[0].name + " bet " + str(self.submittedbid[1]) + " " + str(self.submittedbid[2]) + "'s!")
					else:
						print(Players[0].name + " bet exactly " + str(self.submittedbid[1]) + " " + str(self.submittedbid[2]) + "'s!")
					#Add the currentbid to the bidhistory
					self.bidhistory.append(self.currentbid)
					print("Appending " + str(self.currentbid) + "to the bid history. The complete bid history is as follows")
					print(str(self.bidhistory))
					#Make the submitted bid the newly established currentbid of the round
					self.currentbid = self.submittedbid
					#shift to the next player
					Players.rotate(-1)
				#Technically whether or not you submit a valid raise, play continues.
				self.play(Players)
			#Play ends if it's a valid challenge
			pass
		else:
			#Play again if you submitted bad format bid
			self.play(Players)
			
	def isValidChallenge(self):
		#Challenging a non exact bid should be (0,0,0)
		if (self.isChallengeStraight() and self.inHistory(self.currentbid)):
			print("You must indicate over or under!")
			return False
		#Since challenges are Over (1,0,0) Under (0,0,1) and Straight (0,0,0) the second element will always be 0 if it is a challenge, and greater than zero if it's a bid
		if (self.submittedbid[1]>0):
			return False
		else:
			return True
	def inHistory(self,bid):
		bidlist = list(bid)
		bidlist[0] = 0
		bid = tuple(bidlist)
		if bid in self.bidhistory:
			print(str(self.currentbid[1]) + " " + str(self.currentbid[2]) + "'s is in the bid history")
			return True
		else:
			print(str(self.currentbid[1]) + " " + str(self.currentbid[2]) + "'s is not in the bid history")
			return False
	def isChallengeStraight(self):
		if (self.submittedbid[0]==0 and self.submittedbid[1]==0 and self.submittedbid[2]==0):
			return True
		else:
			return False
	def isChallengeUnder(self):
		if (self.submittedbid[0]==0 and self.submittedbid[1]==0 and self.submittedbid[2]==1):
			return True
		else:
			return False
	def isChallengeOver(self):
		if (self.submittedbid[0]==1 and self.submittedbid[1]==0 and self.submittedbid[2]==0):
			return True
		else:
			return False

	def isValidBidFormat(self,bid):
		if str(type(bid))!="<class 'tuple'>":
			#Reject immediately if wrong type
			print("The bid must be a 3 length tuple of 3 integers")
			return False
		if (len(bid)>3 or len(bid)<3):
			print("The bid must be a 3 length tuple of 3 integers")
			return False
		for bidpart in bid:
			if (str(type(bidpart))!="<class 'int'>" or bidpart<0):
				print("Each element in the bid list must be a positive integer.")
				return False
			pass
		return True
	def isValidBidPrecision(self,bid,Players):
		if (bid[0]==1 or bid[0]==0):
			for player in Players:
				if player.isActive():
					if bid[2]<=player.hand[0].numsides:
						return True
					else:
						print("You are betting a magnitude too high!")
						return False
		else:
			print("The first integer must be a 0 or 1, representing an 'at least' or 'exact' type bet accordingly. The third digit refers to the magnitude.")
			return False			
	def isValidRaise(self):
		#accept the bid if the quantity or face value is raised without reducing the quantity
		if self.submittedbid[1]>self.currentbid[1] or (self.submittedbid[1]==self.currentbid[1] and self.submittedbid[0]>self.currentbid[0]) or (self.submittedbid[0]==self.currentbid[0] and self.submittedbid[1]==self.currentbid[1] and self.submittedbid[2]>self.currentbid[2]):
			return True
		else:
			if (self.isChallengeOver() or self.isChallengeStraight() or self.isChallengeUnder()):
				print("This is an Invalid Challenge")
			else:
				print("The submitted bid is not a valid raise. You must raise either the face value or dice quantity but you cannot ever reduce the quantity")
			return False

	def getTotalDiceInPlay(self,players):
		sum = 0
		for x in players:
			sum = sum + len(x.hand)
		return sum
	def getActualDiceCount(self,players):
		sum = 0
		for player in players:
			for dice in player.hand:
				#The reason 6 is currently treated as wild is because my bid ranking is primitive
				#All it does is check to see if it's higher or lower, so wild should be highest
				if (dice.faceup==self.currentbid[2] or dice.faceup==6):
					sum = sum+1
		return sum
	def submitBidRequest(self,players,currentbid):
		print(str(players[0].name) + ", Your hand is " + str(players[0].getDiceFaceUp()) + " and there are currently "+ str(self.getTotalDiceInPlay(players)) + " dice in play with a current bid of " + str(currentbid))
new = Game()